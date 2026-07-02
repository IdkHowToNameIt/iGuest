import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getOpening, getHistory, getFaqs, sendMessage, ApiError } from '../api.js'
import Icon from '../components/Icon.jsx'
import '../chat.css'

// Friendly copy for each link-error code. The guest sees a clean screen instead
// of a raw HTTP error.
const ERROR_COPY = {
  not_found: { icon: 'link', title: 'Link not found', text: 'This link is not valid. Please ask your host for a new one.' },
  revoked: { icon: 'ban', title: 'Link revoked', text: 'This link has been disabled by the host.' },
  expired: { icon: 'hourglass', title: 'Link expired', text: 'This link is no longer valid. Please ask your host for a new one.' },
  not_yet_valid: { icon: 'clock', title: 'Not active yet', text: 'This link is not active yet. Please try again later.' },
  network: { icon: 'wifi-off', title: 'Connection problem', text: 'We could not reach the server. Check your connection and try again.' },
  busy: { icon: 'clock', title: 'Assistant busy', text: 'The assistant is momentarily busy. Please try again in a few moments.' },
  server: { icon: 'alert-triangle', title: 'Something went wrong', text: 'An unexpected error occurred. Please try again in a moment.' },
}

function CenteredError({ code }) {
  const copy = ERROR_COPY[code] || ERROR_COPY.server
  return (
    <div className="screen-center">
      <div className="error-card">
        <div className="error-icon">
          <Icon name={copy.icon} size={26} />
        </div>
        <h2>{copy.title}</h2>
        <p>{copy.text}</p>
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { token } = useParams()
  const [opening, setOpening] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [loading, setLoading] = useState(true)
  // Suggested questions (built from past guests); empty/disabled until enough exist.
  const [faqs, setFaqs] = useState([])

  // Conversation: a list of { role: 'guest' | 'assistant' | 'error', text }
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)

  const messagesRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getOpening(token)
      .then((data) => {
        if (!cancelled) setOpening(data)
        // Load the temporary conversation history so a returning guest sees
        // their previous messages; ignore failures (chat still works empty).
        return getHistory(token).catch(() => null)
      })
      .then((history) => {
        if (!cancelled && history?.messages?.length) {
          setMessages(history.messages.map((m) => ({ role: m.role, text: m.content })))
        }
        // Fetch the FAQ menu only after the link is known valid; ignore failures
        // (the chat works fine without suggestions).
        return getFaqs(token).catch(() => null)
      })
      .then((faqData) => {
        if (!cancelled && faqData?.enabled) setFaqs(faqData.entries || [])
      })
      .catch((err) => {
        if (!cancelled) setLoadError(err instanceof ApiError ? err.code : 'server')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token])

  // Keep the latest message in view.
  useEffect(() => {
    const el = messagesRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, sending])

  async function submitQuestion(raw) {
    const text = raw.trim()
    if (!text || sending) return

    setMessages((m) => [...m, { role: 'guest', text }])
    setInput('')
    setSending(true)
    try {
      const reply = await sendMessage(token, text)
      setMessages((m) => [...m, { role: 'assistant', text: reply.answer }])
    } catch (err) {
      const code = err instanceof ApiError ? err.code : 'server'
      const copy = ERROR_COPY[code] || ERROR_COPY.server
      setMessages((m) => [...m, { role: 'error', text: copy.text }])
    } finally {
      setSending(false)
    }
  }

  function handleSend(e) {
    e.preventDefault()
    submitQuestion(input)
  }

  if (loading) {
    return (
      <div className="screen-center">
        <div className="spinner" />
      </div>
    )
  }

  if (loadError) return <CenteredError code={loadError} />

  return (
    <div className="chat">
      <div className="chat-topbar">
        <span className="chat-topbar-title">{opening?.primary_language?.toUpperCase()} · Assistant</span>
      </div>

      <div className="messages" ref={messagesRef}>
        {opening && (
          <div className="intro">
            <span className="intro-primary">{opening.primary_message}</span>
            {opening.english_message && opening.english_message !== opening.primary_message && (
              <span className="intro-english">{opening.english_message}</span>
            )}
            {opening.language_note && <span className="intro-note">{opening.language_note}</span>}
            {opening.privacy_notice && <span className="intro-privacy">{opening.privacy_notice}</span>}
            {opening.stay_notice && <span className="intro-privacy">{opening.stay_notice}</span>}
          </div>
        )}

        {faqs.length > 0 && messages.length === 0 && (
          <div className="faq-suggestions">
            <span className="faq-label">Frequently asked</span>
            <div className="faq-chips">
              {faqs.map((f, i) => (
                <button
                  key={i}
                  type="button"
                  className="faq-chip"
                  onClick={() => submitQuestion(f.question)}
                  disabled={sending}
                >
                  {f.question}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => {
          const cls =
            m.role === 'guest' ? 'bubble bubble-guest' : m.role === 'error' ? 'bubble bubble-error' : 'bubble bubble-assistant'
          return (
            <div key={i} className={cls}>
              {m.text}
            </div>
          )
        })}

        {sending && (
          <div className="bubble bubble-assistant">
            <span className="typing">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </span>
          </div>
        )}
      </div>

      <form className="composer" onSubmit={handleSend}>
        <input
          className="composer-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your question…"
          disabled={sending}
          autoFocus
        />
        <button className="composer-send" type="submit" disabled={sending || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}
