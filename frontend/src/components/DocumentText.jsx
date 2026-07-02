import { useEffect, useState } from 'react'

// A "View text" toggle for a document. `fetchContent(id)` returns
// { extracted_text, ... } from whichever API client the caller uses (admin or
// host), so this component is reused on both sides. The text is fetched lazily
// the first time it is opened.
// Render extracted plain text as readable, formatted blocks: blank lines split
// paragraphs, single newlines are preserved inside a paragraph, and lines that
// look like Markdown headings (#, ##, …) are shown as headings. Keeps the view
// legible for the host without pulling in a Markdown dependency.
function FormattedText({ text }) {
  const blocks = text.replace(/\r\n/g, '\n').split(/\n{2,}/).map((b) => b.trim()).filter(Boolean)
  return (
    <div className="doc-text-body">
      {blocks.map((block, i) => {
        const heading = block.match(/^(#{1,6})\s+(.*)$/)
        if (heading && !block.includes('\n')) {
          const level = Math.min(heading[1].length + 1, 6) // #→h2, ##→h3, …
          const Tag = `h${level}`
          return <Tag key={i} className="doc-text-h">{heading[2]}</Tag>
        }
        return (
          <p key={i} className="doc-text-p">
            {block}
          </p>
        )
      })}
    </div>
  )
}

function DocBody({ loading, error, content }) {
  if (loading) return <p className="muted">Loading…</p>
  if (error) return <p className="error-text">{error}</p>
  if (content?.text) return <FormattedText text={content.text} />
  if (content?.errorMessage) {
    return <p className="error-text">This document could not be read: {content.errorMessage}</p>
  }
  return <p className="muted">No text extracted (the document may still be processing).</p>
}

// Full-page-ish popup: the document text over most of the viewport, with a
// close button and the usual dismiss affordances (backdrop click, Escape).
function DocModal({ title, loading, error, content, onClose }) {
  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  return (
    <div className="doc-modal-backdrop" onClick={onClose}>
      <div className="doc-modal" onClick={(e) => e.stopPropagation()}>
        <div className="doc-modal-head">
          <h2>{title}</h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>
            ✕ Close
          </button>
        </div>
        <div className="doc-modal-body">
          <DocBody loading={loading} error={error} content={content} />
        </div>
      </div>
    </div>
  )
}

// `variant="inline"` (default) expands the text in place, under the row —
// used in the admin panel. `variant="modal"` opens a large popup instead,
// used in the host portal so the document isn't squeezed into the dashboard.
export default function DocumentText({ docId, fetchContent, variant = 'inline', title }) {
  const [open, setOpen] = useState(false)
  const [content, setContent] = useState(null) // { text, errorMessage }
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function toggle() {
    if (open) {
      setOpen(false)
      return
    }
    setOpen(true)
    if (content === null && !loading) {
      setLoading(true)
      try {
        const data = await fetchContent(docId)
        setContent({ text: data.extracted_text || '', errorMessage: data.error_message || null })
        setError(null)
      } catch (err) {
        setError(err.message || 'Could not load the text.')
      } finally {
        setLoading(false)
      }
    }
  }

  return (
    <>
      <button className="btn btn-ghost btn-sm" onClick={toggle}>
        {open ? (variant === 'modal' ? 'Close' : 'Hide text') : 'View text'}
      </button>
      {open && variant === 'modal' && (
        <DocModal
          title={title || 'Document'}
          loading={loading}
          error={error}
          content={content}
          onClose={() => setOpen(false)}
        />
      )}
      {open && variant !== 'modal' && (
        <div className="doc-text">
          <DocBody loading={loading} error={error} content={content} />
        </div>
      )}
    </>
  )
}
