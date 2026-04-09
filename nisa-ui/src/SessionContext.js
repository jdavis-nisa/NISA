const SESSION_API = "http://localhost:8095"

const NISA_API_KEY = import.meta.env.VITE_NISA_API_KEY || ""

const headers = {
  "Content-Type": "application/json",
  "X-NISA-API-Key": NISA_API_KEY,
}

// Listeners for Chat tab pulse notification
const listeners = []

export function onNewContext(fn) {
  listeners.push(fn)
  return () => {
    const i = listeners.indexOf(fn)
    if (i > -1) listeners.splice(i, 1)
  }
}

function notifyListeners(entry) {
  listeners.forEach(fn => fn(entry))
}

export async function pushContext({ tab, operation, summary, detail = null }) {
  try {
    const res = await fetch(`${SESSION_API}/context/add`, {
      method: "POST",
      headers,
      body: JSON.stringify({ tab, operation, summary, detail }),
    })
    if (res.ok) {
      notifyListeners({ tab, operation, summary })
    }
  } catch (e) {
    console.warn("Session context push failed:", e)
  }
}

export async function getContextSummary() {
  try {
    const res = await fetch(`${SESSION_API}/context/summary`, { headers })
    const data = await res.json()
    return data.summary || null
  } catch (e) {
    return null
  }
}

export async function getLatestContext(limit = 5) {
  try {
    const res = await fetch(`${SESSION_API}/context/latest?limit=${limit}`, { headers })
    const data = await res.json()
    return data.entries || []
  } catch (e) {
    return []
  }
}

export async function clearContext() {
  try {
    await fetch(`${SESSION_API}/context/clear`, { method: "DELETE", headers })
  } catch (e) {
    console.warn("Session context clear failed:", e)
  }
}
