import * as XLSX from 'xlsx';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export async function analyzeStory(story) {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ story }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Analysis failed');
  }
  return res.json();
}

export async function downloadReport(story, analysis, testCases, explanations, template) {
  const url = template && template !== 'standard'
    ? `${API_BASE}/api/report?template=${encodeURIComponent(template)}`
    : `${API_BASE}/api/report`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      story,
      analysis,
      test_cases: testCases,
      explanations,
    }),
  });
  if (!res.ok) throw new Error('Report generation failed');
  const blob = await res.blob();
  const fname = template && template !== 'standard'
    ? `testcraft_report_${template}.pdf`
    : 'testcraft_report.pdf';
  triggerDownload(blob, fname);
}

export async function downloadScript(story, testCases, framework) {
  const res = await fetch(
    `${API_BASE}/api/export/script?framework=${encodeURIComponent(framework)}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ story, test_cases: testCases }),
    },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Script export failed (${framework})`);
  }
  const blob = await res.blob();
  const cd = res.headers.get('Content-Disposition') || '';
  const m = /filename=([^;]+)/i.exec(cd);
  const filename = m ? m[1].trim() : `testcraft_${framework}`;
  triggerDownload(blob, filename);
}

export async function prioritizeTestCases(story, testCases) {
  const res = await fetch(`${API_BASE}/api/prioritize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ story, test_cases: testCases }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Prioritization failed');
  }
  const data = await res.json();
  return data.test_cases;
}

export function downloadExcel(story, analysis, testCases, explanations) {
  const wb = XLSX.utils.book_new();

  // ── Sheet 1: Test Cases ──────────────────────────────
  const tcRows = testCases.map((tc, idx) => ({
    '#':               idx + 1,
    'ID':              tc.id || '',
    'Title':           tc.title || '',
    'Type':            tc.type || '',
    'Preconditions':   (tc.preconditions || []).join('\n'),
    'Test Steps':      (tc.steps || []).map((s, i) => `${i + 1}. ${s}`).join('\n'),
    'Expected Results':(tc.expected_results || []).join('\n'),
  }));
  const tcSheet = XLSX.utils.json_to_sheet(tcRows);
  // set column widths
  tcSheet['!cols'] = [
    { wch: 4 }, { wch: 10 }, { wch: 40 }, { wch: 12 },
    { wch: 36 }, { wch: 50 }, { wch: 40 },
  ];
  XLSX.utils.book_append_sheet(wb, tcSheet, 'Test Cases');

  // ── Sheet 2: NLP Analysis ────────────────────────────
  const analysisRows = [
    { Component: 'Story Input', Value: story || '' },
    { Component: 'Actor',       Value: analysis?.actor || '' },
    { Component: 'Action',      Value: analysis?.action || '' },
    { Component: 'Outcome',     Value: analysis?.outcome || '' },
    { Component: 'Conditions',  Value: (analysis?.conditions || []).map(c => c.context).join('; ') },
    { Component: 'Key Verbs',   Value: (analysis?.verbs || []).map(v => v.text).join(', ') },
    { Component: 'Key Objects', Value: (analysis?.objects || []).map(o => o.text).join(', ') },
  ];
  const anlSheet = XLSX.utils.json_to_sheet(analysisRows);
  anlSheet['!cols'] = [{ wch: 18 }, { wch: 70 }];
  XLSX.utils.book_append_sheet(wb, anlSheet, 'NLP Analysis');

  // ── Sheet 3: Explanations ────────────────────────────
  if (explanations?.length) {
    const expRows = explanations.map(exp => ({
      'Test Case ID':   exp.test_case_id || '',
      'Title':          exp.test_case_title || '',
      'Confidence':     exp.confidence || '',
      'Reasoning':      (exp.reasoning || []).join('\n'),
      'Story Mapping':  (exp.story_mapping || []).map(sm => `${sm.element}: ${sm.description}`).join('\n'),
    }));
    const expSheet = XLSX.utils.json_to_sheet(expRows);
    expSheet['!cols'] = [{ wch: 12 }, { wch: 40 }, { wch: 12 }, { wch: 60 }, { wch: 50 }];
    XLSX.utils.book_append_sheet(wb, expSheet, 'Explanations');
  }

  // ── Sheet 4: Summary ─────────────────────────────────
  const counts = testCases.reduce((acc, tc) => {
    acc[tc.type] = (acc[tc.type] || 0) + 1;
    return acc;
  }, {});
  const summaryRows = [
    { Metric: 'Total Test Cases', Count: testCases.length },
    { Metric: 'Positive Cases',   Count: counts.positive  || 0 },
    { Metric: 'Negative Cases',   Count: counts.negative  || 0 },
    { Metric: 'Boundary Cases',   Count: counts.boundary  || 0 },
    { Metric: 'Generated On',     Count: new Date().toLocaleString() },
  ];
  const summarySheet = XLSX.utils.json_to_sheet(summaryRows);
  summarySheet['!cols'] = [{ wch: 22 }, { wch: 20 }];
  XLSX.utils.book_append_sheet(wb, summarySheet, 'Summary');

  const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
  const blob = new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  triggerDownload(blob, 'testcraft_test_cases.xlsx');
}

export function downloadTestCaseExcel(tc) {
  const wb = XLSX.utils.book_new();

  // ── Sheet: Test Case Details (label-value layout) ──────
  const rows = [
    { Field: 'Test Case ID',    Value: tc.id || '' },
    { Field: 'Title',           Value: tc.title || '' },
    { Field: 'Type',            Value: (tc.type || '').charAt(0).toUpperCase() + (tc.type || '').slice(1) },
    { Field: '', Value: '' },
    { Field: 'PRECONDITIONS',   Value: '' },
    ...(tc.preconditions || []).map((p, i) => ({ Field: `  ${i + 1}.`, Value: p })),
    { Field: '', Value: '' },
    { Field: 'TEST STEPS',      Value: '' },
    ...(tc.steps || []).map((s, i) => ({ Field: `  Step ${i + 1}`, Value: s })),
    { Field: '', Value: '' },
    { Field: 'EXPECTED RESULTS', Value: '' },
    ...(tc.expected_results || []).map((e, i) => ({ Field: `  ${i + 1}.`, Value: e })),
  ];



  const sheet = XLSX.utils.json_to_sheet(rows, { skipHeader: false });
  sheet['!cols'] = [{ wch: 22 }, { wch: 70 }];
  XLSX.utils.book_append_sheet(wb, sheet, 'Test Case');

  const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
  const blob = new Blob([wbout], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  triggerDownload(blob, `${tc.id || 'test_case'}.xlsx`);
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
