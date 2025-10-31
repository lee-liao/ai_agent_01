"use client";

import { useEffect, useMemo, useState } from "react";
import {
  RotateCcw,
  Play,
  Edit,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Users,
  FileText,
  Search,
  Zap,
  Settings,
  Loader2,
} from "lucide-react";

import { api } from "../../lib/api";

type GenericRecord = Record<string, any>;

const agentPaths = [
  {
    value: "manager_worker",
    label: "Manager–Worker",
    description: "Task decomposition with parallel workers for clause parsing and risk tagging",
    icon: Users,
    color: "bg-blue-500",
  },
  {
    value: "planner_executor",
    label: "Planner–Executor",
    description: "Multi-step sequential plan with replayable state and checkpoints",
    icon: CheckCircle,
    color: "bg-green-500",
  },
  {
    value: "reviewer_referee",
    label: "Reviewer/Referee",
    description: "Checklist-driven review with referee arbitration for contested clauses",
    icon: AlertTriangle,
    color: "bg-orange-500",
  },
];

interface PlaybookSummary {
  playbook_id: string;
  name: string;
}

interface RiskCounts {
  high: number;
  medium: number;
  low: number;
}

interface ClauseSnapshot {
  text?: string;
  risk_level?: string | null;
  rationale?: string | null;
  policy_refs?: string[] | null;
}

interface ClauseComparison {
  clause_id: string;
  heading?: string;
  original?: ClauseSnapshot;
  replay?: ClauseSnapshot;
  delta?: {
    risk_level_change?: "up" | "down" | null;
    risk_level_delta?: number;
    text_changed?: boolean;
    risk_changed?: boolean;
    present_in_original?: boolean;
    present_in_replay?: boolean;
  };
}

interface ReplayMetrics {
  run_id: string;
  doc_id?: string;
  agent_path?: string;
  playbook_id?: string;
  score?: number;
  duration_seconds?: number;
  assessments?: GenericRecord[];
  clauses?: GenericRecord[];
  proposals?: GenericRecord[];
  decisions?: GenericRecord[];
  artifacts?: GenericRecord;
  history?: GenericRecord[];
  started_at?: string;
  completed_at?: string;
  risk_counts?: RiskCounts;
  costs?: Record<string, number>;
}

interface RunSummary {
  run_id: string;
  doc_id?: string;
  doc_name?: string;
  agent_path?: string;
  playbook_id?: string;
  status?: string;
  score?: number;
  created_at?: string;
  updated_at?: string;
  history?: GenericRecord[];
  assessments?: GenericRecord[];
  proposals?: GenericRecord[];
}

interface HistoryStep {
  step_id: string;
  step_name: string;
  agent: string;
  status: string;
  input: string;
  output: string;
  duration_ms?: number;
  timestamp?: string;
  clause_id?: string;
  metadata: GenericRecord;
}

interface ReplayResult {
  run_id: string;
  workflow_result?: any;
  replay: ReplayMetrics;
  comparison: {
    score?: { original?: number | null; replay?: number | null; delta?: number | null };
    duration_seconds?: { original?: number | null; replay?: number | null; delta?: number | null };
    risk_counts?: { original: RiskCounts; replay: RiskCounts; delta: RiskCounts };
    costs?: {
      original: Record<string, number>;
      replay: Record<string, number>;
      delta: Record<string, number>;
    };
    clauses?: ClauseComparison[];
  };
  score?: number;
  costs?: Record<string, number>;
  clause_comparisons?: ClauseComparison[];
}

interface ClauseReplayResult {
  run_id: string;
  clause_id: string;
  prompt?: string;
  duration_seconds?: number;
  assessment: {
    clause_id: string;
    risk_level: string;
    rationale?: string;
    policy_refs?: string[];
  };
  comparison: {
    risk_level: { original?: string | null; replay?: string | null };
    cost: { original?: number | null; replay?: number | null; delta?: number | null };
    duration_seconds: { original?: number | null; replay?: number | null; delta?: number | null };
  };
  original_assessment?: GenericRecord | null;
  policy_rules?: GenericRecord | null;
}

const formatTime = (iso?: string) => {
  if (!iso) return "--";
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const formatDuration = (ms?: number) => {
  if (!ms && ms !== 0) return "--";
  return `${Math.round(ms)} ms`;
};

const getStatusIcon = (status: string) => {
  const normalized = (status || "").toLowerCase();
  if (normalized.includes("success") || normalized.includes("complete")) {
    return <CheckCircle className="w-5 h-5 text-green-600" />;
  }
  if (normalized.includes("fail") || normalized.includes("error")) {
    return <XCircle className="w-5 h-5 text-red-600" />;
  }
  return <Clock className="w-5 h-5 text-blue-600" />;
};

const countRiskLevels = (assessments: GenericRecord[] | undefined) => {
  const items = assessments || [];
  return {
    high: items.filter((a) => (a.risk_level || "").toUpperCase() === "HIGH").length,
    medium: items.filter((a) => (a.risk_level || "").toUpperCase() === "MEDIUM").length,
    low: items.filter((a) => (a.risk_level || "").toUpperCase() === "LOW").length,
  };
};

const buildHistorySteps = (history: GenericRecord[] | undefined) => {
  if (!history) return [] as HistoryStep[];
  const toDisplay = (value: any) => {
    if (value === null || value === undefined) return "";
    if (typeof value === "string") return value;
    if (typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }
    try {
      return JSON.stringify(value, null, 2);
    } catch (error) {
      console.error("Failed to stringify history value", error, value);
      return String(value);
    }
  };
  const pickFirst = (...candidates: any[]) => {
    for (const candidate of candidates) {
      if (candidate === undefined || candidate === null) {
        continue;
      }
      if (typeof candidate === "string" && candidate.trim() === "") {
        continue;
      }
      return candidate;
    }
    return "";
  };
  return history.map((entry, index) => ({
    step_id: entry.step_id || entry.id || `step_${index + 1}`,
    step_name: entry.step_name || entry.step || `Step ${index + 1}`,
    agent: entry.agent || entry.team || entry.agent_name || "unknown",
    status: entry.status || entry.result || "unknown",
    clause_id: entry.clause_id || entry.metadata?.clause_id,
    input: toDisplay(
      pickFirst(
        entry.input,
        entry.prompt,
        entry.context,
        entry.task,
        entry.request,
        entry.payload,
        entry.details?.input,
        entry.metadata?.input
      )
    ),
    output: toDisplay(
      pickFirst(
        entry.output,
        entry.response,
        entry.result,
        entry.details,
        entry.review_result,
        entry.arbitration_result,
        entry.error
      )
    ),
    duration_ms: entry.duration_ms || entry.elapsed_ms,
    timestamp: entry.timestamp,
    metadata: entry.metadata || {},
  }));
};

const ensureRiskCounts = (counts?: RiskCounts | null): RiskCounts => {
  if (!counts) {
    return { high: 0, medium: 0, low: 0 };
  }
  return {
    high: counts.high ?? 0,
    medium: counts.medium ?? 0,
    low: counts.low ?? 0,
  };
};

const formatSeconds = (seconds?: number | null) => {
  if (seconds === undefined || seconds === null) return "--";
  if (!Number.isFinite(seconds)) return "--";
  if (seconds < 1) {
    return `${(seconds * 1000).toFixed(0)} ms`;
  }
  return `${seconds.toFixed(2)} s`;
};

const formatRiskLevel = (risk?: string | null) => {
  if (!risk) return "--";
  const normalized = risk.toUpperCase();
  return normalized.charAt(0) + normalized.slice(1).toLowerCase();
};

const formatCost = (value?: number | null) => {
  if (value === undefined || value === null || Number.isNaN(value)) return "--";
  return `$${value.toFixed(4)}`;
};

const ReplayPage = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [runsError, setRunsError] = useState<string | null>(null);

  const [playbooks, setPlaybooks] = useState<PlaybookSummary[]>([]);
  const [playbooksLoading, setPlaybooksLoading] = useState(false);
  const [playbooksError, setPlaybooksError] = useState<string | null>(null);

  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [agentPathOverride, setAgentPathOverride] = useState<string>("manager_worker");
  const [playbookOverride, setPlaybookOverride] = useState<string>("");

  const [editingStep, setEditingStep] = useState<string | null>(null);
  const [modifiedInput, setModifiedInput] = useState<string>("");

  const [runReplayResult, setRunReplayResult] = useState<ReplayResult | null>(null);
  const [runReplayLoading, setRunReplayLoading] = useState(false);
  const [runReplayError, setRunReplayError] = useState<string | null>(null);

  const [clauseReplayResults, setClauseReplayResults] = useState<Record<string, ClauseReplayResult>>({});
  const [clauseReplayLoading, setClauseReplayLoading] = useState<string | null>(null);
  const [clauseReplayErrors, setClauseReplayErrors] = useState<Record<string, string>>({});

  const [selectedRunDetail, setSelectedRunDetail] = useState<RunSummary | null>(null);
  const [selectedRunDetailLoading, setSelectedRunDetailLoading] = useState(false);
  const [selectedRunDetailError, setSelectedRunDetailError] = useState<string | null>(null);

  useEffect(() => {
    const loadRuns = async () => {
      setRunsLoading(true);
      setRunsError(null);
      try {
        const data = await api.listRuns();
        setRuns(data);
      } catch (error) {
        console.error("Failed to load runs", error);
        setRunsError("Unable to load runs. Please try again.");
      } finally {
        setRunsLoading(false);
      }
    };

    loadRuns();
  }, []);

  useEffect(() => {
    const loadPlaybooks = async () => {
      setPlaybooksLoading(true);
      setPlaybooksError(null);
      try {
        const data = await api.listPlaybooks();
        setPlaybooks(data);
      } catch (error) {
        console.error("Failed to load playbooks", error);
        setPlaybooksError("Unable to load playbooks.");
      } finally {
        setPlaybooksLoading(false);
      }
    };

    loadPlaybooks();
  }, []);

  const selectedRunSummary = useMemo(
    () => runs.find((run) => run.run_id === selectedRunId) || null,
    [runs, selectedRunId]
  );

  const selectedRun = selectedRunDetail ?? selectedRunSummary ?? null;

  const historySteps = useMemo(
    () => buildHistorySteps(selectedRun?.history),
    [selectedRun]
  );

  const riskCounts = useMemo(
    () => countRiskLevels(selectedRun?.assessments),
    [selectedRun]
  );

  useEffect(() => {
    if (!selectedRunId) {
      setSelectedRunDetail(null);
      setSelectedRunDetailError(null);
      setSelectedRunDetailLoading(false);
      setAgentPathOverride("manager_worker");
      setPlaybookOverride("");
      setRunReplayResult(null);
      setRunReplayError(null);
      setClauseReplayResults({});
      setClauseReplayErrors({});
      setEditingStep(null);
      setModifiedInput("");
      return;
    }

    let cancelled = false;
    setSelectedRunDetailLoading(true);
    setSelectedRunDetailError(null);

    api.getRun(selectedRunId)
      .then((data) => {
        if (cancelled) return;
        setSelectedRunDetail(data);
        setAgentPathOverride(data.agent_path || "manager_worker");
        setPlaybookOverride(data.playbook_id || "");
        setRunReplayResult(null);
        setRunReplayError(null);
        setClauseReplayResults({});
        setClauseReplayErrors({});
        setEditingStep(null);
        setModifiedInput("");
      })
      .catch((error) => {
        if (cancelled) return;
        console.error("Failed to load run details", error);
        setSelectedRunDetail(null);
        setSelectedRunDetailError("Unable to load run details.");
      })
      .finally(() => {
        if (!cancelled) {
          setSelectedRunDetailLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedRunId]);

  const runComparison = runReplayResult?.comparison;
  const replayMetrics = runReplayResult?.replay;

  const formatScoreValue = (value: number | null | undefined) => {
    if (value === null || value === undefined) {
      return "--";
    }
    return `${Math.round(value)} / 100`;
  };

  const describeRiskCounts = (countsInput: RiskCounts) =>
    `${countsInput.high} High / ${countsInput.medium} Medium / ${countsInput.low} Low`;
  const originalRiskCounts = useMemo(
    () =>
      ensureRiskCounts(
        (runComparison?.risk_counts?.original as RiskCounts | undefined) || riskCounts
      ),
    [riskCounts, runComparison]
  );

  const replayRiskCounts = useMemo(
    () =>
      ensureRiskCounts(
        (runComparison?.risk_counts?.replay as RiskCounts | undefined) || replayMetrics?.risk_counts
      ),
    [runComparison, replayMetrics]
  );

  const replayProposals = (runReplayResult?.replay?.proposals as GenericRecord[] | undefined) || [];

  const originalScore = runComparison?.score?.original ?? selectedRun?.score ?? null;
  const replayScore = runComparison?.score?.replay ?? runReplayResult?.score ?? replayMetrics?.score ?? null;

  const originalDuration = runComparison?.duration_seconds?.original ?? null;
  const replayDuration = runComparison?.duration_seconds?.replay ?? replayMetrics?.duration_seconds ?? null;

  const totalOriginalCost = useMemo(() => {
    const base = runComparison?.costs?.original;
    if (!base) return undefined;
    return base.total_cost ?? base.total_cost_usd ?? undefined;
  }, [runComparison]);

  const totalReplayCost = useMemo(() => {
    const base = runReplayResult?.costs ?? replayMetrics?.costs;
    if (!base) return undefined;
    return base.total_cost ?? base.total_cost_usd ?? undefined;
  }, [replayMetrics, runReplayResult]);

  const handleLoadTrace = (runId: string) => {
    setSelectedRunDetail(null);
    setSelectedRunId(runId);
  };

  const handleEditStep = (
    stepId: string,
    clauseId: string | undefined,
    currentInput: string
  ) => {
    if (!clauseId || !currentInput || currentInput.trim().length === 0) {
      return;
    }
    setEditingStep(stepId);
    setModifiedInput(currentInput);
    setClauseReplayErrors((prev) => ({ ...prev, [clauseId]: "" }));
  };

  const handleCancelEdit = () => {
    setEditingStep(null);
    setModifiedInput("");
  };

  const handleRunReplay = async () => {
    if (!selectedRunId) return;

    setRunReplayLoading(true);
    setRunReplayError(null);
    try {
      const payload = {
        agent_path: agentPathOverride,
        playbook_id: playbookOverride === "" ? null : playbookOverride,
      };
      const response = await api.replayRun(selectedRunId, payload);
      setRunReplayResult(response);
    } catch (error) {
      console.error("Run-level replay failed", error);
      setRunReplayError("Run-level replay failed. Please try again.");
    } finally {
      setRunReplayLoading(false);
    }
  };

  const handleClauseReplay = async (clauseId: string | undefined, promptText: string) => {
    if (!selectedRunId || !clauseId) return;

    setClauseReplayLoading(clauseId);
    setClauseReplayErrors((prev) => {
      const next = { ...prev };
      delete next[clauseId];
      return next;
    });

    try {
      const response = await api.replayClause(selectedRunId, clauseId, {
        prompt: promptText || undefined,
      });
      setClauseReplayResults((prev) => ({ ...prev, [clauseId]: response }));
      setEditingStep(null);
      setModifiedInput("");
    } catch (error) {
      console.error("Clause replay failed", error);
      setClauseReplayErrors((prev) => ({
        ...prev,
        [clauseId]: "Clause replay failed. Please try again.",
      }));
    } finally {
      setClauseReplayLoading(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Replay & Debug</h1>
        <p className="text-gray-600">
          Replay previous runs, modify LLM prompts, and compare outcomes side-by-side.
        </p>
      </div>

      <div className="card mb-8">
        <div className="flex items-center mb-6">
          <Search className="w-6 h-6 text-primary-600 mr-3" />
          <h2 className="text-xl font-semibold text-gray-900">Select Run to Replay</h2>
        </div>

        {runsError && (
          <div className="mb-4 border border-red-200 bg-red-50 text-red-700 px-4 py-3 rounded">
            {runsError}
          </div>
        )}

        <div className="grid grid-cols-1 gap-3">
          {runsLoading ? (
            <div className="p-4 border-2 border-dashed border-gray-200 rounded-lg text-gray-500 text-sm flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Loading runs…</span>
            </div>
          ) : runs.length === 0 ? (
            <div className="p-6 border-2 border-gray-200 rounded-lg text-gray-500 text-sm text-center">
              No runs available. Execute a review to populate history.
            </div>
          ) : (
            runs.map((run) => (
              <button
                key={run.run_id}
                onClick={() => handleLoadTrace(run.run_id)}
                className={`flex items-center justify-between p-4 border-2 rounded-lg text-left transition-all ${
                  selectedRunId === run.run_id
                    ? "border-primary-500 bg-primary-50"
                    : "border-gray-200 hover:border-primary-300 hover:bg-gray-50"
                }`}
              >
                <div className="flex items-center space-x-4 flex-1">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      (run.status || "")
                        .toLowerCase()
                        .includes("complete")
                        ? "bg-green-500"
                        : (run.status || "")
                            .toLowerCase()
                            .includes("fail")
                        ? "bg-red-500"
                        : "bg-orange-500"
                    }`}
                  ></div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{run.doc_name || run.doc_id || "Untitled"}</p>
                    <p className="text-xs text-gray-500 font-mono mt-1">{run.run_id}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6 text-sm">
                  <div className="text-center">
                    <p className="text-gray-600 text-xs">Agent</p>
                    <p className="font-medium text-gray-900">
                      {(run.agent_path || "-").replace("_", "-")}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-600 text-xs">Score</p>
                    <p className="font-semibold text-gray-900">
                      {run.score !== undefined ? `${Math.round(run.score)}/100` : "--"}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-600 text-xs">Steps</p>
                    <p className="font-medium text-gray-900">{run.history ? run.history.length : "--"}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-600 text-xs">Started</p>
                    <p className="text-gray-700" suppressHydrationWarning>
                      {formatTime(run.created_at)}
                    </p>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {selectedRun ? (
        <>
          {selectedRunDetailError && (
            <div className="mb-4 border border-red-200 bg-red-50 text-red-700 px-3 py-2 rounded text-sm">
              {selectedRunDetailError}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Total Steps</p>
                <Zap className="w-5 h-5 text-blue-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">{historySteps.length}</p>
              <p className="text-sm text-green-600 mt-1">Trace entries recorded</p>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Document</p>
                <FileText className="w-5 h-5 text-purple-600" />
              </div>
              <p className="text-lg font-semibold text-gray-900 truncate">
                {selectedRun.doc_name || selectedRun.doc_id || "Unknown"}
              </p>
              <p className="text-sm text-gray-600 mt-1">Run ID: {selectedRun.run_id}</p>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Agent Path</p>
                <Users className="w-5 h-5 text-indigo-600" />
              </div>
              <p className="text-lg font-semibold text-gray-900">
                {(selectedRun.agent_path || "-").replace("_", "-")}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                Status: {(selectedRun.status || "unknown").toUpperCase()}
              </p>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Risk Clauses</p>
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div className="flex items-center space-x-2 mt-2">
                <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">
                  {riskCounts.high} High
                </span>
                <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-semibold rounded">
                  {riskCounts.medium} Med
                </span>
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                  {riskCounts.low} Low
                </span>
              </div>
            </div>
          </div>

          <div className="card mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <RotateCcw className="w-6 h-6 text-primary-600 mr-3" />
                <h2 className="text-xl font-semibold text-gray-900">Run-Level Replay Configuration</h2>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2">Agent Path</p>
                <div className="grid grid-cols-1 gap-3">
                  {agentPaths.map((path) => {
                    const Icon = path.icon;
                    return (
                      <label
                        key={path.value}
                        className={`flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          agentPathOverride === path.value
                            ? "border-primary-500 bg-primary-50"
                            : "border-gray-200 hover:border-primary-300 hover:bg-gray-50"
                        }`}
                      >
                        <input
                          type="radio"
                          name="agentPathOverride"
                          value={path.value}
                          checked={agentPathOverride === path.value}
                          onChange={(e) => setAgentPathOverride(e.target.value)}
                          className="mt-1 mr-3"
                        />
                        <div className={`${path.color} p-2 rounded-lg mr-3`}>
                          <Icon className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-gray-900">{path.label}</p>
                          <p className="text-sm text-gray-600 mt-1">{path.description}</p>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2">Playbook (Optional)</p>
                {playbooksError && (
                  <div className="mb-3 border border-red-200 bg-red-50 text-red-700 px-3 py-2 rounded text-sm">
                    {playbooksError}
                  </div>
                )}
                <select
                  value={playbookOverride}
                  onChange={(e) => setPlaybookOverride(e.target.value)}
                  className="input w-full"
                  disabled={playbooksLoading}
                >
                  <option value="">No Playbook</option>
                  {playbooks.map((playbook) => (
                    <option key={playbook.playbook_id} value={playbook.playbook_id}>
                      {playbook.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-2">
                  Document selection stays fixed to the original run. Adjust agent path or playbook to
                  debug alternate strategies.
                </p>
              </div>
            </div>

            {runReplayError && (
              <div className="mt-4 border border-red-200 bg-red-50 text-red-700 px-4 py-3 rounded">
                {runReplayError}
              </div>
            )}

            <div className="mt-6 flex justify-end">
              <button
                onClick={handleRunReplay}
                className="btn-primary flex items-center"
                disabled={runReplayLoading}
              >
                {runReplayLoading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Play className="w-4 h-4 mr-2" />
                )}
                {runReplayLoading ? "Replaying..." : "Replay Run"}
              </button>
            </div>
          </div>

          {runReplayResult && (
            <div className="card bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200 mb-8">
              <div className="flex items-center mb-4">
                <CheckCircle className="w-6 h-6 text-green-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">Run-Level Comparison</h3>
              </div>
              <p className="text-gray-700 mb-4">
                Compared replayed outcomes against original run
                <code className="bg-white px-2 py-1 rounded font-mono text-sm ml-2">{selectedRunId}</code>
              </p>

              <div className="overflow-x-auto">
                <table className="w-full border border-gray-200 text-sm">
                  <thead className="bg-gray-100 text-gray-600 uppercase text-xs">
                    <tr>
                      <th className="px-4 py-2 text-left">Metric</th>
                      <th className="px-4 py-2 text-left">Original</th>
                      <th className="px-4 py-2 text-left">Replay</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    <tr>
                      <td className="px-4 py-3 font-semibold text-gray-700">Score</td>
                      <td className="px-4 py-3 text-gray-900">{formatScoreValue(originalScore)}</td>
                      <td className="px-4 py-3 text-green-700 font-semibold">{formatScoreValue(replayScore)}</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 font-semibold text-gray-700">Total Duration</td>
                      <td className="px-4 py-3 text-gray-900">{formatSeconds(originalDuration)}</td>
                      <td className="px-4 py-3 text-green-700 font-semibold">{formatSeconds(replayDuration)}</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 font-semibold text-gray-700">Risk Counts</td>
                      <td className="px-4 py-3 text-gray-900">{describeRiskCounts(originalRiskCounts)}</td>
                      <td className="px-4 py-3 text-green-700 font-semibold">{describeRiskCounts(replayRiskCounts)}</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 font-semibold text-gray-700">Estimated Cost</td>
                      <td className="px-4 py-3 text-gray-900">{formatCost(totalOriginalCost)}</td>
                      <td className="px-4 py-3 text-green-700 font-semibold">{formatCost(totalReplayCost)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

            </div>
          )}

          {runReplayResult && (
            <div className="card mb-8">
              <div className="flex items-center mb-4">
                <FileText className="w-6 h-6 text-blue-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">Replay Redline Proposals</h3>
              </div>
              {replayProposals.length > 0 ? (
                <div className="space-y-4">
                  {replayProposals.map((proposal, index) => (
                    <div
                      key={`${proposal.clause_id || index}-${index}`}
                      className="border border-blue-200 bg-blue-50 rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="text-sm font-semibold text-gray-900">
                            Clause: {proposal.clause_id || "Unknown"}
                          </p>
                          {proposal.heading && (
                            <p className="text-xs text-gray-600">{proposal.heading}</p>
                          )}
                        </div>
                        <span className="text-xs font-semibold text-blue-700 bg-white px-2 py-1 rounded border border-blue-200">
                          {proposal.variant || "proposal"}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {proposal.edited_text || proposal.proposed_text || "(No edited text generated)"}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500 py-6 text-center">
                  No proposals were generated during this replay.
                </div>
              )}
            </div>
          )}

          <div className="card mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <RotateCcw className="w-6 h-6 text-primary-600 mr-3" />
                <h2 className="text-xl font-semibold text-gray-900">Execution Trace</h2>
              </div>
            </div>

            {selectedRunDetailLoading ? (
              <div className="text-sm text-gray-500">Loading execution trace…</div>
            ) : historySteps.length === 0 ? (
              <div className="text-sm text-gray-500">No trace data captured.</div>
            ) : (
              <div className="space-y-4">
                {historySteps.map((step, index) => {
                  const clauseId = step.clause_id || step.metadata?.clause_id || step.step_id;
                  const clauseReplay = clauseId ? clauseReplayResults[clauseId] : undefined;
                  const clauseError = clauseId ? clauseReplayErrors[clauseId] : undefined;
                  const canEdit = Boolean(clauseId && step.input && step.input.trim().length > 0);

                  const clauseComparison = clauseReplay?.comparison;
                  const clauseOriginalRisk = clauseComparison?.risk_level?.original ?? clauseReplay?.original_assessment?.risk_level ?? null;
                  const clauseReplayRisk = clauseComparison?.risk_level?.replay ?? clauseReplay?.assessment?.risk_level ?? null;
                  const clauseOriginalDurationSeconds = clauseComparison?.duration_seconds?.original ?? (typeof step.duration_ms === "number" ? step.duration_ms / 1000 : undefined);
                  const clauseReplayDurationSeconds = clauseComparison?.duration_seconds?.replay ?? clauseReplay?.duration_seconds ?? undefined;
                  const clauseOriginalCostValue = clauseComparison?.cost?.original ?? (typeof step.metadata?.cost_usd === "number" ? step.metadata.cost_usd : undefined);
                  const clauseReplayCostValue = clauseComparison?.cost?.replay ?? undefined;

                  const showClauseMatrix = Boolean(clauseReplay);

                  return (
                    <div key={step.step_id} className="border border-gray-200 rounded-lg overflow-hidden">
                      <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <span className="flex-shrink-0 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                            {index + 1}
                          </span>
                          {getStatusIcon(step.status)}
                          <div>
                            <h3 className="font-semibold text-gray-900">{step.step_name}</h3>
                            <p className="text-xs text-gray-500">
                              {step.agent} • {formatDuration(step.duration_ms)}
                              {step.metadata?.model ? ` • ${step.metadata.model}` : ""}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => canEdit && handleEditStep(step.step_id, clauseId, step.input)}
                          className={`p-2 rounded-lg transition-colors ${
                            canEdit ? "text-primary-600 hover:bg-primary-50" : "text-gray-300 cursor-not-allowed"
                          }`}
                          title="Edit LLM prompt"
                          disabled={!canEdit}
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="p-4 space-y-3">
                        <div>
                          <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                            Input Prompt
                          </label>
                          {editingStep === step.step_id ? (
                            <div className="mt-1">
                              <textarea
                                className="input font-mono text-sm"
                                rows={4}
                                value={modifiedInput}
                                onChange={(e) => setModifiedInput(e.target.value)}
                                placeholder="Modify the LLM prompt/input here"
                              />
                              <div className="flex flex-wrap gap-2 mt-2">
                                <button
                                  onClick={() => clauseId && handleClauseReplay(clauseId, modifiedInput)}
                                  className="btn-primary text-sm"
                                  disabled={!clauseId || clauseReplayLoading === clauseId}
                                >
                                  {clauseReplayLoading === clauseId ? "Running…" : "Replay Clause"}
                                </button>
                                <button
                                  onClick={handleCancelEdit}
                                  className="btn-secondary text-sm"
                                  disabled={clauseReplayLoading === clauseId}
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <p className="mt-1 text-sm text-gray-700 bg-gray-50 p-3 rounded border border-gray-200 whitespace-pre-wrap">
                              {step.input && step.input.trim().length > 0 ? step.input : "(No prompt recorded)"}
                            </p>
                          )}
                        </div>

                        <div>
                          <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                            Output
                          </label>
                          <p className="mt-1 text-sm text-gray-700 bg-green-50 p-3 rounded border border-green-200 whitespace-pre-wrap">
                            {step.output || "(No output recorded)"}
                          </p>
                        </div>

                        <div className="flex flex-wrap gap-4 pt-2 border-t border-gray-200 text-xs">
                          {step.metadata?.tokens_in && (
                            <div>
                              <span className="text-gray-600">Tokens In:</span>
                              <span className="font-semibold text-gray-900 ml-1">
                                {step.metadata.tokens_in.toLocaleString()}
                              </span>
                            </div>
                          )}
                          {step.metadata?.tokens_out && (
                            <div>
                              <span className="text-gray-600">Tokens Out:</span>
                              <span className="font-semibold text-gray-900 ml-1">
                                {step.metadata.tokens_out.toLocaleString()}
                              </span>
                            </div>
                          )}
                          {step.metadata?.cost_usd && (
                            <div>
                              <span className="text-gray-600">Cost:</span>
                              <span className="font-semibold text-green-700 ml-1">
                                ${step.metadata.cost_usd.toFixed(3)}
                              </span>
                            </div>
                          )}
                          {step.metadata?.cache_hit && (
                            <div className="px-2 py-1 bg-blue-100 text-blue-800 rounded font-semibold">
                              Cache Hit
                            </div>
                          )}
                          {step.timestamp && (
                            <div>
                              <span className="text-gray-600">Timestamp:</span>
                              <span className="font-semibold text-gray-900 ml-1">
                                {formatTime(step.timestamp)}
                              </span>
                            </div>
                          )}
                        </div>

                        {showClauseMatrix && (
                          <div className="mt-3">
                            <table className="w-full border border-gray-200 text-xs">
                              <thead className="bg-gray-100 text-gray-600 uppercase">
                                <tr>
                                  <th className="px-3 py-2 text-left">Metric</th>
                                  <th className="px-3 py-2 text-left">Original</th>
                                  <th className="px-3 py-2 text-left">Replay</th>
                                </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                                <tr>
                                  <td className="px-3 py-2 font-semibold text-gray-700">Risk Level</td>
                                  <td className="px-3 py-2 text-gray-900">{formatRiskLevel(clauseOriginalRisk)}</td>
                                  <td className="px-3 py-2 text-green-700 font-semibold">{formatRiskLevel(clauseReplayRisk)}</td>
                                </tr>
                                <tr>
                                  <td className="px-3 py-2 font-semibold text-gray-700">Duration</td>
                                  <td className="px-3 py-2 text-gray-900">{formatSeconds(clauseOriginalDurationSeconds)}</td>
                                  <td className="px-3 py-2 text-green-700 font-semibold">{formatSeconds(clauseReplayDurationSeconds)}</td>
                                </tr>
                                <tr>
                                  <td className="px-3 py-2 font-semibold text-gray-700">Cost</td>
                                  <td className="px-3 py-2 text-gray-900">{formatCost(clauseOriginalCostValue ?? null)}</td>
                                  <td className="px-3 py-2 text-green-700 font-semibold">{formatCost(clauseReplayCostValue ?? null)}</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        )}

                        {clauseError && (
                          <div className="border border-red-200 bg-red-50 text-red-700 px-3 py-2 rounded text-sm">
                            {clauseError}
                          </div>
                        )}

                        {clauseReplay && (
                          <div className="mt-3 border border-blue-200 bg-blue-50 p-4 rounded">
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="text-sm font-semibold text-blue-900">Clause Replay Comparison</h4>
                              <span className="text-xs text-gray-600">
                                Duration Δ {formatSeconds(clauseReplay.comparison.duration_seconds?.delta)}
                              </span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                              <div className="bg-white border border-gray-200 rounded p-3">
                                <p className="text-xs uppercase font-semibold text-gray-600 mb-1">Risk</p>
                                <p className="text-gray-700">
                                  {formatRiskLevel(clauseReplay.comparison.risk_level.original)} → {formatRiskLevel(clauseReplay.comparison.risk_level.replay)}
                                </p>
                              </div>
                              <div className="bg-white border border-gray-200 rounded p-3">
                                <p className="text-xs uppercase font-semibold text-gray-600 mb-1">Cost</p>
                                <p className="text-gray-700">
                                  {formatCost(clauseReplay.comparison.cost?.original)} → {formatCost(clauseReplay.comparison.cost?.replay)}
                                  <span className="text-xs text-gray-500 ml-2">
                                    Δ {formatCost(clauseReplay.comparison.cost?.delta)}
                                  </span>
                                </p>
                              </div>
                              <div className="bg-white border border-gray-200 rounded p-3">
                                <p className="text-xs uppercase font-semibold text-gray-600 mb-1">Replay Duration</p>
                                <p className="text-gray-700">{formatSeconds(clauseReplay.duration_seconds)}</p>
                              </div>
                            </div>
                            {clauseReplay.assessment.rationale && (
                              <p className="mt-3 text-xs text-gray-600">
                                Replay rationale: {clauseReplay.assessment.rationale}
                              </p>
                            )}
                            {clauseReplay.prompt && (
                              <details className="mt-3">
                                <summary className="text-xs font-semibold text-gray-700 cursor-pointer">
                                  Prompt Used
                                </summary>
                                <pre className="mt-2 text-xs whitespace-pre-wrap bg-white border border-gray-200 rounded p-3">
                                  {clauseReplay.prompt}
                                </pre>
                              </details>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="card bg-blue-50 border-2 border-blue-200 mt-8">
            <div className="flex items-center mb-4">
              <Settings className="w-6 h-6 text-blue-600 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900">What-If Scenarios</h3>
            </div>
            <p className="text-sm text-gray-700 mb-4">
              Modify LLM prompts, replay from that step, and track how results evolve.
            </p>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Edit any step’s prompt and replay just that clause to inspect changes.</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Compare replayed outcomes (duration, risk, cost) against the original clause.</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Run-level replay re-executes the full review with alternate agent paths or playbooks.</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Use clause-level replay to validate prompt tweaks without impacting Risk Gate queues.</span>
              </li>
            </ul>
          </div>
        </>
      ) : (
        <div className="card text-center py-12">
          <RotateCcw className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-gray-600 mb-2">No run selected</p>
          <p className="text-sm text-gray-500">
            Select a run from the list above to inspect and replay its execution trace.
          </p>
        </div>
      )}
    </div>
  );
};
export default ReplayPage;
