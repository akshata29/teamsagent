// Option B — Custom Engine Agent message handler.
//
// Flow (the per-user OBO trust boundary):
//   1. Teams SSO provides the signed-in user token.
//   2. exchangeToken (MSAL OBO) exchanges it for a downstream token
//      (OBOConnectionName / OBOScopes = https://search.azure.com/.default).
//   3. The proxy calls the Capital Markets backend, which performs the per-user
//      AI Search retrieval + hosted-agent synthesis and returns a grounded answer.
//
// This file shows the wiring; `atk provision` generates the bot/app registrations.

import { ActivityHandler, TurnContext } from '@microsoft/agents-hosting'
import axios from 'axios'

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8010'
const OBO_CONNECTION = process.env.OBOConnectionName ?? 'search-obo'
const PERSONA_ID = process.env.DEMO_PERSONA_ID ?? 'equity-research'

export class CapMarketsAgent extends ActivityHandler {
  constructor() {
    super()

    this.onMessage(async (context: TurnContext, next) => {
      const query = (context.activity.text ?? '').trim()
      if (!query) {
        await context.sendActivity('Ask a Capital Markets research question.')
        await next()
        return
      }

      // 1 + 2: Teams SSO -> OBO exchange for the Azure AI Search scope.
      const userSearchToken = await exchangeForSearchToken(context)

      // 3: Call the backend Option B path (per-user OBO retrieval + hosted agent).
      const { data } = await axios.post(`${BACKEND_URL}/api/demo/optionB/invoke`, {
        persona_id: resolvePersona(context),
        query,
        variant: 'b1',
      }, {
        headers: userSearchToken
          ? { 'x-ms-query-source-authorization': userSearchToken }
          : {},
      })

      const cited = (data.doc_hits ?? []).map((d: { id: string }) => `[${d.id}]`).join(' ')
      await context.sendActivity(`${data.answer}\n\nSources: ${cited || '(none)'}`)
      await next()
    })
  }
}

/** Exchange the Teams-user token for a Search-scoped OBO token. */
async function exchangeForSearchToken(context: TurnContext): Promise<string | undefined> {
  try {
    // The Agents SDK exposes the OBO exchange on the user-token client.
    // Signature varies by SDK version: exchangeToken / ExchangeTurnTokenAsync.
    const userTokenClient = (context.adapter as unknown as {
      exchangeToken?: (ctx: TurnContext, connectionName: string, scopes: string[]) => Promise<{ token: string }>
    }).exchangeToken
    if (!userTokenClient) return undefined
    const result = await userTokenClient(context, OBO_CONNECTION, [
      'https://search.azure.com/.default',
    ])
    return result?.token
  } catch {
    // Fail-closed: without a token the backend returns public-only documents.
    return undefined
  }
}

function resolvePersona(context: TurnContext): string {
  // In production, derive the persona/entitlements from the signed-in user's
  // Entra group membership. For the demo we default to a configured persona.
  return (context.activity.from?.aadObjectId && PERSONA_ID) || PERSONA_ID
}
