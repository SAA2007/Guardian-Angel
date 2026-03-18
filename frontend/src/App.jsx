/**
 * Guardian Angel — Main Dashboard App
 *
 * Two-column dashboard grid with live polling.
 */

import { useState, useEffect } from 'react';
import { getStatus, getConfig, updateConfig, getStats, postQuit } from './api';
import AngelBadge from './components/AngelBadge';
import StatusBar from './components/StatusBar';
import StatsPanel from './components/StatsPanel';
import ConfigPanel from './components/ConfigPanel';
import DetectionClassesPanel from './components/DetectionClassesPanel';
import PersistencePanel from './components/PersistencePanel';

export default function App() {
  const [status, setStatus] = useState(null);
  const [stats, setStats] = useState(null);
  const [config, setConfig] = useState(null);
  const [shutdownMsg, setShutdownMsg] = useState(null);

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

  // Handle shutdown
  async function handleShutdown() {
    setShutdownMsg('Shutting down...');
    await postQuit();
    setTimeout(() => {
      setShutdownMsg('You can close this window.');
    }, 2000);
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

      {/* Main content — two-column grid */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left column (40%) — Stats + Persistence */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            <StatsPanel stats={stats} />
            <PersistencePanel />
          </div>

          {/* Right column (60%) — Config + Detection Classes */}
          <div className="lg:col-span-3 flex flex-col gap-6">
            <ConfigPanel config={config} onUpdate={handleConfigUpdate} />
            <DetectionClassesPanel config={config} onUpdate={setConfig} />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="flex justify-between items-center px-6 py-4">
        <p className="text-xs" style={{ color: '#8B7332' }}>
          Guardian Angel — protecting your journey
        </p>
        {shutdownMsg ? (
          <span className="text-xs text-red-400">{shutdownMsg}</span>
        ) : (
          <button
            onClick={handleShutdown}
            className="text-xs text-red-900/70 hover:text-red-400 transition-colors bg-transparent border-none cursor-pointer"
          >
            Shut down Guardian Angel
          </button>
        )}
      </footer>
    </div>
  );
}
