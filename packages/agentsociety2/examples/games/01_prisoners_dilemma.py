"""Prisoner's Dilemma example using contrib game agent + env.

Runs a short multi-round game via ``society.step()``. Requires LLM credentials
(``AGENTSOCIETY_LLM_API_KEY`` / ``AGENTSOCIETY_LLM_API_BASE``).
"""

from __future__ import annotations

import os

os.environ.setdefault("MEM0_TELEMETRY", "False")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import asyncio
from datetime import datetime
from pathlib import Path

from agentsociety2.contrib.env import PrisonersDilemmaEnv
from agentsociety2.env import CodeGenRouter
from agentsociety2.society import AgentSociety

NUM_ROUNDS = 3


async def main() -> None:
    run_dir = Path("run_prisoners_dilemma")
    agent_names = ["Agent A", "Agent B"]
    agent_specs = [
        {
            "id": i + 1,
            "profile": {"id": i + 1, "name": name},
            "config": {},
        }
        for i, name in enumerate(agent_names)
    ]

    env_module = PrisonersDilemmaEnv()
    society = AgentSociety(
        agent_specs=agent_specs,
        agent_class_name="PrisonersDilemmaAgent",
        env_router=CodeGenRouter(env_modules=[env_module]),
        start_t=datetime.now(),
        run_dir=run_dir,
        enable_replay=True,
    )
    await society.init()

    print("=== Prisoner's Dilemma ===\n")
    print(f"Running {NUM_ROUNDS} rounds with {agent_names}...\n")

    for round_num in range(1, NUM_ROUNDS + 1):
        print(f"--- Round {round_num}/{NUM_ROUNDS} ---")
        await society.step(tick=1)
        if env_module.round_history:
            latest = env_module.round_history[-1]
            print(
                f"  A={latest.get('agent_a_action')} "
                f"B={latest.get('agent_b_action')} "
                f"payoffs=({latest.get('agent_a_payoff')}, "
                f"{latest.get('agent_b_payoff')})"
            )
        else:
            print("  (no round settled yet — check agent step logs)")

    await society.close()
    print(f"\nDone. ENV state / replay under {run_dir}")
    print(f"Rounds recorded: {len(env_module.round_history)}")


if __name__ == "__main__":
    asyncio.run(main())
