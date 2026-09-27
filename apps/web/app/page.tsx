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

const demoPromptsByLanguage = {
  en: [
    'I have a turmeric-based Ayurvedic formulation and want to sell it in Germany.',
    'Can I protect an Ashwagandha product and what claims are safe to make?',
    'We want to export an herbal supplement into the US with a new formulation.',
  ],
  hi: [
    'मेरे पास टमाटर-आधारित आयुर्वेदिक फॉर्मूलेशन है और मैं इसे जर्मनी में बेचना चाहता हूं।',
    'क्या मैं अश्वगंधा उत्पाद को सुरक्षित रूप से Protect कर सकता हूं और कौन-से दावे सही हैं?',
    'हम US में एक नई फॉर्मूलेशन के साथ हर्बल सप्लीमेंट निर्यात करना चाहते हैं।',
  ],
  kn: [
    'ನನಗೆ ಹುಣಿಸೆ-ಆಧಾರಿತ ಆಯುರ್ವೇದ ಫಾರ್ಮ್ಯುಲೇಷನ್ ಇದೆ ಮತ್ತು ಅದನ್ನು ಜರ್ಮನಿಯಲ್ಲಿ ಮಾರಾಟ ಮಾಡಲು ಬಯಸುತ್ತೇನೆ.',
    'ನಾನು ಅಶ್ವಗಂಧ ಉತ್ಪನ್ನವನ್ನು ರಕ್ಷಿಸಬಹುದೇ ಮತ್ತು ಯಾವ ಕ್ಲೈಮ್ಗಳು ಸುರಕ್ಷಿತ?',
    'ನಾವು US ಗೆ ಹೊಸ ಫಾರ್ಮ್ಯುಲೇಷನ್ ಹೊಂದಿದ ನೈಸರ್ಗಿಕ ಸಪ್ಲಿಮೆಂಟ್ ಅನ್ನು ರಫ್ತು ಮಾಡಲು ಬಯಸುತ್ತೇವೆ.',
  ],
} as const

const translations = {
  en: {
    appName: 'IP-SAKTI SAHAYAK',
    subtitle: 'Evidence-first legal navigator',
    india: 'India',
    international: 'International',
    caseLibrary: 'Case Library',
    newCase: '+ New case',
    safety: 'Safety architecture',
    humanReview: 'Human review',
    ready: 'Start with your innovation.',
    prompt: 'Describe product, ingredients, intended use, claims and target market. IP-SAKTI asks only what is needed.',
    ask: 'Ask',
    awaitingProfile: 'Awaiting profile',
    profileHint: 'A structured legal digital twin will be created from your query.',
    title: 'Ayurveda Legal & Regulatory Navigator',
    subtitle2: 'Classification-first • jurisdiction-aware • source-grounded',
    trace: 'Trace',
    evidence: 'Evidence',
    recommendations: 'Recommendations',
    noSources: 'No verified sources cleared the trust gate, so legal conclusions are withheld.',
    loading: 'Understanding → Classifying → Retrieving → Verifying…',
    classification: 'Classification',
    jurisdiction: 'Jurisdiction',
    domains: 'Domains',
    trust: 'Evidence trust',
    experts: 'Expert review recommended',
    sourceCheck: 'Sources',
    officialStartingPoints: 'Official starting points · not verified evidence',
    expertReview: 'Escalate when evidence is weak',
    language: 'Language',
  },
  hi: {
    appName: 'आई-एसएकेटी सहायक',
    subtitle: 'साक्ष्य-आधारित कानूनी मार्गदर्शक',
    india: 'भारत',
    international: 'अंतर्राष्ट्रीय',
    caseLibrary: 'केस लाइब्रेरी',
    newCase: '+ नया केस',
    safety: 'सुरक्षा ढांचा',
    humanReview: 'मानव समीक्षा',
    ready: 'अपने नवाचार से शुरू करें।',
    prompt: 'उत्पाद, सामग्री, प्रयोजन, दावे और लक्षित बाजार का वर्णन करें। आई-एसएकेटी केवल आवश्यक जानकारी पूछता है।',
    ask: 'पूछें',
    awaitingProfile: 'प्रोफ़ाइल प्रतीक्षा में',
    profileHint: 'आपके प्रश्न से एक संरचित कानूनी डिजिटल ट्विन बनेगा।',
    title: 'आयुर्वेद कानूनी और नियामक नेविगेटर',
    subtitle2: 'वर्गीकरण-प्रथम • क्षेत्राधिकार-आधारित • स्रोत-आधारित',
    trace: 'ट्रेस',
    evidence: 'साक्ष्य',
    recommendations: 'सिफ़ारिशें',
    noSources: 'कोई भी सत्यापित स्रोत ट्रस्ट गेट से पार नहीं हुआ, इसलिए कानूनी निष्कर्ष रोके गए हैं।',
    loading: 'समझना → वर्गीकरण → पुनः प्राप्ति → सत्यापन…',
    classification: 'वर्गीकरण',
    jurisdiction: 'अधिकार क्षेत्र',
    domains: 'डोमेन',
    trust: 'साक्ष्य भरोसा',
    experts: 'विशेषज्ञ समीक्षा की अनुशंसा',
    sourceCheck: 'स्रोत',
    officialStartingPoints: 'आधिकारिक प्रारंभिक बिंदु · सत्यापित साक्ष्य नहीं',
    expertReview: 'जब साक्ष्य कमजोर हो तब escalation करें',
    language: 'भाषा',
  },
  kn: {
    appName: 'ಐ-ಸ Ak ti ಸಹಾಯಕ',
    subtitle: 'ಸಂತ್ರ evidence-ಆಧಾರಿತ ಕಾನೂನು ನ್ಯಾವಿಗೇಟರ್',
    india: 'ಭಾರತ',
    international: 'ಅಂತಾರಾಷ್ಟ್ರೀಯ',
    caseLibrary: 'ಕೇಸ್ ಲೈಬ್ರರಿ',
    newCase: '+ ಹೊಸ ಪ್ರಕರಣ',
    safety: 'ಸುರಕ್ಷತಾ arquitetura',
    humanReview: 'ಮನುಷ್ಯ ಪರಿಶೀಲನೆ',
    ready: 'ನಿಮ್ಮ ಕ್ರಾಂತಿಯೊಂದಿಗೆ ಪ್ರಾರಂಭಿಸಿ.',
    prompt: 'ಉತ್ಪನ್ನ, ಘಟಕಗಳು, ಉದ್ದೇಶಿತ ಬಳಕೆ, ಕ್ಲೈಮ್ಗಳು ಮತ್ತು ಗುರಿ ಮಾರುಕಟ್ಟೆಯನ್ನು ವಿವರಿಸಿ. ಐ-ಸ Ak ti ಅಗತ್ಯವಿರುವುದನ್ನು ಮಾತ್ರ ಕೇಳುತ್ತದೆ.',
    ask: 'ಕೇಳು',
    awaitingProfile: 'ಪ್ರೊಫೈಲ್ ನಿರೀಕ್ಷೆಯಲ್ಲಿದೆ',
    profileHint: 'ನಿಮ್ಮ ಪ್ರಶ್ನೆಯಿಂದ ಒಂದು संरಚಿತ ಕಾನೂನು ಡಿಜಿಟಲ್ ट्वಿನ್ ರಚನೆಯಾಗುತ್ತದೆ.',
    title: 'ಆಯುರ್ವೇದ ಕಾನೂನು ಮತ್ತು ವಿತರಣಾ ನ್ಯಾವಿಗೇಟರ್',
    subtitle2: 'ವರ್ಗೀಕರಣ-ಮೊದಲ • ಅಧಿಕಾರ ಪ್ರದೇಶ-ಆಧಾರಿತ • ಮೂಲ-ಆಧಾರಿತ',
    trace: 'ಟ್ರೇಸ್',
    evidence: 'ಸಮರ್ಥನ',
    recommendations: 'ಸಲಹೆಗಳು',
    noSources: 'ಯಾವುದೇ ಪರಿಶೀಲಿತ ಮೂಲಗಳು ಟ್ರಸ್ ಗೇಟನ್ನು ತಲುಪಿಲ್ಲ, ಆದ್ದರಿಂದ ಕಾನೂನು ತೀರ್ಮಾನಗಳನ್ನು ಹಿಂತೆಗೆದುಕೊಳ್ಳಲಾಗಿದೆ.',
    loading: 'ಅರ್ಥಮಾಡಿಕೊಳ್ಳುವುದು → ವಿಂಗಡಣೆ → ಹಿಂಭಾಗದಿಂದ ಪಡೆಯುವುದು → ಪರಿಶೀಲನೆ…',
    classification: 'ವರ್ಗೀಕರಣ',
    jurisdiction: 'ಅಧಿಕಾರ ಪ್ರದೇಶ',
    domains: 'ಡೊಮೇನ್ಗಳು',
    trust: 'ಸಮರ್ಥನ ವಿಶ್ವಾಸ',
    experts: 'ವಿಶೇಷಜ್ಞ ಪರಿಶೀಲನೆ ಶಿಫಾರಸು',
    sourceCheck: 'ಮೂಲಗಳು',
    officialStartingPoints: 'ಅಧಿಕೃತ ಆರಂಭಿಕ ಬಿಂದುಗಳು · ಪರಿಶೀಲಿಸಿದ evidence ಅಲ್ಲ',
    expertReview: 'ಸಮರ್ಥನ ದುರ್ಬಲವಾಗಿದ್ದಾಗ ತುರ್ತು human review',
    language: 'ಭಾಷೆ',
  },
} as const

type Language = keyof typeof translations

export default function Home() {
  const [mode, setMode] = useState<'india' | 'international'>('international')
  const [language, setLanguage] = useState<Language>('en')
  const [country, setCountry] = useState('DE')
  const [input, setInput] = useState<string>(demoPromptsByLanguage.en[0])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Result | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [userId, setUserId] = useState('')
  const [error, setError] = useState<string | null>(null)

  const activeCountryLabel = country === 'DE' ? 'Germany' : country === 'US' ? 'United States' : country === 'AE' ? 'UAE' : country === 'JP' ? 'Japan' : country === 'AU' ? 'Australia' : 'Brazil'
  const t = translations[language]
  const demoPrompts = demoPromptsByLanguage[language]

  const renderSummaryText = (text: string) => {
    const paragraphs = text.split(/(?<=[.!?])\s+/).filter(Boolean)
    return paragraphs.slice(0, 3).map((paragraph, index) => (
      <p key={`${paragraph.slice(0, 12)}-${index}`} className="summary-paragraph">{paragraph}</p>
    ))
  }

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
          language,
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
            <div className="brand-title">{t.appName}</div>
            <div className="brand-subtitle">{t.subtitle}</div>
          </div>
        </div>

        <div className="toolbar">
          <button
            className={`segmented ${mode === 'india' ? 'active' : ''}`}
            onClick={() => setMode('india')}
          >
            <Landmark size={14} /> {t.india}
          </button>
          <button
            className={`segmented ${mode === 'international' ? 'active' : ''}`}
            onClick={() => setMode('international')}
          >
            <Globe2 size={14} /> {t.international}
          </button>

          <select
            className="country-select"
            value={language}
            onChange={(e) => {
              const selected = e.target.value as Language
              setLanguage(selected)
              setInput(demoPromptsByLanguage[selected][0])
            }}
            aria-label={t.language}
          >
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="kn">ಕನ್ನಡ</option>
          </select>

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
            <span>{t.caseLibrary}</span>
          </div>

          <button className="primary-btn" onClick={() => { setMessages([]); setResult(null); setError(null); setUserId(crypto.randomUUID()) }}>
            {t.newCase}
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
            <div className="mini-label">{t.safety}</div>
            <div className="mini-value">Evidence → Verify → Act</div>
          </div>
          <div className="mini-card">
            <div className="mini-label">{t.humanReview}</div>
            <div className="mini-value">{t.expertReview}</div>
          </div>
        </aside>

        <section className="chat-panel">
          <div className="chat-header">
            <div>
              <div className="chat-title">{t.title}</div>
              <div className="chat-subtitle">{t.subtitle2}</div>
            </div>
            <div className="trace-pill">{t.trace}: {result?.trace_id || '—'}</div>
          </div>

          <div className="conversation">
            {messages.length === 0 && (
              <div className="bubble assistant welcome">
                <div className="bubble-icon"><Sparkles size={16} /></div>
                <div>
                  <strong>{t.ready}</strong>
                  <p>{t.prompt}</p>
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={`${m.role}-${i}`} className={`bubble ${m.role}`}>
                {m.role === 'assistant' ? (
                  <div className="answer-card">
                    <div className="answer-header">
                      <span className="answer-badge">Preliminary view</span>
                      <span className={`status-pill ${m.risks?.length ? 'warning' : 'ok'}`}>
                        {m.risks?.length ? 'Risk review' : 'Evidence reviewed'}
                      </span>
                    </div>
                    <div className="message-summary">{renderSummaryText(m.text)}</div>
                    {m.risks?.length ? (
                      <div className="risk-inline">
                        {m.risks.slice(0, 2).map((risk, index) => (
                          <span key={`${risk}-${index}`} className="risk-chip">{risk}</span>
                        ))}
                      </div>
                    ) : null}
                    {m.sourceCheck && (
                      <div className="answer-sources">
                        <div className="answer-sources-title">{m.evidence?.length ? t.sourceCheck : 'Source check'}</div>
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
                          <p className="answer-no-sources">{t.noSources}</p>
                        )}
                        {!!m.risks?.length && (
                          <ul className="answer-risks">
                            {m.risks.map((risk, index) => <li key={`${risk}-${index}`}>{risk}</li>)}
                          </ul>
                        )}
                        {!!m.sourcePointers?.length && (
                          <div className="source-pointers">
                            <div className="answer-sources-title">{t.officialStartingPoints}</div>
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
                ) : (
                  <p className="message-text">{m.text}</p>
                )}
              </div>
            ))}

            {loading && (
              <div className="bubble assistant loading">
                <span className="dot" />
                {t.loading}
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
              placeholder={t.prompt}
            />
            <button className="send-btn" onClick={send} disabled={loading || !input.trim()}>
              {loading ? '…' : t.ask}
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
              <div className="empty-title">{t.awaitingProfile}</div>
              <p>{t.profileHint}</p>
            </div>
          ) : (
            <>
              <div className="profile-card">
                <div className="label-row">
                  <span className="stat-label">{t.classification}</span>
                  <span className="confidence-badge">{Math.round((result.classification.confidence || 0) * 100)}%</span>
                </div>
                <div className="stat-value">{result.classification.category}</div>
              </div>

              <div className="profile-card">
                <div className="label-row">
                  <span className="stat-label">{t.jurisdiction}</span>
                </div>
                <div className="stat-value">
                  {mode === 'international' ? `${activeCountryLabel} · Global + country profile` : 'India · Domestic route'}
                </div>
              </div>

              <div className="profile-card">
                <div className="label-row">
                  <span className="stat-label">{t.domains}</span>
                </div>
                <div className="stat-value compact">{result.applicable_domains.join(' • ') || '—'}</div>
              </div>

              <div className="profile-card">
                <div className="label-row">
                  <span className="stat-label">{t.trust}</span>
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
                  <span className="stat-label">{t.evidence}</span>
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
                    <span className="stat-label">{t.recommendations}</span>
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
                  <AlertTriangle size={14} /> {t.experts}
                </div>
              )}
            </>
          )}
        </aside>
      </main>
    </div>
  )
}
