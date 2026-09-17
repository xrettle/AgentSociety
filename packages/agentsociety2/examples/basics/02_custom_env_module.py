"""Custom Environment Module Example.

Shows how to define an EnvBase module with @tool methods and drive it through
AgentSociety using agent_specs (no direct PersonAgent construction).
"""

from __future__ import annotations

import os

os.environ.setdefault("MEM0_TELEMETRY", "False")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict

from agentsociety2.env import CodeGenRouter, EnvBase, tool
from agentsociety2.society import AgentSociety


class WeatherEnvironment(EnvBase):
    """A simple weather environment module."""

    def __init__(self) -> None:
        super().__init__()
        self._weather = "sunny"
        self._temperature = 25
        self._agent_locations: Dict[int, str] = {}

    @tool(readonly=True, kind="observe")
    def get_weather(self, agent_id: int) -> str:
        """Get the current weather for an agent's location."""
        location = self._agent_locations.get(agent_id, "unknown location")
        return (
            f"The weather in {location} is {self._weather} "
            f"with {self._temperature}°C."
        )

    @tool(readonly=False)
    def change_weather(self, weather: str, temperature: int) -> str:
        """Change the weather conditions."""
        self._weather = weather
        self._temperature = temperature
        return f"Weather changed to {weather} at {temperature}°C."

    @tool(readonly=False)
    def set_agent_location(self, agent_id: int, location: str) -> str:
        """Set an agent's location."""
        self._agent_locations[agent_id] = location
        return f"Agent {agent_id} is now in {location}."

    @tool(readonly=True, kind="statistics")
    def get_average_temperature(self) -> str:
        """Get the current average temperature."""
        return f"The current temperature is {self._temperature}°C."


async def main() -> None:
    run_dir = Path("run_custom_env")
    agent_specs = [
        {
            "id": i,
            "profile": {"id": i, "name": f"Agent{i}", "personality": "curious"},
            "config": {},
        }
        for i in range(1, 3)
    ]

    env_router = CodeGenRouter(env_modules=[WeatherEnvironment()])
    society = AgentSociety(
        agent_specs=agent_specs,
        agent_class_name="PersonAgent",
        env_router=env_router,
        start_t=datetime.now(),
        run_dir=run_dir,
    )
    await society.init()

    print("=== Custom Environment Module ===\n")

    print("1. What's the current environment state?")
    print(f"Answer: {await society.ask('What is the current weather and temperature?')}\n")

    print("2. Change the weather to rainy, 18°C")
    print(
        "Result:",
        await society.intervene(
            "Change the weather to rainy and set temperature to 18 degrees Celsius"
        ),
        "\n",
    )

    print("3. What's the weather now?")
    print(f"Answer: {await society.ask('What is the current temperature?')}\n")

    await society.close()


if __name__ == "__main__":
    asyncio.run(main())
