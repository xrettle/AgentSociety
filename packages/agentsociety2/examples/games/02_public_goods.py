"""Public Goods Game example using contrib PublicGoodsAgent + PublicGoodsEnv.

Requires LLM credentials (``AGENTSOCIETY_LLM_API_KEY`` / ``AGENTSOCIETY_LLM_API_BASE``).
"""

from __future__ import annotations

import os

os.environ.setdefault("MEM0_TELEMETRY", "False")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import asyncio
from datetime import datetime
from pathlib import Path

from agentsociety2.contrib.env import PublicGoodsEnv
from agentsociety2.env import CodeGenRouter
from agentsociety2.society import AgentSociety

NUM_ROUNDS = 3
NUM_AGENTS = 4
INITIAL_ENDOWMENT = 20
PUBLIC_POOL_MULTIPLIER = 1.6


async def main() -> None:
    run_dir = Path("run_public_goods")
    personalities = [
        "altruistic and community-minded",
        "self-interested and rational",
        "cautious and skeptical",
        "optimistic and trusting",
    ]
    names = ["Alice", "Bob", "Charlie", "Diana"]
    agent_specs = [
        {
            "id": i + 1,
            "profile": {
                "id": i + 1,
                "name": names[i],
                "personality": personalities[i],
            },
            "config": {
                "num_rounds": NUM_ROUNDS,
                "num_agents": NUM_AGENTS,
                "initial_endowment": INITIAL_ENDOWMENT,
                "public_pool_multiplier": PUBLIC_POOL_MULTIPLIER,
            },
        }
        for i in range(NUM_AGENTS)
    ]

    env_module = PublicGoodsEnv(
        num_agents=NUM_AGENTS,
        initial_endowment=INITIAL_ENDOWMENT,
        public_pool_multiplier=PUBLIC_POOL_MULTIPLIER,
    )
    society = AgentSociety(
        agent_specs=agent_specs,
        agent_class_name="PublicGoodsAgent",
        env_router=CodeGenRouter(env_modules=[env_module]),
        start_t=datetime.now(),
        run_dir=run_dir,
        enable_replay=True,
    )
    await society.init()

    print("=== Public Goods Game ===\n")
    print(f"Running {NUM_ROUNDS} rounds with {NUM_AGENTS} agents...\n")

    for round_num in range(1, NUM_ROUNDS + 1):
        print(f"--- Round {round_num}/{NUM_ROUNDS} ---")
        await society.step(tick=1)
        if env_module.round_history:
            latest = env_module.round_history[-1]
            print(
                f"  total={latest.get('total_contribution')} "
                f"gain_per_agent={latest.get('gain_per_agent')} "
                f"contributions={latest.get('contributions')}"
            )
        else:
            print("  (no round settled yet — check agent step logs)")

    await society.close()
    print(f"\nDone. Results under {run_dir}")
    print(f"Rounds recorded: {len(env_module.round_history)}")


if __name__ == "__main__":
    asyncio.run(main())
