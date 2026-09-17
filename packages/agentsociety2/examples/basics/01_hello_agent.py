"""Basic Agent Example: Hello Agent.

Demonstrates the AgentSociety2 workspace contract: declare agent_specs,
let AgentSociety create workspaces during init(), then ask questions.
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
    run_dir = Path("run_hello_agent")
    agent_specs = [
        {
            "id": 1,
            "profile": {
                "id": 1,
                "name": "Alice",
                "age": 28,
                "personality": "friendly, curious, and optimistic",
                "bio": "A software engineer who loves hiking, reading sci-fi novels, and cooking.",
                "location": "San Francisco",
            },
            "config": {},
        }
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
    )
    await society.init()

    print("=== Basic Agent Interaction ===\n")
    questions = [
        "What's the name of all agents?",
        "Tell me about Alice's personality and interests.",
        "What agents exist in this simulation?",
    ]
    for question in questions:
        print(f"Question: {question}")
        response = await society.ask(question)
        print(f"Answer: {response}\n")

    await society.close()


if __name__ == "__main__":
    asyncio.run(main())
