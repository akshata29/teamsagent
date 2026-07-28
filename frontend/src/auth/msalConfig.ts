// MSAL (Microsoft Authentication Library) configuration for SPA sign-in.
//
// The browser signs the user in against Entra ID and acquires an access token for
// THIS backend's API scope (api://<backend-app>/access_as_user). That token is sent
// as `Authorization: Bearer <token>` to the backend, which performs the On-Behalf-Of
// exchange for Azure AI Search — the same per-user retrieval path the Teams proxy
// drives, so one agent works in both surfaces.
//
// Values come from Vite env (frontend/.env.local). If VITE_AAD_CLIENT_ID is unset,
// auth is disabled and the app runs in persona-simulation mode as before.
import { PublicClientApplication, type Configuration } from '@azure/msal-browser'

const clientId = import.meta.env.VITE_AAD_CLIENT_ID as string | undefined
const tenantId = (import.meta.env.VITE_AAD_TENANT_ID as string | undefined) ?? 'common'
const redirectUri =
  (import.meta.env.VITE_REDIRECT_URI as string | undefined) ?? window.location.origin

/** True when SPA sign-in is configured. */
export const authEnabled = Boolean(clientId)

/** The backend API scope the SPA requests a token for. */
export const apiScope =
  (import.meta.env.VITE_API_SCOPE as string | undefined) ??
  (clientId ? `api://${clientId}/access_as_user` : '')

const msalConfig: Configuration = {
  auth: {
    clientId: clientId ?? '00000000-0000-0000-0000-000000000000',
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
}

export const msalInstance = new PublicClientApplication(msalConfig)

/** Scopes requested at login (backend API scope + basic profile). */
export const loginRequest = {
  scopes: apiScope ? [apiScope] : ['openid', 'profile'],
}
