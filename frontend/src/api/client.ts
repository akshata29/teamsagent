// Axios instance + typed API namespace for the demo backend.
import axios from 'axios'
import type {
  AuditRecord,
  CompareResult,
  DocHit,
  InvokeRequest,
  InvokeResult,
  Persona,
  SettingsView,
} from '@/types/demo'
import { apiScope, authEnabled, loginRequest, msalInstance } from '@/auth/msalConfig'

const api = axios.create({ baseURL: '/api' })

// Attach the signed-in user's access token so the backend can perform the OBO
// exchange for Azure AI Search (per-user document-level trimming). When no user is
// signed in (or auth is disabled), requests go out unauthenticated and the backend
// falls back to persona simulation / public-only.
api.interceptors.request.use(async (config) => {
  if (!authEnabled) return config
  const account = msalInstance.getActiveAccount() ?? msalInstance.getAllAccounts()[0]
  if (!account) return config
  try {
    const result = await msalInstance.acquireTokenSilent({
      scopes: apiScope ? [apiScope] : loginRequest.scopes,
      account,
    })
    config.headers.set('Authorization', `Bearer ${result.accessToken}`)
  } catch {
    // Silent acquisition failed (e.g. consent/interaction required) — send
    // unauthenticated; the UI sign-in button will prompt interactively.
  }
  return config
})

export const demoApi = {
  async getPersonas(): Promise<Persona[]> {
    const { data } = await api.get<Persona[]>('/demo/personas')
    return data
  },
  async getCorpus(): Promise<DocHit[]> {
    const { data } = await api.get<DocHit[]>('/demo/corpus')
    return data
  },
  async invokeA(req: InvokeRequest): Promise<InvokeResult> {
    const { data } = await api.post<InvokeResult>('/demo/optionA/invoke', req)
    return data
  },
  async invokeB(req: InvokeRequest): Promise<InvokeResult> {
    const { data } = await api.post<InvokeResult>('/demo/optionB/invoke', req)
    return data
  },
  async compare(req: InvokeRequest): Promise<CompareResult> {
    const { data } = await api.post<CompareResult>('/demo/compare', req)
    return data
  },
  async getAudit(limit = 50): Promise<AuditRecord[]> {
    const { data } = await api.get<AuditRecord[]>('/demo/audit', { params: { limit } })
    return data
  },
  async getSettings(): Promise<SettingsView> {
    const { data } = await api.get<SettingsView>('/settings')
    return data
  },
}
