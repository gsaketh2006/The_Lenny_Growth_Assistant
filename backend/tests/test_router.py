import pytest
from backend.app.agent.router import skill_router


def test_router_growth_experiment_skill():
    """Verifies that experiment triggers route to growth_experiment with rationale."""
    queries = [
        "turn this into a growth experiment",
        "what could we test based on this retention insight?",
        "how do we test this hypothesis with a 1-week sprint?",
        "create an experiment card for our onboarding flow",
        "design an experiment to test the referral loop"
    ]
    for q in queries:
        decision = skill_router.route(q)
        assert decision.skill == "growth_experiment", f"Failed for query: {q}"
        assert decision.confidence >= 0.90
        assert "growth experiment" in decision.rationale.lower() or "experiment" in decision.rationale.lower()


def test_router_ship30_essay_skill():
    """Verifies that essay triggers route to ship30_essay with rationale."""
    queries = [
        "write a ship 30 for 30 essay about finding product-market fit",
        "draft an essay in ship30 style on B2B pricing",
        "publish an essay summarizing Brian Balfour's growth loops",
        "write a comprehensive essay on retention inflection points",
        "turn this into an essay for our team newsletter"
    ]
    for q in queries:
        decision = skill_router.route(q)
        assert decision.skill == "ship30_essay", f"Failed for query: {q}"
        assert decision.confidence >= 0.90
        assert "essay" in decision.rationale.lower() or "publication" in decision.rationale.lower()


def test_router_grounded_qa_skill():
    """Verifies that standard product strategy queries route to grounded_qa."""
    queries = [
        "What did Brian Balfour say about growth loops?",
        "How does Elena Verna define B2B product-led growth?",
        "What are the best frameworks for customer discovery?",
        "Explain Shreyas Doshi's LNO framework"
    ]
    for q in queries:
        decision = skill_router.route(q)
        assert decision.skill == "grounded_qa", f"Failed for query: {q}"
        assert decision.confidence >= 0.90
        assert "grounded q&a" in decision.rationale.lower()
