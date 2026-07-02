import { useState } from 'react'
import { Link } from 'react-router-dom'
import ChatMock from '../components/ChatMock.jsx'
import { submitVisitRequest } from '../publicApi.js'
import { LANDING, FEATURE_ICON, FEATURE_TONE } from './landingContent.js'
import './landing.css'

// Small inline-SVG helpers (kept local so the landing stays self-contained and
// pixel-faithful to the concept).
const Logo = ({ size = 18, stroke = '#fff' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
  </svg>
)
const ArrowRight = ({ stroke = '#fff', size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h14" />
    <path d="m12 5 7 7-7 7" />
  </svg>
)
const Check = ({ stroke = '#14a08f', size = 15 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 6 9 17l-5-5" />
  </svg>
)
const Chevron = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#6b3bff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m6 9 6 6 6-6" />
  </svg>
)

function FeatureIcon({ featureKey }) {
  const tone = FEATURE_TONE[featureKey] || FEATURE_TONE.lang
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke={tone.stroke}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      dangerouslySetInnerHTML={{ __html: FEATURE_ICON[featureKey] }}
    />
  )
}

// Public marketing landing (the app's home). Guests still reach the chat via
// their capability link; hosts log in from here; the admin area is not linked.
export default function Landing() {
  const [lang, setLang] = useState('it')
  const [faqOpen, setFaqOpen] = useState(0)
  const t = LANDING[lang]

  return (
    <div className="lp">
      <div className="lp-wash" />
      <div className="lp-shell">
        <header className="lp-header">
          <div className="lp-header-inner">
            <a href="#top" className="lp-brand">
              <span className="lp-brand-mark"><Logo /></span>
              <span className="lp-brand-name">iGuest</span>
            </a>
            <nav className="lp-nav">
              <a href="#features">{t.nav.product}</a>
              <a href="#how">{t.nav.how}</a>
              <a href="#pricing">{t.nav.pricing}</a>
              <a href="#faq">{t.nav.faq}</a>
            </nav>
            <div className="lp-header-actions">
              <div className="lp-langtoggle">
                <button className={lang === 'it' ? 'active' : ''} onClick={() => setLang('it')}>IT</button>
                <button className={lang === 'en' ? 'active' : ''} onClick={() => setLang('en')}>EN</button>
              </div>
              <a href="#login" className="lp-btn-dark">{t.nav.login}</a>
            </div>
          </div>
        </header>

        <span id="top" />

        {/* hero */}
        <section className="lp-hero">
          <div className="lp-hero-grid">
            <div>
              <div className="lp-badge"><span className="lp-badge-dot" />{t.hero.eyebrow}</div>
              <h1 className="lp-hero-title">{t.hero.title}</h1>
              <p className="lp-hero-sub">{t.hero.sub}</p>
              <div className="lp-hero-cta">
                <a href="#login" className="lp-btn-primary">{t.hero.ctaPrimary}<ArrowRight /></a>
                <a href="#book" className="lp-btn-secondary">{t.hero.ctaSecondary}</a>
              </div>
              <p className="lp-hero-note"><Check />{t.hero.note}</p>
            </div>
            <div className="lp-hero-visual">
              <div className="lp-hero-glow" />
              <div className="lp-hero-mock"><ChatMock lang={lang} /></div>
            </div>
          </div>
        </section>

        {/* audience strip */}
        <section className="lp-audience">
          <div className="lp-audience-inner">
            <p className="lp-audience-lead">{t.audience.lead}</p>
            <div className="lp-audience-tags">
              {t.audience.tags.map((tag) => (
                <span className="lp-audience-tag" key={tag}>{tag}</span>
              ))}
            </div>
          </div>
        </section>

        {/* how it works */}
        <section id="how" className="lp-section">
          <div className="lp-section-head">
            <p className="lp-kicker">{t.how.kicker}</p>
            <h2 className="lp-h2">{t.how.title}</h2>
            <p className="lp-section-sub">{t.how.sub}</p>
          </div>
          <div className="lp-grid-4">
            {t.how.steps.map((s) => (
              <div className="lp-card" key={s.n}>
                <div className="lp-step-num">{s.n}</div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* features */}
        <section id="features" className="lp-section">
          <div className="lp-section-head">
            <p className="lp-kicker">{t.features.kicker}</p>
            <h2 className="lp-h2">{t.features.title}</h2>
            <p className="lp-section-sub">{t.features.sub}</p>
          </div>
          <div className="lp-grid-3">
            {t.features.items.map((f) => (
              <div className="lp-card" key={f.key}>
                <div className="lp-feature-chip" style={{ background: (FEATURE_TONE[f.key] || {}).chip }}>
                  <FeatureIcon featureKey={f.key} />
                </div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* book a visit */}
        <BookSection t={t.book} />

        {/* pricing */}
        <section id="pricing" className="lp-section">
          <div className="lp-section-head" style={{ marginBottom: 16 }}>
            <p className="lp-kicker">{t.pricing.kicker}</p>
            <h2 className="lp-h2">{t.pricing.title}</h2>
            <p className="lp-section-sub">{t.pricing.sub}</p>
          </div>
          <p className="lp-pricing-note">{t.pricing.note}</p>
          <div className="lp-plans">
            {t.pricing.plans.map((p) => (
              <div className={`lp-plan${p.featured ? ' lp-featured' : ''}`} key={p.name}>
                {p.featured && <div className="lp-plan-badge">{t.pricing.popular}</div>}
                <h3 className="lp-plan-name">{p.name}</h3>
                <p className="lp-plan-tagline">{p.tagline}</p>
                <div className="lp-plan-price"><b>{p.price}</b><span>{p.per}</span></div>
                <div className="lp-plan-features">
                  {p.features.map((pf) => (
                    <div className="lp-plan-feature" key={pf}>
                      <Check stroke={p.featured ? '#4fd3c2' : '#14a08f'} size={16} />
                      <span>{pf}</span>
                    </div>
                  ))}
                </div>
                <a href="#login" className="lp-plan-cta">{p.cta}</a>
              </div>
            ))}
          </div>
        </section>

        {/* about */}
        <section id="about" className="lp-section">
          <div className="lp-about-grid">
            <div className="lp-about">
              <p className="lp-kicker">{t.about.kicker}</p>
              <h2>{t.about.title}</h2>
              <p>{t.about.body1}</p>
              <p style={{ marginBottom: 0 }}>{t.about.body2}</p>
            </div>
            <div className="lp-stats">
              {t.about.stats.map((st) => (
                <div className="lp-stat" key={st.label}>
                  <div className="lp-stat-num">{st.num}</div>
                  <div className="lp-stat-label">{st.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* faq */}
        <section id="faq" className="lp-section lp-section-narrow">
          <div className="lp-section-head" style={{ marginBottom: 40 }}>
            <p className="lp-kicker">{t.faq.kicker}</p>
            <h2 className="lp-h2" style={{ margin: 0 }}>{t.faq.title}</h2>
          </div>
          <div className="lp-faq-list">
            {t.faq.items.map((q, i) => (
              <div className="lp-faq-item" key={q.q}>
                <button className="lp-faq-q" onClick={() => setFaqOpen((o) => (o === i ? -1 : i))}>
                  <span>{q.q}</span>
                  <span className={`lp-faq-chevron${faqOpen === i ? ' open' : ''}`}><Chevron /></span>
                </button>
                {faqOpen === i && <div className="lp-faq-a">{q.a}</div>}
              </div>
            ))}
          </div>
        </section>

        {/* login / cta */}
        <section id="login" className="lp-login">
          <div className="lp-login-inner">
            <div className="lp-login-glow" />
            <div className="lp-login-content">
              <h2>{t.login.title}</h2>
              <p className="lp-login-sub">{t.login.sub}</p>
              <div className="lp-login-actions">
                <Link to="/host" className="lp-btn-primary">{t.login.host}<ArrowRight /></Link>
                <a href="#book" className="lp-btn-soft">{t.login.request}</a>
              </div>
              <p className="lp-login-hint">{t.login.hint}</p>
            </div>
          </div>
        </section>

        {/* footer */}
        <footer className="lp-footer">
          <div className="lp-footer-inner">
            <div>
              <div className="lp-brand" style={{ marginBottom: 4 }}>
                <span className="lp-brand-mark" style={{ width: 30, height: 30 }}><Logo size={17} /></span>
                <span className="lp-footer-brand-name">iGuest</span>
              </div>
              <p className="lp-footer-tag">{t.footer.tagline}</p>
              <a href={`mailto:${t.footer.email}`} className="lp-footer-email">{t.footer.email}</a>
            </div>
            {t.footer.cols.map((col) => (
              <div key={col.title}>
                <div className="lp-footer-col-title">{col.title}</div>
                <div className="lp-footer-col-links">
                  {col.links.map((l) =>
                    l.href.startsWith('/') ? (
                      <Link to={l.href} key={l.label}>{l.label}</Link>
                    ) : (
                      <a href={l.href} key={l.label}>{l.label}</a>
                    ),
                  )}
                </div>
              </div>
            ))}
          </div>
          <div className="lp-footer-bar">
            <div className="lp-footer-bar-inner">
              <span>{t.footer.copy}</span>
              <span>{t.footer.made}</span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}

// "Book a visit" — the only interactive piece: submits a lead to the public API.
function BookSection({ t }) {
  const [form, setForm] = useState({
    structure_name: '',
    city: '',
    business_type: t.types[0].value,
    contact_name: '',
    contact_email: '',
    preferred_date: '',
  })
  const [status, setStatus] = useState('idle') // idle | sending | done | error
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus('sending')
    try {
      await submitVisitRequest({
        structure_name: form.structure_name.trim(),
        city: form.city.trim() || null,
        business_type: form.business_type || null,
        contact_name: form.contact_name.trim(),
        contact_email: form.contact_email.trim(),
        preferred_date: form.preferred_date || null,
      })
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }

  return (
    <section id="book" className="lp-book">
      <div className="lp-book-inner">
        <div>
          <div className="lp-book-badge">{t.kicker}</div>
          <h2 className="lp-book-title">{t.title}</h2>
          <p className="lp-book-lead">{t.lead}</p>
          <p className="lp-book-body">{t.body}</p>
          <div className="lp-book-bullets">
            {t.bullets.map((b) => (
              <div className="lp-book-bullet" key={b}>
                <span className="lp-book-bullet-ic"><Check stroke="#4fd3c2" size={14} /></span>
                <span>{b}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lp-book-form-wrap">
          {status === 'done' ? (
            <div className="lp-book-ok">
              <div className="lp-book-ok-ic">
                <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#14a08f" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
              </div>
              <h3>{t.okTitle}</h3>
              <p>{t.okBody}</p>
            </div>
          ) : (
            <form className="lp-book-form" onSubmit={handleSubmit}>
              <h3>{t.formTitle}</h3>
              <p className="lp-book-form-sub">{t.formSub}</p>
              <div className="lp-form-grid">
                <label className="lp-field">
                  <span className="lp-field-label">{t.fStructure}</span>
                  <input className="lp-input" required placeholder={t.phStructure} value={form.structure_name} onChange={set('structure_name')} />
                </label>
                <label className="lp-field">
                  <span className="lp-field-label">{t.fCity}</span>
                  <input className="lp-input" placeholder={t.phCity} value={form.city} onChange={set('city')} />
                </label>
                <label className="lp-field lp-full">
                  <span className="lp-field-label">{t.fType}</span>
                  <select className="lp-input" value={form.business_type} onChange={set('business_type')}>
                    {t.types.map((opt) => (
                      <option value={opt.value} key={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </label>
                <label className="lp-field">
                  <span className="lp-field-label">{t.fName}</span>
                  <input className="lp-input" required placeholder={t.phName} value={form.contact_name} onChange={set('contact_name')} />
                </label>
                <label className="lp-field">
                  <span className="lp-field-label">{t.fEmail}</span>
                  <input className="lp-input" required type="email" placeholder={t.phEmail} value={form.contact_email} onChange={set('contact_email')} />
                </label>
                <label className="lp-field lp-full">
                  <span className="lp-field-label">{t.fDate}</span>
                  <input className="lp-input" type="date" value={form.preferred_date} onChange={set('preferred_date')} />
                </label>
              </div>
              {status === 'error' && <p className="lp-book-error">{t.error}</p>}
              <button type="submit" className="lp-book-submit" disabled={status === 'sending'}>
                {status === 'sending' ? t.submitting : t.submit}
              </button>
            </form>
          )}
        </div>
      </div>
    </section>
  )
}
