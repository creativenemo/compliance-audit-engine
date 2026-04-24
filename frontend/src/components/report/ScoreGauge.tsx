"use client";

interface Props {
  score: number;   // 0–100
  label: string;
  weight?: string; // e.g. "25%"
}

// Map a 0-100 score to a color string
function scoreColor(score: number): string {
  if (score >= 80) return "#16a34a"; // green-600
  if (score >= 60) return "#d97706"; // amber-600
  if (score >= 40) return "#dc2626"; // red-600
  return "#7f1d1d";                  // red-900 (dark-red)
}

// Map score to a track + needle angle on a 180° semi-circle
// 0 → left end (-180deg from 12 o'clock), 100 → right end (0deg)
function describeArc(cx: number, cy: number, r: number, score: number) {
  // Full arc spans from 180° to 0° (left half-circle on top)
  // score 0 → startAngle = 180, score 100 → startAngle = 0
  const startDeg = 180; // fixed left end
  const endDeg = 180 - (score / 100) * 180; // sweeps right as score increases

  function polarToCartesian(angle: number) {
    const rad = ((angle - 90) * Math.PI) / 180;
    return {
      x: cx + r * Math.cos(rad),
      y: cy + r * Math.sin(rad),
    };
  }

  const start = polarToCartesian(startDeg);
  const end = polarToCartesian(endDeg);
  const largeArc = score > 50 ? 1 : 0;

  // Arc sweeps counter-clockwise from left to right
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}

// The full background arc (always the full semi-circle)
function fullArc(cx: number, cy: number, r: number) {
  const left = { x: cx - r, y: cy };
  const right = { x: cx + r, y: cy };
  return `M ${left.x} ${left.y} A ${r} ${r} 0 1 1 ${right.x} ${right.y}`;
}

export function ScoreGauge({ score, label, weight }: Props) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const cx = 60;
  const cy = 60;
  const r = 46;
  const color = scoreColor(clamped);
  const trackPath = fullArc(cx, cy, r);
  const fillPath = clamped === 0 ? null : describeArc(cx, cy, r, clamped);

  return (
    <div className="flex flex-col items-center gap-1">
      <svg
        viewBox="0 0 120 68"
        className="w-28 h-16 sm:w-32 sm:h-[4.5rem]"
        aria-label={`${label}: ${clamped} out of 100`}
        role="img"
      >
        {/* Background track */}
        <path
          d={trackPath}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="9"
          strokeLinecap="round"
        />
        {/* Score fill */}
        {fillPath && (
          <path
            d={fillPath}
            fill="none"
            stroke={color}
            strokeWidth="9"
            strokeLinecap="round"
          />
        )}
        {/* Center numeric score */}
        <text
          x={cx}
          y={cy - 2}
          textAnchor="middle"
          dominantBaseline="auto"
          fontSize="18"
          fontWeight="700"
          fill={color}
        >
          {clamped}
        </text>
      </svg>
      <p className="text-xs font-semibold text-gray-700 text-center leading-tight">{label}</p>
      {weight && (
        <p className="text-[10px] text-gray-400 text-center">{weight}</p>
      )}
    </div>
  );
}
