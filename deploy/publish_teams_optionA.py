"""Option A — publish the hosted agent to Teams / M365 Copilot (direct Foundry publish).

Steps (GA publish flow):
  1. Ensure the Microsoft.BotService resource provider is registered.
  2. Ensure the agent has the `activity` protocol + a BotService auth scheme enabled.
  3. POST the microsoft365/publish request with the Bot Service ARM id + publish scope.
  4. Download the Teams app manifest .zip for sideloading / admin approval.

RBAC prereqs: Foundry User (on the project) + Azure Bot Service Contributor
(Microsoft.BotService/botServices/write + .../channels/write). Tenant scope also
requires M365 admin approval in the admin center.

Run:  python -m deploy.publish_teams_optionA
"""

from __future__ import annotations

import os

import requests
from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")
AGENT_NAME = os.environ.get("FOUNDRY_AGENT_NAME", "capmarkets-research-agent")
BOT_SERVICE_ARM_ID = os.environ.get("BOT_SERVICE_ARM_ID", "")
PUBLISH_SCOPE = os.environ.get("PUBLISH_SCOPE", "Tenant")  # 'Shared' or 'Tenant'


def _token() -> str:
    cred = DefaultAzureCredential()
    # Cognitive Services / Foundry data-plane scope.
    return cred.get_token("https://ai.azure.com/.default").token


def publish() -> dict:
    if not BOT_SERVICE_ARM_ID:
        raise SystemExit("Set BOT_SERVICE_ARM_ID (deploy the Bot Service via bicep first).")

    url = f"{PROJECT_ENDPOINT}/agents/{AGENT_NAME}/microsoft365/publish?api-version=v1"
    headers = {
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
    }
    body = {
        "botServiceArmId": BOT_SERVICE_ARM_ID,
        "publishScope": PUBLISH_SCOPE,  # Shared -> BotServiceRbac, Tenant -> BotServiceTenant
    }
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    result = publish()
    print("Publish accepted:", result)
    print(
        "Next: download the Teams manifest from the Foundry portal and upload via "
        "Teams > Apps > Manage your apps > Upload an app. Tenant scope needs M365 admin "
        "approval at admin.cloud.microsoft/#/agents/all/requested."
    )
