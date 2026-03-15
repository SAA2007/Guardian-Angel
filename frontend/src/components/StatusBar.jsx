/**
 * StatusBar — Top status indicator bar
 *
 * Shows 3 pill indicators (Detection, Overlay, Audio) with
 * live/dead states, plus FPS counter.
 */

export default function StatusBar({ status }) {
  if (!status) return null;

  const pills = [
    { label: 'Detection', alive: status.detection_alive },
    { label: 'Overlay', alive: status.overlay_alive },
    { label: 'Audio', alive: status.audio_alive },
  ];

  return (
    <div
      className="flex items-center justify-between px-6 py-3"
      style={{
        backgroundColor: '#1A1408',
        borderBottom: '2px solid #C9A84C',
      }}
    >
      <div className="flex gap-3">
        {pills.map((p) => (
          <span
            key={p.label}
            className="flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium"
            style={{
              backgroundColor: p.alive ? '#1A2E1A' : '#2E1A1A',
              color: p.alive ? '#4ADE80' : '#F87171',
              border: `1px solid ${p.alive ? '#22C55E33' : '#EF444433'}`,
            }}
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor: p.alive ? '#4ADE80' : '#F87171',
                boxShadow: p.alive
                  ? '0 0 6px #4ADE80'
                  : '0 0 6px #F87171',
              }}
            />
            {p.label}
          </span>
        ))}
      </div>

      <span
        className="text-sm font-mono font-bold"
        style={{ color: '#C9A84C' }}
      >
        {(status.fps_actual || 0).toFixed(1)} FPS
      </span>
    </div>
  );
}
