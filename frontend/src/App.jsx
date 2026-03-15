/**
 * Guardian Angel — Main Dashboard App
 *
 * Single-page dashboard with live polling.
 */

import { useState, useEffect } from 'react';
import { getStatus, getConfig, updateConfig, getStats } from './api';
import AngelBadge from './components/AngelBadge';
import StatusBar from './components/StatusBar';
import StatsPanel from './components/StatsPanel';
import ConfigPanel from './components/ConfigPanel';

export default function App() {
  const [status, setStatus] = useState(null);
  const [stats, setStats] = useState(null);
  const [config, setConfig] = useState(null);

  // Poll /status every 2 seconds
  useEffect(() => {
    getStatus().then(setStatus);
    const id = setInterval(() => {
      getStatus().then(setStatus);
    }, 2000);
    return () => clearInterval(id);
  }, []);

  // Poll /stats every 5 seconds
  useEffect(() => {
    getStats().then(setStats);
    const id = setInterval(() => {
      getStats().then(setStats);
    }, 5000);
    return () => clearInterval(id);
  }, []);

  // Load config once
  useEffect(() => {
    getConfig().then(setConfig);
  }, []);

  // Handle config changes
  async function handleConfigUpdate(patch) {
    const updated = await updateConfig(patch);
    if (updated) setConfig(updated);
  }

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: '#0F0A00' }}
    >
      {/* Header */}
      <AngelBadge />

      {/* Status bar */}
      <StatusBar status={status} />

      {/* Main content */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <StatsPanel stats={stats} />
          <ConfigPanel config={config} onUpdate={handleConfigUpdate} />
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center py-4">
        <p className="text-xs" style={{ color: '#8B7332' }}>
          Guardian Angel — protecting your journey
        </p>
      </footer>
    </div>
  );
}
