/**
 * ConfigPanel — Settings controls
 *
 * Uses local state for sliders to prevent snap-back.
 * Commits on mouseup/blur, selects commit immediately.
 */

import { useState, useEffect, useRef } from 'react';

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

const SCALE_OPTIONS = [
  { value: 1.0, label: 'Quality (100%) — most accurate' },
  { value: 0.5, label: 'Balanced (50%) — recommended' },
  { value: 0.25, label: 'Performance (25%) — faster' },
  { value: 0.125, label: 'Ultra-Low (12.5%) — weak hardware' },
];

const SKIP_OPTIONS = [
  { value: 1, label: 'Every frame — most responsive' },
  { value: 2, label: 'Every 2nd frame — balanced (default)' },
  { value: 3, label: 'Every 3rd frame — fastest' },
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
  // Local state for sliders/inputs — prevents snap-back
  const [local, setLocal] = useState({});
  const isDirty = useRef(false);

  // Sync from API config when not dirty
  useEffect(() => {
    if (config && !isDirty.current) {
      setLocal({
        sensitivity: config.sensitivity ?? 0.1,
        detection_box_padding: config.detection_box_padding ?? 0.4,
        onnx_threads: config.onnx_threads ?? 4,
        fps_max: config.fps_max ?? 10,
      });
    }
  }, [config]);

  if (!config) return null;

  // Slider/input: update local only
  function handleLocalChange(key, value) {
    isDirty.current = true;
    setLocal((prev) => ({ ...prev, [key]: value }));
  }

  // Commit on mouseup/blur — fire PATCH
  function handleCommit(key) {
    isDirty.current = false;
    onUpdate({ [key]: local[key] });
  }

  // Selects/checkboxes commit immediately
  function handleDirect(field, value) {
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
          <p className="text-xs text-gray-500 mb-2 mt-[-2px]">
            How detected content is covered on screen
          </p>
          <select
            style={selectStyle}
            value={config.censor_style}
            onChange={(e) => handleDirect('censor_style', e.target.value)}
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
            Sensitivity: {(local.sensitivity ?? 0.1).toFixed(2)}
          </label>
          <p className="text-xs text-gray-500 mb-2 mt-[-2px]">
            0.1 = catches more (may have false positives) | 1.0 = explicit content only
          </p>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={local.sensitivity ?? 0.1}
            onChange={(e) =>
              handleLocalChange('sensitivity', parseFloat(e.target.value))
            }
            onMouseUp={() => handleCommit('sensitivity')}
            onTouchEnd={() => handleCommit('sensitivity')}
            className="w-full"
            style={{ accentColor: '#C9A84C' }}
          />
        </div>

        {/* Box Padding */}
        <div>
          <label style={labelStyle}>
            Box Padding: {(local.detection_box_padding ?? 0.4).toFixed(2)}
          </label>
          <p className="text-xs text-gray-500 mb-2 mt-[-2px]">
            Expands censor boxes around detected regions. Higher = more coverage.
          </p>
          <input
            type="range"
            min="0.0"
            max="1.0"
            step="0.05"
            value={local.detection_box_padding ?? 0.4}
            onChange={(e) =>
              handleLocalChange('detection_box_padding', parseFloat(e.target.value))
            }
            onMouseUp={() => handleCommit('detection_box_padding')}
            onTouchEnd={() => handleCommit('detection_box_padding')}
            className="w-full"
            style={{ accentColor: '#C9A84C' }}
          />
        </div>

        {/* Detection Scale */}
        <div>
          <label style={labelStyle}>Detection Resolution</label>
          <p className="text-xs text-gray-500 mb-2 mt-[-2px]">
            Lower = faster detection, slightly less accurate
          </p>
          <select
            style={selectStyle}
            value={config.detection_scale ?? 0.5}
            onChange={(e) => handleDirect('detection_scale', parseFloat(e.target.value))}
          >
            {SCALE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {/* Frame Skip */}
        <div>
          <label style={labelStyle}>Detection Rate</label>
          <p className="text-xs text-gray-500 mb-2 mt-[-2px]">
            Higher skip = better FPS, slight detection delay
          </p>
          <select
            style={selectStyle}
            value={config.detection_skip_frames ?? 2}
            onChange={(e) => handleDirect('detection_skip_frames', parseInt(e.target.value, 10))}
          >
            {SKIP_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {/* ONNX Threads */}
        <div>
          <label style={labelStyle}>CPU Threads</label>
          <p className="text-xs text-gray-500 mb-2 mt-[-2px]">
            i7-8700 has 12 threads. Higher = faster detection, more CPU. Takes effect on next detection cycle.
          </p>
          <input
            type="number"
            min="1"
            max="16"
            step="1"
            value={local.onnx_threads ?? 4}
            onChange={(e) =>
              handleLocalChange('onnx_threads', parseInt(e.target.value, 10))
            }
            onBlur={() => handleCommit('onnx_threads')}
            style={{ ...selectStyle, width: '80px' }}
          />
        </div>

        {/* FPS max */}
        <div>
          <label style={labelStyle}>Max FPS</label>
          <p className="text-xs text-gray-500 mb-2 mt-[-2px]">
            Detection frame rate target. 10 recommended for CPU-only machines.
          </p>
          <input
            type="number"
            min="1"
            max="60"
            value={local.fps_max ?? 10}
            onChange={(e) =>
              handleLocalChange('fps_max', parseInt(e.target.value, 10))
            }
            onBlur={() => handleCommit('fps_max')}
            style={{ ...selectStyle, width: '80px' }}
          />
        </div>

        {/* Audio action */}
        <div>
          <label style={labelStyle}>Audio Action</label>
          <p className="text-xs text-gray-500 mb-2 mt-[-2px]">
            What happens to audio when explicit content is detected
          </p>
          <select
            style={selectStyle}
            value={config.audio_action}
            onChange={(e) => handleDirect('audio_action', e.target.value)}
          >
            {AUDIO_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {/* Auto FPS Drop */}
        <div>
            <label className="flex items-center gap-2 cursor-pointer mb-1">
              <input
                type="checkbox"
                checked={config.fps_auto_drop || false}
                onChange={(e) =>
                  handleDirect('fps_auto_drop', e.target.checked)
                }
                style={{ accentColor: '#C9A84C' }}
              />
              <span style={{ color: '#A89B80', fontSize: '0.85rem' }}>
                Auto FPS Drop
              </span>
            </label>
            <p className="text-xs text-gray-500 ml-6">
              Automatically reduces FPS if your machine cannot keep up
            </p>
        </div>

        {/* Dev Mode */}
        <div>
            <label className="flex items-center gap-2 cursor-pointer mb-1">
              <input
                type="checkbox"
                checked={config.dev_mode || false}
                onChange={(e) => handleDirect('dev_mode', e.target.checked)}
                style={{ accentColor: '#C9A84C' }}
              />
              <span style={{ color: '#A89B80', fontSize: '0.85rem' }}>
                Developer Mode
              </span>
            </label>
            <p className="text-xs text-gray-500 ml-6">
              Shows bounding boxes, FPS counter, and confidence scores
            </p>
        </div>
      </div>
    </div>
  );
}
