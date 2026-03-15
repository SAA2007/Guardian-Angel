/**
 * Guardian Angel — API Client
 *
 * All functions use fetch to /api/... (proxied to localhost:8421).
 * Returns parsed JSON on success, null on error (never throws).
 */

const BASE = '/api';

async function safeFetch(url, options) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function getStatus() {
  return safeFetch(`${BASE}/status`);
}

export async function getConfig() {
  return safeFetch(`${BASE}/config`);
}

export async function updateConfig(obj) {
  return safeFetch(`${BASE}/config`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(obj),
  });
}

export async function getStats() {
  return safeFetch(`${BASE}/stats`);
}

export async function getOverlay() {
  return safeFetch(`${BASE}/overlay`);
}

export async function getAudio() {
  return safeFetch(`${BASE}/audio`);
}

export async function getPersistenceStatus() {
  return safeFetch(`${BASE}/persistence/status`);
}

export async function startDisableFlow() {
  return safeFetch(`${BASE}/persistence/start-disable`, { method: 'POST' });
}

export async function getDisableState() {
  return safeFetch(`${BASE}/persistence/disable-state`);
}

export async function advanceDisableFlow(payload = {}) {
  return safeFetch(`${BASE}/persistence/advance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
}

export async function setPersistenceMode(mode, lock_duration_days = null) {
  return safeFetch(`${BASE}/persistence/set-mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode, lock_duration_days })
  });
}

export async function getWatchdogHealth() {
  return safeFetch(`${BASE}/watchdog/health`);
}

export async function postQuit() {
  return safeFetch(`${BASE}/quit`, { method: 'POST' });
}
