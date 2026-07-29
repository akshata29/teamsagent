// Option B — Custom Engine Agent proxy (the OBO trust boundary).
//
// Flow per Teams message:
//   1. The `search` authorization handler runs Teams SSO (auto-triggered because the
//      message route lists it in authHandlers).
//   2. authorization.exchangeToken(...) performs the On-Behalf-Of exchange for the
//      Azure AI Search scope — a token that represents the SIGNED-IN Teams user.
//   3. We POST the Capital Markets backend Option B endpoint, passing that token in
//      `x-ms-query-source-authorization` so Azure AI Search trims documents per user.
//   4. The backend returns the grounded answer + entitled docs; we render an Adaptive
//      Card (Teams-native rich UI with citations + a "trimmed for you" footer).
import { ActivityTypes } from "@microsoft/agents-activity";
import {
  AgentApplication,
  CardFactory,
  MemoryStorage,
  MessageFactory,
  TurnContext,
} from "@microsoft/agents-hosting";
import axios from "axios";
import config from "./config";
import { buildResearchCard, buildWelcomeCard } from "./cards";

const AUTH_HANDLER = "search";

// Define storage and application
const storage = new MemoryStorage();
export const agentApp = new AgentApplication({
  storage,
  authorization: {
    // Teams SSO + OBO handler. The Azure Bot OAuth connection issues the user token;
    // oboScopes drives the On-Behalf-Of exchange for Azure AI Search.
    [AUTH_HANDLER]: {
      azureBotOAuthConnectionName: config.oauthConnectionName,
      oboScopes: [config.searchScope],
      enableSso: true,
      title: "Sign in to Capital Markets Research",
      text: "Sign in so your results are trimmed to your entitlements.",
    },
  },
});

/** Run a research query: OBO -> backend Option B -> Adaptive Card. */
async function runResearch(context: TurnContext, query: string): Promise<void> {
  let searchToken: string | undefined;
  if (config.requireSso) {
    try {
      // On-Behalf-Of: exchange the Teams SSO token for an Azure AI Search token.
      const tokenResponse = await agentApp.authorization.exchangeToken(
        context,
        [config.searchScope],
        AUTH_HANDLER,
      );
      searchToken = tokenResponse?.token;
    } catch (ex) {
      // Not signed in yet / exchange pending — fall through and let the backend
      // fail-closed to public-only, with a "sign in" hint on the card.
      console.error("[OBO] exchangeToken failed:", (ex as Error)?.message ?? ex);
    }
  }

  try {
    const { data } = await axios.post(
      `${config.backendUrl}/api/demo/optionB/invoke`,
      { persona_id: config.defaultPersonaId, query, variant: "b1" },
      {
        headers: searchToken ? { "x-ms-query-source-authorization": searchToken } : {},
        timeout: 60000,
      },
    );
    await context.sendActivity(
      MessageFactory.attachment(CardFactory.adaptiveCard(buildResearchCard(data))),
    );
  } catch (err) {
    await context.sendActivity(
      `Sorry - I couldn't reach the research backend. ${
        (err as Error)?.message ?? ""
      }`.trim(),
    );
  }
}

agentApp.onConversationUpdate("membersAdded", async (context: TurnContext) => {
  await context.sendActivity(
    MessageFactory.attachment(CardFactory.adaptiveCard(buildWelcomeCard())),
  );
});

// Message route. When SSO is required (real Teams), listing AUTH_HANDLER auto-triggers
// the Teams sign-in flow before the handler runs. In the Agents Playground (no SSO),
// REQUIRE_SSO=false so the route is unauthenticated and the OBO exchange is skipped.
const messageHandler = async (context: TurnContext): Promise<void> => {
  // Adaptive Card Action.Submit sends the refinement query in activity.value.
  const submitted = (context.activity.value as { query?: string } | undefined)?.query;
  const query = (submitted ?? context.activity.text ?? "").trim();
  if (!query) {
    await context.sendActivity("Ask a Capital Markets research question.");
    return;
  }
  await runResearch(context, query);
};

if (config.requireSso) {
  agentApp.onActivity(ActivityTypes.Message, messageHandler, [AUTH_HANDLER]);
} else {
  agentApp.onActivity(ActivityTypes.Message, messageHandler);
}

agentApp.authorization.onSignInSuccess(async (context: TurnContext) => {
  await context.sendActivity("Signed in - ask your question to see per-user results.");
});

// Surface the real reason an SSO/OAuth sign-in failed (AADSTS code, consent, etc.)
// instead of the SDK's generic "Failed to sign-in" card.
// SDK signature: (context, state, authHandlerId, errorMessage).
const onFail = (agentApp.authorization as unknown as {
  onSignInFailure?: (
    h: (context: TurnContext, state: unknown, authHandlerId?: string, reason?: unknown) => Promise<void> | void,
  ) => void;
}).onSignInFailure;
if (typeof onFail === "function") {
  onFail.call(
    agentApp.authorization,
    async (context: TurnContext, _state: unknown, authHandlerId?: string, reason?: unknown) => {
      let detail: string;
      try {
        detail =
          typeof reason === "string" ? reason : JSON.stringify(reason, Object.getOwnPropertyNames(reason ?? {}));
      } catch {
        detail = String(reason);
      }
      console.error(`[SSO] sign-in failed (handler=${authHandlerId}):`, detail);
      await context.sendActivity(
        "Sign-in couldn't complete silently. (Check proxy logs for the AADSTS detail.)",
      );
    },
  );
}
