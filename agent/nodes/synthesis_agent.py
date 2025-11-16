"""
Synthesis Agent Node
Generates final answer and updates UI with ranked results
"""

import logging
from typing import Any, Dict, List
from typing_extensions import Literal
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.graph import END
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import AgentState, update_agent_status, track_task, add_agent_error, get_session_manager

logger = logging.getLogger(__name__)


class SynthesisAgent:
    """
    Synthesizes final answer from ranked results and calls frontend actions
    """

    @staticmethod
    async def generate_answer(
        ranked_results: List[Dict[str, Any]],
        query: str,
        verification_summary: str = "",
        reranking_summary: str = ""
    ) -> str:
        """
        Generate comprehensive answer using GPT-4

        Args:
            ranked_results: Top-ranked results
            query: Original user query
            verification_summary: Summary from verification agent
            reranking_summary: Summary from reranking agent

        Returns:
            Generated answer string
        """
        if not ranked_results:
            return f"I couldn't find any deals for '{query}'. Try a different search or check back later for new deals."

        try:
            model = ChatOpenAI(model="gpt-4o", temperature=0.3)

            # Prepare results for context with numbered references
            results_context = "\n".join([
                f"#{r.get('result_number', i+1)}. **{r.get('clean_name') or r.get('title', 'Unknown Product')}**\n"
                f"   - Price: {r.get('price', 'N/A')}\n"
                f"   - Store: {r.get('store', 'Unknown')}\n"
                + (f"   - Original Price: {r.get('originalPrice', 'N/A')}, " if r.get('originalPrice') else "")
                + (f"Discount: {r.get('discount', 'N/A')}\n" if r.get('discount') else "\n")
                + f"   - Rating: {r.get('rating', 'N/A')}/5\n"
                f"   - Score: {r.get('final_score', r.get('verification_score', r.get('score', 0))):.1f}/100\n"
                f"   - URL: {r.get('url', 'N/A')}\n"
                + (f"   - Keywords: {', '.join(r.get('keywords', [])[:5])}\n" if r.get('keywords') else "")
                + (f"   - Content: {r.get('content', '')[:100]}...\n" if r.get('content') else "")
                for i, r in enumerate(ranked_results[:5])  # Top 5 for context
            ])

            prompt = f"""You are a helpful shopping assistant. Generate a comprehensive response about the best deals found.

User Query: "{query}"

Top Deals Found (numbered for easy reference):
{results_context}

Verification Summary: {verification_summary}
Ranking Summary: {reranking_summary}

Generate a helpful response that:
1. Summarizes the best deals found (top 3-5) using their numbers (e.g., "#1", "#2")
2. Highlights key value propositions (best price, highest rating, best discount)
3. **IMPORTANT**: Include product numbers in your summary so users can ask follow-up questions like "Tell me more about #2"
3. Provides actionable recommendations
4. Mentions any important caveats or considerations
5. Is concise but informative (2-3 paragraphs max)

Be enthusiastic but honest. Focus on helping the user make an informed decision."""

            response = await model.ainvoke(prompt)
            answer = response.content

            logger.info(f"✅ Generated answer ({len(answer)} chars)")
            return answer

        except Exception as e:
            logger.error(f"❌ Error generating answer: {str(e)}")
            # Fallback to simple summary
            return (
                f"Found {len(ranked_results)} deals for '{query}'. "
                f"Top deal: {ranked_results[0].get('title')} at {ranked_results[0].get('price')} "
                f"from {ranked_results[0].get('store')}."
            )

    @staticmethod
    def format_deal_for_frontend(result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a result for frontend display with numbered reference

        Args:
            result: Result dictionary

        Returns:
            Formatted deal for frontend
        """
        return {
            "resultNumber": result.get("result_number"),  # Add number for reference
            "resultId": result.get("result_id"),  # Add unique ID
            "title": result.get("title", "Unknown Product"),
            "cleanName": result.get("clean_name"),  # Add clean name
            "price": result.get("price", "N/A"),
            "originalPrice": result.get("originalPrice"),
            "discount": result.get("discount"),
            "url": result.get("url", "#"),
            "store": result.get("store", "Unknown Store"),
            "rating": result.get("rating"),
            "image": result.get("image"),
            "score": result.get("final_score", result.get("verification_score", result.get("score", 0))),
            "verified": result.get("verified", True),
            "keywords": result.get("keywords", []),  # Add keywords for search
            "descriptors": result.get("descriptors", {}),  # Add descriptors
        }

    @staticmethod
    def create_price_comparison(ranked_results: List[Dict[str, Any]], product_name: str) -> Dict[str, Any]:
        """
        Create price comparison data from results

        Args:
            ranked_results: Ranked results list
            product_name: Product name for comparison

        Returns:
            Price comparison dictionary
        """
        prices = []
        for result in ranked_results[:10]:  # Top 10 for comparison
            prices.append({
                "store": result.get("store", "Unknown"),
                "price": result.get("price", "N/A"),
                "url": result.get("url", "#"),
            })

        return {
            "productName": product_name,
            "prices": prices
        }


async def synthesis_agent(
    state: AgentState,
    config: RunnableConfig
) -> Command[Literal["__end__"]]:
    """
    Synthesis Agent Node

    Generates final answer and updates frontend with results.
    This is the final agent in the pipeline.

    Args:
        state: Current agent state
        config: Runtime configuration

    Returns:
        Command to end the workflow
    """
    logger.info("🎨 Synthesis Agent activated")

    # Update agent status
    state = update_agent_status(state, "synthesis_agent", "running")
    state = track_task(state, "synthesize")

    # Get ranked results
    ranked_results = state.get("ranked_results") or state.get("verified_results") or state.get("raw_search_results") or []

    if not ranked_results:
        logger.warning("⚠️  No results to synthesize")
        error_message = "I couldn't find any deals matching your query. Please try a different search or be more specific."

        return Command(
            goto=END,
            update={
                "final_answer": error_message,
                "messages": [*state["messages"], AIMessage(content=error_message)],
                "agent_status": {**state.get("agent_status", {}), "synthesis_agent": "no_data"},
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

        # Generate comprehensive answer
        synthesizer = SynthesisAgent()
        answer = await synthesizer.generate_answer(
            ranked_results,
            query,
            state.get("verification_summary", ""),
            state.get("reranking_summary", "")
        )

        # Format deals for frontend
        formatted_deals = [synthesizer.format_deal_for_frontend(r) for r in ranked_results]

        # Create price comparison if multiple stores
        price_comparison = None
        stores = set(r.get("store") for r in ranked_results if r.get("store"))
        if len(stores) > 1:
            price_comparison = synthesizer.create_price_comparison(ranked_results, query)

        # Create final response message
        final_message = AIMessage(content=answer)

        # Update agent status
        state = update_agent_status(state, "synthesis_agent", "completed")

        # Create agent summary
        agent_summary = (
            f"\\n\\n**Agent Pipeline Summary:**\\n"
            f"- 🔍 Search: {len(state.get('raw_search_results', []))} results found "
            f"{'(cached)' if state.get('cache_hit') else '(fresh)'}\\n"
            f"- ✓ Verification: {len(state.get('verified_results', []))} passed "
            f"({state.get('filtered_count', 0)} filtered)\\n"
            f"- 🔄 Reranking: {len(ranked_results)} results ranked "
            f"(confidence: {state.get('reranking_confidence', 0):.0%})\\n"
            f"- 🎯 Top Recommendation: {ranked_results[0].get('title', 'N/A')}"
        )

        final_answer_with_summary = answer + agent_summary

        logger.info(f"✅ Synthesis complete. Final answer: {len(answer)} chars")

        # Save session context at completion of pipeline
        session_id = state.get("session_id")
        if session_id:
            session_manager = get_session_manager()
            
            # Save numbered results for product queries
            session_manager.save_numbered_results(session_id, ranked_results)
            logger.info(f"💾 Saved {len(ranked_results)} numbered results to session")
            
            # Create context summary for future conversations
            context_summary = f"User searched for '{query}' and found {len(ranked_results)} deals."
            
            # Save conversation context and session
            session_manager.save_conversation_context(
                session_id, 
                state["messages"] + [final_message],
                context_summary
            )
            session_manager.save_session(session_id, state)
            logger.info(f"💾 Session context saved for {session_id}")

        # Prepare update with all results
        update_dict = {
            "final_answer": final_answer_with_summary,
            "deals_found": formatted_deals,
            "messages": [*state["messages"], final_message],
            "agent_status": state.get("agent_status", {}),
            "current_agent": "synthesis_agent",
        }

        # Add price comparison if available
        if price_comparison:
            update_dict["price_comparisons"] = [
                *state.get("price_comparisons", []),
                price_comparison
            ]

        return Command(
            goto=END,
            update=update_dict
        )

    except Exception as e:
        logger.error(f"❌ Synthesis agent error: {str(e)}")
        state = add_agent_error(state, "synthesis_agent", str(e))

        # Return error message
        error_message = f"I encountered an error while preparing your results: {str(e)}. Please try again."

        return Command(
            goto=END,
            update={
                "final_answer": error_message,
                "messages": [*state["messages"], AIMessage(content=error_message)],
                "agent_status": {**state.get("agent_status", {}), "synthesis_agent": "failed"},
                "agent_errors": state.get("agent_errors", []),
            }
        )
