"""
Reranking Agent Node
Intelligently orders search results using hybrid approach (algorithmic + LLM)
"""

import logging
from typing import Any, Dict, List, Tuple
from typing_extensions import Literal
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.types import Command
import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import AgentState, update_agent_status, track_task, add_agent_error, CacheManager
from redis_config import (
    RERANKING_STRATEGY,
    RERANKING_MODEL,
    MAX_RANKED_RESULTS,
    ENABLE_RERANKING
)

logger = logging.getLogger(__name__)


class RerankingAgent:
    """
    Reranks verified results using hybrid approach (algorithmic scoring + LLM semantic understanding)
    """

    @staticmethod
    def calculate_price_score(result: Dict[str, Any], user_preferences: Dict[str, Any] = None) -> float:
        """
        Calculate price-based score

        Args:
            result: Result dictionary
            user_preferences: User preferences including max_price

        Returns:
            Price score (0-100)
        """
        price_str = result.get("price", "")

        if not price_str:
            return 50.0  # Neutral score if no price

        try:
            # Extract numeric price (handle formats like "$99.99", "99.99", etc.)
            price_match = re.search(r'[\d,]+\.?\d*', str(price_str).replace(',', ''))
            if not price_match:
                return 50.0

            price = float(price_match.group())

            # Check against user's max price preference
            max_price = user_preferences.get("max_price") if user_preferences else None

            if max_price:
                if price > max_price:
                    return 0.0  # Over budget, lowest score
                # Score based on how far below max price
                score = ((max_price - price) / max_price) * 100
                return min(score, 100.0)

            # If no max price, prefer lower prices (relative scoring)
            # Assuming typical range of $0-$1000
            max_expected = 1000.0
            score = 100.0 - ((price / max_expected) * 100)
            return max(score, 0.0)

        except (ValueError, AttributeError):
            return 50.0

    @staticmethod
    def calculate_discount_score(result: Dict[str, Any]) -> float:
        """
        Calculate discount-based score

        Args:
            result: Result dictionary

        Returns:
            Discount score (0-100)
        """
        # Check for discount information
        discount_str = result.get("discount", "")
        original_price = result.get("originalPrice")
        current_price = result.get("price")

        # Try to extract discount percentage
        if discount_str:
            try:
                # Extract percentage (e.g., "20% off" -> 20)
                percent_match = re.search(r'(\d+)%', str(discount_str))
                if percent_match:
                    discount_percent = float(percent_match.group(1))
                    return min(discount_percent, 100.0)
            except (ValueError, AttributeError):
                pass

        # Calculate from original vs current price
        if original_price and current_price:
            try:
                orig_match = re.search(r'[\d,]+\.?\d*', str(original_price).replace(',', ''))
                curr_match = re.search(r'[\d,]+\.?\d*', str(current_price).replace(',', ''))

                if orig_match and curr_match:
                    orig = float(orig_match.group())
                    curr = float(curr_match.group())

                    if orig > curr:
                        discount_percent = ((orig - curr) / orig) * 100
                        return min(discount_percent, 100.0)
            except (ValueError, AttributeError):
                pass

        # No discount information
        return 0.0

    @staticmethod
    def calculate_rating_score(result: Dict[str, Any]) -> float:
        """
        Calculate rating-based score

        Args:
            result: Result dictionary

        Returns:
            Rating score (0-100)
        """
        rating = result.get("rating")

        if not rating:
            return 50.0  # Neutral score if no rating

        try:
            rating_float = float(rating)
            # Convert 0-5 star rating to 0-100 score
            return (rating_float / 5.0) * 100
        except (ValueError, TypeError):
            return 50.0

    @staticmethod
    def calculate_freshness_score(result: Dict[str, Any]) -> float:
        """
        Calculate freshness/recency score

        Args:
            result: Result dictionary

        Returns:
            Freshness score (0-100)
        """
        # Use verification score as proxy for freshness
        # Results with accessible URLs are likely more current
        if result.get("url_valid", True):
            return 80.0
        return 40.0

    @staticmethod
    def calculate_algorithmic_score(
        result: Dict[str, Any],
        user_preferences: Dict[str, Any] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate overall algorithmic score

        Args:
            result: Result dictionary
            user_preferences: User preferences

        Returns:
            Tuple of (overall_score, factor_scores)
        """
        # Calculate individual factor scores
        price_score = RerankingAgent.calculate_price_score(result, user_preferences)
        discount_score = RerankingAgent.calculate_discount_score(result)
        rating_score = RerankingAgent.calculate_rating_score(result)
        verification_score = result.get("verification_score", 50.0)
        relevance_score = result.get("relevance_score", 50.0)
        freshness_score = RerankingAgent.calculate_freshness_score(result)

        # Factor weights (configurable)
        weights = {
            "price": 0.25,
            "discount": 0.20,
            "rating": 0.15,
            "verification": 0.15,
            "relevance": 0.15,
            "freshness": 0.10,
        }

        # Calculate weighted score
        overall_score = (
            price_score * weights["price"] +
            discount_score * weights["discount"] +
            rating_score * weights["rating"] +
            verification_score * weights["verification"] +
            relevance_score * weights["relevance"] +
            freshness_score * weights["freshness"]
        )

        factor_scores = {
            "price": price_score,
            "discount": discount_score,
            "rating": rating_score,
            "verification": verification_score,
            "relevance": relevance_score,
            "freshness": freshness_score,
        }

        return overall_score, factor_scores

    @staticmethod
    async def llm_semantic_rerank(
        results: List[Dict[str, Any]],
        query: str,
        top_k: int = MAX_RANKED_RESULTS
    ) -> List[Tuple[int, float, str]]:
        """
        Use LLM to semantically understand query and adjust rankings

        Args:
            results: List of results with algorithmic scores
            query: Original user query
            top_k: Number of top results to focus on

        Returns:
            List of (result_index, llm_boost, reasoning) tuples
        """
        if not results:
            return []

        try:
            model = ChatOpenAI(model=RERANKING_MODEL, temperature=0)

            # Prepare results summary for LLM
            results_summary = "\n".join([
                f"{i+1}. {r.get('title', 'No title')} - {r.get('price', 'No price')} "
                f"(Store: {r.get('store', 'Unknown')}, Score: {r.get('algorithmic_score', 0):.1f})"
                for i, r in enumerate(results[:top_k])
            ])

            prompt = f"""You are a shopping assistant helping rank product deals based on user intent.

User Query: "{query}"

Current Top Results (ranked algorithmically):
{results_summary}

Analyze the user's query to understand their intent and preferences. For each result, provide:
1. A semantic relevance boost score (+/- 20 points)
2. Brief reasoning (one sentence)

Consider:
- Product type match with query
- Brand preferences implied in query
- Feature requirements mentioned
- Value proposition (price vs quality)

Respond in this exact format for each result:
1. Boost: [number], Reason: [reason]
2. Boost: [number], Reason: [reason]
...

Keep boosts between -20 and +20."""

            response = await model.ainvoke(prompt)
            content = response.content

            # Parse LLM response
            adjustments = []
            lines = content.strip().split('\n')

            for line in lines:
                # Parse format: "1. Boost: 10, Reason: Great match"
                match = re.match(r'(\d+)\.\s*Boost:\s*([+-]?\d+),\s*Reason:\s*(.+)', line)
                if match:
                    idx = int(match.group(1)) - 1  # Convert to 0-based index
                    boost = float(match.group(2))
                    reason = match.group(3).strip()

                    # Clamp boost to -20 to +20
                    boost = max(-20, min(20, boost))

                    adjustments.append((idx, boost, reason))

            logger.info(f"✅ LLM provided {len(adjustments)} ranking adjustments")
            return adjustments

        except Exception as e:
            logger.error(f"❌ LLM reranking error: {str(e)}")
            return []

    @staticmethod
    async def rerank_results(
        results: List[Dict[str, Any]],
        query: str,
        user_preferences: Dict[str, Any] = None,
        strategy: str = RERANKING_STRATEGY
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Rerank results using specified strategy

        Args:
            results: List of verified results
            query: Original search query
            user_preferences: User preferences
            strategy: "llm", "hybrid", or "algorithmic"

        Returns:
            Tuple of (ranked_results, ranking_metadata)
        """
        if not results:
            return [], {"strategy": strategy, "count": 0}

        # Step 1: Calculate algorithmic scores for all results
        scored_results = []
        for result in results:
            algo_score, factor_scores = RerankingAgent.calculate_algorithmic_score(result, user_preferences)
            scored_result = {
                **result,
                "algorithmic_score": algo_score,
                "factor_scores": factor_scores
            }
            scored_results.append(scored_result)

        # Step 2: Apply strategy-specific ranking
        if strategy == "algorithmic":
            # Pure algorithmic ranking
            ranked_results = sorted(scored_results, key=lambda x: x["algorithmic_score"], reverse=True)
            final_scores = [r["algorithmic_score"] for r in ranked_results]
            confidence = 0.7  # Moderate confidence for algorithmic-only

        elif strategy == "llm":
            # Pure LLM-based ranking
            llm_adjustments = await RerankingAgent.llm_semantic_rerank(scored_results, query)

            # Apply LLM boosts
            for idx, boost, reason in llm_adjustments:
                if 0 <= idx < len(scored_results):
                    scored_results[idx]["llm_boost"] = boost
                    scored_results[idx]["llm_reason"] = reason

            ranked_results = sorted(scored_results, key=lambda x: x.get("llm_boost", 0), reverse=True)
            final_scores = [r.get("llm_boost", 0) for r in ranked_results]
            confidence = 0.85  # Higher confidence with LLM

        else:  # hybrid (default)
            # Combine algorithmic + LLM
            llm_adjustments = await RerankingAgent.llm_semantic_rerank(scored_results, query)

            # Apply LLM boosts to algorithmic scores
            for idx, boost, reason in llm_adjustments:
                if 0 <= idx < len(scored_results):
                    scored_results[idx]["llm_boost"] = boost
                    scored_results[idx]["llm_reason"] = reason
                    scored_results[idx]["final_score"] = scored_results[idx]["algorithmic_score"] + boost
                else:
                    scored_results[idx]["llm_boost"] = 0
                    scored_results[idx]["llm_reason"] = "No LLM adjustment"
                    scored_results[idx]["final_score"] = scored_results[idx]["algorithmic_score"]

            # Ensure all results have final_score
            for result in scored_results:
                if "final_score" not in result:
                    result["llm_boost"] = 0
                    result["llm_reason"] = "No LLM adjustment"
                    result["final_score"] = result["algorithmic_score"]

            ranked_results = sorted(scored_results, key=lambda x: x["final_score"], reverse=True)
            final_scores = [r["final_score"] for r in ranked_results]
            confidence = 0.9  # Highest confidence with hybrid

        # Limit to top results
        ranked_results = ranked_results[:MAX_RANKED_RESULTS]

        # Create metadata
        metadata = {
            "strategy": strategy,
            "count": len(ranked_results),
            "confidence": confidence,
            "score_range": {
                "min": min(final_scores) if final_scores else 0,
                "max": max(final_scores) if final_scores else 0,
                "avg": sum(final_scores) / len(final_scores) if final_scores else 0
            }
        }

        logger.info(f"✅ Reranked {len(ranked_results)} results using {strategy} strategy")

        return ranked_results, metadata


async def reranking_agent(
    state: AgentState,
    config: RunnableConfig
) -> Command[Literal["synthesis_agent"]]:
    """
    Reranking Agent Node

    Intelligently orders verified results using hybrid approach.
    Combines algorithmic scoring with LLM semantic understanding.

    Args:
        state: Current agent state
        config: Runtime configuration

    Returns:
        Command to route to synthesis agent
    """
    logger.info("🔄 Reranking Agent activated")

    # Check if reranking is enabled
    if not ENABLE_RERANKING:
        logger.info("⏭️  Reranking disabled, passing through verified results")
        return Command(
            goto="synthesis_agent",
            update={
                "ranked_results": state.get("verified_results", []),
                "reranking_summary": "Reranking disabled",
                "agent_status": {**state.get("agent_status", {}), "reranking_agent": "skipped"},
            }
        )

    # Update agent status
    state = update_agent_status(state, "reranking_agent", "running")
    state = track_task(state, "rerank")

    # Get verified results
    verified_results = state.get("verified_results", [])

    if not verified_results:
        logger.warning("⚠️  No verified results to rerank")
        return Command(
            goto="synthesis_agent",
            update={
                "ranked_results": [],
                "reranking_summary": "No results to rerank",
                "agent_status": {**state.get("agent_status", {}), "reranking_agent": "no_data"},
            }
        )

    try:
        # Get original query
        query = ""
        from langchain_core.messages import HumanMessage
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                query = msg.content
                break

        # Rerank results
        reranker = RerankingAgent()
        ranked_results, metadata = await reranker.rerank_results(
            verified_results,
            query,
            state.get("user_preferences", {}),
            strategy=RERANKING_STRATEGY
        )

        # Cache ranked results
        if state.get("session_id"):
            cache_manager = CacheManager()
            cache_manager.save_ranked_results(state["session_id"], ranked_results)

        # Create summary string
        summary_str = (
            f"Reranked {metadata['count']} results using {metadata['strategy']} strategy. "
            f"Confidence: {metadata['confidence']:.2f}. "
            f"Score range: {metadata['score_range']['min']:.1f} - {metadata['score_range']['max']:.1f}"
        )

        logger.info(f"✅ {summary_str}")

        # Update agent status
        state = update_agent_status(state, "reranking_agent", "completed")

        return Command(
            goto="synthesis_agent",
            update={
                "ranked_results": ranked_results,
                "reranking_summary": summary_str,
                "reranking_confidence": metadata["confidence"],
                "reranking_factors": metadata.get("score_range", {}),
                "agent_status": state.get("agent_status", {}),
                "current_agent": "reranking_agent",
            }
        )

    except Exception as e:
        logger.error(f"❌ Reranking agent error: {str(e)}")
        state = add_agent_error(state, "reranking_agent", str(e))

        # On error, pass through verified results
        return Command(
            goto="synthesis_agent",
            update={
                "ranked_results": verified_results[:MAX_RANKED_RESULTS],
                "reranking_summary": f"Reranking failed, using verification order: {str(e)}",
                "agent_status": {**state.get("agent_status", {}), "reranking_agent": "failed"},
                "agent_errors": state.get("agent_errors", []),
            }
        )
