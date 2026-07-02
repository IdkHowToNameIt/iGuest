// Static chat preview shown in the landing hero. Purely presentational — it
// mirrors the "ChatMock" concept and takes its copy from the active language.
const STRINGS = {
  it: {
    online: 'Online · risponde nella tua lingua',
    q1: 'A che ora è il check-out?',
    a1: 'Il check-out è entro le 10:30. Lascia le chiavi sul tavolo e chiudi la porta. Buon viaggio! 🌿',
    q2: 'Where can I park nearby?',
    a2: 'There is free street parking on Via del Mare, 50 m from the entrance. A paid garage is 200 m away.',
    placeholder: 'Scrivi un messaggio…',
  },
  en: {
    online: 'Online · answers in your language',
    q1: 'What time is check-out?',
    a1: 'Check-out is by 10:30. Leave the keys on the table and close the door. Safe travels! 🌿',
    q2: 'Où puis-je me garer à proximité ?',
    a2: 'Il y a un stationnement gratuit dans la Via del Mare, à 50 m de l’entrée. Un garage payant est à 200 m.',
    placeholder: 'Type a message…',
  },
}

export default function ChatMock({ lang = 'it' }) {
  const m = STRINGS[lang] || STRINGS.it
  return (
    <div className="lp-chatmock">
      <div className="lp-chatmock-head">
        <span className="lp-chatmock-avatar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
          </svg>
        </span>
        <div style={{ flex: 1 }}>
          <div className="lp-chatmock-name">Casa Marina</div>
          <div className="lp-chatmock-status">
            <span className="lp-chatmock-dot" />
            {m.online}
          </div>
        </div>
      </div>

      <div className="lp-chatmock-body">
        <div className="lp-chatmock-bubble lp-out">{m.q1}</div>
        <div className="lp-chatmock-bubble lp-in">{m.a1}</div>
        <div className="lp-chatmock-bubble lp-out">{m.q2}</div>
        <div className="lp-chatmock-bubble lp-in">{m.a2}</div>
      </div>

      <div className="lp-chatmock-input">
        <div className="lp-chatmock-field">{m.placeholder}</div>
        <span className="lp-chatmock-send">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14" />
            <path d="m12 5 7 7-7 7" />
          </svg>
        </span>
      </div>
    </div>
  )
}
