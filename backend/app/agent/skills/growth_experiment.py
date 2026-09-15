import json
import re
from typing import List, Dict, Any, AsyncGenerator
from backend.app.agent.skills.base import BaseSkill
from backend.app.agent.providers import BaseLLMClient
from backend.app.models.schemas import GroundingResult, ArtifactBase, GrowthExperimentCard, TestPlanStep, GroundingSource
from backend.app.core.logging import logger


class GrowthExperimentSkill(BaseSkill):
    name = "growth_experiment"
    description = (
        "Transforms podcast insights into an actionable, sprint-ready Growth Experiment Card "
        "with hypothesis, target metric, 1-week test plan, invalidation risks, and source citations."
    )

    async def execute_stream(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        grounding: GroundingResult,
        llm: BaseLLMClient
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if grounding.is_refusal:
            yield {
                "type": "chunk",
                "content": (
                    f"⚠️ **Insufficient Grounding for Growth Experiment Formulation**\n\n"
                    f"{grounding.refusal_reason}\n\n"
                    f"To design a high-fidelity growth experiment, I need specific podcast frameworks or case studies from the transcript archive."
                )
            }
            return

        # Top source details
        top_cit = grounding.citations[0] if grounding.citations else None
        guest = top_cit.guest_name if top_cit else "Lenny's Guest"
        episode = top_cit.episode_title if top_cit else "Growth Framework"

        context_blocks = []
        for i, cit in enumerate(grounding.citations, start=1):
            context_blocks.append(
                f"[Source {i} | Guest: {cit.guest_name} | Episode: '{cit.episode_title}']\n"
                f"{cit.snippet}\n"
            )
        context_text = "\n---\n".join(context_blocks)

        system_prompt = (
            "You are a Lead Growth Experimentation Engineer.\n"
            "Your job is to convert strategic product advice from Lenny's Podcast into a concrete, executable 'Growth Experiment Card'.\n\n"
            "OUTPUT RULES:\n"
            "You MUST output a valid JSON object wrapped in ```json ... ``` with EXACTLY this structure:\n"
            "{\n"
            '  "title": "Clear experiment name",\n'
            '  "hypothesis": "If we [Action], then [Expected Outcome] will happen, because [Specific mechanism from transcript].",\n'
            '  "target_metric": "The single primary metric to move (e.g. Day-7 Activation Rate)",\n'
            '  "secondary_metrics": ["Guardrail 1", "Guardrail 2"],\n'
            '  "test_plan": [\n'
            '    {"day_range": "Day 1-2", "action": "Instrumentation & baseline metric setup"},\n'
            '    {"day_range": "Day 3-4", "action": "Launch 50/50 test variant to cohort"},\n'
            '    {"day_range": "Day 5-7", "action": "Evaluate statistical significance & go/no-go call"}\n'
            '  ],\n'
            '  "risks_and_invalidation": ["Risk 1", "Risk 2"],\n'
            '  "expected_impact": "High",\n'
            '  "grounding_source": {\n'
            f'    "guest": "{guest}",\n'
            f'    "episode": "{episode}",\n'
            '    "quote_or_concept": "Key quote or mechanism from the transcript"\n'
            '  }\n'
            "}\n\n"
            f"TRANSCRIPT SOURCES:\n{context_text}"
        )

        user_prompt = f"Design a rigorous Growth Experiment Card based on: {query}"
        messages = [{"role": "user", "content": user_prompt}]

        yield {
            "type": "chunk",
            "content": "🧪 **Synthesizing Growth Experiment Card...**\n\nMounting interactive Growth Experiment Card in the Artifact Viewer.\n\n"
        }

        generated_chunks = []
        async for token in llm.generate_stream(messages, system_prompt=system_prompt, temperature=0.3):
            generated_chunks.append(token)

        full_raw_text = "".join(generated_chunks)

        # Parse JSON
        card_data = None
        json_match = re.search(r"```json\s*(.*?)\s*```", full_raw_text, re.DOTALL)
        if json_match:
            try:
                card_data = json.loads(json_match.group(1))
            except Exception as e:
                logger.warning(f"Error parsing json in experiment card: {e}")
        
        if not card_data:
            # Fallback direct json parse
            try:
                card_data = json.loads(full_raw_text)
            except Exception:
                # Construct graceful fallback from text
                card_data = {
                    "title": f"Growth Experiment: {query[:50]}",
                    "hypothesis": f"If we implement the growth mechanism discussed by {guest}, then conversion will increase.",
                    "target_metric": "Conversion / Activation Rate",
                    "secondary_metrics": ["Retention Rate", "Bounce Rate"],
                    "test_plan": [
                        {"day_range": "Day 1-2", "action": "Configure tracking events & baseline sample"},
                        {"day_range": "Day 3-4", "action": "Deploy MVP experiment to 20% of new traffic"},
                        {"day_range": "Day 5-7", "action": "Analyze sample lift & determine permanent rollout"}
                    ],
                    "risks_and_invalidation": ["Sample size noise", "Short-term novelty effect"],
                    "expected_impact": "High",
                    "grounding_source": {
                        "guest": guest,
                        "episode": episode,
                        "quote_or_concept": top_cit.snippet[:150] if top_cit else "Grounded transcript tactic"
                    }
                }

        # Build readable Markdown summary for chat window
        chat_summary = (
            f"### 📋 {card_data.get('title', 'Growth Experiment Card')}\n\n"
            f"**Hypothesis:** {card_data.get('hypothesis', '')}\n\n"
            f"🎯 **Target Metric:** `{card_data.get('target_metric', '')}`\n\n"
            f"⚡ **Expected Impact:** `{card_data.get('expected_impact', 'High')}`\n\n"
            f"🎙️ **Grounding Source:** {card_data.get('grounding_source', {}).get('guest', guest)} (*{card_data.get('grounding_source', {}).get('episode', episode)}*)\n\n"
            f"> *\"{card_data.get('grounding_source', {}).get('quote_or_concept', '')}\"*\n\n"
            f"*(Inspect the full 1-Week Test Plan and Invalidation Matrix in the Artifact Viewer.)*"
        )
        yield {"type": "chunk", "content": chat_summary}

        # Emit artifact event
        artifact = ArtifactBase(
            title=card_data.get("title", "Growth Experiment Card"),
            artifact_type="growth_experiment",
            content=json.dumps(card_data, indent=2),
            structured_data=card_data,
            version=1
        )
        yield {"type": "artifact", "artifact": artifact}


growth_experiment_skill = GrowthExperimentSkill()
