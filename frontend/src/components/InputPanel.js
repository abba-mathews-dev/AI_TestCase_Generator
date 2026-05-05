import React from 'react';
import { Zap } from 'lucide-react';

const EXAMPLES = [
  'As a user, I want to login so that I can access my dashboard.',
  'As an admin, I want to manage user roles so that I can control access permissions.',
  'As a customer, I want to search for products so that I can find items to purchase.',
  'As a user, I want to reset my password so that I can recover my account if I forget it.',
];

export default function InputPanel({ story, setStory, onAnalyze, loading }) {
  return (
    <div className="input-panel">
      <div className="input-panel-header">
        <h2>User Story Input</h2>
        <p className="subtitle">
          Enter a user story in plain English - TestCraft will generate structured test cases with full reasoning.
        </p>
      </div>

      <textarea
        className="story-textarea"
        value={story}
        onChange={(e) => setStory(e.target.value)}
        placeholder='e.g. "As a user, I want to login so that I can access my dashboard."'
        disabled={loading}
        rows={4}
      />

      <div className="input-controls">
        <button
          className="btn-primary"
          onClick={onAnalyze}
          disabled={loading || !story.trim()}
        >
          {loading ? (
            <>
              <span className="spinner-sm" />
              Analyzing…
            </>
          ) : (
            <>
              <Zap size={15} />
              Generate Test Cases
            </>
          )}
        </button>
      </div>

      <div className="example-stories">
        <span style={{ fontSize: 12, color: 'var(--text-muted)', marginRight: 4, flexShrink: 0 }}>
          Try:
        </span>
        {EXAMPLES.map((ex, i) => (
          <button
            key={i}
            className="example-chip"
            onClick={() => setStory(ex)}
            disabled={loading}
          >
            {ex.length > 52 ? ex.slice(0, 52) + '…' : ex}
          </button>
        ))}
      </div>
    </div>
  );
}
