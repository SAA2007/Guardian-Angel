/**
 * ConfigPanel — Settings controls
 *
 * Sends PATCH /config on every change.
 */

const CENSOR_OPTIONS = [
  { value: 'guardian_angel', label: 'Guardian Angel' },
  { value: 'solid_black', label: 'Solid Black' },
  { value: 'solid_white', label: 'Solid White' },
  { value: 'blur_light', label: 'Blur (Light)' },
  { value: 'blur_medium', label: 'Blur (Medium)' },
  { value: 'blur_heavy', label: 'Blur (Heavy)' },
  { value: 'pixelate', label: 'Pixelate' },
];

const AUDIO_OPTIONS = [
  { value: 'silence', label: 'Silence' },
  { value: 'bleep', label: 'Bleep' },
];

const selectStyle = {
  backgroundColor: '#0F0A00',
  color: '#F5F0E6',
  border: '1px solid #2A2010',
  padding: '6px 10px',
  borderRadius: '6px',
  width: '100%',
  outline: 'none',
};

const labelStyle = {
  color: '#A89B80',
  fontSize: '0.85rem',
  marginBottom: '4px',
  display: 'block',
};

export default function ConfigPanel({ config, onUpdate }) {
  if (!config) return null;

  function handleChange(field, value) {
    onUpdate({ [field]: value });
  }

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
        ⚙️ Settings
      </h2>

      <div className="flex flex-col gap-4">
        {/* Censor style */}
        <div>
          <label style={labelStyle}>Censor Style</label>
          <select
            style={selectStyle}
            value={config.censor_style}
            onChange={(e) => handleChange('censor_style', e.target.value)}
          >
            {CENSOR_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {/* Sensitivity */}
        <div>
          <label style={labelStyle}>
            Sensitivity: {config.sensitivity?.toFixed(2)}
          </label>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={config.sensitivity || 0.6}
            onChange={(e) =>
              handleChange('sensitivity', parseFloat(e.target.value))
            }
            className="w-full"
            style={{ accentColor: '#C9A84C' }}
          />
        </div>

        {/* FPS max */}
        <div>
          <label style={labelStyle}>Max FPS</label>
          <input
            type="number"
            min="1"
            max="60"
            value={config.fps_max || 60}
            onChange={(e) =>
              handleChange('fps_max', parseInt(e.target.value, 10))
            }
            style={{ ...selectStyle, width: '80px' }}
          />
        </div>

        {/* Audio action */}
        <div>
          <label style={labelStyle}>Audio Action</label>
          <select
            style={selectStyle}
            value={config.audio_action}
            onChange={(e) => handleChange('audio_action', e.target.value)}
          >
            {AUDIO_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {/* Auto FPS Drop */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={config.fps_auto_drop || false}
            onChange={(e) =>
              handleChange('fps_auto_drop', e.target.checked)
            }
            style={{ accentColor: '#C9A84C' }}
          />
          <span style={{ color: '#A89B80', fontSize: '0.85rem' }}>
            Auto FPS Drop
          </span>
        </label>

        {/* Dev Mode */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={config.dev_mode || false}
            onChange={(e) => handleChange('dev_mode', e.target.checked)}
            style={{ accentColor: '#C9A84C' }}
          />
          <span style={{ color: '#A89B80', fontSize: '0.85rem' }}>
            Developer Mode
          </span>
        </label>
      </div>
    </div>
  );
}
