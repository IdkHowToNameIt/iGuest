// Bilingual copy for the marketing landing page, ported from the "iGuest-Landing"
// concept. Kept in its own module so Landing.jsx stays focused on layout.
// NOTE: the admin area is intentionally NOT linked from the public landing — the
// admin panel is reachable only by typing its URL / via its own container.

export const LANDING = {
  it: {
    nav: { product: 'Prodotto', how: 'Come funziona', pricing: 'Prezzi', faq: 'FAQ', login: 'Accedi' },
    hero: {
      eyebrow: 'Il manuale digitale che risponde per te',
      title: 'Ogni domanda dei tuoi ospiti, con la risposta giusta. In ogni lingua.',
      sub: 'iGuest è l’assistente per affitti brevi e strutture ricettive. I tuoi ospiti aprono un link e chiedono qualsiasi cosa sull’alloggio: il bot risponde solo dal tuo manuale, nella loro lingua.',
      ctaPrimary: 'Accedi',
      ctaSecondary: 'Prenota una visita',
      note: 'Nessun dato personale richiesto agli ospiti · Conforme GDPR',
    },
    audience: {
      lead: 'Pensato per chi ospita, di qualsiasi dimensione.',
      tags: ['B&B e hotel', 'Host privati', 'Property manager'],
    },
    how: {
      kicker: 'Come funziona',
      title: 'Dalla visita al link, in quattro passi',
      sub: 'Non ti lasciamo solo davanti a una pagina bianca: il manuale lo costruiamo insieme.',
      steps: [
        { n: '1', title: 'Prenoti una visita', desc: 'Fissi un appuntamento: veniamo da te per il check-in della struttura.' },
        { n: '2', title: 'Creiamo il manuale insieme', desc: 'Di persona, con te, costruiamo un manuale ricco e pensato per come ragiona il bot.' },
        { n: '3', title: 'Generi il link ospite', desc: 'Dal portale host crei un link univoco per ogni prenotazione, con validità opzionale.' },
        { n: '4', title: 'L’ospite chatta', desc: 'L’ospite apre il link e chiede tutto, nella sua lingua. Il bot risponde solo dal tuo manuale.' },
      ],
    },
    features: {
      kicker: 'Prodotto',
      title: 'Cosa fa iGuest',
      sub: 'Un assistente che conosce solo il tuo alloggio, e lo racconta bene.',
      items: [
        { key: 'lang', title: 'Multilingua', desc: 'Risponde nella lingua dell’ospite, qualunque sia, senza che tu debba tradurre niente.' },
        { key: 'doc', title: 'Solo dal tuo manuale', desc: 'Niente invenzioni: attinge solo ai tuoi documenti. Se non sa, lascia il recapito del titolare.' },
        { key: 'analytics', title: 'Analytics delle domande', desc: 'Scopri cosa chiedono di più i tuoi ospiti e arricchisci il manuale nel tempo.' },
        { key: 'host', title: 'Portale host', desc: 'Leggi la documentazione, consulti le FAQ e invii richieste di modifica all’admin.' },
        { key: 'link', title: 'Link ospite temporanei', desc: 'Un link per prenotazione, con scadenza opzionale. Revocabile in un clic.' },
        { key: 'privacy', title: 'Privacy by design', desc: 'Nessun dato personale richiesto agli ospiti. Conservazione configurabile e cancellazione automatica.' },
      ],
    },
    book: {
      kicker: 'Il nostro tocco in più',
      title: 'Prenota una visita: il manuale lo facciamo insieme',
      lead: 'Il manuale è il cuore del prodotto. Per questo non ti lasciamo solo.',
      body: 'Veniamo di persona a fare il check-in della struttura con te e costruiamo insieme un manuale davvero completo, pensato per come ragiona il bot. Più il manuale è ricco, migliori sono le risposte per i tuoi ospiti.',
      bullets: [
        'Sopralluogo e check-in della struttura',
        'Manuale creato con te, ottimizzato per il bot',
        'Nessuna competenza tecnica richiesta',
      ],
      formTitle: 'Richiedi la tua visita',
      formSub: 'Ti ricontattiamo per fissare data e ora.',
      fStructure: 'Nome struttura', phStructure: 'Es. Casa Marina',
      fCity: 'Città', phCity: 'Es. Firenze',
      fType: 'Tipo di attività',
      types: [
        { value: 'bnb_hotel', label: 'B&B / Hotel' },
        { value: 'private_host', label: 'Host privato' },
        { value: 'property_manager', label: 'Property manager / Agenzia' },
      ],
      fName: 'Referente', phName: 'Nome e cognome',
      fEmail: 'Email', phEmail: 'tu@esempio.it',
      fDate: 'Data preferita',
      submit: 'Prenota la visita',
      submitting: 'Invio…',
      okTitle: 'Richiesta inviata!',
      okBody: 'Grazie. Ti ricontattiamo a breve per confermare la visita.',
      error: 'Qualcosa è andato storto. Riprova tra poco.',
    },
    pricing: {
      kicker: 'Prezzi',
      title: 'Parti con una visita, cresci quando vuoi',
      sub: 'Un piano per ogni tipo di attività.',
      note: 'Prezzi indicativi a scopo dimostrativo.',
      popular: 'Più scelto',
      plans: [
        { name: 'Host', tagline: 'Per un singolo alloggio', price: '€29', per: '/mese', featured: false, cta: 'Richiedi accesso', features: ['1 struttura', 'Chat multilingua illimitata', 'Link ospite con scadenza', 'Portale host + FAQ'] },
        { name: 'Pro', tagline: 'Per chi gestisce più unità', price: '€79', per: '/mese', featured: true, cta: 'Richiedi accesso', features: ['Fino a 10 strutture', 'Analytics delle domande', 'Visita e manuale inclusi', 'Supporto prioritario'] },
        { name: 'Business', tagline: 'Agenzie e property manager', price: 'Su misura', per: '', featured: false, cta: 'Parla con noi', features: ['Strutture illimitate', 'Onboarding dedicato', 'Più host per struttura', 'Referente dedicato'] },
      ],
    },
    about: {
      kicker: 'Chi siamo',
      title: 'Crediamo che l’ospitalità sia fatta di risposte pronte',
      body1: 'Siamo un piccolo team nato tra tecnologia e accoglienza. Abbiamo creato iGuest per togliere agli host le stesse domande ripetute mille volte.',
      body2: 'E per dare agli ospiti un’esperienza migliore: informazioni chiare, subito, nella loro lingua, a qualsiasi ora.',
      stats: [
        { num: '24/7', label: 'Risposte agli ospiti' },
        { num: '30+', label: 'Lingue supportate' },
        { num: '0', label: 'Dati personali richiesti' },
        { num: '100%', label: 'Dal tuo manuale' },
      ],
    },
    faq: {
      kicker: 'FAQ',
      title: 'Domande frequenti',
      items: [
        { q: 'Gli ospiti devono registrarsi?', a: 'No. Accedono con un link univoco, senza fornire nome, email o telefono. Nessun dato personale richiesto.' },
        { q: 'In che lingue risponde il bot?', a: 'Nella lingua dell’ospite, rilevata automaticamente. Il manuale può essere in una sola lingua: il bot traduce.' },
        { q: 'Il bot può inventare informazioni?', a: 'No. Risponde solo in base ai documenti che carichi. Se una domanda non è coperta, fornisce il recapito del titolare.' },
        { q: 'Chi crea il manuale?', a: 'Lo creiamo insieme a te durante la visita, così è completo e ottimizzato per il bot. Poi lo aggiorni quando vuoi.' },
        { q: 'Come si accede?', a: 'Gli host accedono dal portale host con email e password. L’ospite usa solo il link della chat.' },
        { q: 'È conforme al GDPR?', a: 'Sì. Minimizzazione dei dati, conservazione configurabile e cancellazione automatica delle conversazioni.' },
      ],
    },
    login: {
      title: 'Pronto a partire?',
      sub: 'Accedi al portale host o richiedi una visita per creare il tuo manuale.',
      host: 'Accedi al portale host',
      request: 'Richiedi accesso',
      hint: 'Sei un ospite? Usa il link ricevuto dal tuo host per aprire la chat.',
    },
    footer: {
      tagline: 'Il manuale digitale che risponde ai tuoi ospiti, in ogni lingua.',
      email: 'ciao@iguest.app',
      copy: '© 2026 iGuest. Tutti i diritti riservati.',
      made: 'Fatto con cura per chi ospita.',
      cols: [
        { title: 'Prodotto', links: [{ label: 'Funzionalità', href: '#features' }, { label: 'Prezzi', href: '#pricing' }, { label: 'Come funziona', href: '#how' }] },
        { title: 'Azienda', links: [{ label: 'Chi siamo', href: '#about' }, { label: 'Prenota una visita', href: '#book' }, { label: 'Contatti', href: 'mailto:ciao@iguest.app' }] },
        { title: 'Accessi', links: [{ label: 'Accedi (host)', href: '/host' }, { label: 'FAQ', href: '#faq' }] },
      ],
    },
  },

  en: {
    nav: { product: 'Product', how: 'How it works', pricing: 'Pricing', faq: 'FAQ', login: 'Log in' },
    hero: {
      eyebrow: 'The digital manual that answers for you',
      title: 'Every guest question, with the right answer. In every language.',
      sub: 'iGuest is the assistant for short-term rentals and hospitality. Your guests open a link and ask anything about the property: the bot answers only from your manual, in their language.',
      ctaPrimary: 'Log in',
      ctaSecondary: 'Book a visit',
      note: 'No personal data required from guests · GDPR compliant',
    },
    audience: {
      lead: 'Built for hosts of every size.',
      tags: ['B&Bs & hotels', 'Private hosts', 'Property managers'],
    },
    how: {
      kicker: 'How it works',
      title: 'From the visit to the link, in four steps',
      sub: 'We don’t leave you staring at a blank page: we build the manual together.',
      steps: [
        { n: '1', title: 'Book a visit', desc: 'Set an appointment: we come to you for a check-in of the property.' },
        { n: '2', title: 'We build the manual together', desc: 'In person, with you, we craft a rich manual designed for how the bot thinks.' },
        { n: '3', title: 'Generate the guest link', desc: 'From the host portal you create a unique link per booking, with optional validity.' },
        { n: '4', title: 'The guest chats', desc: 'The guest opens the link and asks anything, in their language. The bot answers only from your manual.' },
      ],
    },
    features: {
      kicker: 'Product',
      title: 'What iGuest does',
      sub: 'An assistant that knows only your property, and tells it well.',
      items: [
        { key: 'lang', title: 'Multilingual', desc: 'Answers in the guest’s language, whatever it is, with no translation work on your side.' },
        { key: 'doc', title: 'Only from your manual', desc: 'No made-up answers: it draws solely from your documents. If it doesn’t know, it shares the owner’s contact.' },
        { key: 'analytics', title: 'Question analytics', desc: 'See what your guests ask most and enrich the manual over time.' },
        { key: 'host', title: 'Host portal', desc: 'Read the documentation, browse FAQs and send change requests to the admin.' },
        { key: 'link', title: 'Temporary guest links', desc: 'One link per booking, with optional expiry. Revocable in one click.' },
        { key: 'privacy', title: 'Privacy by design', desc: 'No personal data required from guests. Configurable retention and automatic deletion.' },
      ],
    },
    book: {
      kicker: 'Our extra touch',
      title: 'Book a visit: we build the manual together',
      lead: 'The manual is the heart of the product. That’s why we don’t leave you alone.',
      body: 'We come in person to check in the property with you and build a truly complete manual, designed for how the bot reasons. The richer the manual, the better the answers for your guests.',
      bullets: [
        'On-site survey and property check-in',
        'Manual built with you, optimized for the bot',
        'No technical skills required',
      ],
      formTitle: 'Request your visit',
      formSub: 'We’ll reach out to set date and time.',
      fStructure: 'Property name', phStructure: 'E.g. Casa Marina',
      fCity: 'City', phCity: 'E.g. Florence',
      fType: 'Type of business',
      types: [
        { value: 'bnb_hotel', label: 'B&B / Hotel' },
        { value: 'private_host', label: 'Private host' },
        { value: 'property_manager', label: 'Property manager / Agency' },
      ],
      fName: 'Contact', phName: 'Full name',
      fEmail: 'Email', phEmail: 'you@example.com',
      fDate: 'Preferred date',
      submit: 'Book the visit',
      submitting: 'Sending…',
      okTitle: 'Request sent!',
      okBody: 'Thank you. We’ll get back to you shortly to confirm the visit.',
      error: 'Something went wrong. Please try again shortly.',
    },
    pricing: {
      kicker: 'Pricing',
      title: 'Start with a visit, grow when you want',
      sub: 'A plan for every kind of business.',
      note: 'Indicative prices for demonstration purposes.',
      popular: 'Most popular',
      plans: [
        { name: 'Host', tagline: 'For a single property', price: '€29', per: '/mo', featured: false, cta: 'Request access', features: ['1 property', 'Unlimited multilingual chat', 'Guest link with expiry', 'Host portal + FAQ'] },
        { name: 'Pro', tagline: 'For multiple units', price: '€79', per: '/mo', featured: true, cta: 'Request access', features: ['Up to 10 properties', 'Question analytics', 'Visit and manual included', 'Priority support'] },
        { name: 'Business', tagline: 'Agencies and property managers', price: 'Custom', per: '', featured: false, cta: 'Talk to us', features: ['Unlimited properties', 'Dedicated onboarding', 'Multiple hosts per property', 'Dedicated contact'] },
      ],
    },
    about: {
      kicker: 'About us',
      title: 'We believe hospitality is made of ready answers',
      body1: 'We’re a small team born between technology and hospitality. We built iGuest to spare hosts the same questions asked a thousand times.',
      body2: 'And to give guests a better experience: clear information, right away, in their language, at any hour.',
      stats: [
        { num: '24/7', label: 'Answers to guests' },
        { num: '30+', label: 'Languages supported' },
        { num: '0', label: 'Personal data required' },
        { num: '100%', label: 'From your manual' },
      ],
    },
    faq: {
      kicker: 'FAQ',
      title: 'Frequently asked questions',
      items: [
        { q: 'Do guests have to register?', a: 'No. They access with a unique link, without providing name, email or phone. No personal data required.' },
        { q: 'What languages does the bot answer in?', a: 'In the guest’s language, detected automatically. The manual can be in a single language: the bot translates.' },
        { q: 'Can the bot make things up?', a: 'No. It answers only based on the documents you upload. If a question isn’t covered, it shares the owner’s contact.' },
        { q: 'Who creates the manual?', a: 'We create it together with you during the visit, so it’s complete and optimized for the bot. Then you update it whenever you like.' },
        { q: 'How do I log in?', a: 'Hosts log in from the host portal with email and password. The guest only uses the chat link.' },
        { q: 'Is it GDPR compliant?', a: 'Yes. Data minimization, configurable retention and automatic deletion of conversations.' },
      ],
    },
    login: {
      title: 'Ready to start?',
      sub: 'Log in to the host portal or request a visit to create your manual.',
      host: 'Log in to host portal',
      request: 'Request access',
      hint: 'Are you a guest? Use the link from your host to open the chat.',
    },
    footer: {
      tagline: 'The digital manual that answers your guests, in every language.',
      email: 'ciao@iguest.app',
      copy: '© 2026 iGuest. All rights reserved.',
      made: 'Made with care for those who host.',
      cols: [
        { title: 'Product', links: [{ label: 'Features', href: '#features' }, { label: 'Pricing', href: '#pricing' }, { label: 'How it works', href: '#how' }] },
        { title: 'Company', links: [{ label: 'About us', href: '#about' }, { label: 'Book a visit', href: '#book' }, { label: 'Contact', href: 'mailto:ciao@iguest.app' }] },
        { title: 'Access', links: [{ label: 'Log in (host)', href: '/host' }, { label: 'FAQ', href: '#faq' }] },
      ],
    },
  },
}

// Feature icon SVG paths + accent tones (ported from the concept's featureIcon()).
export const FEATURE_ICON = {
  lang: [{ type: 'path', d: 'M7.9 20A9 9 0 1 0 4 16.1L2 22Z' }],
  doc: [
    { type: 'path', d: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' },
    { type: 'path', d: 'M14 2v6h6' },
    { type: 'path', d: 'M16 13H8M16 17H8M10 9H8' },
  ],
  analytics: [
    { type: 'circle', cx: '11', cy: '11', r: '8' },
    { type: 'path', d: 'm21 21-4.3-4.3' },
  ],
  host: [
    { type: 'path', d: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2' },
    { type: 'circle', cx: '9', cy: '7', r: '4' },
    { type: 'path', d: 'M22 21v-2a4 4 0 0 0-3-3.87' },
    { type: 'path', d: 'M16 3.13a4 4 0 0 1 0 7.75' },
  ],
  link: [
    { type: 'path', d: 'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71' },
    { type: 'path', d: 'M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71' },
  ],
  privacy: [
    { type: 'path', d: 'm21 2-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0 3 3L22 7l-3-3m-3.5 3.5L19 4' },
  ],
}

export const FEATURE_TONE = {
  lang: { stroke: '#6b3bff', chip: '#f1ecff' },
  doc: { stroke: '#14a08f', chip: '#e0f5f2' },
  analytics: { stroke: '#2f6fed', chip: '#e8effd' },
  host: { stroke: '#e07c1f', chip: '#fdf0e0' },
  link: { stroke: '#6b3bff', chip: '#f1ecff' },
  privacy: { stroke: '#14a08f', chip: '#e0f5f2' },
}
