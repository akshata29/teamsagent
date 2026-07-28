"""Foundry hosted-agent entry point (Agent Framework).

Serves the Capital Markets research assistant on port 8088. Uses the in-container
``search_capital_markets_docs`` tool (app-only Search). Deployed as a hosted agent
via ``deploy/deploy_hosted_agent.py``.
"""

from __future__ import annotations

import logging
import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

from tools.search_tool import search_capital_markets_docs

logging.basicConfig(level=logging.INFO)

INSTRUCTIONS = (
    "You are a Capital Markets research desk assistant. Use the "
    "search_capital_markets_docs tool to ground every answer in internal research. "
    "Cite document ids in square brackets. If nothing relevant is entitled, say so. "
    "All content is synthetic demo data; never fabricate market data."
)


def build_agent() -> Agent:
    return Agent(
        client=FoundryChatClient(
            project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            model=os.environ.get("MODEL_DEPLOYMENT_NAME")
            or os.environ.get("FOUNDRY_MODEL_DEPLOYMENT", "gpt-4o"),
            credential=DefaultAzureCredential(),
        ),
        name=os.environ.get("FOUNDRY_AGENT_NAME", "capmarkets-research-agent"),
        instructions=INSTRUCTIONS,
        tools=[search_capital_markets_docs],
    )


if __name__ == "__main__":
    from agent_framework_foundry_hosting import ResponsesHostServer

    # Agent Framework Foundry hosting serves the agent over the Responses protocol.
    # The Foundry runtime injects PORT; default to 8088 (the container contract).
    port = int(os.environ.get("PORT", "8088"))
    ResponsesHostServer(build_agent()).run(host="0.0.0.0", port=port)
