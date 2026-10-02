export default function RoadIllustration(props) {
  return (
    <svg viewBox="0 0 480 560" fill="none" {...props}>
      {/* Road surface */}
      <path d="M170 0 L120 560 L360 560 L310 0 Z" fill="#262B29" />
      {/* Lane markings, receding */}
      <g stroke="#EFEEE7" strokeWidth="10" strokeLinecap="round" opacity="0.85">
        <line x1="240" y1="40" x2="238" y2="90" />
        <line x1="238" y1="140" x2="236" y2="190" />
        <line x1="236" y1="240" x2="233" y2="292" />
        <line x1="233" y1="344" x2="230" y2="400" />
        <line x1="230" y1="452" x2="226" y2="512" />
      </g>
      {/* Pothole marker */}
      <ellipse cx="205" cy="330" rx="34" ry="20" fill="#171A19" />
      <ellipse cx="205" cy="330" rx="34" ry="20" stroke="#D98A2B" strokeWidth="3" />

      {/* Location pin, oversized, planted on the road — the one bold element */}
      <g transform="translate(240 150)">
        <path
          d="M0 0C-46 0-84 37-84 83c0 64 84 157 84 157s84-93 84-157C84 37 46 0 0 0Z"
          fill="#D98A2B"
        />
        <circle cx="0" cy="83" r="34" fill="#1E2321" />
        <path d="M-14 83l10 10 20-22" stroke="#EFEEE7" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
      </g>

      {/* Distant buildings, low silhouette */}
      <g fill="#1E2321" opacity="0.9">
        <rect x="20" y="470" width="46" height="90" />
        <rect x="76" y="440" width="34" height="120" />
        <rect x="380" y="450" width="40" height="110" />
        <rect x="428" y="480" width="32" height="80" />
      </g>
    </svg>
  )
}
