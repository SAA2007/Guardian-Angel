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

export async function postQuit() {
  return safeFetch(`${BASE}/quit`, { method: 'POST' });
}
