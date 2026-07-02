// Geo reference client (public /api/geo endpoints — Italian regions/provinces/
// cities). Cascading: provinces depend on a region, cities on a province. The
// data lives server-side, so the SPA stays light.

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

async function get(path) {
  try {
    const r = await fetch(`${BACKEND_URL}${path}`)
    if (!r.ok) return []
    return await r.json()
  } catch {
    return []
  }
}

export const fetchRegions = () => get('/api/geo/regions')
export const fetchProvinces = (region) =>
  get(`/api/geo/provinces${region ? `?region=${encodeURIComponent(region)}` : ''}`)
export const fetchCities = (province) =>
  get(`/api/geo/cities${province ? `?province=${encodeURIComponent(province)}` : ''}`)
