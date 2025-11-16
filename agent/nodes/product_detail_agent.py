"""
Product Detail Agent Node
Handles product-specific queries and follow-up questions
Supports both number-based (#1, #2) and natural language references
"""

import logging
from typing import Any, Dict, List
from typing_extensions import Literal
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.graph import END
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    AgentState, 
    update_agent_status, 
    track_task, 
    add_agent_error,
    get_session_manager,
    get_product_matcher,
    get_fact_verifier,
    ProductMatch
)

logger = logging.getLogger(__name__)


class ProductDetailAgent:
    """
    Handles product-specific queries with intelligent matching and fact verification
    """

    def __init__(self):
        self.product_matcher = get_product_matcher()
        self.fact_verifier = get_fact_verifier()
        self.model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    async def answer_product_query(
        self,
        query: str,
        product: Dict[str, Any],
        match_info: ProductMatch,
        all_results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate fact-verified answer about a specific product

        Args:
            query: User's question about the product
            product: The matched product data
            match_info: Matching metadata (confidence, method)
            all_results: All available products for comparison context

        Returns:
            Verified answer string
        """
        # Extract product information with fact verification
        product_number = product.get("result_number", "?")
        product_name = product.get("clean_name") or product.get("title", "Unknown Product")
        
        # Verify key facts
        verified_price = self.fact_verifier.verify_price(product)
        verified_specs = self.fact_verifier.verify_specification(product, "all")
        verified_availability = self.fact_verifier.verify_availability(product)
        
        # Create fact sheet for LLM context
        fact_sheet = self.fact_verifier.create_fact_sheet(product)

        # Build context for LLM
        context = f"""Product #{product_number}: {product_name}

**VERIFIED FACTS (Use ONLY these - DO NOT invent information):**
{fact_sheet}

**Matching Information:**
- Confidence: {match_info.confidence * 100:.0f}%
- Method: {match_info.method}
- Ambiguity: {match_info.is_ambiguous}

**User Query Classification:**
- Question Type: {self._classify_question_type(query)}
- Requires Comparison: {self._needs_comparison(query)}

**Source URL:** {product.get('url', 'N/A')}

**ALL AVAILABLE PRODUCTS FOR COMPARISON (if needed):**
{self._format_comparison_context(all_results[:10])}
"""

        # Create anti-hallucination prompt
        prompt = f"""You are a fact-based product assistant. Answer the user's question using ONLY verified facts.

{context}

User's Question: "{query}"

**CRITICAL RULES:**
1. ✅ Use ONLY facts marked as VERIFIED from the fact sheet above
2. ❌ NEVER invent specifications, features, or details not in the source
3. ⚠️ If asked about unverified info, say "I don't have verified information about that"
4. 📊 For comparisons, use data from "ALL AVAILABLE PRODUCTS FOR COMPARISON"
5. 🔗 Cite source URL when providing facts
6. 💡 Be helpful but honest - admit when data is missing

**Response Guidelines:**
- Keep answer concise (2-3 sentences for simple questions, 1 paragraph for complex ones)
- Use natural, conversational tone
- Include product number (#{product_number}) in response
- For price questions: Always include verified price with ✅ marker
- For spec questions: Only mention verified specs
- For comparison questions: Compare only available verified data
- If confidence is low (<70%), acknowledge uncertainty

Generate a helpful, fact-based response:"""

        try:
            response = await self.model.ainvoke(prompt)
            answer = response.content

            # Validate response for hallucinations
            validation = self.fact_verifier.validate_response(answer, product)
            
            if not validation["passes_validation"]:
                # Response contains potential hallucinations - regenerate with stronger constraints
                logger.warning(f"⚠️ Potential hallucination detected: {validation['issues']}")
                
                strict_prompt = f"""{prompt}

**VALIDATION FAILED - Issues detected:**
{'; '.join(validation['issues'])}

**REGENERATE with absolute fact-checking:**
- Remove any unverified claims
- Stick strictly to the fact sheet
- If uncertain, say "This information isn't available in the verified data"

Regenerated response:"""
                
                response = await self.model.ainvoke(strict_prompt)
                answer = response.content

            # Add matching confidence note if low
            if match_info.confidence < 0.7:
                answer = f"ℹ️ *Note: Match confidence {match_info.confidence*100:.0f}% - please verify this is the product you meant.*\n\n{answer}"

            # Add alternatives if ambiguous
            if match_info.is_ambiguous and match_info.alternatives:
                alt_text = "\n\n**Did you mean one of these instead?**\n"
                for alt in match_info.alternatives[:3]:
                    alt_text += f"- #{alt.get('result_number')}: {alt.get('clean_name') or alt.get('title')}\n"
                answer += alt_text

            logger.info(f"✅ Generated verified answer for product #{product_number}")
            return answer

        except Exception as e:
            logger.error(f"❌ Error generating product answer: {str(e)}")
            return f"I encountered an error while analyzing product #{product_number}. Please try again or rephrase your question."

    def _classify_question_type(self, query: str) -> str:
        """Classify the type of question being asked"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["price", "cost", "how much", "expensive", "cheap"]):
            return "pricing"
        elif any(word in query_lower for word in ["spec", "feature", "detail", "about", "tell me"]):
            return "specifications"
        elif any(word in query_lower for word in ["compare", "vs", "versus", "difference", "better"]):
            return "comparison"
        elif any(word in query_lower for word in ["review", "rating", "quality", "good"]):
            return "reviews"
        elif any(word in query_lower for word in ["available", "stock", "buy", "purchase"]):
            return "availability"
        else:
            return "general"

    def _needs_comparison(self, query: str) -> bool:
        """Check if query requires comparing multiple products"""
        comparison_keywords = ["compare", "vs", "versus", "difference", "better", "cheaper", "best", "worst"]
        return any(keyword in query.lower() for keyword in comparison_keywords)

    def _format_comparison_context(self, results: List[Dict[str, Any]]) -> str:
        """Format product list for comparison context"""
        if not results:
            return "No other products available for comparison."
        
        formatted = []
        for product in results:
            num = product.get("result_number", "?")
            name = product.get("clean_name") or product.get("title", "Unknown")
            price = product.get("price", "N/A")
            store = product.get("store", "Unknown")
            score = product.get("final_score", product.get("score", 0))
            
            formatted.append(f"#{num}. {name} - {price} at {store} (Score: {score:.1f}/100)")
        
        return "\n".join(formatted)

    async def handle_comparison_query(
        self,
        query: str,
        products: List[Dict[str, Any]],
        all_results: List[Dict[str, Any]]
    ) -> str:
        """
        Handle multi-product comparison queries

        Args:
            query: Comparison query
            products: List of products to compare
            all_results: All available products

        Returns:
            Comparison answer
        """
        if len(products) < 2:
            return "I need at least two products to compare. Please specify which products you'd like to compare."

        # Create comparison table with verified facts
        comparison_data = []
        for product in products[:5]:  # Max 5 products
            verified_facts = self.fact_verifier.create_fact_sheet(product)
            comparison_data.append({
                "number": product.get("result_number", "?"),
                "name": product.get("clean_name") or product.get("title", "Unknown"),
                "facts": verified_facts,
                "url": product.get("url", "N/A")
            })

        context = f"""COMPARISON REQUEST

**Products to Compare:**
{self._format_comparison_table(comparison_data)}

User's Comparison Query: "{query}"

**CRITICAL RULES:**
1. Compare ONLY verified facts from the tables above
2. Use actual data - DO NOT invent specifications
3. Highlight key differences objectively
4. Include product numbers in comparison
5. Cite sources for factual claims
6. If data is missing for comparison, acknowledge it

Generate a concise comparison (max 1 paragraph):"""

        try:
            response = await self.model.ainvoke(context)
            answer = response.content

            # Validate comparison for hallucinations
            for product in products:
                validation = self.fact_verifier.validate_response(answer, product)
                if not validation["passes_validation"]:
                    logger.warning(f"⚠️ Comparison hallucination: {validation['issues']}")
                    answer += f"\n\n⚠️ *Note: Some claims couldn't be verified from source data.*"
                    break

            return answer

        except Exception as e:
            logger.error(f"❌ Error generating comparison: {str(e)}")
            return "I encountered an error while comparing products. Please try again."

    def _format_comparison_table(self, comparison_data: List[Dict]) -> str:
        """Format product data as comparison table"""
        table = []
        for data in comparison_data:
            table.append(f"""
**Product #{data['number']}: {data['name']}**
{data['facts']}
Source: {data['url']}
---""")
        return "\n".join(table)


async def product_detail_agent(
    state: AgentState,
    config: RunnableConfig
) -> Command[Literal["synthesis_agent", "__end__"]]:
    """
    Product Detail Agent Node

    Handles follow-up questions about specific products from search results.
    Supports both number-based (#1, #2) and natural language references.

    Args:
        state: Current agent state
        config: Runtime configuration

    Returns:
        Command to route to synthesis or end
    """
    logger.info("🔍 Product Detail Agent activated")

    # Update agent status
    state = update_agent_status(state, "product_detail_agent", "running")
    state = track_task(state, "product_detail")

    # Get the user's query
    query = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            query = msg.content
            break

    if not query:
        logger.warning("⚠️ No query found for product detail agent")
        return Command(
            goto=END,
            update={
                "final_answer": "I didn't receive a question. What would you like to know?",
                "agent_status": {**state.get("agent_status", {}), "product_detail_agent": "no_query"}
            }
        )

    try:
        # Get session and numbered results
        session_id = state.get("session_id")
        if not session_id:
            return Command(
                goto=END,
                update={
                    "final_answer": "I don't have any search results to reference. Please search for products first.",
                    "agent_status": {**state.get("agent_status", {}), "product_detail_agent": "no_session"}
                }
            )

        session_manager = get_session_manager()
        all_results_data = session_manager.get_all_results_data(session_id)
        
        if not all_results_data or not all_results_data.get("numbered_results"):
            return Command(
                goto=END,
                update={
                    "final_answer": "I don't have any previous search results. Please search for products first.",
                    "agent_status": {**state.get("agent_status", {}), "product_detail_agent": "no_results"}
                }
            )

        numbered_results = all_results_data["numbered_results"]
        all_results = list(numbered_results.values())

        # Match the product(s) mentioned in query
        agent = ProductDetailAgent()
        matches = agent.product_matcher.match_product(query, all_results)

        if not matches:
            # No matches found
            answer = (
                f"I couldn't identify which product you're referring to in your query: '{query}'\n\n"
                f"Available products:\n" +
                "\n".join([f"#{num}. {prod.get('clean_name') or prod.get('title', 'Unknown')}" 
                          for num, prod in sorted(numbered_results.items())])
            )
            
            return Command(
                goto=END,
                update={
                    "final_answer": answer,
                    "agent_status": {**state.get("agent_status", {}), "product_detail_agent": "no_match"}
                }
            )

        # Check if it's a comparison query
        if agent._needs_comparison(query) and len(matches) >= 2:
            # Multi-product comparison
            matched_products = [m.product for m in matches]
            answer = await agent.handle_comparison_query(query, matched_products, all_results)
        else:
            # Single product query (use highest confidence match)
            best_match = matches[0]
            answer = await agent.answer_product_query(query, best_match.product, best_match, all_results)

        # Create response message
        response_message = AIMessage(content=answer)

        # Update agent status
        state = update_agent_status(state, "product_detail_agent", "completed")

        logger.info(f"✅ Product detail response generated")

        return Command(
            goto=END,
            update={
                "final_answer": answer,
                "messages": [*state["messages"], response_message],
                "agent_status": state.get("agent_status", {}),
                "current_agent": "product_detail_agent",
            }
        )

    except Exception as e:
        logger.error(f"❌ Product detail agent error: {str(e)}")
        state = add_agent_error(state, "product_detail_agent", str(e))

        error_message = f"I encountered an error while processing your question: {str(e)}. Please try rephrasing."

        return Command(
            goto=END,
            update={
                "final_answer": error_message,
                "messages": [*state["messages"], AIMessage(content=error_message)],
                "agent_status": {**state.get("agent_status", {}), "product_detail_agent": "failed"},
                "agent_errors": state.get("agent_errors", []),
            }
        )
