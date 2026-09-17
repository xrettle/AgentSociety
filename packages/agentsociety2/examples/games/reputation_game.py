"""Reputation game example using ReputationGameEnv + LLMDonorAgent.

Uses agent_specs / workspace creation. Optional mem0 config can be placed in
each agent's ``config`` under ``memory_config`` when available.
Requires LLM credentials.
"""

from __future__ import annotations

import os
import random

os.environ.setdefault("MEM0_TELEMETRY", "False")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import asyncio
from datetime import datetime
from pathlib import Path

from agentsociety2.contrib.env.reputation_game import (
    ReputationGameConfig,
    ReputationGameEnv,
)
from agentsociety2.env import CodeGenRouter
from agentsociety2.society import AgentSociety

POPULATION = 6
NUM_STEPS = 5
TICK_SECONDS = 2

PERSONALITIES = [
    "You are a rational and cautious agent, tending to maximize long-term benefits.",
    "You are an emotional agent, and your decisions are influenced by your current emotional state.",
    "You are a fair-minded agent, tending to help those with good reputation and refusing to help those with bad reputation.",
    "You are an altruistic agent, more willing to help others even if it may harm your short-term benefits.",
    "You are a selfish agent, mainly focusing on your own benefits and not caring much about others' reputation.",
    "You are an optimistic agent, believing that cooperation will bring better results.",
]


async def main() -> None:
    run_dir = Path("run_reputation_game")
    env_config = ReputationGameConfig(
        Z=POPULATION,
        BENEFIT=5,
        COST=1,
        norm_type="stern_judging",
        seed=42,
    )
    env_module = ReputationGameEnv(config=env_config)

    agent_specs = []
    for i in range(POPULATION):
        personality = random.choice(PERSONALITIES)
        agent_specs.append(
            {
                "id": i,
                "profile": {
                    "id": i,
                    "name": f"Agent {i}",
                    "custom_fields": {
                        "learning_frequency": 5,
                        "personality": personality,
                    },
                },
                "config": {},
            }
        )

    society = AgentSociety(
        agent_specs=agent_specs,
        agent_class_name="LLMDonorAgent",
        env_router=CodeGenRouter(env_modules=[env_module]),
        start_t=datetime.now(),
        run_dir=run_dir,
        enable_replay=True,
    )
    await society.init()

    print("=== Reputation Game ===\n")
    print(f"Population={POPULATION}, steps={NUM_STEPS}, norm={env_config.norm_type}\n")

    for step_idx in range(1, NUM_STEPS + 1):
        print(f"--- Step {step_idx}/{NUM_STEPS} ---")
        await society.step(tick=TICK_SECONDS)

    await society.close()
    print(f"\nDone. Artifacts under {run_dir}")


if __name__ == "__main__":
    asyncio.run(main())
