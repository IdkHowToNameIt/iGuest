import { useEffect, useState } from 'react'
import { fetchRegions, fetchProvinces, fetchCities } from '../geoApi.js'

// Cascading Region → Province → City selectors over the static /api/geo dataset.
// Controlled: `value` is { region, province, city } (any may be ''), and
// `onChange` receives the next full object. Picking a higher level resets the
// lower ones. The empty option reads `allLabel` (e.g. "All regions") when used
// as a filter, or a neutral placeholder when used in a form.
export default function GeoSelect({ value, onChange, allLabel = '— select —', idPrefix = 'geo' }) {
  const { region = '', province = '', city = '' } = value || {}
  const [regions, setRegions] = useState([])
  const [provinces, setProvinces] = useState([])
  const [cities, setCities] = useState([])

  useEffect(() => {
    fetchRegions().then(setRegions)
  }, [])

  useEffect(() => {
    if (!region) {
      setProvinces([])
      return
    }
    fetchProvinces(region).then(setProvinces)
  }, [region])

  useEffect(() => {
    if (!province) {
      setCities([])
      return
    }
    fetchCities(province).then(setCities)
  }, [province])

  return (
    <div className="geo-select">
      <div className="form-row">
        <label htmlFor={`${idPrefix}-region`}>Region</label>
        <select
          id={`${idPrefix}-region`}
          className="select"
          value={region}
          onChange={(e) => onChange({ region: e.target.value, province: '', city: '' })}
        >
          <option value="">{allLabel}</option>
          {regions.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>
      <div className="form-row">
        <label htmlFor={`${idPrefix}-province`}>Province</label>
        <select
          id={`${idPrefix}-province`}
          className="select"
          value={province}
          disabled={!region}
          onChange={(e) => onChange({ region, province: e.target.value, city: '' })}
        >
          <option value="">{allLabel}</option>
          {provinces.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>
      <div className="form-row">
        <label htmlFor={`${idPrefix}-city`}>City</label>
        <select
          id={`${idPrefix}-city`}
          className="select"
          value={city}
          disabled={!province}
          onChange={(e) => onChange({ region, province, city: e.target.value })}
        >
          <option value="">{allLabel}</option>
          {cities.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>
    </div>
  )
}
