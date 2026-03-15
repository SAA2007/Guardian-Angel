/**
 * AngelBadge — Decorative header with angel art
 *
 * Shows guardian_angel_medium.png with Arabic text.
 */

export default function AngelBadge() {
  return (
    <div className="flex flex-col items-center py-6">
      <img
        src="/api/assets/guardian_angel_medium.png"
        alt="Guardian Angel"
        className="h-16 mb-3"
        style={{
          filter: 'drop-shadow(0 0 12px #C9A84C66)',
          objectFit: 'contain',
        }}
        onError={(e) => {
          e.target.style.display = 'none';
        }}
      />

      <h1
        className="text-2xl font-bold tracking-wide"
        style={{ color: '#C9A84C' }}
      >
        Guardian Angel 🛡️
      </h1>

      <p
        className="text-xl mt-2 font-serif"
        style={{
          color: '#C9A84C',
          fontFamily: "'Amiri', 'Traditional Arabic', serif",
          direction: 'rtl',
        }}
      >
        كِرَامًا كَاتِبِين
      </p>

      <p
        className="text-xs mt-1 italic"
        style={{ color: '#A89B80' }}
      >
        &ldquo;Honourable Recorders&rdquo; &mdash; Quran 82:11
      </p>
    </div>
  );
}
