"""Deploy the Capital Markets container as a Foundry HOSTED agent.

Builds/pushes the container image (done separately with docker/az acr), then creates
or updates the hosted-agent definition via azure-ai-projects (>= 2.3.0).

Run:  python -m deploy.deploy_hosted_agent
Prereq: the image at $AGENT_IMAGE has been pushed to a registry the project can pull.
"""

from __future__ import annotations

import os

from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
AGENT_NAME = os.environ.get("FOUNDRY_AGENT_NAME", "capmarkets-research-agent")
AGENT_IMAGE = os.environ.get("AGENT_IMAGE", "<registry>.azurecr.io/capmarkets-agent:latest")
# The in-container agent-framework Responses path adds `reasoning.encrypted_content`
# for stateless calls, which gpt-4o rejects. Use a model that supports it
# (GPT-5 family or a reasoning model, e.g. chat5nano / chato4mini / chato1).
MODEL = os.environ.get("AGENT_MODEL_DEPLOYMENT", "chat5nano")


def main() -> None:
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import (
        AgentEndpointProtocol,
        ContainerConfiguration,
        HostedAgentDefinition,
        ProtocolVersionRecord,
    )

    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    # Hosted-agent definition references the pushed container image. The container
    # brings its own model (agent/app.py uses FoundryChatClient + FOUNDRY_MODEL_DEPLOYMENT);
    # env passed here supplies the Search endpoint/index so the in-container app-only
    # tool can query. The container serves the Responses protocol on port 8088 — this
    # MUST be declared via protocol_versions or provisioning fails.
    definition = HostedAgentDefinition(
        protocol_versions=[
            ProtocolVersionRecord(protocol=AgentEndpointProtocol.RESPONSES, version="2.0.0")
        ],
        cpu=os.environ.get("AGENT_CPU", "1"),
        memory=os.environ.get("AGENT_MEMORY", "2Gi"),
        container_configuration=ContainerConfiguration(image=AGENT_IMAGE),
        environment_variables={
            "SEARCH_ENDPOINT": os.environ.get("SEARCH_ENDPOINT", ""),
            "SEARCH_INDEX_NAME": os.environ.get("SEARCH_INDEX_NAME", "capmarkets-research"),
            "SEARCH_API_VERSION": os.environ.get("SEARCH_API_VERSION", "2026-05-01-preview"),
            "MODEL_DEPLOYMENT_NAME": MODEL,
        },
    )

    result = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=definition,
    )
    print(f"Deployed hosted agent '{AGENT_NAME}': {result}")


if __name__ == "__main__":
    main()
