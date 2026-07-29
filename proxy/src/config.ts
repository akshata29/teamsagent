// Runtime configuration for the Option B Custom Engine Agent proxy.
//
// The proxy is the trust boundary: it performs Teams SSO + On-Behalf-Of (OBO) to
// obtain an Azure AI Search-scoped token for the signed-in Teams user, then calls
// the Capital Markets backend so Search results are trimmed per user.
const config = {
  // Capital Markets FastAPI backend (per-user retrieval + hosted-agent synthesis).
  backendUrl: process.env.BACKEND_URL ?? "http://localhost:8010",
  // Azure Bot Service OAuth connection name (Teams SSO connection on the bot).
  oauthConnectionName: process.env.AAD_OAUTH_CONNECTION_NAME ?? "search-sso",
  // Downstream OBO scope — Azure AI Search.
  searchScope: process.env.OBO_SCOPE ?? "https://search.azure.com/.default",
  // Persona used for backend audit / GA-trimming fallback. With native ACL the real
  // trimming comes from the OBO token, so this is mostly for display/audit.
  defaultPersonaId: process.env.DEMO_PERSONA_ID ?? "equity-research",
  // Require Teams SSO before answering (auto-triggers sign-in on the message route).
  // Set REQUIRE_SSO=false for the Agents Playground, which does not support SSO — the
  // handler then runs without gating and the backend fail-closes to public-only.
  requireSso: (process.env.REQUIRE_SSO ?? "true").toLowerCase() !== "false",
};

export default config;
