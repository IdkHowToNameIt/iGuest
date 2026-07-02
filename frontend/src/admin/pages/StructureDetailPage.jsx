import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import {
  getStructure,
  updateStructure,
  deleteStructure,
  listUnits,
  createUnit,
  deleteUnit,
  listDocuments,
  uploadDocument,
  deleteDocument,
  getDocumentContent,
  listHosts,
  createHost,
  updateHost,
  deleteHost,
} from '../adminApi.js'
import { useAuth } from '../auth.jsx'
import GeoSelect from '../../components/GeoSelect.jsx'
import { DocumentRow } from '../../components/DocumentText.jsx'
import { useT } from '../../i18n/index.jsx'

function StatusBadge({ status }) {
  const { t } = useT()
  return <span className={`badge badge-${status}`}>{t(status)}</span>
}

export default function StructureDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { logout } = useAuth()
  const { t } = useT()

  const [structure, setStructure] = useState(null)
  const [units, setUnits] = useState([])
  const [documents, setDocuments] = useState([])
  const [hosts, setHosts] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const [unitName, setUnitName] = useState('')
  const [busy, setBusy] = useState(false)
  const [docFile, setDocFile] = useState(null)
  const [uploading, setUploading] = useState(false)

  // editable details (seeded on load)
  const [details, setDetails] = useState(null) // {name, country_language, owner_contact, contact_*}
  const [geo, setGeo] = useState({ region: '', province: '', city: '' })
  const [savingDetails, setSavingDetails] = useState(false)

  // host management
  const [hostEmail, setHostEmail] = useState('')
  const [creatingHost, setCreatingHost] = useState(false)
  const [tempPassword, setTempPassword] = useState(null) // { hostId, password }

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
      const [s, u, d, h] = await Promise.all([
        getStructure(id),
        listUnits(id),
        listDocuments({ structureId: id }),
        listHosts(id),
      ])
      setStructure(s)
      setUnits(u)
      setDocuments(d.filter((doc) => doc.scope_type === 'structure'))
      setHosts(h)
      setDetails({
        name: s.name,
        country_language: s.country_language,
        owner_contact: s.owner_contact,
        contact_name: s.contact_name || '',
        contact_phone: s.contact_phone || '',
        contact_email: s.contact_email || '',
        welcome_message: s.welcome_message || '',
      })
      setGeo({ region: s.region || '', province: s.province || '', city: s.city || '' })
      setError(null)
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const setDetail = (k) => (e) => setDetails((p) => ({ ...p, [k]: e.target.value }))

  async function handleSaveDetails(e) {
    e.preventDefault()
    setSavingDetails(true)
    try {
      await updateStructure(id, {
        name: details.name.trim(),
        country_language: details.country_language.trim(),
        owner_contact: details.owner_contact.trim(),
        region: geo.region || null,
        province: geo.province || null,
        city: geo.city || null,
        contact_name: details.contact_name.trim() || null,
        contact_phone: details.contact_phone.trim() || null,
        contact_email: details.contact_email.trim() || null,
        welcome_message: details.welcome_message.trim() || null,
      })
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setSavingDetails(false)
    }
  }

  async function handleCreateUnit(e) {
    e.preventDefault()
    setBusy(true)
    try {
      await createUnit(id, { name: unitName.trim() })
      setUnitName('')
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleDeleteUnit(unitId) {
    if (!window.confirm(t('Delete this unit and all its data?'))) return
    try {
      await deleteUnit(unitId)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleUpload(e) {
    e.preventDefault()
    if (!docFile) return
    setUploading(true)
    try {
      await uploadDocument('structure', id, docFile)
      setDocFile(null)
      e.target.reset()
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  async function handleDeleteDoc(docId) {
    if (!window.confirm(t('Delete this document?'))) return
    try {
      await deleteDocument(docId)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleDeleteStructure() {
    if (!window.confirm(t('Delete this structure with all units, documents, hosts and conversations?'))) return
    try {
      await deleteStructure(id)
      navigate('/admin/structures', { replace: true })
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  // ── hosts ──
  async function handleCreateHost(e) {
    e.preventDefault()
    if (!hostEmail.trim()) return
    setCreatingHost(true)
    try {
      const host = await createHost(id, hostEmail.trim())
      setHostEmail('')
      setTempPassword({ hostId: host.id, password: host.temp_password })
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setCreatingHost(false)
    }
  }

  async function handleToggleHost(host) {
    try {
      await updateHost(host.id, { is_active: !host.is_active })
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleResetPassword(hostId) {
    if (!window.confirm(t('Issue a new temporary password for this host?'))) return
    try {
      const host = await updateHost(hostId, { reset_password: true })
      setTempPassword({ hostId: host.id, password: host.temp_password })
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleDeleteHost(hostId) {
    if (!window.confirm(t('Delete this host account?'))) return
    try {
      await deleteHost(hostId)
      if (tempPassword?.hostId === hostId) setTempPassword(null)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  if (loading || !details) return <p className="muted">{t('Loading…')}</p>
  if (!structure) return <p className="error-text">{error || t('Structure not found.')}</p>

  return (
    <>
      <div className="admin-breadcrumb">
        <Link to="/admin/structures">{t('Structures')}</Link> / {structure.name}
      </div>

      <div className="page-head">
        <h1>{structure.name}</h1>
        <button className="btn btn-danger btn-sm" onClick={handleDeleteStructure}>
          {t('Delete structure')}
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}

      <section className="card">
        <h2>{t('Details, location & contacts')}</h2>
        <form className="form" onSubmit={handleSaveDetails}>
          <div className="form-grid">
            <div className="form-row">
              <label htmlFor="d-name">{t('Name')}</label>
              <input id="d-name" className="input" value={details.name} onChange={setDetail('name')} />
            </div>
            <div className="form-row">
              <label htmlFor="d-lang">{t('Guest language (BCP-47)')}</label>
              <input id="d-lang" className="input" value={details.country_language} onChange={setDetail('country_language')} />
            </div>
            <div className="form-row">
              <label htmlFor="d-owner">{t('Owner contact (shown to guests)')}</label>
              <input id="d-owner" className="input" value={details.owner_contact} onChange={setDetail('owner_contact')} />
            </div>
          </div>

          <h3 className="form-section">{t('Location')}</h3>
          <GeoSelect value={geo} onChange={setGeo} idPrefix="edit" />

          <h3 className="form-section">{t('Host contacts (admin-only — never shown to guests)')}</h3>
          <div className="form-grid">
            <div className="form-row">
              <label htmlFor="d-cn">{t('Contact name')}</label>
              <input id="d-cn" className="input" value={details.contact_name} onChange={setDetail('contact_name')} />
            </div>
            <div className="form-row">
              <label htmlFor="d-cp">{t('Phone')}</label>
              <input id="d-cp" className="input" value={details.contact_phone} onChange={setDetail('contact_phone')} />
            </div>
            <div className="form-row">
              <label htmlFor="d-ce">{t('Email')}</label>
              <input id="d-ce" className="input" value={details.contact_email} onChange={setDetail('contact_email')} />
            </div>
          </div>

          <h3 className="form-section">{t('Chatbot welcome message')}</h3>
          <div className="form-row">
            <label htmlFor="d-welcome">
              {t(
                'Custom greeting shown to guests when they open the chat (leave empty to use the default greeting for the guest language)',
              )}
            </label>
            <textarea
              id="d-welcome"
              className="input"
              rows={3}
              maxLength={2000}
              value={details.welcome_message}
              onChange={setDetail('welcome_message')}
              placeholder={t("e.g. Welcome to Casa Bella! I'm here to help with anything about your stay.")}
            />
          </div>

          <div className="form-actions">
            <button className="btn" type="submit" disabled={savingDetails || !details.name.trim()}>
              {savingDetails ? t('Saving…') : t('Save changes')}
            </button>
          </div>
        </form>
      </section>

      <section className="card">
        <h2>{t('Units')}</h2>
        <form className="form" onSubmit={handleCreateUnit}>
          <div className="form-row">
            <label htmlFor="unitName">{t('New unit name')}</label>
            <input id="unitName" className="input" value={unitName} onChange={(e) => setUnitName(e.target.value)} placeholder="Room 1" />
          </div>
          <div className="form-actions">
            <button className="btn" type="submit" disabled={busy || !unitName.trim()}>
              {busy ? t('Adding…') : t('Add unit')}
            </button>
          </div>
        </form>
        {units.length === 0 ? (
          <p className="muted">{t('No units yet.')}</p>
        ) : (
          <ul className="list">
            {units.map((u) => (
              <li className="row" key={u.id}>
                <div className="row-main">
                  <span className="row-title">
                    <Link to={`/admin/units/${u.id}`}>{u.name}</Link>
                  </span>
                </div>
                <div className="row-actions">
                  <Link className="btn btn-ghost btn-sm" to={`/admin/units/${u.id}`}>{t('Open')}</Link>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDeleteUnit(u.id)}>{t('Delete')}</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <h2>{t('Hosts')}</h2>
        <p className="muted">
          {t('A host signs in at')} <code>/host</code>{' '}
          {t(
            "to read this structure's documentation and send change requests. The temporary password is shown once — share it securely.",
          )}
        </p>
        <form className="form" onSubmit={handleCreateHost}>
          <div className="form-row">
            <label htmlFor="hostEmail">{t('Host email')}</label>
            <input id="hostEmail" type="email" className="input" value={hostEmail} onChange={(e) => setHostEmail(e.target.value)} placeholder="host@example.com" />
          </div>
          <div className="form-actions">
            <button className="btn" type="submit" disabled={creatingHost || !hostEmail.trim()}>
              {creatingHost ? t('Creating…') : t('Add host')}
            </button>
          </div>
        </form>
        {hosts.length === 0 ? (
          <p className="muted">{t('No hosts yet.')}</p>
        ) : (
          <ul className="list">
            {hosts.map((h) => (
              <li className="row" key={h.id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                  <div className="row-main">
                    <span className="row-title">{h.email}</span>
                    <span className="row-sub">
                      <span className={`badge badge-${h.is_active ? 'active' : 'revoked'}`}>
                        {h.is_active ? t('active') : t('disabled')}
                      </span>
                      {h.must_change_password ? ` · ${t('awaiting password change')}` : ''}
                    </span>
                  </div>
                  <div className="row-actions">
                    <button className="btn btn-ghost btn-sm" onClick={() => handleToggleHost(h)}>
                      {h.is_active ? t('Disable') : t('Enable')}
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleResetPassword(h.id)}>{t('Reset password')}</button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDeleteHost(h.id)}>{t('Delete')}</button>
                  </div>
                </div>
                {tempPassword?.hostId === h.id && (
                  <p className="temp-password">
                    {t('Temporary password (shown once):')} <code>{tempPassword.password}</code>
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <h2>{t('Shared documents (whole structure)')}</h2>
        <form className="form" onSubmit={handleUpload}>
          <div className="form-row">
            <label htmlFor="docFile">{t('Upload a document (PDF, DOCX, TXT, MD, HTML…)')}</label>
            <input id="docFile" type="file" className="input" onChange={(e) => setDocFile(e.target.files[0] || null)} />
          </div>
          <div className="form-actions">
            <button className="btn" type="submit" disabled={uploading || !docFile}>
              {uploading ? t('Uploading…') : t('Upload')}
            </button>
          </div>
        </form>
        {documents.length === 0 ? (
          <p className="muted">{t('No shared documents yet.')}</p>
        ) : (
          <ul className="list">
            {documents.map((d) => (
              <DocumentRow
                key={d.id}
                docId={d.id}
                fetchContent={getDocumentContent}
                title={d.original_filename}
                subtitle={
                  <>
                    {d.file_type} <StatusBadge status={d.status} />
                    {d.error_message ? ` · ${d.error_message}` : ''}
                  </>
                }
                actions={
                  <button className="btn btn-danger btn-sm" onClick={() => handleDeleteDoc(d.id)}>
                    {t('Delete')}
                  </button>
                }
              />
            ))}
          </ul>
        )}
      </section>
    </>
  )
}
