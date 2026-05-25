import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Bell,
  Bolt,
  ChevronDown,
  CircleHelp,
  Database,
  Download,
  Folder,
  History,
  LogOut,
  Plus,
  Search,
  Settings,
  Settings2,
  ShieldCheck,
  TerminalSquare,
  UserCircle,
  Zap,
} from 'lucide-react';
import './styles.css';

const API_BASE_URL = window.location.origin;
const GENERATION_POLL_INTERVAL_MS = 2000;
const GENERATION_POLL_TIMEOUT_MS = 10 * 60 * 1000;

const TEST_TYPES = [
  { label: 'Functional', value: 'functional' },
  { label: 'Negative', value: 'negative' },
  { label: 'Edge Case', value: 'boundary' },
  { label: 'API Layer', value: 'api' },
  { label: 'UI/UX', value: 'ui' },
  { label: 'Regression', value: 'regression' },
];

const INITIAL_RESULT = {
  jira_key: 'SYN-4020',
  status: 'idle',
  summary: { total_cases: 0, jira_score: null, rag_score: null, source: 'mcp', score_mode: 'live_response' },
  test_cases: [],
  traceability_matrix: [],
  coverage_summary: [],
  final_answer: '',
  debug: {},
};

function App() {
  const [query, setQuery] = useState('Generate test cases for SCRUM-5');
  const [selectedTypes, setSelectedTypes] = useState(['functional']);
  const [result, setResult] = useState(INITIAL_RESULT);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedCaseIds, setExpandedCaseIds] = useState([]);
  const [knowledgeDocs, setKnowledgeDocs] = useState([]);
  const [isKnowledgeLoading, setIsKnowledgeLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const visibleCases = result.test_cases || [];
  const statusText = result.status === 'idle' ? 'Awaiting query' : result.status;
  const selectedTypeLabels = useMemo(
    () => TEST_TYPES.filter((type) => selectedTypes.includes(type.value)).map((type) => type.label),
    [selectedTypes],
  );
  const activeRagDocs = knowledgeDocs.length;
  const traceabilityCards = useMemo(
    () => deriveTraceability(result.traceability_matrix || [], visibleCases),
    [result.traceability_matrix, visibleCases],
  );
  const coverageCards = useMemo(
    () => deriveCoverageSummary(result.coverage_summary || [], visibleCases, selectedTypeLabels),
    [result.coverage_summary, visibleCases, selectedTypeLabels],
  );

  useEffect(() => {
    refreshKnowledgeDocs();
  }, []);

  async function refreshKnowledgeDocs() {
    setIsKnowledgeLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/documents`);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Unable to load knowledge documents.');
      setKnowledgeDocs(payload.documents || []);
    } catch (docsError) {
      setError(docsError.message);
    } finally {
      setIsKnowledgeLoading(false);
    }
  }

  async function uploadKnowledgeDocs(files) {
    if (!files.length) return;
    const form = new FormData();
    Array.from(files).forEach((file) => form.append('files', file));

    setIsUploading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/documents`, {
        method: 'POST',
        body: form,
      });
      const payload = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(payload.detail) ? payload.detail.map((item) => item.error).join(', ') : payload.detail;
        throw new Error(detail || 'Document upload failed.');
      }
      await refreshKnowledgeDocs();
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setIsUploading(false);
    }
  }

  async function deleteKnowledgeDoc(documentId) {
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/documents/${documentId}`, {
        method: 'DELETE',
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || 'Document delete failed.');
      await refreshKnowledgeDocs();
    } catch (deleteError) {
      setError(deleteError.message);
    }
  }

  async function generate() {
    const trimmed = query.trim();
    if (!trimmed) {
      setError('Enter a JIRA ID or test request.');
      return;
    }
    if (!selectedTypes.length) {
      setError('Select at least one specialist agent.');
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed, test_types: selectedTypes }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Generation failed.');
      }

      const completedResult = await pollGenerationJob(payload.job_id);
      setResult(completedResult);
      setExpandedCaseIds([]);
    } catch (generationError) {
      setError(generationError.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function pollGenerationJob(jobId) {
    if (!jobId) throw new Error('Generation job was not created.');

    const startedAt = Date.now();
    while (Date.now() - startedAt < GENERATION_POLL_TIMEOUT_MS) {
      await wait(GENERATION_POLL_INTERVAL_MS);

      const response = await fetch(`${API_BASE_URL}/api/generate/jobs/${jobId}`);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Unable to check generation status.');
      }

      if (payload.status === 'completed') {
        return payload.result;
      }
      if (payload.status === 'failed') {
        throw new Error(payload.error || 'Generation failed.');
      }
    }

    throw new Error('Generation is still running. Please try again in a few minutes.');
  }

  async function exportExcel() {
    if (!visibleCases.length) {
      setError('Generate test cases before exporting.');
      return;
    }

    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/export/excel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result),
      });
      if (!response.ok) {
        throw new Error('Excel export failed.');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `apextest-${result.jira_key || 'test-pack'}.xlsx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (exportError) {
      setError(exportError.message);
    }
  }

  function toggleType(value) {
    setSelectedTypes((current) =>
      current.includes(value) ? current.filter((item) => item !== value) : [...current, value],
    );
  }

  function toggleCase(caseKey) {
    setExpandedCaseIds((current) =>
      current.includes(caseKey) ? current.filter((item) => item !== caseKey) : [...current, caseKey],
    );
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="workspace">
        <Topbar />

        <section className="hero-section">
          <div className="aurora" />
          <div className="hero-copy">
            <p className="eyebrow">ApexTest DeepTech Engine</p>
            <h1>Build Test Coverage</h1>
            <p>
              Enter a JIRA ID or focused test request to generate comprehensive, traceable QA coverage
              powered by your LangGraph agents.
            </p>
          </div>

          <div className={`prompt-panel ${isLoading ? 'is-loading' : ''}`}>
            <Search aria-hidden="true" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') generate();
              }}
              placeholder="e.g. SCRUM-5 or Test login with MFA"
            />
            <button type="button" className="primary-action" onClick={generate} disabled={isLoading}>
              <Bolt size={20} />
              {isLoading ? 'Generating' : 'Generate'}
            </button>
          </div>

          <div className="chips" aria-label="Specialist test type filters">
            {TEST_TYPES.map((type) => (
              <button
                key={type.value}
                type="button"
                className={selectedTypes.includes(type.value) ? 'chip active' : 'chip'}
                onClick={() => toggleType(type.value)}
              >
                {type.label}
              </button>
            ))}
          </div>

          {error ? <div className="alert">{error}</div> : null}
        </section>

        <section className="metrics-strip">
          <Metric label="Status" value={statusText} />
          <Metric label="Cases" value={String(result.summary?.total_cases || visibleCases.length)} />
          <Metric label="JIRA Score" value={formatScore(result.summary?.jira_score, result.status)} />
          <Metric label="RAG Score" value={formatScore(result.summary?.rag_score, result.status)} />
          <Metric label="RAG Docs" value={`${activeRagDocs} active`} />
        </section>

        <KnowledgeBasePanel
          documents={knowledgeDocs}
          isLoading={isKnowledgeLoading}
          isUploading={isUploading}
          onUpload={uploadKnowledgeDocs}
          onDelete={deleteKnowledgeDoc}
        />

        <section className="results-header">
          <div>
            <h2>Generated Test Cases</h2>
            <p>
              {visibleCases.length
                ? `${visibleCases.length} cases found for ${result.jira_key || 'selected request'}`
                : 'No cases generated yet'}
            </p>
          </div>
          <button type="button" className="ghost-action" onClick={exportExcel} disabled={!visibleCases.length}>
            <Download size={18} />
            Export to Excel
          </button>
        </section>

        <GuardrailPanel result={result} />

        <InsightCards traceability={traceabilityCards} coverage={coverageCards} />

        <QualityGatePanel qualityGate={result.quality_gate} status={result.status} />

        <Results
          cases={visibleCases}
          isLoading={isLoading}
          expandedCaseIds={expandedCaseIds}
          onToggleCase={toggleCase}
        />
      </main>
      <button type="button" className="fab" aria-label="New manual case">
        <Plus />
      </button>
    </div>
  );
}

function GuardrailPanel({ result }) {
  if (!['blocked', 'error'].includes(result.status)) return null;

  const reason =
    result.debug?.output_rejection_reason ||
    result.debug?.errors?.join(', ') ||
    result.final_answer ||
    'ApexTest could not process this request because a guardrail or evaluation check failed.';

  return (
    <section className="guardrail-panel">
      <span>{result.status === 'blocked' ? 'Guardrail Blocked Request' : 'Processing Error'}</span>
      <h2>Request Cannot Be Processed</h2>
      <p>{reason}</p>
    </section>
  );
}

function KnowledgeBasePanel({ documents, isLoading, isUploading, onUpload, onDelete }) {
  return (
    <section className="knowledge-panel">
      <div className="knowledge-header">
        <div>
          <span>Configurable RAG Knowledge Base</span>
          <h2>Project Documents</h2>
        </div>
        <label className="upload-action">
          {isUploading ? 'Ingesting...' : 'Upload Documents'}
          <input
            type="file"
            multiple
            accept=".txt,.md,.docx,.pdf"
            onChange={(event) => {
              onUpload(event.target.files || []);
              event.target.value = '';
            }}
          />
        </label>
      </div>

      <div className="document-list">
        {isLoading ? (
          <p className="muted-copy">Loading documents...</p>
        ) : documents.length ? (
          documents.map((document) => (
            <div className="document-row" key={document.document_id}>
              <div>
                <strong>{document.filename}</strong>
                <span>{document.chunk_count} chunks ingested</span>
              </div>
              <button type="button" onClick={() => onDelete(document.document_id)}>
                Delete
              </button>
            </div>
          ))
        ) : (
          <p className="muted-copy">
            Upload BRDs, requirement notes, test standards, or product docs. ApexTest will ground generation in
            those documents.
          </p>
        )}
      </div>
    </section>
  );
}

function Sidebar() {
  const nav = [
    { label: 'Command Center', icon: TerminalSquare, active: true },
    { label: 'History', icon: History },
    { label: 'Test Suites', icon: Folder },
    { label: 'Settings', icon: Settings2 },
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <TerminalSquare size={22} />
        </div>
        <div>
          <strong>ApexTest</strong>
          <span>DeepTech Engine</span>
        </div>
      </div>

      <nav className="side-nav">
        {nav.map((item) => {
          const Icon = item.icon;
          return (
            <button key={item.label} type="button" className={item.active ? 'nav-item active' : 'nav-item'}>
              <Icon size={22} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="agent-card">
        <div className="agent-orb">
          <ShieldCheck size={18} />
        </div>
        <div>
          <strong>Swapnil Jadhav</strong>
          <span>Lead Agentic AI Engineer</span>
        </div>
      </div>

      <div className="account-links">
        <button type="button">
          <UserCircle size={22} />
          Account
        </button>
        <button type="button">
          <LogOut size={22} />
          Logout
        </button>
      </div>
    </aside>
  );
}

function Topbar() {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <h2>Command Center</h2>
        <nav>
          <a href="#dashboard" className="active">
            Dashboard
          </a>
          <a href="#automation">Automation</a>
          <a href="#reports">Reports</a>
        </nav>
      </div>
      <div className="topbar-actions">
        <span className="node-pill">
          <Database size={18} />
          NODE_01_SYNTH
        </span>
        <button type="button" aria-label="Notifications">
          <Bell />
        </button>
        <button type="button" aria-label="Settings">
          <Settings />
        </button>
        <button type="button" aria-label="Help">
          <CircleHelp />
        </button>
      </div>
    </header>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Results({ cases, isLoading, expandedCaseIds, onToggleCase }) {
  if (isLoading) {
    return (
      <section className="empty-state scanning">
        <Zap />
        <h2>Specialist agents are synthesizing coverage</h2>
        <p>Fetching JIRA, grounding with RAG, and assembling executable QA scenarios.</p>
      </section>
    );
  }

  if (!cases.length) {
    return (
      <section className="empty-state">
        <TerminalSquare />
        <h2>Ready for analysis</h2>
        <p>Choose specialist agents, enter a JIRA request, and generate the first test pack.</p>
      </section>
    );
  }

  return (
    <section className="case-list">
      <div className="table-head">
        <span>ID</span>
        <span>JIRA Ref</span>
        <span>Description</span>
        <span>Type</span>
        <span>Status</span>
      </div>
      {cases.map((testCase, index) => {
        const caseKey = `${testCase.id || 'case'}-${index}`;
        const isExpanded = expandedCaseIds.includes(caseKey);
        return (
        <article
          key={caseKey}
          className={isExpanded ? 'case-card expanded' : 'case-card'}
          onClick={() => onToggleCase(caseKey)}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              onToggleCase(caseKey);
            }
          }}
        >
          <div className="case-id">{testCase.id || `TC-${index + 1}`}</div>
          <div className="case-ref">{testCase.jira_ref || 'REQ'}</div>
          <div className="case-main">
            <h3>
              {testCase.title}
              <ChevronDown className={isExpanded ? 'chevron open' : 'chevron'} size={20} />
            </h3>
            {isExpanded ? (
              <div className="steps-box">
                <span>Test Steps</span>
                {(testCase.steps || []).slice(0, 5).map((step, stepIndex) => (
                  <p key={`${testCase.id}-step-${stepIndex}`}>
                    <b>{String(stepIndex + 1).padStart(2, '0')}</b>
                    {step}
                  </p>
                ))}
                {testCase.expected_result ? <em>{testCase.expected_result}</em> : null}
              </div>
            ) : null}
          </div>
          <div className="case-type">{formatType(testCase.type)}</div>
          <div className="case-status">
            <span />
            Ready
          </div>
        </article>
        );
      })}
    </section>
  );
}

function InsightCards({ traceability, coverage }) {
  return (
    <section className="insight-grid">
      <article className="insight-card">
        <div>
          <span>Traceability Matrix</span>
          <h2>Requirement Coverage</h2>
        </div>
        {traceability.length ? (
          <div className="traceability-list">
            {traceability.map((row, index) => (
              <div key={`${row.acceptance_criteria}-${index}`} className="trace-row">
                <strong>{row.acceptance_criteria}</strong>
                <p>{row.test_case_ids || 'No mapped cases'}</p>
                <em>{row.coverage_status || 'Coverage pending'}</em>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted-copy">Traceability details will appear after generation.</p>
        )}
      </article>

      <article className="insight-card">
        <div>
          <span>Coverage Summary</span>
          <h2>Execution Readiness</h2>
        </div>
        {coverage.length ? (
          <ul className="coverage-list">
            {coverage.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="muted-copy">Coverage summary will appear after generation.</p>
        )}
      </article>
    </section>
  );
}

function QualityGatePanel({ qualityGate, status }) {
  if (status !== 'needs_clarification') return null;

  return (
    <section className="quality-gate-panel">
      <div>
        <span>Requirement Quality Gate Agent</span>
        <h2>Clarification Required Before Test Generation</h2>
        <p>{qualityGate?.reason || 'The JIRA story is missing details needed for accurate test cases.'}</p>
      </div>

      <div className="quality-grid">
        <div>
          <h3>Identified Gaps</h3>
          <ul>
            {(qualityGate?.gaps?.length ? qualityGate.gaps : ['Missing requirement details.']).map((gap, index) => (
              <li key={`${gap}-${index}`}>{gap}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Questions for PO/BA</h3>
          <ul>
            {(qualityGate?.clarifying_questions?.length
              ? qualityGate.clarifying_questions
              : ['Can the PO/BA provide complete acceptance criteria and business rules?']
            ).map((question, index) => (
              <li key={`${question}-${index}`}>{question}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

function formatScore(value, status) {
  if (status === 'idle') return 'Run to score';
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : 'Pending';
}

function formatType(value) {
  if (!value) return 'General';
  return value.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function wait(milliseconds) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });
}

function deriveTraceability(traceability, cases) {
  if (traceability.length) return traceability;

  const byCriteria = new Map();
  cases.forEach((testCase) => {
    const criteria = testCase.mapped_acceptance_criteria?.length
      ? testCase.mapped_acceptance_criteria
      : ['Generated requirement coverage'];

    criteria.forEach((criterion) => {
      const key = criterion || 'Generated requirement coverage';
      const current = byCriteria.get(key) || { ids: new Set(), types: new Set() };
      current.ids.add(testCase.id || 'Unassigned');
      current.types.add(formatType(testCase.type));
      byCriteria.set(key, current);
    });
  });

  return Array.from(byCriteria.entries()).map(([criterion, value]) => ({
    acceptance_criteria: criterion,
    test_case_ids: Array.from(value.ids).join(', '),
    test_types: Array.from(value.types).join(', '),
    coverage_status: 'Covered',
  }));
}

function deriveCoverageSummary(coverage, cases, selectedTypeLabels) {
  if (coverage.length) return coverage;
  if (!cases.length) return [];

  const types = new Set(cases.map((testCase) => formatType(testCase.type)));
  const criteria = new Set();
  cases.forEach((testCase) => {
    (testCase.mapped_acceptance_criteria || []).forEach((criterion) => criteria.add(criterion));
  });

  return [
    `Requested agents: ${selectedTypeLabels.join(', ') || 'Selected specialists'}`,
    `Generated cases: ${cases.length}`,
    `Generated test types: ${Array.from(types).join(', ') || 'General'}`,
    `Acceptance criteria mapped: ${criteria.size || 'Not explicitly provided by source story'}`,
  ];
}

createRoot(document.getElementById('root')).render(<App />);
