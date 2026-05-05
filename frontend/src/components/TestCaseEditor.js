import React, { useState, useEffect } from 'react';
import { X, Save, Plus, Trash2 } from 'lucide-react';

/**
 * TestCaseEditor - inline modal that lets the user edit a single
 * generated test case. The result is returned via onSave; persistence
 * happens in the parent App state so the edits flow into PDF/Excel
 * exports without any backend change.
 */
export default function TestCaseEditor({ testCase, onSave, onClose }) {
  const [draft, setDraft] = useState(null);

  useEffect(() => {
    if (testCase) {
      setDraft({
        ...testCase,
        preconditions: [...(testCase.preconditions || [])],
        steps: [...(testCase.steps || [])],
        expected_results: [...(testCase.expected_results || [])],
      });
    }
  }, [testCase]);

  if (!testCase || !draft) return null;

  const updateList = (key, idx, value) => {
    const next = [...draft[key]];
    next[idx] = value;
    setDraft({ ...draft, [key]: next });
  };
  const addItem = (key) =>
    setDraft({ ...draft, [key]: [...draft[key], ''] });
  const removeItem = (key, idx) =>
    setDraft({ ...draft, [key]: draft[key].filter((_, i) => i !== idx) });

  const handleSave = () => {
    const cleaned = {
      ...draft,
      preconditions: draft.preconditions.filter((x) => x.trim()),
      steps: draft.steps.filter((x) => x.trim()),
      expected_results: draft.expected_results.filter((x) => x.trim()),
      _edited: true,
      _edited_at: new Date().toISOString(),
    };
    onSave(cleaned);
  };

  const renderListEditor = (key, label, placeholder) => (
    <div className="tce-section">
      <div className="tce-section-head">
        <label>{label}</label>
        <button
          type="button"
          className="tce-mini-btn"
          onClick={() => addItem(key)}
        >
          <Plus size={11} /> Add
        </button>
      </div>
      {draft[key].length === 0 && (
        <div className="tce-empty">No items. Click "Add" to create one.</div>
      )}
      {draft[key].map((item, i) => (
        <div key={i} className="tce-list-row">
          <span className="tce-list-num">{i + 1}.</span>
          <input
            type="text"
            value={item}
            placeholder={placeholder}
            onChange={(e) => updateList(key, i, e.target.value)}
          />
          <button
            type="button"
            className="tce-del-btn"
            onClick={() => removeItem(key, i)}
            title="Remove"
          >
            <Trash2 size={12} />
          </button>
        </div>
      ))}
    </div>
  );

  return (
    <div className="tce-overlay" onMouseDown={onClose}>
      <div className="tce-modal" onMouseDown={(e) => e.stopPropagation()}>
        <div className="tce-header">
          <div>
            <div className="tce-id">{draft.id}</div>
            <div className="tce-sub">Edit test case</div>
          </div>
          <button className="tce-close" onClick={onClose} title="Close">
            <X size={16} />
          </button>
        </div>

        <div className="tce-body">
          <div className="tce-section">
            <label>Title</label>
            <input
              type="text"
              value={draft.title || ''}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            />
          </div>

          <div className="tce-row-2">
            <div className="tce-section">
              <label>Type</label>
              <select
                value={draft.type || ''}
                onChange={(e) => setDraft({ ...draft, type: e.target.value })}
              >
                <option value="positive">positive</option>
                <option value="negative">negative</option>
                <option value="boundary">boundary</option>
              </select>
            </div>
            <div className="tce-section">
              <label>Category</label>
              <input
                type="text"
                value={draft.category || ''}
                onChange={(e) => setDraft({ ...draft, category: e.target.value })}
              />
            </div>
          </div>

          {renderListEditor('preconditions', 'Preconditions', 'e.g. The user is logged in')}
          {renderListEditor('steps',         'Test Steps',     'e.g. Click the Submit button')}
          {renderListEditor('expected_results', 'Expected Results', 'e.g. A confirmation dialog appears')}
        </div>

        <div className="tce-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave}>
            <Save size={13} /> Save changes
          </button>
        </div>
      </div>
    </div>
  );
}
