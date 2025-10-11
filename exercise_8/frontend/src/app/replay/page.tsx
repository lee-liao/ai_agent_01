"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
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
  Eye,
  Copy,
  Loader2,
} from "lucide-react";

import { api } from "../../lib/api";

type GenericRecord = Record<string, any>;

interface RunSummary {
  run_id: string;
  doc_id?: string;
  doc_name?: string;
  agent_path?: string;
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
  metadata: GenericRecord;
}

interface ReplayResult {
  run_id: string;
  workflow_result?: any;
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

const ReplayPage = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [runsError, setRunsError] = useState<string | null>(null);

  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [editingStep, setEditingStep] = useState<string | null>(null);
  const [modifiedInput, setModifiedInput] = useState<string>("");
  const [replayResult, setReplayResult] = useState<ReplayResult | null>(null);
  const [showComparison, setShowComparison] = useState(false);
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayError, setReplayError] = useState<string | null>(null);

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

  const selectedRun = useMemo(
    () => runs.find((run) => run.run_id === selectedRunId) || null,
    [runs, selectedRunId]
  );

  const historySteps = useMemo(
    () => buildHistorySteps(selectedRun?.history),
    [selectedRun]
  );

  const riskCounts = useMemo(
    () => countRiskLevels(selectedRun?.assessments),
    [selectedRun]
  );

  const comparisonRun = useMemo(
    () => (replayResult ? runs.find((run) => run.run_id === replayResult.run_id) || null : null),
    [replayResult, runs]
  );

  const handleLoadTrace = (runId: string) => {
    setSelectedRunId(runId);
    setReplayResult(null);
    setShowComparison(false);
    setReplayError(null);
    setEditingStep(null);
    setModifiedInput("");
  };

  const handleEditStep = (stepId: string, currentInput: string) => {
    if (!currentInput || currentInput.trim().length === 0) {
      return;
    }
    setEditingStep(stepId);
    setModifiedInput(currentInput);
  };

  const handleCancelEdit = () => {
    setEditingStep(null);
    setModifiedInput("");
  };

  const handleReplay = async (stepId?: string) => {
    if (!selectedRunId) return;

    setReplayLoading(true);
    setReplayError(null);
    try {
      const payload = stepId
        ? { step_id: stepId, input_override: modifiedInput || undefined }
        : undefined;
      const response = await api.replay(selectedRunId, payload);
      setReplayResult(response);
      setShowComparison(true);
      setEditingStep(null);
      setModifiedInput("");

      const refreshed = await api.listRuns();
      setRuns(refreshed);
    } catch (error) {
      console.error("Replay failed", error);
      setReplayError("Replay failed. Please try again.");
    } finally {
      setReplayLoading(false);
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
                      (run.status || "").toLowerCase().includes("complete") ||
                      (run.status || "").toLowerCase() === "completed"
                        ? "bg-green-500"
                        : (run.status || "").toLowerCase().includes("fail")
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
                <h2 className="text-xl font-semibold text-gray-900">Execution Trace</h2>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleReplay()}
                  className="btn-primary flex items-center"
                  disabled={replayLoading}
                >
                  {replayLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4 mr-2" />
                  )}
                  {replayLoading ? "Replaying..." : "Replay Run"}
                </button>
                <button className="btn-secondary flex items-center" disabled>
                  <Copy className="w-4 h-4 mr-2" />
                  Clone & Modify
                </button>
              </div>
            </div>

            {historySteps.length === 0 ? (
              <div className="text-sm text-gray-500">No trace data captured.</div>
            ) : (
              <div className="space-y-4">
                {historySteps.map((step, index) => {
                  const canEdit = Boolean(step.input && step.input.trim().length > 0);
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
                        onClick={() => canEdit && handleEditStep(step.step_id, step.input)}
                        className={`p-2 rounded-lg transition-colors ${
                          canEdit
                            ? "text-primary-600 hover:bg-primary-50"
                            : "text-gray-300 cursor-not-allowed"
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
                                onClick={() => handleReplay(step.step_id)}
                                className="btn-primary text-sm"
                                disabled={replayLoading}
                              >
                                {replayLoading ? "Running…" : "Replay from Here"}
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="btn-secondary text-sm"
                                disabled={replayLoading}
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <p className="mt-1 text-sm text-gray-700 bg-gray-50 p-3 rounded border border-gray-200 whitespace-pre-wrap">
                            {step.input && step.input.trim().length > 0
                              ? step.input
                              : "(No prompt recorded)"}
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
                    </div>
                  </div>
                  );
                })}
              </div>
            )}

            {replayError && (
              <div className="mt-4 border border-red-200 bg-red-50 text-red-700 px-4 py-3 rounded">
                {replayError}
              </div>
            )}
          </div>

          {replayResult && (
            <div className="card bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200">
              <div className="flex items-center mb-4">
                <CheckCircle className="w-6 h-6 text-green-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">Replay Complete!</h3>
              </div>
              <p className="text-gray-700 mb-4">
                New run created with ID: {""}
                <code className="bg-white px-2 py-1 rounded font-mono text-sm">
                  {replayResult.run_id}
                </code>
              </p>
              <div className="flex space-x-3">
                <Link href={`/run/${replayResult.run_id}`} className="btn-primary flex items-center">
                  <Eye className="w-4 h-4 mr-2" />
                  View New Run
                </Link>
                <button
                  onClick={() => setShowComparison((prev) => !prev)}
                  className="btn-secondary flex items-center"
                >
                  <Settings className="w-4 h-4 mr-2" />
                  {showComparison ? "Hide" : "Show"} Comparison
                </button>
              </div>

              {showComparison && (
                <div className="mt-6 pt-6 border-t border-green-300">
                  <h4 className="font-semibold text-gray-900 mb-3">
                    Comparison: Original vs Replay
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <p className="text-sm font-semibold text-gray-700 mb-2">
                        Original Run
                      </p>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Score:</span>
                          <span className="font-semibold">{selectedRun?.score ?? "--"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">High Risk:</span>
                          <span className="font-semibold">{riskCounts.high}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Medium Risk:</span>
                          <span className="font-semibold">{riskCounts.medium}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Low Risk:</span>
                          <span className="font-semibold">{riskCounts.low}</span>
                        </div>
                      </div>
                    </div>
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <p className="text-sm font-semibold text-gray-700 mb-2">
                        Replay Run
                      </p>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Score:</span>
                          <span className="font-semibold text-green-600">
                            {comparisonRun?.score ?? "--"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">High Risk:</span>
                          <span className="font-semibold text-green-600">
                            {countRiskLevels(comparisonRun?.assessments).high}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Medium Risk:</span>
                          <span className="font-semibold text-green-600">
                            {countRiskLevels(comparisonRun?.assessments).medium}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Low Risk:</span>
                          <span className="font-semibold text-green-600">
                            {countRiskLevels(comparisonRun?.assessments).low}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

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
                <span>Edit any step’s prompt and replay from that point forward.</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Compare replayed outcomes (score, risk mix) against the original run.</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Capture replay lineage via run metadata for future analysis.</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Extend with cost and duration tracking as persistence matures.</span>
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
