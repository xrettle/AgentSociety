"""Correctness + same-condition A/B timing for concurrency / log tail."""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

import pytest

from agentsociety2.agent.person import PersonAgent
from agentsociety2.backend.routers.experiments import read_log_tail
from agentsociety2.contrib.env.economy_space import EconomySpace
from agentsociety2.contrib.env.global_information import GlobalInformationEnv
from agentsociety2.contrib.env.mobility_space.environment import MobilitySpace
from agentsociety2.contrib.env.simple_social_space import SimpleSocialSpace


def test_locked_contrib_modules_declare_concurrency_safe() -> None:
    assert SimpleSocialSpace.is_concurrency_safe() is True
    assert EconomySpace.is_concurrency_safe() is True
    assert GlobalInformationEnv.is_concurrency_safe() is True
    assert MobilitySpace.is_concurrency_safe() is True


def test_typical_stack_enables_env_actor_parallelism() -> None:
    types = [SimpleSocialSpace, GlobalInformationEnv, MobilitySpace]
    assert all(cls.is_concurrency_safe() for cls in types)


@pytest.mark.asyncio
async def test_module_local_locks_faster_than_global_lock() -> None:
    """A/B: global serialize lock (before) vs module-local locks (after)."""
    delay = 0.04
    n_per_module = 4
    lock_a = asyncio.Lock()
    lock_b = asyncio.Lock()
    global_lock = asyncio.Lock()

    async def ask(module_lock: asyncio.Lock, *, use_global: bool) -> None:
        if use_global:
            async with global_lock, module_lock:
                await asyncio.sleep(delay)
        else:
            async with module_lock:
                await asyncio.sleep(delay)

    async def run_batch(*, use_global: bool) -> float:
        t0 = time.perf_counter()
        await asyncio.gather(
            *(ask(lock_a, use_global=use_global) for _ in range(n_per_module)),
            *(ask(lock_b, use_global=use_global) for _ in range(n_per_module)),
        )
        return time.perf_counter() - t0

    before_s = await run_batch(use_global=True)
    after_s = await run_batch(use_global=False)
    assert before_s >= delay * (n_per_module * 2) * 0.85
    assert after_s <= before_s * 0.75
    assert after_s < delay * (n_per_module + 1.5)


def test_read_log_tail_ab_bytes_and_time(tmp_path: Path) -> None:
    """A/B: full read vs tail — bytes transferred and wall time."""
    log_path = tmp_path / "output.log"
    line = ("x" * 200) + "\n"
    with log_path.open("w", encoding="utf-8") as fh:
        for i in range(12_000):
            fh.write(f"{i:06d}:{line}")

    full_bytes = log_path.stat().st_size
    t0 = time.perf_counter()
    full_text = log_path.read_text(encoding="utf-8")
    before_ms = (time.perf_counter() - t0) * 1000
    before_bytes = len(full_text.encode("utf-8"))

    t0 = time.perf_counter()
    tail = read_log_tail(log_path, tail=500)
    after_ms = (time.perf_counter() - t0) * 1000
    after_bytes = len(tail.encode("utf-8"))

    assert after_bytes < before_bytes * 0.08
    assert after_ms < before_ms * 2.0 or after_ms < 50.0
    assert tail.splitlines()[-1].startswith("011999:")
    assert before_bytes == full_bytes or abs(before_bytes - full_bytes) < 8


def test_world_description_persists_in_agent_json(tmp_path: Path) -> None:
    agent = PersonAgent()
    agent._id = 1
    agent._name = "alice"
    agent._profile = {"name": "alice"}
    agent._config = {}
    agent._world_description = "A quiet riverside town."
    agent._bind_workspace(tmp_path)
    agent._setup_skill_runtime(agent_id=1)

    data = agent.build_agent_json(tick=3, t=datetime(2026, 1, 1, 12, 0, 0))
    assert data["world_description"] == "A quiet riverside town."
    assert "world_description" not in agent.build_prompt_agent_view(
        tick=3, t=datetime(2026, 1, 1, 12, 0, 0)
    )

    (tmp_path / "AGENT.json").write_text(json.dumps(data), encoding="utf-8")
    meta = json.loads((tmp_path / "AGENT.json").read_text(encoding="utf-8"))
    assert str(meta.get("world_description") or "") == "A quiet riverside town."


def test_rate_limit_retry_seconds_parses_provider_hint() -> None:
    from agentsociety2.config.llm_dispatcher import rate_limit_retry_seconds

    assert (
        rate_limit_retry_seconds(
            Exception("Try again in 60 seconds. Passed model=x"),
            1.0,
        )
        == 60.0
    )
    assert rate_limit_retry_seconds(Exception("no hint"), 1.5) == 1.5
