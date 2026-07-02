import { useState } from 'react'
import { useT } from '../i18n/index.jsx'

// Render extracted plain text as readable, formatted blocks: blank lines split
// paragraphs, single newlines are preserved inside a paragraph, and lines that
// look like Markdown headings (#, ##, …) are shown as headings. Keeps the view
// legible without pulling in a Markdown dependency.
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

function DocBody({ loading, error, content, t }) {
  if (loading) return <p className="muted">{t('Loading…')}</p>
  if (error) return <p className="error-text">{error}</p>
  if (content?.text) return <FormattedText text={content.text} />
  if (content?.errorMessage) {
    return (
      <p className="error-text">
        {t('This document could not be read:')} {content.errorMessage}
      </p>
    )
  }
  return <p className="muted">{t('No text extracted (the document may still be processing).')}</p>
}

// A single document row: the metadata line (title + subtitle + optional extra
// actions) with a "View text" toggle, and — when open — the extracted manual
// text rendered full-width BELOW the row. Rendering the panel as a sibling of
// the row (not inside the narrow actions column) keeps it from being squeezed,
// so it looks identical in the admin pages and the host dashboard grid.
//
// `fetchContent(id)` returns { extracted_text, error_message } from whichever
// API client the caller uses (admin or host); the text is fetched lazily on
// first open.
export function DocumentRow({ docId, fetchContent, title, subtitle, actions }) {
  const { t } = useT()
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
    <li className="row" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
      <div className="row" style={{ border: 'none', padding: 0, background: 'transparent' }}>
        <div className="row-main">
          <span className="row-title">{title}</span>
          {subtitle != null && <span className="row-sub">{subtitle}</span>}
        </div>
        <div className="row-actions">
          <button className="btn btn-ghost btn-sm" onClick={toggle}>
            {open ? t('Hide text') : t('View text')}
          </button>
          {actions}
        </div>
      </div>
      {open && (
        <div className="doc-text">
          <DocBody loading={loading} error={error} content={content} t={t} />
        </div>
      )}
    </li>
  )
}
