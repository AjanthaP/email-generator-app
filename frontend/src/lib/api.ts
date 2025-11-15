export interface EmailGenerateRequest {
  prompt: string
  user_id?: string
  tone?: string
  recipient?: string
  recipient_email?: string
  length_preference?: number
  save_to_history?: boolean
  use_stub?: boolean
  reset_context?: boolean
}

export interface MetricsSummary {
  session_id: string
  llm_calls: number
  successful_calls: number
  input_tokens: number
  output_tokens: number
  total_tokens: number
  estimated_cost_usd: number
  avg_latency_ms: number
  errors: number
  feature_enabled: boolean
  cost_tracking_enabled: boolean
  last_call?: {
    model: string
    latency_ms: number
    input_tokens: number
    output_tokens: number
    cost_usd: number
    error?: string | null
    timestamp: number
  }
}

export interface EmailGenerateResponse {
  draft: string
  metadata: Record<string, unknown>
  review_notes: Record<string, unknown>
  saved: boolean
  metrics: MetricsSummary
  context_mode: string
}

export interface OAuthStartResponse {
  authorization_url: string
  state: string
  session_id?: string
  provider: string
}

export interface OAuthCallbackResponse {
  session_id: string
  provider: string
  user_id?: string | null
  user_info: Record<string, string | null | undefined>
  tokens: Record<string, string | null | undefined>
}

export interface UserProfile {
  user_id: string
  user_name: string
  user_title: string
  user_company: string
  signature: string
  style_notes: string
  preferences: Record<string, unknown>
  learned_preferences: Record<string, unknown>
}

export interface UserProfileUpdate {
  user_name?: string
  user_title?: string
  user_company?: string
  signature?: string
  style_notes?: string
  preferences?: Record<string, unknown>
  learned_preferences?: Record<string, unknown>
}

export interface DraftHistoryEntry {
  draft: string
  metadata?: Record<string, unknown>
  timestamp?: string
  [key: string]: unknown
}

export interface DraftHistoryResponse {
  drafts: DraftHistoryEntry[]
}

export interface LearnFromEditsPayload {
  original: string
  edited: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    ...options,
  })

  const contentType = response.headers.get('content-type') ?? ''
  const isJson = contentType.includes('application/json')
  const payload = isJson ? await response.json().catch(() => ({})) : await response.text()

  if (!response.ok) {
    const detail = typeof payload === 'string' ? undefined : (payload as { detail?: string }).detail
    throw new Error(detail || `Request failed with status ${response.status}`)
  }

  return (payload as T) ?? ({} as T)
}

export async function generateEmail(payload: EmailGenerateRequest) {
  return request<EmailGenerateResponse>(`/email/generate`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function listOAuthProviders() {
  return request<string[]>(`/auth/providers`).catch((error) => {
    // Surface empty list when OAuth is disabled rather than failing the UI entirely.
    console.warn('OAuth providers unavailable:', error)
    return []
  })
}

export async function startOAuth(provider: string, userId?: string) {
  return request<OAuthStartResponse>(`/auth/start`, {
    method: 'POST',
    body: JSON.stringify({ provider, user_id: userId }),
  })
}

export async function completeOAuth(provider: string, code: string, state: string) {
  // Use SPA-friendly POST exchange to avoid CORS on callback fetch
  return request<OAuthCallbackResponse>(`/auth/exchange`, {
    method: 'POST',
    body: JSON.stringify({ provider, code, state }),
  })
}

export async function logout() {
  return request<{ status: string }>(`/auth/logout`, {
    method: 'POST',
  })
}

export async function getUserProfile(userId: string) {
  return request<UserProfile>(`/users/${encodeURIComponent(userId)}/profile`)
}

export async function updateUserProfile(userId: string, payload: UserProfileUpdate) {
  return request<UserProfile>(`/users/${encodeURIComponent(userId)}/profile`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function getDraftHistory(userId: string, limit = 20) {
  const params = new URLSearchParams({ limit: String(limit) })
  return request<DraftHistoryResponse>(
    `/users/${encodeURIComponent(userId)}/history?${params.toString()}`,
  )
}

export async function learnFromEdits(userId: string, payload: LearnFromEditsPayload) {
  return request<{ status: string }>(
    `/users/${encodeURIComponent(userId)}/history/learn`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )
}
