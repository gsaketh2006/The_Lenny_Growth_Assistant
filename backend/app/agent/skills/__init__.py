from typing import Dict
from backend.app.agent.skills.base import BaseSkill
from backend.app.agent.skills.grounded_qa import grounded_qa_skill
from backend.app.agent.skills.ship30_essay import ship30_essay_skill
from backend.app.agent.skills.growth_experiment import growth_experiment_skill

SKILL_REGISTRY: Dict[str, BaseSkill] = {
    "grounded_qa": grounded_qa_skill,
    "ship30_essay": ship30_essay_skill,
    "growth_experiment": growth_experiment_skill,
}


def get_skill(name: str) -> BaseSkill:
    """Returns the matching skill instance, defaulting to grounded_qa."""
    return SKILL_REGISTRY.get(name, grounded_qa_skill)
