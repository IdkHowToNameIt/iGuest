// Theme preference: 'light' | 'dark' | 'system'. Persisted per browser and
// applied as a `data-theme` attribute on <html> so CSS can key off it.
// index.html also sets this attribute inline on load to avoid a flash of the
// wrong theme before this module runs.
const KEY = 'iguest_theme'

function resolveSystem() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function getThemePreference() {
  return localStorage.getItem(KEY) || 'system'
}

function applyTheme(pref) {
  document.documentElement.setAttribute('data-theme', pref === 'system' ? resolveSystem() : pref)
}

export function setThemePreference(pref) {
  localStorage.setItem(KEY, pref)
  applyTheme(pref)
}

// Call once at startup: keeps the resolved theme in sync if the OS preference
// changes while "system" is selected.
export function initTheme() {
  applyTheme(getThemePreference())
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (getThemePreference() === 'system') applyTheme('system')
  })
}
