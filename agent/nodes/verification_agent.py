"""
Verification Agent Node
Validates search results for quality, relevance, and data completeness
"""

import logging
import requests
from typing import Any, Dict, List, Tuple
from typing_extensions import Literal
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import AgentState, update_agent_status, track_task, add_agent_error
from redis_config import (
    VERIFICATION_STRICTNESS,
    VERIFICATION_TIMEOUT,
    MAX_VERIFICATION_RETRIES,
    MAX_VERIFIED_RESULTS,
    ENABLE_VERIFICATION
)

logger = logging.getLogger(__name__)


class VerificationAgent:
    """
    Verifies the quality and validity of search results
    """

    @staticmethod
    def verify_url_accessibility(url: str, timeout: int = VERIFICATION_TIMEOUT) -> Tuple[bool, str]:
        """
        Check if URL is accessible

        Args:
            url: URL to check
            timeout: Request timeout in seconds

        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code == 200:
                return True, "URL accessible"
            elif response.status_code == 404:
                return False, "Page not found (404)"
            elif response.status_code >= 500:
                return False, f"Server error ({response.status_code})"
            else:
                return True, f"Accessible with status {response.status_code}"
        except requests.Timeout:
            return False, "Request timeout"
        except requests.ConnectionError:
            return False, "Connection failed"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"

    @staticmethod
    def verify_data_completeness(result: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Check if result has all required fields

        Args:
            result: Result dictionary to verify

        Returns:
            Tuple of (is_complete, completeness_score, reason)
        """
        required_fields = ["title", "url"]
        important_fields = ["price", "store", "content"]
        optional_fields = ["rating", "discount", "originalPrice"]

        missing_required = [f for f in required_fields if not result.get(f)]
        missing_important = [f for f in important_fields if not result.get(f)]

        if missing_required:
            return False, 0.0, f"Missing required fields: {', '.join(missing_required)}"

        # Calculate completeness score
        total_fields = len(required_fields) + len(important_fields) + len(optional_fields)
        present_fields = sum([
            len([f for f in required_fields if result.get(f)]),
            len([f for f in important_fields if result.get(f)]),
            len([f for f in optional_fields if result.get(f)])
        ])

        completeness_score = (present_fields / total_fields) * 100

        if VERIFICATION_STRICTNESS == "strict":
            if missing_important:
                return False, completeness_score, f"Missing important fields: {', '.join(missing_important)}"
        elif VERIFICATION_STRICTNESS == "moderate":
            if len(missing_important) > 1:  # Allow 1 missing important field
                return False, completeness_score, f"Too many missing fields: {', '.join(missing_important)}"

        return True, completeness_score, "Data complete"

    @staticmethod
    def calculate_relevance_score(result: Dict[str, Any], query: str = "") -> float:
        """
        Calculate relevance score for a result

        Args:
            result: Result dictionary
            query: Original search query

        Returns:
            Relevance score (0-100)
        """
        score = 50.0  # Base score

        # Boost if has price information
        if result.get("price"):
            score += 15.0

        # Boost if has rating
        if result.get("rating"):
            rating = float(result.get("rating", 0))
            score += (rating / 5.0) * 10.0  # Up to 10 points

        # Boost if has discount
        if result.get("discount") or result.get("originalPrice"):
            score += 10.0

        # Boost if from known retailer
        known_retailers = ["amazon", "ebay", "walmart", "target", "bestbuy", "costco"]
        store = result.get("store", "").lower()
        if any(retailer in store for retailer in known_retailers):
            score += 10.0

        # Boost for title/content relevance if query provided
        if query:
            query_lower = query.lower()
            title_lower = result.get("title", "").lower()
            content_lower = result.get("content", "").lower()

            query_words = set(query_lower.split())
            title_words = set(title_lower.split())
            content_words = set(content_lower.split())

            # Calculate word overlap
            title_overlap = len(query_words & title_words) / max(len(query_words), 1)
            content_overlap = len(query_words & content_words) / max(len(query_words), 1)

            score += title_overlap * 5.0
            score += content_overlap * 2.0

        return min(score, 100.0)

    @staticmethod
    def verify_single_result(
        result: Dict[str, Any],
        query: str = "",
        check_url: bool = True
    ) -> Tuple[bool, float, str, Dict[str, Any]]:
        """
        Verify a single search result

        Args:
            result: Result to verify
            query: Original search query
            check_url: Whether to check URL accessibility

        Returns:
            Tuple of (is_valid, score, reason, verified_result)
        """
        # Check data completeness
        is_complete, completeness_score, completeness_reason = VerificationAgent.verify_data_completeness(result)

        if not is_complete:
            return False, completeness_score, completeness_reason, result

        # Check URL accessibility (if enabled and URL present)
        url_valid = True
        url_reason = "URL not checked"

        if check_url and result.get("url"):
            url_valid, url_reason = VerificationAgent.verify_url_accessibility(result["url"])

            if not url_valid and VERIFICATION_STRICTNESS == "strict":
                return False, completeness_score, f"URL invalid: {url_reason}", result

        # Calculate relevance score
        relevance_score = VerificationAgent.calculate_relevance_score(result, query)

        # Overall score (weighted average)
        overall_score = (completeness_score * 0.4) + (relevance_score * 0.6)

        # Determine if result passes verification
        min_score_threshold = {
            "strict": 75.0,
            "moderate": 60.0,
            "lenient": 40.0
        }.get(VERIFICATION_STRICTNESS, 60.0)

        is_valid = overall_score >= min_score_threshold and url_valid

        # Add verification metadata to result
        verified_result = {
            **result,
            "verified": is_valid,
            "verification_score": overall_score,
            "completeness_score": completeness_score,
            "relevance_score": relevance_score,
            "url_valid": url_valid,
            "verification_reason": url_reason if not url_valid else "Passed verification"
        }

        reason = f"Score: {overall_score:.1f} (threshold: {min_score_threshold})"
        return is_valid, overall_score, reason, verified_result

    @staticmethod
    def verify_batch(
        results: List[Dict[str, Any]],
        query: str = "",
        max_workers: int = 5
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Verify multiple results in parallel

        Args:
            results: List of results to verify
            query: Original search query
            max_workers: Number of parallel workers

        Returns:
            Tuple of (verified_results, verification_summary)
        """
        verified_results = []
        failed_results = []
        scores = []

        # Use ThreadPoolExecutor for parallel verification
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_result = {
                executor.submit(VerificationAgent.verify_single_result, result, query): result
                for result in results
            }

            for future in as_completed(future_to_result):
                try:
                    is_valid, score, reason, verified_result = future.result()
                    scores.append(score)

                    if is_valid:
                        verified_results.append(verified_result)
                    else:
                        failed_results.append({
                            "result": verified_result,
                            "reason": reason
                        })

                except Exception as e:
                    logger.error(f"Error verifying result: {str(e)}")

        # Create summary
        summary = {
            "total_input": len(results),
            "verified_count": len(verified_results),
            "filtered_count": len(failed_results),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "verification_strictness": VERIFICATION_STRICTNESS,
        }

        logger.info(f"✅ Verification complete: {summary['verified_count']}/{summary['total_input']} passed")

        return verified_results, summary


async def verification_agent(
    state: AgentState,
    config: RunnableConfig
) -> Command[Literal["reranking_agent", "synthesis_agent"]]:
    """
    Verification Agent Node

    Validates search results for quality, accessibility, and relevance.
    Filters out low-quality or invalid results.

    Args:
        state: Current agent state
        config: Runtime configuration

    Returns:
        Command to route to next agent
    """
    logger.info("✓ Verification Agent activated")

    # Check if verification is enabled
    if not ENABLE_VERIFICATION:
        logger.info("⏭️  Verification disabled, passing through all results")
        return Command(
            goto="reranking_agent",
            update={
                "verified_results": state.get("raw_search_results", []),
                "verification_summary": "Verification disabled",
                "agent_status": {**state.get("agent_status", {}), "verification_agent": "skipped"},
            }
        )

    # Update agent status
    state = update_agent_status(state, "verification_agent", "running")
    state = track_task(state, "verify")

    # Get raw search results
    raw_results = state.get("raw_search_results", [])

    # If no raw results in state, try to extract from recent tool messages
    if not raw_results and state["messages"]:
        from langchain_core.messages import ToolMessage
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage):
                # Parse tool results and create structured data
                raw_results = [{
                    "content": str(msg.content),
                    "source": "tool_execution",
                    "tool_name": getattr(msg, 'name', 'unknown'),
                    "url": "https://example.com",  # placeholder
                    "title": "Tool Result"
                }]
                logger.info(f"📥 Extracted {len(raw_results)} results from tool messages")
                break

    if not raw_results:
        logger.warning("⚠️  No raw search results to verify")
        return Command(
            goto="synthesis_agent",
            update={
                "verified_results": [],
                "verification_summary": "No results to verify",
                "agent_status": {**state.get("agent_status", {}), "verification_agent": "no_data"},
                "agent_errors": state.get("agent_errors", []) + [{
                    "agent": "verification_agent",
                    "error": "No raw search results available",
                    "task": "verify"
                }],
            }
        )

    try:
        # Get original query from messages
        query = ""
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'content') and hasattr(msg, '__class__') and 'HumanMessage' in str(msg.__class__):
                query = msg.content
                break

        # Verify results
        verifier = VerificationAgent()
        verified_results, summary = verifier.verify_batch(raw_results, query)

        # Limit to max verified results
        verified_results = verified_results[:MAX_VERIFIED_RESULTS]

        # Create summary string
        summary_str = (
            f"Verified {summary['verified_count']} out of {summary['total_input']} results. "
            f"Filtered {summary['filtered_count']} results. "
            f"Average score: {summary['average_score']:.1f}"
        )

        logger.info(f"✅ {summary_str}")

        # Update agent status
        state = update_agent_status(state, "verification_agent", "completed")

        # Route to reranking if we have results, otherwise to synthesis
        next_agent = "reranking_agent" if verified_results else "synthesis_agent"

        return Command(
            goto=next_agent,
            update={
                "verified_results": verified_results,
                "verification_summary": summary_str,
                "filtered_count": summary["filtered_count"],
                "agent_status": state.get("agent_status", {}),
                "current_agent": "verification_agent",
            }
        )

    except Exception as e:
        logger.error(f"❌ Verification agent error: {str(e)}")
        state = add_agent_error(state, "verification_agent", str(e))

        # On error, pass through raw results to next agent
        return Command(
            goto="synthesis_agent",
            update={
                "verified_results": raw_results[:MAX_VERIFIED_RESULTS],
                "verification_summary": f"Verification failed: {str(e)}",
                "agent_status": {**state.get("agent_status", {}), "verification_agent": "failed"},
                "agent_errors": state.get("agent_errors", []),
            }
        )
