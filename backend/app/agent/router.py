import re
from typing import List, Dict, Any, Optional
from backend.app.core.logging import logger
from backend.app.models.schemas import RoutingDecision


class SkillRouter:
    """Intelligent 3-Skill Router with explicit, auditable decision logs."""

    # Keywords for Skill 2: Ship 30 for 30 Essay Generator
    ESSAY_TRIGGERS = [
        "ship 30", "ship30", "write an essay", "write a 1250 word", "publish an essay",
        "longform essay", "thought leadership post", "write an article", "write a comprehensive essay",
        "draft an essay", "create an essay", "turn this into an essay", "write a blog post",
        "write a newsletter", "ship30 style", "ship 30 for 30"
    ]

    # Keywords for Skill 3: Growth Experiment Card Generator (Differentiator)
    EXPERIMENT_TRIGGERS = [
        "growth experiment", "experiment card", "turn this into an experiment",
        "what could we test", "how do we test this", "create an experiment",
        "test plan", "growth test", "design an experiment", "test this hypothesis",
        "hypothesis card", "ab test plan", "a/b test", "sprint test", "experiment on"
    ]

    def route(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> RoutingDecision:
        """Determines the target skill, confidence, and audit rationale."""
        q_lower = query.lower().strip()

        # 1. Evaluate Growth Experiment Card triggers
        for trigger in self.EXPERIMENT_TRIGGERS:
            if trigger in q_lower:
                rationale = (
                    f"Matched high-priority growth experiment trigger '{trigger}'. "
                    f"User requested actionable test plan, hypothesis, or experiment design."
                )
                logger.info(f"[ROUTER DECISION] -> growth_experiment | Rationale: {rationale}")
                return RoutingDecision(
                    skill="growth_experiment",
                    confidence=0.96,
                    rationale=rationale,
                    entities={"trigger_matched": trigger}
                )

        # 2. Evaluate Ship 30 for 30 Essay triggers
        for trigger in self.ESSAY_TRIGGERS:
            if trigger in q_lower:
                rationale = (
                    f"Matched longform publication trigger '{trigger}'. "
                    f"User requested Ship 30 for 30–style structured essay (~1,250 words)."
                )
                logger.info(f"[ROUTER DECISION] -> ship30_essay | Rationale: {rationale}")
                return RoutingDecision(
                    skill="ship30_essay",
                    confidence=0.95,
                    rationale=rationale,
                    entities={"trigger_matched": trigger}
                )

        # 3. Contextual heuristic from conversation history
        if chat_history and len(chat_history) > 0:
            last_assistant_msg = chat_history[-1].get("content", "").lower()
            if any(term in q_lower for term in ["test it", "experiment with it", "how to test", "make it a card"]):
                rationale = (
                    "Contextual follow-up to prior growth advice requesting an experiment formulation."
                )
                logger.info(f"[ROUTER DECISION] -> growth_experiment | Rationale: {rationale}")
                return RoutingDecision(
                    skill="growth_experiment",
                    confidence=0.90,
                    rationale=rationale,
                    entities={"contextual_continuation": True}
                )

        # 4. Default: Grounded Q&A
        rationale = (
            "Standard product management / growth strategy inquiry. "
            "Routing to Grounded Q&A Engine for multi-turn conversational advice with transcript citations."
        )
        logger.info(f"[ROUTER DECISION] -> grounded_qa | Rationale: {rationale}")
        return RoutingDecision(
            skill="grounded_qa",
            confidence=0.98,
            rationale=rationale,
            entities={}
        )


skill_router = SkillRouter()
