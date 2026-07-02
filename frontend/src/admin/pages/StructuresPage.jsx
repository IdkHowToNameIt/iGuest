import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listStructures, createStructure } from '../adminApi.js'
import { useAuth } from '../auth.jsx'
import GeoSelect from '../../components/GeoSelect.jsx'
import Icon from '../../components/Icon.jsx'
import { useT } from '../../i18n/index.jsx'

const EMPTY_GEO = { region: '', province: '', city: '' }
const EMPTY_FORM = {
  name: '',
  country_language: '',
  owner_contact: '',
  contact_name: '',
  contact_phone: '',
  contact_email: '',
}

function locationLine(s, t) {
  const parts = [s.city, s.province, s.region].filter(Boolean)
  return parts.length ? parts.join(' · ') : t('No location set')
}

export default function StructuresPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const { t } = useT()

  const [structures, setStructures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // search + filters
  const [query, setQuery] = useState('')
  const [filterGeo, setFilterGeo] = useState(EMPTY_GEO)
  const debounceRef = useRef(null)

  // create form
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formGeo, setFormGeo] = useState(EMPTY_GEO)
  const [busy, setBusy] = useState(false)

  function handleAuthError(err) {
    if (err.status === 401) {
      logout()
      navigate('/admin/login', { replace: true })
      return true
    }
    return false
  }

  async function refresh() {
    setLoading(true)
    try {
      const items = await listStructures({
        q: query.trim() || undefined,
        region: filterGeo.region || undefined,
        province: filterGeo.province || undefined,
        city: filterGeo.city || undefined,
      })
      setStructures(items)
      setError(null)
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Re-fetch when filters change; debounce the free-text search a little.
  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(refresh, 250)
    return () => clearTimeout(debounceRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, filterGeo.region, filterGeo.province, filterGeo.city])

  const hasFilters = query || filterGeo.region || filterGeo.province || filterGeo.city

  const withLocation = structures.filter((s) => s.region || s.province || s.city).length
  const withHostContact = structures.filter(
    (s) => s.contact_name || s.contact_phone || s.contact_email,
  ).length

  async function handleCreate(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await createStructure({
        name: form.name.trim(),
        country_language: form.country_language.trim(),
        owner_contact: form.owner_contact.trim(),
        region: formGeo.region || null,
        province: formGeo.province || null,
        city: formGeo.city || null,
        contact_name: form.contact_name.trim() || null,
        contact_phone: form.contact_phone.trim() || null,
        contact_email: form.contact_email.trim() || null,
      })
      setForm(EMPTY_FORM)
      setFormGeo(EMPTY_GEO)
      setShowForm(false)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const setField = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <>
      <div className="page-head">
        <h1>{t('Structures')}</h1>
        <button className="btn btn-sm" onClick={() => setShowForm((v) => !v)}>
          {showForm ? t('Close') : t('+ New structure')}
        </button>
      </div>

      {!loading && !showForm && (
        <div className="stat-grid">
          <div className="stat-card">
            <span className="stat-card-label">{t('Structures shown')}</span>
            <span className="stat-card-value">{structures.length}</span>
            {hasFilters && <span className="stat-card-sub">{t('filtered view')}</span>}
          </div>
          <div className="stat-card">
            <span className="stat-card-label">{t('With location set')}</span>
            <span className="stat-card-value">{withLocation}</span>
          </div>
          <div className="stat-card">
            <span className="stat-card-label">{t('With host contact')}</span>
            <span className="stat-card-value">{withHostContact}</span>
          </div>
        </div>
      )}

      {showForm && (
        <section className="card">
          <h2>{t('Create a structure')}</h2>
          <form className="form" onSubmit={handleCreate}>
            <div className="form-grid">
              <div className="form-row">
                <label htmlFor="name">{t('Name')}</label>
                <input id="name" className="input" value={form.name} onChange={setField('name')} />
              </div>
              <div className="form-row">
                <label htmlFor="lang">{t('Guest language (BCP-47, e.g. it)')}</label>
                <input id="lang" className="input" value={form.country_language} onChange={setField('country_language')} placeholder="it" />
              </div>
              <div className="form-row">
                <label htmlFor="owner">{t('Owner contact (shown to guests if needed)')}</label>
                <input id="owner" className="input" value={form.owner_contact} onChange={setField('owner_contact')} placeholder="info@example.com" />
              </div>
            </div>

            <h3 className="form-section">{t('Location')}</h3>
            <GeoSelect value={formGeo} onChange={setFormGeo} idPrefix="create" />

            <h3 className="form-section">{t('Host contacts (admin-only)')}</h3>
            <div className="form-grid">
              <div className="form-row">
                <label htmlFor="cn">{t('Contact name')}</label>
                <input id="cn" className="input" value={form.contact_name} onChange={setField('contact_name')} />
              </div>
              <div className="form-row">
                <label htmlFor="cp">{t('Phone')}</label>
                <input id="cp" className="input" value={form.contact_phone} onChange={setField('contact_phone')} />
              </div>
              <div className="form-row">
                <label htmlFor="ce">{t('Email')}</label>
                <input id="ce" className="input" value={form.contact_email} onChange={setField('contact_email')} />
              </div>
            </div>

            <div className="form-actions">
              <button className="btn" type="submit" disabled={busy || !form.name.trim() || !form.country_language.trim() || !form.owner_contact.trim()}>
                {busy ? t('Creating…') : t('Create')}
              </button>
            </div>
          </form>
        </section>
      )}

      {/* The search box belongs to the main listing view only — hide it while the
          "New structure" creation form is open. */}
      {!showForm && (
        <section className="card">
          <h2>{t('Find structures')}</h2>
          <div className="form-row">
            <label htmlFor="search">{t('Search by name, city, province or region')}</label>
            <input
              id="search"
              className="input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('e.g. Colosseo, Roma, Lazio…')}
            />
          </div>
          <GeoSelect value={filterGeo} onChange={setFilterGeo} allLabel={t('— all —')} idPrefix="filter" />
          {hasFilters && (
            <div className="form-actions">
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => {
                  setQuery('')
                  setFilterGeo(EMPTY_GEO)
                }}
              >
                {t('Clear filters')}
              </button>
            </div>
          )}
        </section>
      )}

      {error && <p className="error-text">{error}</p>}
      {showForm ? null : loading ? (
        <p className="muted">{t('Loading…')}</p>
      ) : structures.length === 0 ? (
        <p className="muted">{hasFilters ? t('No structures match your search.') : t('No structures yet.')}</p>
      ) : (
        <div className="structure-grid">
          {structures.map((s) => (
            <div className="structure-card" key={s.id}>
              <div className="structure-card-head">
                <Link className="structure-card-title" to={`/admin/structures/${s.id}`}>{s.name}</Link>
                <span className="badge">{s.country_language}</span>
              </div>
              <div className="structure-card-loc">
                <Icon name="map-pin" size={14} /> {locationLine(s, t)}
              </div>

              <div className="structure-card-contacts">
                <span className="row-sub">{t('Owner (guests):')} {s.owner_contact}</span>
                {(s.contact_name || s.contact_phone || s.contact_email) ? (
                  <span className="row-sub">
                    {t('Host:')} {[s.contact_name, s.contact_phone, s.contact_email].filter(Boolean).join(' · ')}
                  </span>
                ) : (
                  <span className="row-sub muted">{t('No host contact set')}</span>
                )}
              </div>

              <div className="structure-card-actions">
                <Link className="btn btn-ghost btn-sm" to={`/admin/structures/${s.id}`}>{t('Open')}</Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
