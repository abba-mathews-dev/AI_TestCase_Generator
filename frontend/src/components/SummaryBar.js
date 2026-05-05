import React from 'react';
import { ClipboardList, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

export default function SummaryBar({ testCases }) {
  if (!testCases?.length) return null;

  const total    = testCases.length;
  const positive = testCases.filter(t => t.type === 'positive').length;
  const negative = testCases.filter(t => t.type === 'negative').length;
  const boundary = testCases.filter(t => t.type === 'boundary').length;

  const stats = [
    { label: 'Total Cases',  value: total,    color: 'accent',   Icon: ClipboardList  },
    { label: 'Positive',     value: positive, color: 'positive', Icon: CheckCircle2   },
    { label: 'Negative',     value: negative, color: 'negative', Icon: XCircle        },
    { label: 'Boundary',     value: boundary, color: 'boundary', Icon: AlertTriangle  },
  ];

  return (
    <div className="summary-bar">
      {stats.map(({ label, value, color, Icon }) => (
        <div key={label} className="summary-stat">
          <div className={`summary-stat-icon ${color}`}>
            <Icon size={18} />
          </div>
          <div className="summary-stat-body">
            <div className="label">{label}</div>
            <div className={`value ${color}`}>{value}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
