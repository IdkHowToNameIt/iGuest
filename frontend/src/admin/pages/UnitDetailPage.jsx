import { useEffect, useRef, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { QRCodeCanvas } from 'qrcode.react'
import {
  getUnit,
  listDocuments,
  uploadDocument,
  deleteDocument,
  getDocumentContent,
  listLinks,
  createLink,
  revokeLink,
  listConversations,
  getConversation,
  deleteConversation,
  getUnitAnalytics,
} from '../adminApi.js'
import { useAuth } from '../auth.jsx'
import DocumentText from '../../components/DocumentText.jsx'

// The guest URL the host shares. Built from the SPA origin + the link token.
function guestUrl(token) {
  return `${window.location.origin}/c/${token}`
}

function statusBadge(status) {
  return <span className={`badge badge-${status}`}>{status}</span>
}

// A guest link's QR code, with a "Download PNG" action. A plain black-on-white
// panel so it stays scannable regardless of the app's light/dark theme.
function LinkQr({ url, filenameHint }) {
  const canvasRef = useRef(null)

  function handleDownload() {
    const canvas = canvasRef.current?.querySelector('canvas')
    if (!canvas) return
    const link = document.createElement('a')
    link.download = `iguest-link-${filenameHint}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
  }

  return (
    <div className="qr-panel" ref={canvasRef}>
      <QRCodeCanvas value={url} size={160} marginSize={2} />
      <button type="button" className="btn btn-ghost btn-sm" onClick={handleDownload}>
        Download PNG
      </button>
    </div>
  )
}

export default function UnitDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { logout } = useAuth()

  const [unit, setUnit] = useState(null)
  const [documents, setDocuments] = useState([])
  const [links, setLinks] = useState([])
  const [conversations, setConversations] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const [docFile, setDocFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [creatingLink, setCreatingLink] = useState(false)
  const [openConv, setOpenConv] = useState(null) // { id, messages }
  const [copied, setCopied] = useState(null)
  const [qrOpenFor, setQrOpenFor] = useState(null) // link id whose QR is shown

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
      const [u, d, l, c, a] = await Promise.all([
        getUnit(id),
        listDocuments({ unitId: id }),
        listLinks(id),
        listConversations(id),
        getUnitAnalytics(id),
      ])
      setUnit(u)
      setDocuments(d.filter((doc) => doc.scope_type === 'unit'))
      setLinks(l)
      setConversations(c)
      setAnalytics(a)
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

  async function handleUpload(e) {
    e.preventDefault()
    if (!docFile) return
    setUploading(true)
    try {
      await uploadDocument('unit', id, docFile)
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
    if (!window.confirm('Delete this document?')) return
    try {
      await deleteDocument(docId)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleCreateLink() {
    setCreatingLink(true)
    try {
      const newLink = await createLink(id, {})
      setQrOpenFor(newLink.id) // reveal its QR immediately
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    } finally {
      setCreatingLink(false)
    }
  }

  async function handleRevoke(linkId) {
    if (!window.confirm('Revoke this link? It will be deleted permanently, stop working, and disappear from the list.')) return
    try {
      await revokeLink(linkId)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleCopy(token) {
    try {
      await navigator.clipboard.writeText(guestUrl(token))
      setCopied(token)
      setTimeout(() => setCopied(null), 1500)
    } catch {
      // clipboard blocked â€” the link is still visible to copy manually
    }
  }

  async function handleOpenConv(convId) {
    if (openConv?.id === convId) {
      setOpenConv(null)
      return
    }
    try {
      const conv = await getConversation(convId)
      setOpenConv(conv)
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  async function handleDeleteConv(convId) {
    if (!window.confirm('Delete this conversation and all its messages (GDPR)?')) return
    try {
      await deleteConversation(convId)
      if (openConv?.id === convId) setOpenConv(null)
      await refresh()
    } catch (err) {
      if (!handleAuthError(err)) setError(err.message)
    }
  }

  if (loading) return <p className="muted">Loadingâ€¦</p>
  if (!unit) return <p className="error-text">{error || 'Unit not found.'}</p>

  return (
    <>
      <div className="admin-breadcrumb">
        <Link to="/admin/structures">Structures</Link> /{' '}
        <Link to={`/admin/structures/${unit.structure_id}`}>structure</Link> / {unit.name}
      </div>

      <h1>{unit.name}</h1>
      {error && <p className="error-text">{error}</p>}

      <section className="card">
        <h2>Documents (this unit)</h2>
        <form className="form" onSubmit={handleUpload}>
          <div className="form-row">
            <label htmlFor="docFile">Upload a document</label>
            <input id="docFile" type="file" className="input" onChange={(e) => setDocFile(e.target.files[0] || null)} />
          </div>
          <div className="form-actions">
            <button className="btn" type="submit" disabled={uploading || !docFile}>
              {uploading ? 'Uploadingâ€¦' : 'Upload'}
            </button>
          </div>
        </form>
        {documents.length === 0 ? (
          <p className="muted">No documents yet.</p>
        ) : (
          <ul className="list">
            {documents.map((d) => (
              <li className="row" key={d.id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                  <div className="row-main">
                    <span className="row-title">{d.original_filename}</span>
                    <span className="row-sub">
                      {d.file_type} {statusBadge(d.status)}
                      {d.error_message ? ` Â· ${d.error_message}` : ''}
                    </span>
                  </div>
                  <div className="row-actions">
                    <DocumentText docId={d.id} fetchContent={getDocumentContent} />
                    <button className="btn btn-danger btn-sm" onClick={() => handleDeleteDoc(d.id)}>
                      Delete
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <h2>Guest links</h2>
        <div className="form-actions">
          <button className="btn" onClick={handleCreateLink} disabled={creatingLink}>
            {creatingLink ? 'Generatingâ€¦' : 'Generate link'}
          </button>
        </div>
        {links.length === 0 ? (
          <p className="muted">No links yet.</p>
        ) : (
          <ul className="list">
            {links.map((l) => (
              <li className="row" key={l.id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                  <div className="row-main">
                    <span className="row-title">{statusBadge(l.status)}</span>
                    <span className="row-sub">{guestUrl(l.token)}</span>
                  </div>
                  <div className="row-actions">
                    <button className="btn btn-ghost btn-sm" onClick={() => handleCopy(l.token)}>
                      {copied === l.token ? 'Copied!' : 'Copy'}
                    </button>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => setQrOpenFor(qrOpenFor === l.id ? null : l.id)}
                    >
                      {qrOpenFor === l.id ? 'Hide QR' : 'QR code'}
                    </button>
                    {l.status === 'active' && (
                      <button className="btn btn-danger btn-sm" onClick={() => handleRevoke(l.id)}>
                        Revoke
                      </button>
                    )}
                  </div>
                </div>
                {qrOpenFor === l.id && (
                  <LinkQr url={guestUrl(l.token)} filenameHint={l.token.slice(0, 8)} />
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="card">
        <h2>Question analytics</h2>
        {!analytics || analytics.total === 0 ? (
          <p className="muted">
            No analytics yet. They are built from guest questions by the recompute
            job (<code>scripts/recompute_faqs.py</code>).
          </p>
        ) : (
          <>
            <p className="muted">{analytics.total} guest question(s) analysed.</p>
            <ul className="list">
              {analytics.categories.map((cat) => (
                <li className="row" key={cat.label} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                  <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                    <div className="row-main">
                      <span className="row-title">{cat.label}</span>
                      <span className="row-sub">
                        {cat.count} question(s) Â· {Math.round(cat.share * 100)}%
                      </span>
                    </div>
                  </div>
                  <ul className="list" style={{ marginTop: 8 }}>
                    {cat.questions.map((q) => (
                      <li className="row" key={q.question}>
                        <div className="row-main">
                          <span className="row-sub">{q.question}</span>
                        </div>
                        <span className="badge">{q.count} Â· {Math.round(q.share * 100)}%</span>
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="card">
        <h2>Conversations</h2>
        {conversations.length === 0 ? (
          <p className="muted">No conversations yet.</p>
        ) : (
          <ul className="list">
            {conversations.map((c) => (
              <li className="row" key={c.id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
                  <div className="row-main">
                    <span className="row-title">{new Date(c.created_at).toLocaleString()}</span>
                    <span className="row-sub">
                      {c.delete_after ? `Auto-delete: ${new Date(c.delete_after).toLocaleDateString()}` : ''}
                    </span>
                  </div>
                  <div className="row-actions">
                    <button className="btn btn-ghost btn-sm" onClick={() => handleOpenConv(c.id)}>
                      {openConv?.id === c.id ? 'Hide' : 'View'}
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDeleteConv(c.id)}>
                      Delete
                    </button>
                  </div>
                </div>
                {openConv?.id === c.id && (
                  <div className="transcript">
                    {openConv.messages.length === 0 ? (
                      <p className="muted">No messages.</p>
                    ) : (
                      openConv.messages.map((m) => (
                        <div key={m.id} className={`msg msg-${m.role === 'guest' ? 'guest' : 'assistant'}`}>
                          {m.content}
                        </div>
                      ))
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}
