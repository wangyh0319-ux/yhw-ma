const API = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

function errorMessage(payload, fallback) {
  if (typeof payload?.detail === 'string') {
    return payload.detail
  }
  return fallback
}

async function readJson(response, fallback) {
  const text = await response.text()
  let payload = null
  try {
    payload = text ? JSON.parse(text) : null
  } catch {
    if (response.status === 413) {
      throw new Error('File is too large for the server. Try a file under 15 MB.')
    }
    if (response.status === 502 || response.status === 504 || response.status === 408) {
      throw new Error(
        'Analysis timed out on the server. Try a shorter song (under 3 minutes, under 15 MB).',
      )
    }
    throw new Error(fallback)
  }
  if (!response.ok) {
    throw new Error(errorMessage(payload, fallback))
  }
  return payload
}

export async function checkHealth() {
  const response = await fetch(`${API}/health`)
  if (!response.ok) {
    throw new Error('Health check failed')
  }
  return response.json()
}

export async function analyzeAudio(file) {
  const body = new FormData()
  body.append('file', file)

  const response = await fetch(`${API}/api/analyze/run`, {
    method: 'POST',
    body,
  })
  return readJson(response, 'Analysis failed')
}

export async function mixAudio(file) {
  const body = new FormData()
  body.append('file', file)

  const response = await fetch(`${API}/api/mixing/run`, {
    method: 'POST',
    body,
  })
  return readJson(response, 'Mixing analysis failed')
}

export async function listLibraryTaxonomy() {
  const response = await fetch(`${API}/api/library/taxonomy`)
  const payload = await response.json()
  if (!response.ok) {
    throw new Error(errorMessage(payload, 'Could not load tags'))
  }
  return payload
}

export async function listLibraryTracks() {
  const response = await fetch(`${API}/api/library/tracks`)
  const payload = await response.json()
  if (!response.ok) {
    throw new Error(errorMessage(payload, 'Could not load library'))
  }
  return payload.tracks
}

export async function createLibraryTrack(title, artist) {
  const response = await fetch(`${API}/api/library/tracks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, artist }),
  })
  const payload = await response.json()
  if (!response.ok) {
    throw new Error(errorMessage(payload, 'Could not create track'))
  }
  return payload
}

export async function uploadLibraryTrack(file, title, artist) {
  const body = new FormData()
  body.append('file', file)
  body.append('title', title || '')
  body.append('artist', artist || '')

  const response = await fetch(`${API}/api/library/tracks/upload`, {
    method: 'POST',
    body,
  })
  const payload = await response.json()
  if (!response.ok) {
    throw new Error(errorMessage(payload, 'Could not upload track'))
  }
  return payload
}

export function libraryAudioUrl(trackId) {
  return `${API}/api/library/tracks/${trackId}/audio`
}

export async function searchLibraryScene(text) {
  const response = await fetch(`${API}/api/library/search/scene`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return readJson(response, 'Scene search failed')
}

export async function tagLibraryTrack(trackId) {
  const response = await fetch(`${API}/api/library/tracks/${trackId}/tag`, {
    method: 'POST',
  })
  const payload = await response.json()
  if (!response.ok) {
    throw new Error(errorMessage(payload, 'Tagging failed'))
  }
  return payload
}

export async function deleteLibraryTrack(trackId) {
  const response = await fetch(`${API}/api/library/tracks/${trackId}`, {
    method: 'DELETE',
  })
  const payload = await response.json()
  if (!response.ok) {
    throw new Error(errorMessage(payload, 'Could not delete track'))
  }
}
