'use client'

import { useState } from 'react'
import {
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  BriefcaseMedical,
  Building2,
  CheckCircle2,
  FileText,
  Globe2,
  Landmark,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

type Evidence = {
  evidence_id: string
  authority_name: string
  document_title: string
  citation: string
  source_url: string
  jurisdiction: string
  status: string
  relevance_score: number
  verified: boolean
  demo_only?: boolean
}

type Result = {
  summary: string
  classification: { category: string; confidence: number; missing_facts?: string[] }
  applicable_domains: string[]
  recommendations: { text: string; why: string; citations: string[]; confidence: string }[]
  risks: string[]
  next_steps: string[]
  human_review: boolean
  evidence: Evidence[]
  source_pointers?: SourcePointer[]
  trace_id: string
  memory_used?: boolean
  demo_mode?: boolean
  international_profile?: { country: string; mode: string }
}

type SourcePointer = {
  authority: string
  title: string
  url: string
  topic: string
  source_type: string
  verified_as_evidence: boolean
}

type ChatMessage = {
  role: 'user' | 'assistant'
  text: string
  evidence?: Evidence[]
  sourcePointers?: SourcePointer[]
  risks?: string[]
  sourceCheck?: boolean
}

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const demoPrompts = [
  'I have a turmeric-based Ayurvedic formulation and want to sell it in Germany.',
  'Can I protect an Ashwagandha product and what claims are safe to make?',
  'We want to export an herbal supplement into the US with a new formulation.',
]

export default function Home() {
  const [mode, setMode] = useState<'india' | 'international'>('international')
  const [country, setCountry] = useState('DE')
  const [input, setInput] = useState(demoPrompts[0])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Result | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [userId, setUserId] = useState('')
  const [error, setError] = useState<string | null>(null)

  const activeCountryLabel = country === 'DE' ? 'Germany' : country === 'US' ? 'United States' : country === 'AE' ? 'UAE' : country === 'JP' ? 'Japan' : country === 'AU' ? 'Australia' : 'Brazil'

  async function send() {
    const trimmed = input.trim()
    if (!trimmed || loading) return

    setLoading(true)
    setError(null)
    const activeUserId = userId || crypto.randomUUID()
    if (!userId) setUserId(activeUserId)
    setMessages((m) => [...m, {
      role: 'user',
      text: trimmed,
    }])

    try {
      const response = await fetch(`${API}/api/v1/consultations/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          language: 'en',
          jurisdiction_mode: mode,
          target_country: mode === 'international' ? country : null,
          user_id: activeUserId,
        }),
      })

      const payload = (await response.json()) as Result & { detail?: string }
      if (!response.ok) {
        throw new Error(payload?.detail || 'Request failed')
      }

      setResult(payload)
      setMessages((m) => [...m, {
        role: 'assistant',
        text: payload.summary || 'Here is the preliminary guidance.',
        evidence: payload.evidence,
        sourcePointers: payload.source_pointers,
        risks: payload.risks,
        sourceCheck: true,
      }])

    } catch (err) {
      const message = err instanceof Error ? err.message : 'API unavailable. Start the FastAPI service.'
      setError(message)
      setMessages((m) => [...m, {
        role: 'assistant',
        text: message,
      }])

    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-icon">
            <ShieldCheck size={18} />
          </div>
          <div>
            <div className="brand-title">IP-SAKTI SAHAYAK</div>
            <div className="brand-subtitle">Evidence-first legal navigator</div>
          </div>
        </div>

        <div className="toolbar">
          <button
            className={`segmented ${mode === 'india' ? 'active' : ''}`}
            onClick={() => setMode('india')}
          >
            <Landmark size={14} /> India
          </button>
          <button
            className={`segmented ${mode === 'international' ? 'active' : ''}`}
            onClick={() => setMode('international')}
          >
            <Globe2 size={14} /> International
          </button>

          {mode === 'international' && (
            <select className="country-select" value={country} onChange={(e) => setCountry(e.target.value)}>
              <option value="DE">Germany</option>
              <option value="US">United States</option>
              <option value="AE">UAE</option>
              <option value="JP">Japan</option>
              <option value="AU">Australia</option>
              <option value="BR">Brazil</option>
            </select>
          )}
        </div>
      </header>

      <main className="dashboard-grid">
        <aside className="panel left-panel">
          <div className="panel-header">
            <BriefcaseMedical size={16} />
            <span>Case Library</span>
          </div>

          <button className="primary-btn" onClick={() => { setMessages([]); setResult(null); setError(null); setUserId(crypto.randomUUID()) }}>
            + New case
          </button>

          <div className="prompt-list">
            {demoPrompts.map((prompt) => (
              <button
                key={prompt}
                className="prompt-chip"
                onClick={() => {
                  setInput(prompt)
                  if (prompt.includes('Germany')) {
                    setMode('international')
                    setCountry('DE')
                  } else if (prompt.includes('US')) {
                    setMode('international')
                    setCountry('US')
                  } else {
                    setMode('india')
                  }
                }}
              >
                {prompt}
              </button>
            ))}
          </div>

          <div className="mini-card">
            <div className="mini-label">Safety architecture</div>
            <div className="mini-value">Evidence → Verify → Act</div>
          </div>
          <div className="mini-card">
            <div className="mini-label">Human review</div>
            <div className="mini-value">Escalate when evidence is weak</div>
          </div>
        </aside>

        <section className="chat-panel">
          <div className="chat-header">
            <div>
              <div className="chat-title">Ayurveda Legal & Regulatory Navigator</div>
              <div className="chat-subtitle">Classification-first • jurisdiction-aware • source-grounded</div>
            </div>
            <div className="trace-pill">Trace: {result?.trace_id || '—'}</div>
          </div>

          <div className="conversation">
            {messages.length === 0 && (
              <div className="bubble assistant welcome">
                <div className="bubble-icon"><Sparkles size={16} /></div>
                <div>
                  <strong>Start with your innovation.</strong>
                  <p>Describe product, ingredients, intended use, claims and target market. IP-SAKTI asks only what is needed.</p>
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={`${m.role}-${i}`} className={`bubble ${m.role}`}>
                <p className="message-text">{m.text}</p>
                {m.sourceCheck && (
                  <div className="answer-sources">
                    <div className="answer-sources-title">{m.evidence?.length ? 'Sources' : 'Source check'}</div>
                    {m.evidence?.length ? (
                      m.evidence.map((source) => (
                        <a
                          key={source.evidence_id}
                          className="answer-source-link"
                          href={source.source_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <span>{source.authority_name}: {source.citation}</span>
                          <small>
                            {source.document_title} · {source.jurisdiction} · {source.status}
                            {source.demo_only ? ' · demo source' : ''}
                          </small>
                        </a>
                      ))
                    ) : (
                      <p className="answer-no-sources">No verified sources cleared the trust gate, so legal conclusions are withheld.</p>
                    )}
                    {!!m.risks?.length && (
                      <ul className="answer-risks">
                        {m.risks.map((risk, index) => <li key={`${risk}-${index}`}>{risk}</li>)}
                      </ul>
                    )}
                    {!!m.sourcePointers?.length && (
                      <div className="source-pointers">
                        <div className="answer-sources-title">Official starting points · not verified evidence</div>
                        {m.sourcePointers.map((source) => (
                          <a
                            key={source.url}
                            className="answer-source-link"
                            href={source.url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            <span>{source.authority}: {source.title}</span>
                            <small>{source.topic}</small>
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="bubble assistant loading">
                <span className="dot" />
                Understanding → Classifying → Retrieving → Verifying…
              </div>
            )}

            {result && (
              <div className="bubble assistant insights-wrap">
                <div className="insights-title">Recommended next actions</div>
                <ol>
                  {result.next_steps.map((step, index) => (
                    <li key={index}>{step}</li>
                  ))}
                </ol>
              </div>
            )}

            {error && <div className="error-banner">{error}</div>}
          </div>

          <div className="composer">
            <textarea
              rows={3}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  send()
                }
              }}
              placeholder="Describe the product, intended use, ingredients, market and claims..."
            />
            <button className="send-btn" onClick={send} disabled={loading || !input.trim()}>
              {loading ? '…' : 'Ask'}
            </button>
          </div>
        </section>

        <aside className="panel right-panel">
          <div className="panel-header">
            <BrainCircuit size={16} />
            <span>Innovation profile</span>
          </div>

          {!result ? (
            <div className="empty-state">
              <div className="empty-title">Awaiting profile</div>
              <p>A structured legal digital twin will be created from your query.</p>
            </div>
          ) : (
            <>
              <div className="profile-card">
                <div className="label-row">
                  <span className="stat-label">Classification</span>
                  <span className="confidence-badge">{Math.round((result.classification.confidence || 0) * 100)}%</span>
                </div>
                <div className="stat-value">{result.classification.category}</div>
              </div>

              <div className="profile-card">
                <div className="label-row">
                  <span className="stat-label">Jurisdiction</span>
                </div>
                <div className="stat-value">
                  {mode === 'international' ? `${activeCountryLabel} · Global + country profile` : 'India · Domestic route'}
                </div>
              </div>

              <div className="profile-card">
                <div className="label-row">
                  <span className="stat-label">Domains</span>
                </div>
                <div className="stat-value compact">{result.applicable_domains.join(' • ') || '—'}</div>
              </div>

              <div className="profile-card">
                <div className="label-row">
                  <span className="stat-label">Evidence trust</span>
                </div>
                <div className="risk-list">
                  {result.risks.length ? (
                    result.risks.map((risk, index) => (
                      <div key={index} className="risk-item">
                        <AlertTriangle size={14} />
                        <span>{risk}</span>
                      </div>
                    ))
                  ) : (
                    <div className="risk-item positive">
                      <CheckCircle2 size={14} />
                      <span>No trust-gate warnings.</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="profile-card evidence-card">
                <div className="label-row">
                  <span className="stat-label">Evidence</span>
                </div>
                <div className="evidence-list">
                  {result.evidence.map((e) => (
                    <a key={e.evidence_id} className="evidence-item" href={e.source_url} target="_blank" rel="noreferrer">
                      <div className="evidence-topline">
                        <FileText size={13} />
                        <span>{e.authority_name}</span>
                      </div>
                      <div className="evidence-citation">{e.citation}</div>
                      <small>
                        {e.jurisdiction} • {e.status} • {e.verified ? 'verified' : 'unverified'}
                        {e.demo_only ? ' • demo' : ''}
                      </small>
                    </a>
                  ))}
                </div>
              </div>

              {result.recommendations.length > 0 && (
                <div className="profile-card">
                  <div className="label-row">
                    <span className="stat-label">Recommendations</span>
                  </div>
                  <div className="recommendation-list">
                    {result.recommendations.map((rec, index) => (
                      <div key={index} className="recommendation-item">
                        <div className="recommendation-head">
                          <span>{rec.text}</span>
                          <span className={`confidence-chip ${rec.confidence}`}>{rec.confidence}</span>
                        </div>
                        <small>{rec.why}</small>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.human_review && (
                <div className="panel-badge warning">
                  <AlertTriangle size={14} /> Expert review recommended
                </div>
              )}
            </>
          )}
        </aside>
      </main>
    </div>
  )
}
