const SESSION_API = "http://localhost:8095"

const NISA_API_KEY = import.meta.env.VITE_NISA_API_KEY || ""

const headers = {
  "Content-Type": "application/json",
  "X-NISA-API-Key": NISA_API_KEY,
}

// Listeners for Chat tab pulse notification
const listeners = []

// Listeners for Orb alerts
const alertListeners = []
let pendingAlerts = []

export function onAlert(fn) {
  alertListeners.push(fn)
  // Fire immediately if there are pending alerts
  if (pendingAlerts.length > 0) fn(pendingAlerts)
  return () => {
    const i = alertListeners.indexOf(fn)
    if (i > -1) alertListeners.splice(i, 1)
  }
}

export async function pushAlert({ title, summary, severity = 'high', source = 'system', recommendation = '' }) {
  const alert = {
    id: Date.now(),
    title,
    summary,
    severity,
    source,
    recommendation,
    timestamp: new Date().toISOString(),
    acknowledged: false
  }
  pendingAlerts.push(alert)
  alertListeners.forEach(fn => fn([...pendingAlerts]))
  // Also push to session context store
  await pushContext({
    tab: source,
    operation: 'ALERT: ' + title,
    summary: summary,
    detail: alert
  })
  return alert
}

export function acknowledgeAlerts() {
  pendingAlerts = []
  alertListeners.forEach(fn => fn([]))
}

export function getPendingAlerts() {
  return [...pendingAlerts]
}

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
