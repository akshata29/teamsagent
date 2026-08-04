// Shared TypeScript types mirroring the backend Pydantic models.

export type DemoOption = 'A' | 'B1' | 'B2'
export type IdentityBasis = 'app_only' | 'per_user_obo' | 'public_only'
export type Classification = 'public' | 'internal' | 'mnpi'

export interface Persona {
  id: string
  display_name: string
  role: string
  entra_group_id: string
  entitlement_summary: string
}

export interface DocHit {
  id: string
  title: string
  classification: Classification
  snippet: string
  score: number | null
  entitled_to?: string[]
}

export interface InvokeRequest {
  persona_id: string
  query: string
  variant?: string | null
}

export interface InvokeResult {
  option: DemoOption
  persona_id: string
  query: string
  answer: string
  doc_hits: DocHit[]
  visible_doc_ids: string[]
  trimmed_doc_ids: string[]
  identity_basis: IdentityBasis
  latency_ms: number
  trace_id: string | null
  note: string | null
}

export interface CompareResult {
  persona_id: string
  query: string
  option_a: InvokeResult
  option_b: InvokeResult
  difference_doc_ids: string[]
}

export interface AuditRecord {
  timestamp: string
  persona_id: string
  entra_group_id: string
  option: DemoOption
  query: string
  visible_doc_ids: string[]
  trimmed_doc_ids: string[]
  identity_basis: IdentityBasis
  trace_id: string | null
}

export interface SettingsView {
  use_native_acl: boolean
  use_deployed_agent: boolean
  offline_mode: boolean
  azure_configured: boolean
  search_api_version: string
  foundry_agent_name: string
  default_b_variant: string
}
