function resolveApiBase() {
  const envBase = (import.meta.env.VITE_API_BASE_URL || '').trim()
  if (envBase) return envBase

  if (typeof window !== 'undefined') {
    const host = window.location.hostname
    const protocol = window.location.protocol || 'https:'

    if (host === 'smawell.shop' || host === 'www.smawell.shop') {
      return `${protocol}//api.smawell.shop`
    }

    if (host === 'localhost' || host === '127.0.0.1') {
      return 'http://127.0.0.1:5301'
    }
  }

  return 'http://127.0.0.1:5301'
}

export const API_BASE = resolveApiBase()

export async function request(path, options = {}) {
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers || {}),
    },
  })

  const raw = await response.text()
  let data = {}

  if (raw) {
    try {
      data = JSON.parse(raw)
    } catch {
      if (!response.ok) {
        throw new Error('Server returned an invalid response')
      }
      throw new Error('Server returned a non-JSON response')
    }
  }

  if (!response.ok) {
    throw new Error(data.message || 'Request failed')
  }

  return data
}
