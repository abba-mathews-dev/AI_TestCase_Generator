import React from 'react';
import { ClipboardCheck, Download, Pencil, Sparkles } from 'lucide-react';
import { downloadTestCaseExcel } from '../utils/api';

function PriorityBadge({ tc }) {
  if (!tc.priority) return null;
  const className =
    tc.priority >= 5 ? 'p1-crit' :
    tc.priority === 4 ? 'p1' :
    tc.priority === 3 ? 'p2' :
    tc.priority === 2 ? 'p3' : 'p3-low';
  return (
    <span
      className={`tc-priority ${className}`}
      title={(tc.priority_reasons || []).join(' • ')}
    >
      {tc.priority_label || `P${tc.priority}`}
    </span>
  );
}

function TestCaseCard({ tc, onEdit }) {
  const badgeClass =
    tc.type === 'positive' ? 'positive' :
    tc.type === 'boundary' ? 'boundary' : 'negative';

  return (
    <div className={`test-case-card ${tc._edited ? 'tc-edited' : ''}`}>
      <div className="tc-header">
        <div className="tc-header-left">
          <div className="tc-id">
            {tc.id}
            {tc._edited && (
              <span className="tc-edited-flag" title="Edited locally">
                <Sparkles size={10} /> edited
              </span>
            )}
          </div>
          <div className="tc-title">{tc.title}</div>
        </div>
        <div className="tc-header-right">
          <PriorityBadge tc={tc} />
          <span className={`tc-badge ${badgeClass}`}>{tc.type}</span>
          {onEdit && (
            <button
              className="btn-icon"
              title="Edit this test case"
              onClick={() => onEdit(tc)}
            >
              <Pencil size={12} />
            </button>
          )}
          <button
            className="btn-icon"
            title="Download as Excel"
            onClick={() => downloadTestCaseExcel(tc)}
          >
            <Download size={12} />
          </button>
        </div>
      </div>

      {tc.preconditions?.length > 0 && (
        <>
          <div className="tc-section-label">Preconditions</div>
          <ul className="tc-list">
            {tc.preconditions.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </>
      )}

      <div className="tc-section-label">Test Steps</div>
      <ol className="tc-list numbered" style={{ counterReset: 'step' }}>
        {tc.steps?.map((s, i) => <li key={i}>{s}</li>)}
      </ol>

      <div className="tc-section-label">Expected Results</div>
      <ul className="tc-list">
        {tc.expected_results?.map((e, i) => <li key={i}>{e}</li>)}
      </ul>
    </div>
  );
}

export default function TestCasesPanel({ testCases, onEdit }) {
  if (!testCases?.length) return null;

  return (
    <div className="panel test-cases-panel">
      <div className="panel-header">
        <h3>
          <ClipboardCheck size={15} />
          Generated Test Cases
        </h3>
        <span className="panel-count">{testCases.length}</span>
      </div>
      <div className="test-cases-scroll">
        {testCases.map((tc, i) => (
          <TestCaseCard key={tc.id || i} tc={tc} onEdit={onEdit} />
        ))}
      </div>
    </div>
  );
}
