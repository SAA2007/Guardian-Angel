import { useState, useEffect } from 'react';
import * as api from '../api';
import AngelBadge from './AngelBadge';

export default function PersistencePanel() {
  const [status, setStatus] = useState(null);
  const [flowState, setFlowState] = useState(null);
  const [reason, setReason] = useState('');

  async function loadStatus() {
    const s = await api.getPersistenceStatus();
    setStatus(s);
  }

  // Fetch status on mount
  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    const s = await api.getPersistenceStatus();
    setStatus(s);
  }

  // --- Disable Flow Actions ---

  async function handleStartDisable() {
    const res = await api.startDisableFlow();
    setFlowState(res);
  }

  const pollDisableState = async () => {
    if (!flowState || flowState.state !== 'WAITING') return;
    const res = await api.getDisableState();
    setFlowState(res);
  };

  // Poll waiting state every second to show countdown
  useEffect(() => {
    let timer;
    if (flowState?.state === 'WAITING' || flowState?.state === 'LOCKED') {
      timer = setInterval(pollDisableState, 1000);
    }
    return () => clearInterval(timer);
  }, [flowState, pollDisableState]);

  async function handleAdvance(payload = {}) {
    const res = await api.advanceDisableFlow(payload);
    setFlowState(res);
    if (res?.state === 'DONE') {
      loadStatus(); // refresh top-level lock status
    }
  }

  // --- Mode Switching ---

  async function handleSetMode(mode, days = 30) {
    if (!confirm(`Are you sure you want to change protection to ${mode.toUpperCase()} mode?`)) return;
    const res = await api.setPersistenceMode(mode, mode === 'timed' ? days : null);
    setStatus(res);
  }

  // --- Renders ---

  if (!status) return null;

  // 1. If we are inside the disable flow, take over the screen content
  if (flowState && flowState.state !== 'DONE') {
    return (
      <div className="rounded-xl p-8 outline outline-1 outline-red-900/50 bg-[#1A1408] text-center max-w-lg mx-auto mt-8">
        <AngelBadge />
        <h2 className="text-xl font-bold text-[#C9A84C] mt-6 mb-4">Disable Protection</h2>

        {flowState.state === 'LOCKED' && (
          <div>
            <div className="text-4xl mb-4">🔒</div>
            <p className="text-red-400 font-medium mb-2">{flowState.message}</p>
            <p className="text-[#A89B80] mb-6">
              Lock expires in: {Math.ceil((flowState.remaining_seconds || 0) / 86400)} days
            </p>
            <button
              onClick={() => setFlowState(null)}
              className="px-6 py-2 bg-[#2A2010] text-[#F5F0E6] rounded hover:bg-[#3A2D16] transition-colors"
            >
              Return to Dashboard
            </button>
          </div>
        )}

        {flowState.state === 'WAITING' && (
          <div>
            <p className="text-[#F5F0E6] text-lg mb-4 mt-8">Taking a moment to reflect...</p>
            <div className="text-5xl font-mono text-[#C9A84C] mb-8">
              {Math.ceil(flowState.remaining_seconds)}s
            </div>
            <p className="text-[#A89B80] text-sm">Please wait before proceeding.</p>
          </div>
        )}

        {flowState.state === 'REASON' && (
          <div className="text-left">
            <label className="block text-[#C9A84C] font-medium mb-2">
              Why do you want to disable Guardian Angel?
            </label>
            <textarea
              className="w-full h-32 bg-[#0F0A00] text-[#F5F0E6] p-3 rounded border border-[#2A2010] outline-none resize-none focus:border-[#C9A84C] transition-colors"
              placeholder="Please be honest with yourself..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <div className="flex justify-between items-center mt-4">
              <span className="text-xs text-gray-500">
                Minimum 10 characters ({reason.length}/10)
              </span>
              <button
                onClick={() => handleAdvance({ reason })}
                disabled={reason.length < 10}
                className="px-6 py-2 bg-red-900/80 text-white rounded font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-800 transition-colors"
              >
                Submit
              </button>
            </div>
          </div>
        )}

        {flowState.state === 'STATS' && (
          <div>
            <p className="text-[#F5F0E6] text-lg mb-6">Look how far you've come.</p>
            <div className="grid grid-cols-2 gap-4 text-left mb-8">
              <div className="bg-[#0F0A00] p-4 rounded border border-[#2A2010]">
                <div className="text-xs text-[#A89B80] uppercase tracking-wider mb-1">Protected</div>
                <div className="text-2xl text-[#C9A84C] font-semibold">{flowState.stats?.days_protected} days</div>
              </div>
              <div className="bg-[#0F0A00] p-4 rounded border border-[#2A2010]">
                <div className="text-xs text-[#A89B80] uppercase tracking-wider mb-1">Current Streak</div>
                <div className="text-2xl text-[#C9A84C] font-semibold">{flowState.stats?.streak} days</div>
              </div>
              <div className="bg-[#0F0A00] p-4 rounded border border-[#2A2010] col-span-2">
                <div className="text-xs text-[#A89B80] uppercase tracking-wider mb-1">Temptations Blocked</div>
                <div className="text-2xl text-[#C9A84C] font-semibold">{flowState.stats?.total_triggers} triggers</div>
              </div>
            </div>
            <button
              onClick={() => handleAdvance()}
              className="px-6 py-2 bg-red-900/80 text-white rounded font-medium hover:bg-red-800 transition-colors w-full"
            >
              Continue Disable Process
            </button>
          </div>
        )}

        {flowState.state === 'NOTIFY' && (
          <div>
            <p className="text-[#F5F0E6] mb-8">
              Your accountability contact will be notified of this action, including the reason you provided.
            </p>
            <button
              onClick={() => handleAdvance()}
              className="px-6 py-2 bg-red-600 text-white font-bold rounded hover:bg-red-500 transition-colors w-full"
            >
              Disable Guardian Angel
            </button>
          </div>
        )}
      </div>
    );
  }

  // 2. Normal Persistence Panel inside dashboard
  return (
    <div className="rounded-xl p-6 bg-[#1A1408] border border-[#2A2010]">
      <div className="flex justify-between items-start mb-4">
        <h2 className="text-lg font-semibold text-[#C9A84C]">
          🛡️ Lock & Watchdog
        </h2>
        {status.mode === 'off' ? (
          <span className="px-3 py-1 bg-green-900/30 text-green-400 text-xs font-bold rounded-full border border-green-800/50">
            UNLOCKED
          </span>
        ) : (
          <span className="px-3 py-1 bg-red-900/30 text-red-400 text-xs font-bold rounded-full border border-red-800/50">
            LOCKED
          </span>
        )}
      </div>

      <p className="text-sm text-[#F5F0E6] mb-6">
        {status.mode === 'off' && "Protection can be disabled anytime."}
        {status.mode === 'timed' && `Locked for ${Math.ceil((status.remaining_seconds || 0) / 86400)} more days.`}
        {status.mode === 'indefinite' && "Locked indefinitely — complete disable flow required to stop."}
      </p>

      {/* Mode Selector */}
      <div className="space-y-3 mb-8">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="radio"
            name="persistence_mode"
            checked={status.mode === 'off'}
            onChange={() => handleSetMode('off')}
            className="mt-1"
            style={{ accentColor: '#C9A84C' }}
          />
          <div>
            <div className="text-[#F5F0E6] font-medium">Off</div>
            <div className="text-xs text-gray-500">Easy to stop via dashboard. Ideal for testing.</div>
          </div>
        </label>
        
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="radio"
            name="persistence_mode"
            checked={status.mode === 'timed'}
            onChange={() => handleSetMode('timed', 30)}
            className="mt-1"
            style={{ accentColor: '#C9A84C' }}
          />
          <div>
            <div className="text-[#F5F0E6] font-medium">Timed (30 Days)</div>
            <div className="text-xs text-gray-500">Cannot be disabled until timer expires.</div>
          </div>
        </label>
        
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="radio"
            name="persistence_mode"
            checked={status.mode === 'indefinite'}
            onChange={() => handleSetMode('indefinite')}
            className="mt-1"
            style={{ accentColor: '#C9A84C' }}
          />
          <div>
            <div className="text-[#F5F0E6] font-medium">Indefinite</div>
            <div className="text-xs text-gray-500">Requires 60s wait, reason, and accountability notification to stop.</div>
          </div>
        </label>
      </div>

      <button
        onClick={handleStartDisable}
        className="w-full py-3 bg-[#2A2010] text-red-400 font-semibold rounded hover:bg-[#3A2D16] border border-red-900/30 transition-colors"
      >
        Disable Protection...
      </button>
    </div>
  );
}
