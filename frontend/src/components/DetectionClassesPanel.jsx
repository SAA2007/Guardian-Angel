/**
 * DetectionClassesPanel — Toggle which NudeNet classes to censor
 *
 * Groups classes into Explicit / Suggestive / Other sections
 * with proper flex-row toggle switches.
 */

import { updateConfig } from '../api';

// NudeNet class → human label, grouped by category
const CLASS_GROUPS = [
  {
    title: 'Explicit (censored by default)',
    classes: [
      { key: 'FEMALE_BREAST_EXPOSED', label: 'Exposed breast (female)' },
      { key: 'FEMALE_GENITALIA_EXPOSED', label: 'Exposed genitalia (female)' },
      { key: 'MALE_GENITALIA_EXPOSED', label: 'Exposed genitalia (male)' },
      { key: 'BUTTOCKS_EXPOSED', label: 'Exposed buttocks' },
    ],
  },
  {
    title: 'Suggestive (off by default)',
    classes: [
      { key: 'FEMALE_BREAST_COVERED', label: 'Covered breast' },
      { key: 'FEMALE_GENITALIA_COVERED', label: 'Covered genitalia' },
      { key: 'BUTTOCKS_COVERED', label: 'Covered buttocks' },
    ],
  },
  {
    title: 'Other (off by default)',
    classes: [
      { key: 'FACE_FEMALE', label: 'Female face' },
      { key: 'FACE_MALE', label: 'Male face' },
      { key: 'BELLY_EXPOSED', label: 'Belly' },
      { key: 'BELLY_COVERED', label: 'Belly (covered)' },
      { key: 'ARMPITS_EXPOSED', label: 'Armpits' },
      { key: 'ARMPITS_COVERED', label: 'Armpits (covered)' },
      { key: 'FEET_EXPOSED', label: 'Feet' },
    ],
  },
];

export default function DetectionClassesPanel({ config, onUpdate }) {
  if (!config) return null;

  const classes = config.detection_classes || {};

  async function handleToggle(key) {
    const updated = { ...classes, [key]: !classes[key] };
    const result = await updateConfig({ detection_classes: updated });
    if (result && onUpdate) onUpdate(result);
  }

  return (
    <div
      className="rounded-xl p-6"
      style={{
        background: 'linear-gradient(135deg, #1A1200 0%, #0F0A00 100%)',
        border: '1px solid #2A1F00',
      }}
    >
      <h2
        className="text-lg font-semibold mb-4"
        style={{ color: '#C9A84C' }}
      >
        🎯 What to Censor
      </h2>

      {CLASS_GROUPS.map((group) => (
        <div key={group.title} className="mb-5">
          <div
            className="text-xs font-bold tracking-widest uppercase mt-4 mb-2"
            style={{ color: '#8B7332' }}
          >
            {group.title}
          </div>
          <div>
            {group.classes.map((cls) => {
              const enabled = !!classes[cls.key];
              return (
                <div
                  key={cls.key}
                  className="flex items-center justify-between py-2"
                  style={{ borderBottom: '1px solid rgba(139, 115, 50, 0.15)' }}
                >
                  <span
                    className="text-sm"
                    style={{ color: enabled ? '#E8D5A3' : '#666' }}
                  >
                    {cls.label}
                  </span>
                  <button
                    onClick={() => handleToggle(cls.key)}
                    className="relative flex-shrink-0 rounded-full transition-colors duration-200"
                    style={{
                      width: '48px',
                      height: '24px',
                      backgroundColor: enabled ? '#C9A84C' : '#333',
                      border: 'none',
                      cursor: 'pointer',
                      padding: 0,
                    }}
                  >
                    <span
                      className="block rounded-full bg-white transition-all duration-200"
                      style={{
                        width: '18px',
                        height: '18px',
                        position: 'absolute',
                        top: '3px',
                        left: enabled ? '27px' : '3px',
                      }}
                    />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
