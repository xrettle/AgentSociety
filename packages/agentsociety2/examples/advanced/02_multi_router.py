"""Multi-Router Example.

Compares ReAct / PlanExecute / CodeGen routers with the same agent_specs setup.
"""

from __future__ import annotations

import os

os.environ.setdefault("MEM0_TELEMETRY", "False")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from agentsociety2.contrib.env import SimpleSocialSpace
from agentsociety2.env import CodeGenRouter, PlanExecuteRouter, ReActRouter
from agentsociety2.society import AgentSociety


async def demonstrate_router(
    router_class: type[Any],
    router_name: str,
    question: str,
    run_dir: Path,
) -> None:
    agent_specs = [
        {
            "id": 1,
            "profile": {
                "id": 1,
                "name": "Tester",
                "personality": "analytical and helpful",
            },
            "config": {},
        }
    ]
    names = [(spec["id"], spec["profile"]["name"]) for spec in agent_specs]
    env_router = router_class(env_modules=[SimpleSocialSpace(agent_id_name_pairs=names)])
    society = AgentSociety(
        agent_specs=agent_specs,
        agent_class_name="PersonAgent",
        env_router=env_router,
        start_t=datetime.now(),
        run_dir=run_dir,
    )
    await society.init()

    print(f"\n--- {router_name} ---")
    print(f"Question: {question}")
    response = await society.ask(question)
    print(f"Response: {str(response)[:200]}...")
    await society.close()


async def main() -> None:
    print("=== Multi-Router Comparison ===\n")
    question = (
        "I have 10 apples. I give 3 to Alice and 2 to Bob. "
        "Then Alice gives me back 1 apple. How many apples do I have now? "
        "Show your work step by step."
    )

    await demonstrate_router(
        ReActRouter,
        "ReAct Router (Reasoning + Acting)",
        question,
        Path("run_router_react"),
    )
    await demonstrate_router(
        PlanExecuteRouter,
        "Plan-Execute Router (Plan then Execute)",
        question,
        Path("run_router_plan_execute"),
    )
    await demonstrate_router(
        CodeGenRouter,
        "CodeGen Router (Generate Code)",
        question,
        Path("run_router_codegen"),
    )


if __name__ == "__main__":
    asyncio.run(main())
