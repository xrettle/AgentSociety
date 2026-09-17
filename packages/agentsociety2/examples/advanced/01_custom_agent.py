"""Custom Agent Example.

Shows how to implement a workspace-bound AgentBase subclass, register it for
AgentSociety discovery, and run it via agent_specs.
"""

from __future__ import annotations

import os

os.environ.setdefault("MEM0_TELEMETRY", "False")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from agentsociety2.agent import AgentBase
from agentsociety2.contrib.env import SimpleSocialSpace
from agentsociety2.env import CodeGenRouter
from agentsociety2.registry import get_registry
from agentsociety2.society import AgentSociety


class SpecialistAgent(AgentBase):
    """A custom agent that specializes in a particular domain."""

    @classmethod
    def create(cls, workspace_path: Path, profile: dict, config: dict) -> None:
        workspace_path = Path(workspace_path)
        workspace_path.mkdir(parents=True, exist_ok=True)
        (workspace_path / "config.json").write_text(
            json.dumps(config or {}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        agent_id = int(profile.get("id", 0))
        name = str(profile.get("name") or f"Agent_{agent_id}")
        (workspace_path / "AGENT.json").write_text(
            json.dumps(
                {
                    "id": agent_id,
                    "name": name,
                    "profile": profile,
                    "step_count": 0,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    async def from_workspace(
        cls, workspace_path: Path, service_proxy: Any
    ) -> "SpecialistAgent":
        agent = cls()
        await agent._restore(workspace_path, service_proxy)
        return agent

    async def _restore(self, workspace_path: Path, service_proxy: Any) -> None:
        workspace_path = Path(workspace_path)
        cfg: dict[str, Any] = {}
        config_path = workspace_path / "config.json"
        if config_path.exists():
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
        meta = json.loads((workspace_path / "AGENT.json").read_text(encoding="utf-8"))
        self._id = int(meta.get("agent_id", meta.get("id", 0)))
        self._profile = meta.get("profile", {"name": meta.get("name")})
        self._name = meta.get("name") or f"Agent_{self._id}"
        self._config = dict(cfg or {})
        self._bind_services(service_proxy)
        self._step_count = int(meta.get("step_count", 0))
        self._specialty = str(self._config.get("specialty", "general"))

    async def to_workspace(self, workspace_path: Path) -> None:
        workspace_path = Path(workspace_path)
        (workspace_path / "AGENT.json").write_text(
            json.dumps(
                {
                    "id": self._id,
                    "name": self._name,
                    "profile": self.get_profile(),
                    "step_count": self._step_count,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    async def step(self, tick: int, t: datetime) -> str:
        self._step_count += 1
        return f"SpecialistAgent step {tick}"

    async def ask(
        self,
        message: str,
        readonly: bool = True,
        *,
        t: datetime | None = None,
    ) -> str:
        enhanced = (
            f"You are a specialist in {self._specialty}. "
            f"Answer the following question from this perspective: {message}"
        )
        response = await self.acompletion([{"role": "user", "content": enhanced}])
        return response.choices[0].message.content or ""


class RecursiveAgent(AgentBase):
    """An agent that uses chain-of-thought style multi-step asking."""

    @classmethod
    def create(cls, workspace_path: Path, profile: dict, config: dict) -> None:
        workspace_path = Path(workspace_path)
        workspace_path.mkdir(parents=True, exist_ok=True)
        (workspace_path / "config.json").write_text(
            json.dumps(config or {}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        agent_id = int(profile.get("id", 0))
        name = str(profile.get("name") or f"Agent_{agent_id}")
        (workspace_path / "AGENT.json").write_text(
            json.dumps(
                {
                    "id": agent_id,
                    "name": name,
                    "profile": profile,
                    "step_count": 0,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    async def from_workspace(
        cls, workspace_path: Path, service_proxy: Any
    ) -> "RecursiveAgent":
        agent = cls()
        await agent._restore(workspace_path, service_proxy)
        return agent

    async def _restore(self, workspace_path: Path, service_proxy: Any) -> None:
        workspace_path = Path(workspace_path)
        meta = json.loads((workspace_path / "AGENT.json").read_text(encoding="utf-8"))
        self._id = int(meta.get("agent_id", meta.get("id", 0)))
        self._profile = meta.get("profile", {"name": meta.get("name")})
        self._name = meta.get("name") or f"Agent_{self._id}"
        self._config = {}
        self._bind_services(service_proxy)
        self._step_count = int(meta.get("step_count", 0))

    async def to_workspace(self, workspace_path: Path) -> None:
        workspace_path = Path(workspace_path)
        (workspace_path / "AGENT.json").write_text(
            json.dumps(
                {
                    "id": self._id,
                    "name": self._name,
                    "profile": self.get_profile(),
                    "step_count": self._step_count,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    async def step(self, tick: int, t: datetime) -> str:
        self._step_count += 1
        return f"RecursiveAgent step {tick}"

    async def ask(
        self,
        message: str,
        readonly: bool = True,
        *,
        t: datetime | None = None,
    ) -> str:
        breakdown_prompt = (
            f"Break down this question into sub-questions: {message}\n"
            "Respond with a JSON object containing a 'sub_questions' array."
        )
        breakdown = await self._answer(breakdown_prompt)
        import json_repair

        try:
            parsed = json_repair.loads(breakdown)
            sub_questions = parsed.get("sub_questions", []) if isinstance(parsed, dict) else []
        except Exception:
            sub_questions = []

        if not sub_questions:
            return await self._answer(message)

        sub_answers = []
        for sq in sub_questions[:3]:
            answer = await self._answer(str(sq))
            sub_answers.append(f"Q: {sq}\nA: {answer}")

        synthesis_prompt = (
            f"Original question: {message}\n\n"
            f"Sub-question analysis:\n{chr(10).join(sub_answers)}\n\n"
            "Based on the above analysis, provide a comprehensive answer."
        )
        return await self._answer(synthesis_prompt)

    async def _answer(self, question: str) -> str:
        response = await self.acompletion([{"role": "user", "content": question}])
        return response.choices[0].message.content or ""


async def _run_registered_agent(
    *,
    agent_class: type[AgentBase],
    class_name: str,
    agent_specs: list[dict],
    run_dir: Path,
    question: str,
) -> None:
    get_registry().register_agent_module(class_name, agent_class, is_custom=True)
    names = [(spec["id"], spec["profile"]["name"]) for spec in agent_specs]
    society = AgentSociety(
        agent_specs=agent_specs,
        agent_class_name=class_name,
        env_router=CodeGenRouter(
            env_modules=[SimpleSocialSpace(agent_id_name_pairs=names)]
        ),
        start_t=datetime.now(),
        run_dir=run_dir,
    )
    await society.init()
    print(f"Question: {question}")
    print(f"Answer: {await society.ask(question)}\n")
    await society.close()


async def main() -> None:
    print("=== Custom Agent Examples ===\n")

    print("--- Specialist Agent ---\n")
    await _run_registered_agent(
        agent_class=SpecialistAgent,
        class_name="SpecialistAgent",
        agent_specs=[
            {
                "id": 1,
                "profile": {
                    "id": 1,
                    "name": "Dr. Climate",
                    "personality": "scientific and concerned",
                },
                "config": {"specialty": "climate science and environmental policy"},
            }
        ],
        run_dir=Path("run_specialist_agent"),
        question="What should cities do to prepare for extreme weather?",
    )

    print("--- Recursive (CoT) Agent ---\n")
    await _run_registered_agent(
        agent_class=RecursiveAgent,
        class_name="RecursiveAgent",
        agent_specs=[
            {
                "id": 3,
                "profile": {
                    "id": 3,
                    "name": "Deep Thinker",
                    "personality": "analytical and methodical",
                },
                "config": {},
            }
        ],
        run_dir=Path("run_recursive_agent"),
        question="How can we reduce urban traffic congestion?",
    )


if __name__ == "__main__":
    asyncio.run(main())
