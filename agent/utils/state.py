"""
Enhanced Agent State Schema for Multi-Agent System
Defines the state structure shared across all agents
"""

from typing import Any, List, Dict
from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """
    Multi-Agent System State

    This enhanced state manages conversation, intermediate results,
    and coordination between multiple specialized agents.

    Inherits from MessagesState which provides:
        - messages: List[BaseMessage] - Conversation history
    """

    # ========== Existing Fields (Backward Compatible) ==========
    proverbs: List[str] = []
    tools: List[Any] = []
    deals_found: List[Dict[str, Any]] = []
    search_results: List[Dict[str, Any]] = []
    price_comparisons: List[Dict[str, Any]] = []

    # ========== Session Management ==========
    session_id: str = ""
    user_preferences: Dict[str, Any] = {}

    # ========== Task Tracking ==========
    current_task: str = ""  # "search", "verify", "rerank", "synthesize"
    task_history: List[str] = []

    # ========== Multi-Agent Intermediate Results ==========
    raw_search_results: List[Dict[str, Any]] = []  # From search agent
    verified_results: List[Dict[str, Any]] = []    # After verification
    ranked_results: List[Dict[str, Any]] = []      # After reranking
    final_answer: str = ""                         # Synthesized response

    # ========== Agent Coordination ==========
    agent_status: Dict[str, str] = {}  # {agent_name: status}
    current_agent: str = ""            # Currently active agent
    agent_errors: List[Dict[str, str]] = []  # Error tracking

    # ========== Caching Metadata ==========
    cache_keys: List[str] = []               # Keys used for caching
    cached_queries: Dict[str, Any] = {}      # Cache hits/misses tracking
    cache_hit: bool = False                  # Whether results came from cache

    # ========== Verification Metadata ==========
    verification_scores: Dict[str, float] = {}  # {result_id: score}
    filtered_count: int = 0                     # Number of results filtered out
    verification_summary: str = ""              # Verification agent summary

    # ========== Reranking Metadata ==========
    reranking_confidence: float = 0.0        # Overall ranking confidence
    reranking_factors: Dict[str, float] = {} # Scoring factor weights
    reranking_summary: str = ""              # Reranking reasoning

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert state to dictionary for serialization

        Returns:
            Dictionary representation of state
        """
        return {
            # Existing fields
            "proverbs": self.proverbs,
            "deals_found": self.deals_found,
            "search_results": self.search_results,
            "price_comparisons": self.price_comparisons,

            # Session
            "session_id": self.session_id,
            "user_preferences": self.user_preferences,

            # Task tracking
            "current_task": self.current_task,
            "task_history": self.task_history,

            # Results
            "raw_search_results": self.raw_search_results,
            "verified_results": self.verified_results,
            "ranked_results": self.ranked_results,
            "final_answer": self.final_answer,

            # Agent coordination
            "agent_status": self.agent_status,
            "current_agent": self.current_agent,
            "agent_errors": self.agent_errors,

            # Caching
            "cache_keys": self.cache_keys,
            "cached_queries": self.cached_queries,
            "cache_hit": self.cache_hit,

            # Verification
            "verification_scores": self.verification_scores,
            "filtered_count": self.filtered_count,
            "verification_summary": self.verification_summary,

            # Reranking
            "reranking_confidence": self.reranking_confidence,
            "reranking_factors": self.reranking_factors,
            "reranking_summary": self.reranking_summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """
        Create AgentState from dictionary

        Args:
            data: Dictionary representation

        Returns:
            AgentState instance
        """
        state = cls()

        # Update fields from dictionary
        for key, value in data.items():
            if hasattr(state, key):
                setattr(state, key, value)

        return state

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current state

        Returns:
            Summary dictionary with key metrics
        """
        return {
            "session_id": self.session_id,
            "current_agent": self.current_agent,
            "current_task": self.current_task,
            "raw_results_count": len(self.raw_search_results),
            "verified_results_count": len(self.verified_results),
            "ranked_results_count": len(self.ranked_results),
            "deals_found_count": len(self.deals_found),
            "cache_hit": self.cache_hit,
            "errors": len(self.agent_errors),
            "verification_filtered": self.filtered_count,
            "reranking_confidence": self.reranking_confidence,
        }


# Helper functions for state management

def update_agent_status(state: AgentState, agent_name: str, status: str) -> AgentState:
    """
    Update the status of a specific agent

    Args:
        state: Current agent state
        agent_name: Name of the agent
        status: New status ('running', 'completed', 'failed')

    Returns:
        Updated state
    """
    if "agent_status" not in state:
        state["agent_status"] = {}
    state["agent_status"][agent_name] = status
    state["current_agent"] = agent_name
    return state


def add_agent_error(state: AgentState, agent_name: str, error: str) -> AgentState:
    """
    Add an error to the agent error log

    Args:
        state: Current agent state
        agent_name: Name of the agent that encountered error
        error: Error message

    Returns:
        Updated state
    """
    if "agent_errors" not in state:
        state["agent_errors"] = []
    state["agent_errors"].append({
        "agent": agent_name,
        "error": error,
        "task": state.get("current_task", "")
    })
    return state


def track_task(state: AgentState, task_name: str) -> AgentState:
    """
    Track a new task in the task history

    Args:
        state: Current agent state
        task_name: Name of the task

    Returns:
        Updated state
    """
    state["current_task"] = task_name
    if "task_history" not in state:
        state["task_history"] = []
    if task_name not in state["task_history"]:
        state["task_history"].append(task_name)
    return state
