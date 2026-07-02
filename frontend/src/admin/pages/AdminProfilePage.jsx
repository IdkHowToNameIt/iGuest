import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { updateProfile, uploadAvatar, deleteAvatar } from '../adminApi.js'
import Avatar from '../../components/Avatar.jsx'
import { useT } from '../../i18n/index.jsx'

// The single admin account's profile: display name + avatar picture. Backed
// by a singleton `admin_profile` row (the admin itself has no DB row — see
// app/services/auth.py — since credentials come from .env).
export default function AdminProfilePage() {
  const { t } = useT()
  const { profile, refreshProfile } = useOutletContext() ?? {}

  const [displayName, setDisplayName] = useState('')
  const [saving, setSaving] = useState(false)
  const [avatarBusy, setAvatarBusy] = useState(false)
  const [error, setError] = useState(null)

  // AdminLayout fetches the profile asynchronously (it's null on first
  // render); seed the editable field once it arrives.
  useEffect(() => {
    if (profile) setDisplayName(profile.display_name || '')
  }, [profile])

  if (!profile) return <p className="muted">{t('Loading…')}</p>

  async function handleSaveName(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await updateProfile({ display_name: displayName.trim() || null })
      await refreshProfile?.()
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleAvatarChange(e) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setAvatarBusy(true)
    try {
      await uploadAvatar(file)
      await refreshProfile?.()
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setAvatarBusy(false)
    }
  }

  async function handleAvatarDelete() {
    setAvatarBusy(true)
    try {
      await deleteAvatar()
      await refreshProfile?.()
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setAvatarBusy(false)
    }
  }

  return (
    <>
      <h1>{t('Profile')}</h1>
      {error && <p className="error-text">{error}</p>}

      <section className="card">
        <h2>{t('Profile picture')}</h2>
        <div className="avatar-upload">
          <Avatar name={profile.display_name || 'Admin'} avatarUrl={profile.avatar_url} size={80} zoomable />
          <div className="avatar-upload-actions">
            <label className="btn btn-ghost btn-sm">
              {avatarBusy ? t('Uploading…') : t('Upload photo')}
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleAvatarChange}
                disabled={avatarBusy}
                style={{ display: 'none' }}
              />
            </label>
            {profile.avatar_url && (
              <button className="btn btn-ghost btn-sm" onClick={handleAvatarDelete} disabled={avatarBusy}>
                {t('Remove photo')}
              </button>
            )}
          </div>
        </div>
      </section>

      <section className="card">
        <h2>{t('Display name')}</h2>
        <form className="form" onSubmit={handleSaveName}>
          <div className="form-row">
            <label htmlFor="displayName">{t('Name shown in the admin panel')}</label>
            <input
              id="displayName"
              className="input"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Admin"
              maxLength={200}
            />
          </div>
          <div className="form-actions">
            <button className="btn" type="submit" disabled={saving}>
              {saving ? t('Saving…') : t('Save')}
            </button>
          </div>
        </form>
      </section>
    </>
  )
}
