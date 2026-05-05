import React from 'react';
import { ScanSearch } from 'lucide-react';

export default function AnalysisPanel({ analysis }) {
  if (!analysis) return null;

  const rows = [
    ['Actor',   analysis.actor   || 'N/A'],
    ['Action',  analysis.action  || 'N/A'],
    ['Outcome', analysis.outcome || 'Not specified'],
  ];

  if (analysis.conditions?.length) {
    rows.push(['Conditions', analysis.conditions.map(c => c.context).join('; ')]);
  }
  if (analysis.verbs?.length) {
    rows.push(['Key Verbs', analysis.verbs.map(v => v.text).join(', ')]);
  }
  if (analysis.objects?.length) {
    rows.push(['Key Objects', analysis.objects.map(o => o.text).join(', ')]);
  }

  return (
    <div className="panel analysis-panel">
      <div className="panel-header">
        <h3><ScanSearch size={15} /> NLP Analysis</h3>
      </div>
      <div className="panel-body">
        <table className="analysis-table">
          <tbody>
            {rows.map(([label, value], i) => (
              <tr key={i}>
                <td>{label}</td>
                <td>{value}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {analysis.source_mappings?.length > 0 && (
          <div className="extraction-tags">
            <div className="extraction-label">Extraction Method</div>
            {analysis.source_mappings.map((sm, i) => (
              <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '3px 0' }}>
                <span className="mapping-tag">{sm.type.replace(/_/g, ' ')}</span>
                {sm.description}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
