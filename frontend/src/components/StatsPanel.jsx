/**
 * StatsPanel — Session & lifetime stats card
 *
 * Islamic-themed dark card with gold accents.
 */

import { useState, useEffect } from 'react';
import { getRecentEvents } from '../api';

function formatUptime(seconds) {
  const s = Math.floor(seconds || 0);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return [h, m, sec].map((v) => String(v).padStart(2, '0')).join(':');
}

function formatTime(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return iso;
  }
}

export default function StatsPanel({ stats }) {
  const [events, setEvents] = useState(null);

  useEffect(() => {
    getRecentEvents().then(setEvents);
    const id = setInterval(() => {
      getRecentEvents().then(setEvents);
    }, 5000);
    return () => clearInterval(id);
  }, []);

  if (!stats) return null;

  return (
    <div
      className="rounded-xl p-6"
      style={{
        backgroundColor: '#1A1408',
        border: '1px solid #2A2010',
      }}
    >
      <h2
        className="text-lg font-semibold mb-4"
        style={{ color: '#C9A84C' }}
      >
        📊 Protection Stats
      </h2>

      {/* Days protected — hero number */}
      <div className="text-center mb-6">
        <div
          className="text-5xl font-bold"
          style={{ color: '#C9A84C' }}
        >
          {stats.days_protected}
        </div>
        <div className="text-sm mt-1" style={{ color: '#A89B80' }}>
          days protected
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-4">
        <div
          className="rounded-lg p-3 text-center"
          style={{ backgroundColor: '#0F0A00' }}
        >
          <div className="text-2xl font-bold" style={{ color: '#F5F0E6' }}>
            {stats.current_streak} 🔥
          </div>
          <div className="text-xs mt-1" style={{ color: '#A89B80' }}>
            streak
          </div>
        </div>

        <div
          className="rounded-lg p-3 text-center"
          style={{ backgroundColor: '#0F0A00' }}
        >
          <div className="text-2xl font-bold" style={{ color: '#F5F0E6' }}>
            {stats.total_triggers}
          </div>
          <div className="text-xs mt-1" style={{ color: '#A89B80' }}>
            total blocked
          </div>
        </div>

        <div
          className="rounded-lg p-3 text-center"
          style={{ backgroundColor: '#0F0A00' }}
        >
          <div className="text-2xl font-bold" style={{ color: '#F5F0E6' }}>
            {stats.session_triggers}
          </div>
          <div className="text-xs mt-1" style={{ color: '#A89B80' }}>
            session blocked
          </div>
        </div>

        <div
          className="rounded-lg p-3 text-center"
          style={{ backgroundColor: '#0F0A00' }}
        >
          <div
            className="text-2xl font-bold font-mono"
            style={{ color: '#F5F0E6' }}
          >
            {formatUptime(stats.uptime_seconds)}
          </div>
          <div className="text-xs mt-1" style={{ color: '#A89B80' }}>
            uptime
          </div>
        </div>
      </div>

      {/* Live Activity Feed */}
      <div className="mt-6 pt-4" style={{ borderTop: '1px solid #2A2010' }}>
        <h3 className="text-sm font-semibold mb-3" style={{ color: '#C9A84C' }}>
          📡 Live Activity
        </h3>
        {events && events.length > 0 ? (
          <div className="space-y-2">
            {events.map((evt, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="font-mono" style={{ color: '#A89B80' }}>
                  [{formatTime(evt.timestamp)}]
                </span>
                <span style={{ color: '#F5F0E6' }}>
                  {evt.type === 'video' ? '🎬 Video' : '🔊 Audio'} trigger detected
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs" style={{ color: '#A89B80' }}>
            No triggers detected yet. Stay strong. 💪
          </p>
        )}
      </div>
    </div>
  );
}
