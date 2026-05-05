import React, { useState } from 'react';
import { Brain, Hammer, Briefcase, Code2 } from 'lucide-react';

/**
 * Audience-aware reasoning. The backend explanation array is unchanged.
 * This is pure client-side text adaptation that re-frames each reasoning
 * line for the chosen reader.
 */
const AUDIENCES = [
  { key: 'tester',    label: 'Tester',    Icon: Hammer,
    blurb: 'Technical wording that maps to QA practice and ISTQB terms.' },
  { key: 'manager',   label: 'Manager',   Icon: Briefcase,
    blurb: 'Concise business framing that focuses on risk and coverage.' },
  { key: 'developer', label: 'Developer', Icon: Code2,
    blurb: 'Code-oriented framing that highlights inputs, branches, and edge cases.' },
];

function adaptLine(line, audience) {
  if (!line) return line;
  if (audience === 'tester') {
    return line; // already tester-oriented
  }
  if (audience === 'manager') {
    return line
      .replace(/NLP parser/gi,           'requirement analyser')
      .replace(/NLP fallback/gi,         'fallback analysis')
      .replace(/dependency parsing/gi,   'language analysis')
      .replace(/regular expression(s)?/gi, 'pattern matching')
      .replace(/heuristic(s)?/gi,        'rule(s)')
      .replace(/ISTQB/gi,                'industry standard')
      .replace(/QA/gi,                   'quality assurance')
      .replace(/boundary value analysis/gi, 'edge-case checks')
      .replace(/equivalence partitioning/gi, 'input grouping')
      .replace(/precondition/gi,         'prerequisite');
  }
  if (audience === 'developer') {
    return line
      .replace(/user-facing input/gi,    'input field / form parameter')
      .replace(/missing\/empty data/gi,  'null / empty argument')
      .replace(/system-level errors/gi,  'runtime errors (network, timeout, 5xx)')
      .replace(/credentials/gi,          'auth payload')
      .replace(/error handling/gi,       'exception path')
      .replace(/QA practice/gi,          'unit/integration test practice')
      .replace(/edges of valid input ranges/gi, 'min/max bounds (off-by-one zone)')
      .replace(/boundary value analysis/gi, 'min/max boundary checks');
  }
  return line;
}

function buildSummary(exp, audience) {
  const id = exp.test_case_id;
  const conf = (exp.confidence || '').toLowerCase();
  if (audience === 'manager') {
    return `${id} was generated with ${conf || 'unspecified'} confidence. ` +
      `It addresses risk identified directly from the requirement text.`;
  }
  if (audience === 'developer') {
    return `${id} (${conf || '?'} confidence) — driven by signals extracted ` +
      `from the user story (see story_mapping below).`;
  }
  return null; // tester view shows no extra summary
}

function ExplanationCard({ exp, audience }) {
  const summary = buildSummary(exp, audience);
  return (
    <div className="explanation-card">
      <div className="exp-title">
        <span>{exp.test_case_id} - {exp.test_case_title}</span>
        <span className={`exp-confidence ${exp.confidence}`}>{exp.confidence}</span>
      </div>

      {summary && (
        <div className="exp-audience-summary">{summary}</div>
      )}

      <ul className="exp-reasoning">
        {exp.reasoning?.map((r, i) => <li key={i}>{adaptLine(r, audience)}</li>)}
      </ul>

      {exp.story_mapping?.length > 0 && (
        <div className="exp-mapping">
          <div className="exp-mapping-label">Story Mapping</div>
          {exp.story_mapping.map((sm, i) => (
            <span key={i} className="mapping-tag" title={sm.text}>
              {sm.element}: {sm.description?.slice(0, 60)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ExplanationPanel({ explanations }) {
  const [audience, setAudience] = useState('tester');
  if (!explanations?.length) return null;

  const current = AUDIENCES.find((a) => a.key === audience) || AUDIENCES[0];

  return (
    <div className="panel explanation-panel">
      <div className="panel-header">
        <h3><Brain size={15} /> Explainability - Why These Tests?</h3>
        <span className="panel-count">{explanations.length}</span>
      </div>

      <div className="exp-audience-bar">
        <div className="exp-audience-label">Read as:</div>
        <div className="exp-audience-tabs">
          {AUDIENCES.map(({ key, label, Icon }) => (
            <button
              key={key}
              className={`exp-audience-btn ${audience === key ? 'active' : ''}`}
              onClick={() => setAudience(key)}
            >
              <Icon size={12} /> {label}
            </button>
          ))}
        </div>
      </div>
      <div className="exp-audience-blurb">{current.blurb}</div>

      <div className="explanation-cards">
        {explanations.map((exp, i) => (
          <ExplanationCard key={i} exp={exp} audience={audience} />
        ))}
      </div>
    </div>
  );
}
