import React, { useMemo } from 'react';
import {
  BarChart3, PieChart as PieIcon, Gauge, Layers,
} from 'lucide-react';

/**
 * DashboardPanel - lightweight analytics view.
 * Pure inline SVG, NO new npm dependency. Reads only from the
 * existing /api/analyze response payload (testCases, explanations).
 */

const TYPE_COLORS = {
  positive: 'var(--positive)',
  negative: 'var(--negative)',
  boundary: 'var(--boundary)',
  unknown:  'var(--text-muted)',
};

const PRIORITY_COLORS = {
  5: '#DC2626',
  4: '#EA580C',
  3: '#D97706',
  2: '#65A30D',
  1: '#0EA5E9',
};

function countBy(items, fn) {
  return items.reduce((acc, x) => {
    const k = fn(x) || 'unknown';
    acc[k] = (acc[k] || 0) + 1;
    return acc;
  }, {});
}

// ─── Bar chart (horizontal) ─────────────────────────────────────
function BarChart({ data, colorFn, title }) {
  const max = Math.max(1, ...Object.values(data));
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return null;

  return (
    <div className="dash-chart">
      <div className="dash-chart-title">{title}</div>
      <div className="dash-bars">
        {entries.map(([label, val]) => {
          const pct = (val / max) * 100;
          const color = colorFn ? colorFn(label) : 'var(--accent)';
          return (
            <div key={label} className="dash-bar-row">
              <div className="dash-bar-label" title={label}>
                {label.replace(/_/g, ' ')}
              </div>
              <div className="dash-bar-track">
                <div
                  className="dash-bar-fill"
                  style={{ width: `${pct}%`, background: color }}
                />
              </div>
              <div className="dash-bar-value">{val}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Pie chart (SVG) ────────────────────────────────────────────
function PieChart({ data, colorFn, title }) {
  const entries = Object.entries(data).filter(([, v]) => v > 0);
  const total = entries.reduce((a, [, v]) => a + v, 0);
  if (total === 0) return null;

  const radius = 70;
  const cx = 90, cy = 90;
  let acc = 0;
  const slices = entries.map(([label, v]) => {
    const startAngle = (acc / total) * Math.PI * 2 - Math.PI / 2;
    acc += v;
    const endAngle = (acc / total) * Math.PI * 2 - Math.PI / 2;
    const x1 = cx + radius * Math.cos(startAngle);
    const y1 = cy + radius * Math.sin(startAngle);
    const x2 = cx + radius * Math.cos(endAngle);
    const y2 = cy + radius * Math.sin(endAngle);
    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
    const d = `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
    return { label, value: v, d, color: colorFn ? colorFn(label) : 'var(--accent)' };
  });

  return (
    <div className="dash-chart">
      <div className="dash-chart-title">{title}</div>
      <div className="dash-pie-wrap">
        <svg width="180" height="180" viewBox="0 0 180 180" className="dash-pie">
          {slices.length === 1 ? (
            <circle cx={cx} cy={cy} r={radius} fill={slices[0].color} />
          ) : (
            slices.map((s, i) => (
              <path key={i} d={s.d} fill={s.color} stroke="#fff" strokeWidth="2" />
            ))
          )}
        </svg>
        <div className="dash-pie-legend">
          {slices.map((s) => (
            <div key={s.label} className="dash-legend-item">
              <span className="dash-legend-dot" style={{ background: s.color }} />
              <span className="dash-legend-label">{s.label}</span>
              <span className="dash-legend-value">
                {s.value} ({Math.round((s.value / total) * 100)}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Confidence donut (svg) ─────────────────────────────────────
function ConfidenceMeter({ explanations }) {
  const total = explanations?.length || 0;
  if (!total) return null;
  const high = explanations.filter((e) => e.confidence === 'high').length;
  const pct = Math.round((high / total) * 100);
  const radius = 60, stroke = 12, c = 80;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (pct / 100) * circ;

  return (
    <div className="dash-chart">
      <div className="dash-chart-title">Explanation Confidence</div>
      <div className="dash-donut-wrap">
        <svg width="160" height="160" viewBox="0 0 160 160">
          <circle cx={c} cy={c} r={radius} fill="none"
                  stroke="var(--bg-subtle)" strokeWidth={stroke} />
          <circle cx={c} cy={c} r={radius} fill="none"
                  stroke="var(--accent)" strokeWidth={stroke}
                  strokeDasharray={circ} strokeDashoffset={offset}
                  strokeLinecap="round"
                  transform={`rotate(-90 ${c} ${c})`} />
          <text x={c} y={c - 4} textAnchor="middle"
                fontSize="22" fontWeight="700" fill="var(--text-primary)">
            {pct}%
          </text>
          <text x={c} y={c + 16} textAnchor="middle"
                fontSize="10" fill="var(--text-muted)">
            high-confidence
          </text>
        </svg>
        <div className="dash-donut-info">
          <div><b>{high}</b> of {total} explanations are high-confidence.</div>
          <div className="dash-small-muted">
            Lower confidence usually means the case was generated by the NLP
            fallback rather than a direct pattern match.
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── KPI strip ─────────────────────────────────────────────────
function Kpi({ label, value, Icon }) {
  return (
    <div className="dash-kpi">
      <div className="dash-kpi-icon"><Icon size={18} /></div>
      <div>
        <div className="dash-kpi-value">{value}</div>
        <div className="dash-kpi-label">{label}</div>
      </div>
    </div>
  );
}

// ─── Main panel ────────────────────────────────────────────────
export default function DashboardPanel({ testCases = [], explanations = [] }) {
  const stats = useMemo(() => {
    const types = countBy(testCases, (tc) => tc.type);
    const cats  = countBy(testCases, (tc) => tc.category);
    const prios = countBy(
      testCases.filter((tc) => tc.priority),
      (tc) => `P${tc.priority}`,
    );
    const avgPrio =
      testCases.filter((tc) => tc.priority).length > 0
        ? (
            testCases.reduce((a, tc) => a + (tc.priority || 0), 0) /
            testCases.filter((tc) => tc.priority).length
          ).toFixed(1)
        : null;
    return { types, cats, prios, avgPrio };
  }, [testCases]);

  if (!testCases.length) return null;

  return (
    <div className="dashboard-panel">
      <div className="dash-kpi-row">
        <Kpi label="Total cases"     value={testCases.length}                  Icon={Layers} />
        <Kpi label="Categories"      value={Object.keys(stats.cats).length}    Icon={BarChart3} />
        <Kpi label="Explanations"    value={explanations.length}               Icon={PieIcon} />
        {stats.avgPrio && (
          <Kpi label="Avg priority"  value={stats.avgPrio}                     Icon={Gauge} />
        )}
      </div>

      <div className="dash-grid">
        <PieChart
          title="Test Type Distribution"
          data={stats.types}
          colorFn={(t) => TYPE_COLORS[t] || TYPE_COLORS.unknown}
        />
        <BarChart
          title="Cases per Category"
          data={stats.cats}
        />
        {Object.keys(stats.prios).length > 0 && (
          <BarChart
            title="Priority Mix"
            data={stats.prios}
            colorFn={(label) => {
              const n = parseInt(String(label).replace('P', ''), 10);
              return PRIORITY_COLORS[n] || 'var(--accent)';
            }}
          />
        )}
        <ConfidenceMeter explanations={explanations} />
      </div>
    </div>
  );
}
