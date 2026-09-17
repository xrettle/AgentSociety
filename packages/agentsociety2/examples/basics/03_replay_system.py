"""Replay System Example.

AgentSociety enables replay by default when ``run_dir`` is set. Environment
datasets land under ``run_dir/replay/``.
"""

from __future__ import annotations

import os

os.environ.setdefault("MEM0_TELEMETRY", "False")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import asyncio
from datetime import datetime
from pathlib import Path

from agentsociety2.contrib.env import SimpleSocialSpace
from agentsociety2.env import CodeGenRouter
from agentsociety2.society import AgentSociety


async def main() -> None:
    run_dir = Path("run_replay_example")
    agent_specs = [
        {
            "id": i,
            "profile": {
                "id": i,
                "name": f"Agent{i}",
                "personality": "friendly" if i % 2 == 0 else "curious",
            },
            "config": {},
        }
        for i in range(1, 4)
    ]
    names = [(spec["id"], spec["profile"]["name"]) for spec in agent_specs]

    social_env = SimpleSocialSpace(agent_id_name_pairs=names)
    env_router = CodeGenRouter(env_modules=[social_env])
    society = AgentSociety(
        agent_specs=agent_specs,
        agent_class_name="PersonAgent",
        env_router=env_router,
        start_t=datetime.now(),
        run_dir=run_dir,
        enable_replay=True,
    )
    await society.init()

    print("=== Replay System Example ===\n")
    print("Running agent interactions...\n")
    for spec in agent_specs:
        name = spec["profile"]["name"]
        response = await society.ask(f"Hello {name}! Introduce yourself.")
        print(f"{name}: {str(response)[:100]}...")

    await society.close()
    print(f"\nReplay data written under: {run_dir / 'replay'}")
    print("Inspect agent workspaces under:", run_dir / "agents")


if __name__ == "__main__":
    asyncio.run(main())
