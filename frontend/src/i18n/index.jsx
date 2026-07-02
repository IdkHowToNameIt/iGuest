import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { IT } from './it.js'

// Lightweight i18n for the admin + host panels. Strings are authored in English
// in the components and used as keys; the Italian dictionary (it.js) maps them.
// A missing translation falls back to the English source, so partial coverage
// degrades gracefully. Interpolation: t('{n} units', { n: 3 }).

const STORAGE_KEY = 'iguest_lang'
const TABLES = { it: IT, en: null } // en = identity (source strings)

function loadLang() {
  const saved = localStorage.getItem(STORAGE_KEY)
  return saved === 'en' || saved === 'it' ? saved : 'it'
}

function interpolate(str, vars) {
  if (!vars) return str
  return str.replace(/\{(\w+)\}/g, (_, k) => (vars[k] != null ? String(vars[k]) : `{${k}}`))
}

const LanguageContext = createContext({ lang: 'it', setLang: () => {}, t: (s) => s })

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(loadLang)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, lang)
    document.documentElement.setAttribute('lang', lang)
  }, [lang])

  const setLang = useCallback((next) => setLangState(next === 'en' ? 'en' : 'it'), [])

  const t = useCallback(
    (str, vars) => {
      const table = TABLES[lang]
      // Keys may carry a "##context" suffix to disambiguate identical English
      // words (e.g. 'Open##status'); the English fallback drops it.
      const translated = table && table[str] != null ? table[str] : str.split('##')[0]
      return interpolate(translated, vars)
    },
    [lang],
  )

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t])
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useT() {
  return useContext(LanguageContext)
}

// IT/EN pill toggle, styled like the landing's. Drop it into a topbar.
export function LangToggle() {
  const { lang, setLang } = useT()
  return (
    <div className="lang-toggle" role="group" aria-label="Language">
      <button
        type="button"
        className={lang === 'it' ? 'active' : ''}
        onClick={() => setLang('it')}
        aria-pressed={lang === 'it'}
      >
        IT
      </button>
      <button
        type="button"
        className={lang === 'en' ? 'active' : ''}
        onClick={() => setLang('en')}
        aria-pressed={lang === 'en'}
      >
        EN
      </button>
    </div>
  )
}
