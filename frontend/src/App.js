import React, { useState, useRef, useEffect } from 'react';
import {
  FlaskConical, Download, FileText, FileSpreadsheet,
  ChevronDown, AlertCircle, TestTube2, Brain, BarChart3,
  Code2, Gauge, FileCheck2,
} from 'lucide-react';
import InputPanel from './components/InputPanel';
import AnalysisPanel from './components/AnalysisPanel';
import TestCasesPanel from './components/TestCasesPanel';
import ExplanationPanel from './components/ExplanationPanel';
import SummaryBar from './components/SummaryBar';
import DashboardPanel from './components/DashboardPanel';
import TestCaseEditor from './components/TestCaseEditor';
import {
  analyzeStory, downloadReport, downloadExcel,
  downloadScript, prioritizeTestCases,
} from './utils/api';
import './styles/App.css';

const REPORT_TEMPLATES = [
  { key: 'standard',       label: 'Standard PDF (engineering)' },
  { key: 'iso29119',       label: 'ISO/IEC/IEEE 29119 spec' },
  { key: 'one_pager',      label: 'One-pager summary' },
  { key: 'client_summary', label: 'Client / business summary' },
];

const SCRIPT_FRAMEWORKS = [
  { key: 'pytest',     label: 'Pytest (.py)' },
  { key: 'playwright', label: 'Playwright (.spec.js)' },
  { key: 'cypress',    label: 'Cypress (.cy.js)' },
  { key: 'postman',    label: 'Postman collection (.json)' },
  { key: 'cucumber',   label: 'Cucumber (.feature)' },
];

export default function App() {
  const [story, setStory] = useState('');
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('cases');
  const [exportOpen, setExportOpen] = useState(false);
  const [editingCase, setEditingCase] = useState(null);
  const [prioritizing, setPrioritizing] = useState(false);
  const exportRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e) {
      if (exportRef.current && !exportRef.current.contains(e.target)) {
        setExportOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeStory(story, 'plain');
      setResult(data);
      setActiveTab('cases');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePrioritize = async () => {
    if (!result) return;
    setPrioritizing(true);
    setError(null);
    try {
      const enriched = await prioritizeTestCases(story, result.test_cases);
      setResult({ ...result, test_cases: enriched });
    } catch (err) {
      setError('Prioritization failed: ' + err.message);
    } finally {
      setPrioritizing(false);
    }
  };

  const handleSaveEdit = (updated) => {
    if (!result) return;
    const next = result.test_cases.map((tc) =>
      tc.id === updated.id ? updated : tc,
    );
    setResult({ ...result, test_cases: next });
    setEditingCase(null);
  };

  const handleExportPDF = async (template = 'standard') => {
    if (!result) return;
    setExportOpen(false);
    setExporting(true);
    try {
      await downloadReport(
        story, result.analysis, result.test_cases, result.explanations,
        template,
      );
    } catch (err) {
      setError('PDF export failed: ' + err.message);
    } finally {
      setExporting(false);
    }
  };

  const handleExportExcel = () => {
    if (!result) return;
    setExportOpen(false);
    downloadExcel(story, result.analysis, result.test_cases, result.explanations);
  };

  const handleExportScript = async (framework) => {
    if (!result) return;
    setExportOpen(false);
    setExporting(true);
    try {
      await downloadScript(story, result.test_cases, framework);
    } catch (err) {
      setError('Script export failed: ' + err.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="app-container">
      {/* ── Header ──────────────────────────────────────── */}
      <header className="app-header">
        <div className="app-logo">
          <FlaskConical size={20} color="var(--accent)" />
          <h1>Test<span>Craft</span></h1>
        </div>

        <div className="header-actions">
          {result && (
            <>
              <button
                className="btn-secondary"
                onClick={handlePrioritize}
                disabled={prioritizing}
                title="Score each test case 1-5 by risk/priority"
              >
                {prioritizing ? <span className="spinner-sm" /> : <Gauge size={14} />}
                {prioritizing ? 'Scoring…' : 'Prioritize'}
              </button>

              <div className="export-dropdown" ref={exportRef}>
                <button
                  className="btn-secondary"
                  onClick={() => setExportOpen(o => !o)}
                  disabled={exporting}
                >
                  {exporting ? (
                    <span className="spinner-sm" />
                  ) : (
                    <Download size={14} />
                  )}
                  {exporting ? 'Exporting…' : 'Export'}
                  <ChevronDown size={13} style={{ marginLeft: 2, opacity: 0.7 }} />
                </button>

                {exportOpen && (
                  <div className="export-menu wide">
                    <div className="export-menu-section">
                      <div className="export-menu-heading">
                        <FileText size={11} /> PDF Reports
                      </div>
                      {REPORT_TEMPLATES.map((t) => (
                        <button
                          key={t.key}
                          className="export-menu-item"
                          onClick={() => handleExportPDF(t.key)}
                        >
                          <FileCheck2 size={14} className="item-icon" />
                          {t.label}
                        </button>
                      ))}
                    </div>

                    <div className="export-menu-divider" />

                    <div className="export-menu-section">
                      <div className="export-menu-heading">
                        <FileSpreadsheet size={11} /> Spreadsheets
                      </div>
                      <button className="export-menu-item" onClick={handleExportExcel}>
                        <FileSpreadsheet size={14} className="item-icon" />
                        Excel (.xlsx)
                      </button>
                    </div>

                    <div className="export-menu-divider" />

                    <div className="export-menu-section">
                      <div className="export-menu-heading">
                        <Code2 size={11} /> Test Script Skeletons
                      </div>
                      {SCRIPT_FRAMEWORKS.map((f) => (
                        <button
                          key={f.key}
                          className="export-menu-item"
                          onClick={() => handleExportScript(f.key)}
                        >
                          <Code2 size={14} className="item-icon" />
                          {f.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </header>

      {/* ── Main ────────────────────────────────────────── */}
      <main className="app-main">
        <InputPanel
          story={story}
          setStory={setStory}
          onAnalyze={handleAnalyze}
          loading={loading}
        />

        {error && (
          <div className="error-banner">
            <AlertCircle size={15} />
            {error}
          </div>
        )}

        {loading && (
          <div className="loading-overlay">
            <div className="spinner" />
            <div className="loading-text">Generating test cases…</div>
            <div className="loading-sub">Parsing story and applying NLP analysis</div>
          </div>
        )}

        {!loading && !result && !error && (
          <div className="empty-state">
            <div className="empty-state-icon">
              <FlaskConical size={32} />
            </div>
            <h3>No test cases yet</h3>
            <p>Enter a user story above and click "Generate Test Cases" to get started.</p>
          </div>
        )}

        {result && !loading && (
          <>
            <SummaryBar testCases={result.test_cases} />

            <div className="tab-bar">
              <button
                className={activeTab === 'cases' ? 'active' : ''}
                onClick={() => setActiveTab('cases')}
              >
                <TestTube2 size={14} />
                Test Cases
              </button>
              <button
                className={activeTab === 'explain' ? 'active' : ''}
                onClick={() => setActiveTab('explain')}
              >
                <Brain size={14} />
                Explainability
              </button>
              <button
                className={activeTab === 'dashboard' ? 'active' : ''}
                onClick={() => setActiveTab('dashboard')}
              >
                <BarChart3 size={14} />
                Dashboard
              </button>
            </div>

            {activeTab === 'cases' && (
              <div className="results-grid">
                <AnalysisPanel analysis={result.analysis} />
                <TestCasesPanel
                  testCases={result.test_cases}
                  onEdit={(tc) => setEditingCase(tc)}
                />
              </div>
            )}

            {activeTab === 'explain' && (
              <ExplanationPanel explanations={result.explanations} />
            )}

            {activeTab === 'dashboard' && (
              <DashboardPanel
                testCases={result.test_cases}
                explanations={result.explanations}
              />
            )}
          </>
        )}

        {editingCase && (
          <TestCaseEditor
            testCase={editingCase}
            onSave={handleSaveEdit}
            onClose={() => setEditingCase(null)}
          />
        )}
      </main>
    </div>
  );
}
