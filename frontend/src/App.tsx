import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import {
  generateEmail,
  regenerateDraft,
  listOAuthProviders,
  completeOAuth,
  getUserProfile,
  updateUserProfile,
  getDraftHistory,
  type EmailGenerateResponse,
  type OAuthCallbackResponse,
  type DraftHistoryEntry,
} from './lib/api'

const toneOptions = ['formal', 'casual', 'assertive', 'empathetic']

function App() {
  const [prompt, setPrompt] = useState('')
  
  // Restore auth session from localStorage first
  const [authResult, setAuthResult] = useState<OAuthCallbackResponse | null>(() => {
    const stored = localStorage.getItem('auth_result')
    if (stored) {
      try {
        return JSON.parse(stored)
      } catch {
        return null
      }
    }
    return null
  })
  
  // Restore user_id: prefer auth_result.user_id, fallback to stored user_id, then 'default'
  const [userId, setUserId] = useState(() => {
    const stored = localStorage.getItem('auth_result')
    if (stored) {
      try {
        const authData = JSON.parse(stored)
        if (authData?.user_id) {
          return authData.user_id
        }
      } catch {
        // ignore
      }
    }
    return localStorage.getItem('user_id') || 'default'
  })
  
  const [tone, setTone] = useState<string>('formal')
  const [lengthPreference, setLengthPreference] = useState<number>(150)
  const [recipient, setRecipient] = useState('')
  const [recipientEmail, setRecipientEmail] = useState('')
  const [useStub, setUseStub] = useState(false)
  const [saveToHistory, setSaveToHistory] = useState(true)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<EmailGenerateResponse | null>(null)
  const [draftText, setDraftText] = useState('')
  const [copyStatus, setCopyStatus] = useState<string | null>(null)

  const [providers, setProviders] = useState<string[]>([])
  const [authMessage, setAuthMessage] = useState<string | null>(null)

  const [profileLoading, setProfileLoading] = useState(false)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null)
  const [profileForm, setProfileForm] = useState({
    user_name: '',
    user_title: '',
    user_company: '',
    signature: '\n\nBest regards',
    style_notes: 'professional and clear',
  })
  // Track first-time auto initialization so we don't repeat
  const [autoInitDone, setAutoInitDone] = useState(false)

  const [history, setHistory] = useState<DraftHistoryEntry[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const [showHistory, setShowHistory] = useState(true)
  const [pendingContextReset, setPendingContextReset] = useState(false)

  // Regenerate state
  const [originalDraft, setOriginalDraft] = useState('')
  const [isEdited, setIsEdited] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [regenerateInfo, setRegenerateInfo] = useState<{ workflowType: string; diffRatio: number } | null>(null)

  const apiBase = useMemo(() => import.meta.env.VITE_API_BASE_URL, [])
  const normalizedUserId = useMemo(() => userId.trim() || 'default', [userId])

  function formatMetadataValue(value: unknown) {
    if (value === null || value === undefined) {
      return '—'
    }
    if (typeof value === 'object') {
      try {
        return JSON.stringify(value)
      } catch (error) {
        console.warn('Failed to stringify metadata value', error)
        return String(value)
      }
    }
    return String(value)
  }

  useEffect(() => {
    if (result?.draft) {
      setDraftText(result.draft)
    }
  }, [result?.draft])

  useEffect(() => {
    if (!copyStatus) return
    const timer = window.setTimeout(() => setCopyStatus(null), 2500)
    return () => window.clearTimeout(timer)
  }, [copyStatus])

  // Fetch available OAuth providers once so buttons only render when configured.
  useEffect(() => {
    listOAuthProviders().then(setProviders).catch(() => setProviders([]))
  }, [])

  // Persist userId to localStorage whenever it changes
  useEffect(() => {
    if (userId && userId !== 'default') {
      localStorage.setItem('user_id', userId)
    } else {
      localStorage.removeItem('user_id')
    }
  }, [userId])

  // Persist authResult to localStorage whenever it changes
  useEffect(() => {
    if (authResult) {
      localStorage.setItem('auth_result', JSON.stringify(authResult))
      // Also update userId if authResult has a user_id
      if (authResult.user_id && authResult.user_id !== userId) {
        setUserId(authResult.user_id)
      }
    } else {
      localStorage.removeItem('auth_result')
    }
  }, [authResult, userId])

  // Handle OAuth callback if provider redirected back with code/state.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const state = params.get('state')
    if (!code || !state) {
      return
    }

    const storedProvider = window.sessionStorage.getItem('pending_oauth_provider')
    const provider = params.get('provider') || storedProvider
    if (!provider) {
      setAuthMessage('OAuth provider name missing from callback.')
      window.history.replaceState({}, '', window.location.pathname)
      return
    }

    // De-dup guard: avoid exchanging the same code twice (React StrictMode/HMR)
    const exchangeKey = `oauth:exchanged:${provider}:${code}`
    if (window.sessionStorage.getItem(exchangeKey)) {
      // Already exchanged in this session; clean up URL and bail.
      setAuthMessage((m) => m || 'Sign-in already completed.')
      window.history.replaceState({}, '', window.location.pathname)
      return
    }

    let cancelled = false
    setAuthMessage('Completing sign-in…')
    // Mark as in-progress to prevent duplicate attempts
    window.sessionStorage.setItem(exchangeKey, '1')
    completeOAuth(provider, code, state)
      .then((response: OAuthCallbackResponse) => {
        if (cancelled) return
        setAuthResult(response)
        setAuthMessage(
          `Signed in with ${provider}${
            response.user_info?.email ? ` as ${response.user_info.email}` : ''
          }`,
        )
        window.sessionStorage.removeItem('pending_oauth_provider')
        if (response.user_id) {
          setUserId(response.user_id)
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const message = err instanceof Error ? err.message : 'OAuth callback failed.'
        setAuthMessage(message)
        // Allow retry on failure by clearing the guard
        window.sessionStorage.removeItem(exchangeKey)
      })
      .finally(() => {
        if (!cancelled) {
          window.history.replaceState({}, '', window.location.pathname)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Debounced load of profile and history when user id changes.
  useEffect(() => {
    let cancelled = false
    const timer = window.setTimeout(() => {
      setProfileLoading(true)
      setHistoryLoading(true)
      setProfileError(null)
      setHistoryError(null)
      setProfileSuccess(null)

      Promise.all([getUserProfile(normalizedUserId), getDraftHistory(normalizedUserId, 10)])
        .then(([profileData, historyData]) => {
          if (cancelled) return
          setProfileForm({
            user_name: profileData.user_name ?? '',
            user_title: profileData.user_title ?? '',
            user_company: profileData.user_company ?? '',
            signature: profileData.signature ?? '\n\nBest regards',
            style_notes: profileData.style_notes ?? 'professional and clear',
          })
          setHistory(historyData.drafts ?? [])
        })
        .catch((err: unknown) => {
          if (cancelled) return
          const message = err instanceof Error ? err.message : 'Failed to load profile'
          setProfileError(message)
          setHistoryError(message)
        })
        .finally(() => {
          if (!cancelled) {
            setProfileLoading(false)
            setHistoryLoading(false)
          }
        })
    }, 300)

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [normalizedUserId])

  // Auto-initialize & persist profile after first successful OAuth login if empty
  useEffect(() => {
    if (
      !autoInitDone &&
      authResult &&
      !profileLoading &&
      normalizedUserId !== 'default' &&
      profileForm.user_name.trim() === '' &&
      authResult.user_info?.name
    ) {
      const initial = {
        user_name: authResult.user_info.name ?? '',
        user_company: (() => {
          const email = authResult.user_info.email || ''
            ;
          if (email.includes('@')) {
            const domainPart = email.split('@')[1]
            const company = domainPart.split('.')[0]
            return company.charAt(0).toUpperCase() + company.slice(1)
          }
          return ''
        })(),
        user_title: '',
        signature: '\n\nBest regards',
        style_notes: 'professional and clear',
      }
      updateUserProfile(normalizedUserId, initial)
        .then((saved) => {
          setProfileForm({
            user_name: saved.user_name ?? initial.user_name,
            user_title: saved.user_title ?? '',
            user_company: saved.user_company ?? initial.user_company,
            signature: saved.signature ?? initial.signature,
            style_notes: saved.style_notes ?? initial.style_notes,
          })
        })
        .catch((e) => {
          console.warn('Auto profile init failed:', e)
        })
        .finally(() => setAutoInitDone(true))
    }
  }, [authResult, profileForm.user_name, profileLoading, normalizedUserId, autoInitDone])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setResult(null)

    if (!prompt.trim()) {
      setError('Please provide a description for the email.')
      return
    }

    const resetForThisCall = pendingContextReset
    setLoading(true)
    try {
      const response = await generateEmail({
        prompt,
        user_id: normalizedUserId,
        tone,
        recipient: recipient || undefined,
        recipient_email: recipientEmail || undefined,
        length_preference: lengthPreference,
        save_to_history: saveToHistory,
        use_stub: useStub,
        reset_context: resetForThisCall,
      })

      setResult(response)
      setPendingContextReset(false)
      // Store original draft for regeneration
      setOriginalDraft(response.draft)
      setIsEdited(false)
      setRegenerateInfo(null)
      if (response.saved) {
        try {
          const historyData = await getDraftHistory(normalizedUserId, 10)
          setHistory(historyData.drafts ?? [])
        } catch (historyErr) {
          const message =
            historyErr instanceof Error ? historyErr.message : 'Unable to refresh history.'
          setHistoryError(message)
        }
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Unexpected error while generating the email.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleCopyDraft() {
    try {
      await navigator.clipboard.writeText(draftText)
      setCopyStatus('Draft copied to clipboard.')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Copy failed.'
      setCopyStatus(message)
    }
  }

  async function handleRegenerate() {
    if (!isEdited || !originalDraft || !result) return

    setIsRegenerating(true)
    setError(null)
    try {
      const response = await regenerateDraft({
        original_draft: originalDraft,
        edited_draft: draftText,
        tone: result.metadata.tone as string || tone,
        intent: result.metadata.intent as string || 'outreach',
        recipient: recipient || undefined,
        length_preference: lengthPreference,
        user_id: normalizedUserId,
      })

      setDraftText(response.final_draft)
      setOriginalDraft(response.final_draft)
      setIsEdited(false)
      setRegenerateInfo({
        workflowType: response.workflow_type,
        diffRatio: response.diff_ratio,
      })
      setCopyStatus(`Regenerated using ${response.workflow_type} workflow (${(response.diff_ratio * 100).toFixed(0)}% changed)`)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Regeneration failed.'
      setError(message)
    } finally {
      setIsRegenerating(false)
    }
  }

  function handleDraftChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    const newValue = event.target.value
    setDraftText(newValue)
    setIsEdited(newValue !== originalDraft)
  }

  function handleLogout() {
    localStorage.removeItem('auth_result')
    setAuthResult(null)
    setAuthMessage('Signed out successfully.')
  }

  function handleStartOAuth(provider: string) {
    setAuthMessage(`OAuth with ${provider} is not yet implemented.`)
  }

  async function handleProfileSave(event: FormEvent) {
    event.preventDefault()
    setProfileError(null)
    setProfileSuccess(null)
    
    try {
      await updateUserProfile(normalizedUserId, profileForm)
      setProfileSuccess('Profile updated successfully!')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Profile update failed.'
      setProfileError(message)
    }
  }

  const isStubResponse = result?.metadata?.source === 'stub'
  const modelName =
    result && typeof result.metadata?.model === 'string'
      ? (result.metadata.model as string)
      : undefined
  const usage = result?.metrics
  const lastCall = usage?.last_call
  const metadataEntries = result ? Object.entries(result.metadata) : []
  const hasMetadata = metadataEntries.length > 0
  const hasReviewNotes = result ? Object.keys(result.review_notes).length > 0 : false
  const showDraftAside = hasMetadata || Boolean(usage)
  const settingsSubtitle = profileLoading
    ? 'Loading profile…'
    : authResult?.user_info?.email
    ? authResult.user_info.email
    : profileForm.user_name
    ? `Profile: ${profileForm.user_name}`
    : `User ID: ${normalizedUserId}`
  const effectiveContextMode = result?.context_mode ?? (pendingContextReset ? 'fresh' : 'contextual')
  const contextBadgeText =
    effectiveContextMode === 'fresh' ? 'Fresh Context' : 'Uses Previous Context'
  const nextDraftUsesFreshContext = pendingContextReset || history.length === 0
  const nextDraftBadgeText = nextDraftUsesFreshContext
    ? 'Next draft: Fresh context'
    : 'Next draft: Uses history'
  const nextDraftBadgeClass = nextDraftUsesFreshContext ? 'badge--success' : 'badge--info'

  function formatDraftSummary(text?: string | null) {
    if (!text) {
      return 'Draft'
    }
    const firstLine = text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .find((line) => line.length > 0)
    const summary = firstLine ?? text.trim()
    if (!summary) {
      return 'Draft'
    }
    return summary.length > 80 ? `${summary.slice(0, 80)}…` : summary
  }

  function formatTimestamp(value?: string | number | null) {
    if (!value) {
      return ''
    }
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) {
      return String(value)
    }
    return date.toLocaleString()
  }

  function handleResetContext() {
    setPendingContextReset(true)
    setError(null)
    setResult(null)
    setDraftText('')
    setCopyStatus(null)
  }

  return (
    <div className="app">
      <header className="app__header">
        <h1>AI Email Assistant</h1>
        <p className="app__subtitle">
          React frontend connected to the FastAPI workflow backend.
        </p>
        {apiBase ? (
          <span className="badge">API: {apiBase}</span>
        ) : (
          <span className="badge badge--warn">
            API base URL missing. Set VITE_API_BASE_URL.
          </span>
        )}
      </header>

      <details className="settings">
        <summary>
          <div className="settings__title">
            <span>Account &amp; Profile</span>
            <span className="settings__subtitle">{settingsSubtitle}</span>
          </div>
        </summary>
        <div className="settings__content">
          <div className="settings__section">
            <h3>Authentication</h3>
            {authResult ? (
              <div className="auth__info">
                <p>
                  Signed in via <strong>{authResult.provider}</strong>{' '}
                  {authResult.user_info?.email && (
                    <span>as {authResult.user_info.email}</span>
                  )}
                </p>
                <button className="button button--secondary" type="button" onClick={handleLogout}>
                  Sign out
                </button>
              </div>
            ) : providers.length > 0 ? (
              <div className="auth__providers">
                {providers.map((provider) => (
                  <button
                    key={provider}
                    type="button"
                    className="button button--secondary"
                    onClick={() => handleStartOAuth(provider)}
                  >
                    Sign in with {provider}
                  </button>
                ))}
              </div>
            ) : (
              <p className="status">OAuth providers unavailable.</p>
            )}
            {authMessage && <p className="status">{authMessage}</p>}
          </div>

          <div className="settings__section">
            <h3>Profile Details</h3>
            {profileLoading ? (
              <p className="status">Loading profile…</p>
            ) : (
              <form className="profile__form" onSubmit={handleProfileSave}>
                <label className="form__field">
                  <span>Name</span>
                  <input
                    value={profileForm.user_name}
                    onChange={(event) =>
                      setProfileForm((current) => ({
                        ...current,
                        user_name: event.target.value,
                      }))
                    }
                    placeholder="Jane Doe"
                  />
                </label>
                <label className="form__field">
                  <span>Title</span>
                  <input
                    value={profileForm.user_title}
                    onChange={(event) =>
                      setProfileForm((current) => ({
                        ...current,
                        user_title: event.target.value,
                      }))
                    }
                    placeholder="Product Manager"
                  />
                </label>
                <label className="form__field">
                  <span>Company</span>
                  <input
                    value={profileForm.user_company}
                    onChange={(event) =>
                      setProfileForm((current) => ({
                        ...current,
                        user_company: event.target.value,
                      }))
                    }
                    placeholder="Acme Corp"
                  />
                </label>
                <label className="form__field">
                  <span>Signature</span>
                  <textarea
                    rows={3}
                    value={profileForm.signature}
                    onChange={(event) =>
                      setProfileForm((current) => ({
                        ...current,
                        signature: event.target.value,
                      }))
                    }
                  />
                </label>
                <label className="form__field">
                  <span>Style notes</span>
                  <textarea
                    rows={2}
                    value={profileForm.style_notes}
                    onChange={(event) =>
                      setProfileForm((current) => ({
                        ...current,
                        style_notes: event.target.value,
                      }))
                    }
                  />
                </label>
                <button
                  className="button button--secondary"
                  type="submit"
                  disabled={profileLoading}
                >
                  {profileLoading ? 'Saving…' : 'Save profile'}
                </button>
                {profileError && <p className="form__error">{profileError}</p>}
                {profileSuccess && <p className="status status--success">{profileSuccess}</p>}
              </form>
            )}
          </div>
        </div>
      </details>

      <main className="layout">
        <section className="panel panel--form">
          <h2>Compose Request</h2>
          <form className="form" onSubmit={handleSubmit}>
            <label className="form__field">
              <span>Email description</span>
              <textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Describe the email you need..."
                rows={6}
                required
              />
            </label>

            <div className="form__grid">
              <label className="form__field">
                <span>User ID</span>
                <input
                  value={userId}
                  onChange={(event) => setUserId(event.target.value)}
                  placeholder="default"
                />
              </label>

              <label className="form__field">
                <span>Tone</span>
                <select
                  value={tone}
                  onChange={(event) => setTone(event.target.value)}
                >
                  {toneOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="form__grid">
              <label className="form__field">
                <span>Recipient name</span>
                <input
                  value={recipient}
                  onChange={(event) => setRecipient(event.target.value)}
                  placeholder="Jane Doe"
                />
              </label>

              <label className="form__field">
                <span>Recipient email</span>
                <input
                  type="email"
                  value={recipientEmail}
                  onChange={(event) => setRecipientEmail(event.target.value)}
                  placeholder="jane@example.com"
                />
              </label>
            </div>

            <label className="form__field">
              <span>Length preference: {lengthPreference} words</span>
              <input
                type="range"
                min={50}
                max={500}
                step={25}
                value={lengthPreference}
                onChange={(event) => setLengthPreference(Number(event.target.value))}
              />
            </label>

            <div className="form__toggles">
              <label>
                <input
                  type="checkbox"
                  checked={saveToHistory}
                  onChange={(event) => setSaveToHistory(event.target.checked)}
                />
                Save to history
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={useStub}
                  onChange={(event) => setUseStub(event.target.checked)}
                />
                Use stub (skip Gemini)
              </label>
            </div>

            <div className="form__actions">
              <button className="button" type="submit" disabled={loading}>
                {loading ? 'Generating…' : 'Generate Email'}
              </button>
              <button
                className="button button--secondary"
                type="button"
                onClick={handleResetContext}
              >
                Reset Context
              </button>
              <span className={`badge ${nextDraftBadgeClass}`}>
                {nextDraftBadgeText}
              </span>
            </div>

            {error && <p className="form__error">{error}</p>}
          </form>
        </section>

        <section className="panel panel--result">
          <h2>Draft Preview</h2>
          {loading && (
            <div className="draft__loading">
              <span className="spinner" aria-hidden="true" />
              <p>Generating draft…</p>
            </div>
          )}
          {!result && !loading && (
            <p className="placeholder">
              Submit a request to preview the generated email here.
            </p>
          )}

          {result && (
            <div className="draft">
              <div className="draft__status">
                <span className={`badge ${isStubResponse ? 'badge--warn' : 'badge--success'}`}>
                  {isStubResponse ? 'Stub Response' : 'LLM Response'}
                </span>
                {modelName && <span className="badge">Model: {modelName}</span>}
                <span
                  className={`badge ${
                    effectiveContextMode === 'fresh' ? 'badge--success' : 'badge--info'
                  }`}
                >
                  {contextBadgeText}
                </span>
                {copyStatus && <span className="status status--inline">{copyStatus}</span>}
              </div>

              <textarea
                className="draft__content"
                id="draft"
                value={draftText}
                onChange={handleDraftChange}
                rows={16}
              />

              <div className="draft__actions">
                <button className="button button--secondary" type="button" onClick={handleCopyDraft}>
                  Copy Draft
                </button>
                <button className="button button--secondary" type="button" onClick={handleRegenerate} disabled={isRegenerating || !isEdited}>
                  {isRegenerating ? 'Regenerating…' : 'Regenerate Draft'}
                </button>
                {regenerateInfo && (
                  <span className="regenerate-badge">
                    {regenerateInfo.workflowType === 'lightweight' ? '⚡ Quick polish' : '🔄 Full re-polish'}
                    {' '}({(regenerateInfo.diffRatio * 100).toFixed(0)}% changed)
                  </span>
                )}
              </div>

              {showDraftAside && (
                <div className="draft__insights">
                  <div className="draft__insights-left">
                    {hasMetadata && (
                      <details className="accordion" open>
                        <summary>Email Metadata</summary>
                        <dl className="metadata__list">
                          {metadataEntries.map(([key, value]) => (
                            <div key={key} className="metadata__item">
                              <dt>{key}</dt>
                              <dd>{formatMetadataValue(value)}</dd>
                            </div>
                          ))}
                        </dl>
                        <p className="metadata__status">
                          {result.saved ? 'Draft saved to history.' : 'Draft not persisted.'}
                        </p>
                      </details>
                    )}

                    {hasReviewNotes && (
                      <details className="accordion" open>
                        <summary>Review Notes</summary>
                        <pre className="draft__notes">{JSON.stringify(result.review_notes, null, 2)}</pre>
                      </details>
                    )}
                  </div>

                  {usage && (
                    <aside className="draft__insights-right">
                      <details className="accordion" open>
                        <summary>LLM Usage</summary>
                        <dl className="metrics__grid">
                          <div className="metadata__item">
                            <dt>LLM Calls</dt>
                            <dd>{usage.llm_calls}</dd>
                          </div>
                          <div className="metadata__item">
                            <dt>Total Tokens</dt>
                            <dd>{usage.total_tokens}</dd>
                          </div>
                          <div className="metadata__item">
                            <dt>Input Tokens</dt>
                            <dd>{usage.input_tokens}</dd>
                          </div>
                          <div className="metadata__item">
                            <dt>Output Tokens</dt>
                            <dd>{usage.output_tokens}</dd>
                          </div>
                          <div className="metadata__item">
                            <dt>Avg Latency</dt>
                            <dd>{usage.avg_latency_ms} ms</dd>
                          </div>
                          {usage.cost_tracking_enabled && (
                            <div className="metadata__item">
                              <dt>Est. Cost</dt>
                              <dd>${usage.estimated_cost_usd.toFixed(6)}</dd>
                            </div>
                          )}
                        </dl>
                        {lastCall && (
                          <p className="metadata__status">
                            Last call: {lastCall.model} • {lastCall.input_tokens + lastCall.output_tokens} tokens •{' '}
                            {lastCall.latency_ms.toFixed(0)} ms
                          </p>
                        )}
                      </details>
                    </aside>
                  )}
                </div>
              )}
            </div>
          )}
        </section>

      </main>

      {showHistory ? (
        <section className="panel panel--history panel--wide">
          <div className="panel__heading">
            <h2>Draft History</h2>
            <button
              className="history__toggle button button--secondary"
              type="button"
              onClick={() => setShowHistory(false)}
            >
              Hide
            </button>
          </div>
          {historyLoading ? (
            <p className="status">Loading history…</p>
          ) : history.length === 0 ? (
            <p className="placeholder">No drafts saved yet.</p>
          ) : (
            <div className="history__list">
              {history.map((entry, index) => {
                const subjectCandidate = entry.metadata?.['subject']
                const summarySource =
                  typeof subjectCandidate === 'string' && subjectCandidate.trim().length > 0
                    ? subjectCandidate
                    : entry.draft
                const summary = formatDraftSummary(summarySource)
                const timestamp = formatTimestamp(entry.timestamp)
                return (
                  <details key={entry.timestamp ?? index} className="history__item">
                    <summary>
                      <span>{summary}</span>
                      {timestamp && <span className="history__timestamp">{timestamp}</span>}
                    </summary>
                    <div className="history__content">
                      <pre>{entry.draft}</pre>
                      {entry.metadata && (
                        <dl>
                          {Object.entries(entry.metadata).map(([key, value]) => (
                            <div key={key} className="metadata__item">
                              <dt>{key}</dt>
                              <dd>{formatMetadataValue(value)}</dd>
                            </div>
                          ))}
                        </dl>
                      )}
                    </div>
                  </details>
                )
              })}
            </div>
          )}
          {historyError && <p className="form__error">{historyError}</p>}
        </section>
      ) : (
        <button className="history__expand" type="button" onClick={() => setShowHistory(true)}>
          Show History
        </button>
      )}
    </div>
  )
}

export default App
