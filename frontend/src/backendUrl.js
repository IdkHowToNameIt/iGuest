// Shared backend origin, used both for API calls (adminApi.js/hostApi.js) and
// to resolve backend-relative asset paths (e.g. avatar_url like
// "/uploads/avatars/xyz.png") into a full <img src>.
export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
