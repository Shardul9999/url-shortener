const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(message, { status, retryAfter } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.retryAfter = retryAfter
  }
}

/**
 * FastAPI/Pydantic v2 returns 422 bodies as { detail: [{ msg, loc, type }, ...] }.
 * Custom field_validator ValueError messages arrive prefixed "Value error, ".
 */
function extractDetailMessage(body) {
  if (typeof body?.detail === 'string') return body.detail
  if (Array.isArray(body?.detail) && body.detail.length > 0) {
    return body.detail[0].msg.replace(/^Value error,\s*/, '')
  }
  return 'Something went wrong. Please try again.'
}

async function request(path, options) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch {
    throw new ApiError('Could not reach the API. Is the server running?', { status: 0 })
  }

  if (!response.ok) {
    let body = {}
    try {
      body = await response.json()
    } catch {
      // non-JSON error body — fall through with generic message
    }
    throw new ApiError(extractDetailMessage(body), {
      status: response.status,
      retryAfter: response.headers.get('Retry-After'),
    })
  }

  return response.json()
}

export function shortenUrl({ originalUrl, expiresInHours }) {
  return request('/shorten', {
    method: 'POST',
    body: JSON.stringify({
      original_url: originalUrl,
      expires_in_hours: expiresInHours || null,
    }),
  })
}

export function getAnalytics(shortCode) {
  return request(`/analytics/${encodeURIComponent(shortCode)}`, { method: 'GET' })
}
