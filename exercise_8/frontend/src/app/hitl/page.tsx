"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  Shield,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  ArrowRight,
} from "lucide-react";

import { api } from "../../lib/api";

interface PendingRunSummary {
  run_id: string;
  doc_id: string;
  doc_name: string;
  agent_path: string;
  status: string;
  created_at?: string;
  updated_at?: string;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  total_assessments: number;
}

interface AssessmentEntry {
  clause_id: string;
  clause_heading: string;
  clause_text: string;
  risk_level: string;
  rationale: string;
  policy_refs: string[];
  recommended_action: string;
  impact_assessment: string;
}

interface AssessmentResponse {
  run_id: string;
  doc_id: string;
  doc_name: string;
  agent_path: string;
  assessments: AssessmentEntry[];
}

export default function RiskGatePage() {
  const [pendingRuns, setPendingRuns] = useState<PendingRunSummary[]>([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [runsError, setRunsError] = useState<string | null>(null);

  const [selectedRun, setSelectedRun] = useState<string>("");
  const [assessments, setAssessments] = useState<AssessmentResponse | null>(null);
  const [assessmentsLoading, setAssessmentsLoading] = useState(false);
  const [assessmentError, setAssessmentError] = useState<string | null>(null);

  const [approvedClauses, setApprovedClauses] = useState<Set<string>>(new Set());
  const [rejectedClauses, setRejectedClauses] = useState<Set<string>>(new Set());
  const [clauseComments, setClauseComments] = useState<Record<string, string>>({});
  const [approvalComplete, setApprovalComplete] = useState(false);

  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const refreshPendingRuns = async () => {
    setRunsLoading(true);
    setRunsError(null);
    try {
      const data: PendingRunSummary[] = await api.listPendingRiskRuns();
      setPendingRuns(data);
    } catch (error) {
      console.error(error);
      setRunsError("Unable to load pending runs. Please try again.");
    } finally {
      setRunsLoading(false);
    }
  };

  useEffect(() => {
    void refreshPendingRuns();
  }, []);

  const resetDecisionState = () => {
    setApprovedClauses(new Set());
    setRejectedClauses(new Set());
    setClauseComments({});
    setApprovalComplete(false);
    setSubmitError(null);
  };

  const handleLoadRun = async (runId: string) => {
    setSelectedRun(runId);
    resetDecisionState();
    setAssessments(null);
    setAssessmentError(null);
    setAssessmentsLoading(true);
    try {
      const data: AssessmentResponse = await api.getRiskAssessments(runId);
      setAssessments(data);
    } catch (error) {
      console.error(error);
      setAssessmentError("Failed to load risk assessments for this run.");
    } finally {
      setAssessmentsLoading(false);
    }
  };

  const handleToggleApproval = (
    clauseId: string,
    defaultAction: string,
    riskLevel: string
  ) => {
    const newApproved = new Set(approvedClauses);
    const newRejected = new Set(rejectedClauses);

    if (newApproved.has(clauseId)) {
      newApproved.delete(clauseId);
      newRejected.add(clauseId);
    } else if (newRejected.has(clauseId)) {
      newRejected.delete(clauseId);
    } else {
      const normalized = (defaultAction || "").toUpperCase();
      if (normalized.startsWith("APPROVE")) {
        newApproved.add(clauseId);
      } else if (normalized.startsWith("REJECT")) {
        newRejected.add(clauseId);
      } else if ((riskLevel || "").toUpperCase() === "HIGH") {
        newRejected.add(clauseId);
      } else {
        newApproved.add(clauseId);
      }
    }

    setApprovedClauses(newApproved);
    setRejectedClauses(newRejected);
  };

  const handleApproveAllClauses = () => {
    if (!assessments) return;
    const allIds = new Set(assessments.assessments.map((a) => a.clause_id));
    setApprovedClauses(allIds);
    setRejectedClauses(new Set());
  };

  const handleRejectAllClauses = () => {
    if (!assessments) return;
    const allIds = new Set(assessments.assessments.map((a) => a.clause_id));
    setRejectedClauses(allIds);
    setApprovedClauses(new Set());
  };

  const highRiskCount =
    assessments?.assessments.filter((a) => a.risk_level.toUpperCase() === "HIGH").length || 0;
  const mediumRiskCount =
    assessments?.assessments.filter((a) => a.risk_level.toUpperCase() === "MEDIUM").length || 0;
  const lowRiskCount =
    assessments?.assessments.filter((a) => a.risk_level.toUpperCase() === "LOW").length || 0;
  const totalClauses = assessments?.assessments.length ?? 0;
  const pendingCount = Math.max(totalClauses - approvedClauses.size - rejectedClauses.size, 0);

  const allDecisionsMade =
    assessments && totalClauses > 0 && approvedClauses.size + rejectedClauses.size === totalClauses;

  const handleSubmitApproval = async () => {
    if (!assessments || !allDecisionsMade) return;

    setSubmitLoading(true);
    setSubmitError(null);

    try {
      const items = assessments.assessments.map((assessment) => ({
        clause_id: assessment.clause_id,
        decision: rejectedClauses.has(assessment.clause_id) ? "reject" : "approve",
        comments: clauseComments[assessment.clause_id] || undefined,
      }));

      await api.riskApprove({ run_id: assessments.run_id, items });
      setApprovalComplete(true);
      await refreshPendingRuns();
    } catch (error) {
      console.error(error);
      setSubmitError("Failed to submit risk approval. Please try again.");
    } finally {
      setSubmitLoading(false);
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toUpperCase()) {
      case "HIGH":
        return "bg-red-100 text-red-800 border-red-300";
      case "MEDIUM":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "LOW":
        return "bg-green-100 text-green-800 border-green-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel.toUpperCase()) {
      case "HIGH":
        return <XCircle className="w-5 h-5 text-red-600" />;
      case "MEDIUM":
        return <AlertTriangle className="w-5 h-5 text-orange-600" />;
      case "LOW":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      default:
        return <Shield className="w-5 h-5 text-gray-600" />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Risk Gate (HITL)</h1>
        <p className="text-gray-600">
          Human-in-the-loop approval for high-risk clauses before proceeding
        </p>
      </div>

      {/* Pending Runs */}
      <div className="card mb-8">
        <div className="flex items-center mb-6">
          <Clock className="w-6 h-6 text-orange-600 mr-3" />
          <h2 className="text-xl font-semibold text-gray-900">
            Pending Risk Approval
          </h2>
        </div>
        <div className="grid grid-cols-1 gap-3">
          {runsLoading && (
            <div className="text-sm text-gray-500">Loading pending runs…</div>
          )}
          {runsError && (
            <div className="text-sm text-red-600 border border-red-200 bg-red-50 px-3 py-2 rounded">
              {runsError}
            </div>
          )}
          {!runsLoading && !runsError && pendingRuns.length === 0 && (
            <div className="text-sm text-gray-500">No runs currently awaiting risk approval.</div>
          )}
          {pendingRuns.map((run) => {
            const createdAt = run.created_at
              ? new Date(run.created_at).toLocaleTimeString("en-US", {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "—";

            return (
              <button
                key={run.run_id}
                onClick={() => void handleLoadRun(run.run_id)}
                className={`flex items-center justify-between p-4 border-2 rounded-lg text-left transition-all ${
                  selectedRun === run.run_id
                    ? "border-primary-500 bg-primary-50"
                    : "border-gray-200 hover:border-primary-300 hover:bg-gray-50"
                }`}
              >
                <div className="flex items-center space-x-4 flex-1">
                  <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{run.doc_name}</p>
                    <p className="text-xs text-gray-500 font-mono mt-1">{run.run_id}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6 text-sm">
                  <div className="text-center">
                    <p className="text-gray-600 text-xs">Agent</p>
                    <p className="font-medium text-gray-900">
                      {run.agent_path.replace("_", "-")}
                    </p>
                  </div>
                  <div className="text-center">
                  <p className="text-gray-600 text-xs">Risk Clauses</p>
                    <div className="flex items-center space-x-1 mt-1">
                      <span className="px-1.5 py-0.5 bg-red-100 text-red-800 text-xs font-semibold rounded">
                        {run.high_risk_count}H
                      </span>
                      <span className="px-1.5 py-0.5 bg-orange-100 text-orange-800 text-xs font-semibold rounded">
                        {run.medium_risk_count}M
                      </span>
                      <span className="px-1.5 py-0.5 bg-green-100 text-green-800 text-xs font-semibold rounded">
                        {run.low_risk_count}L
                      </span>
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-600 text-xs">Time</p>
                    <p className="text-gray-700" suppressHydrationWarning>
                      {createdAt}
                    </p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Risk Assessments */}
      {assessmentError && (
        <div className="card border border-red-200 bg-red-50 text-red-700 mb-6">
          {assessmentError}
        </div>
      )}

      {assessmentsLoading && (
        <div className="card text-sm text-gray-500 mb-6">Loading risk assessments…</div>
      )}

      {assessments && !approvalComplete && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Total Clauses</p>
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">{totalClauses}</p>
              <p className="text-sm text-gray-600 mt-1">Reviewed</p>
            </div>

            <div className="card bg-red-50 border-red-200">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">High Risk</p>
                <XCircle className="w-5 h-5 text-red-600" />
              </div>
              <p className="text-3xl font-bold text-red-700">{highRiskCount}</p>
              <p className="text-sm text-red-600 mt-1">Requires action</p>
            </div>

            <div className="card bg-orange-50 border-orange-200">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Medium Risk</p>
                <AlertTriangle className="w-5 h-5 text-orange-600" />
              </div>
              <p className="text-3xl font-bold text-orange-700">{mediumRiskCount}</p>
              <p className="text-sm text-orange-600 mt-1">Review needed</p>
            </div>

            <div className="card bg-green-50 border-green-200">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Low Risk</p>
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <p className="text-3xl font-bold text-green-700">{lowRiskCount}</p>
              <p className="text-sm text-green-600 mt-1">Acceptable</p>
            </div>
          </div>

          {/* Assessments List */}
          <div className="card mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <Shield className="w-6 h-6 text-primary-600 mr-3" />
                <div>
                  <p className="text-sm uppercase tracking-wide text-gray-500">{assessments.doc_name}</p>
                  <h2 className="text-xl font-semibold text-gray-900">
                    Risk Assessments ({totalClauses})
                  </h2>
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={handleApproveAllClauses}
                  className="btn-secondary text-sm flex items-center"
                >
                  <ThumbsUp className="w-4 h-4 mr-2" />
                  Approve All
                </button>
                <button
                  onClick={handleRejectAllClauses}
                  className="btn-secondary text-sm flex items-center"
                >
                  <ThumbsDown className="w-4 h-4 mr-2" />
                  Reject All
                </button>
              </div>
            </div>

            <div className="space-y-4">
              {assessments.assessments.map((assessment, index) => {
                const isApproved = approvedClauses.has(assessment.clause_id);
                const isRejected = rejectedClauses.has(assessment.clause_id);

                return (
                  <div
                    key={assessment.clause_id}
                    className={`border-2 rounded-lg overflow-hidden transition-all ${
                      isApproved
                        ? "border-green-300 bg-green-50"
                        : isRejected
                        ? "border-red-300 bg-red-50"
                        : "border-gray-200"
                    }`}
                  >
                    {/* Assessment Header */}
                    <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
                      <div className="flex items-center space-x-4 flex-1">
                        <span className="flex-shrink-0 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                          {index + 1}
                        </span>
                        {getRiskIcon(assessment.risk_level)}
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h3 className="font-semibold text-gray-900">
                              {assessment.clause_heading}
                            </h3>
                            <span
                              className={`px-2 py-1 text-xs font-semibold rounded border ${getRiskColor(
                                assessment.risk_level
                              )}`}
                            >
                              {assessment.risk_level}
                            </span>
                            <span className="text-xs text-gray-500 font-mono">
                              {assessment.clause_id}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            {assessment.recommended_action}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() =>
                          handleToggleApproval(
                            assessment.clause_id,
                            assessment.recommended_action,
                            assessment.risk_level
                          )
                        }
                        className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                          isApproved
                            ? "bg-green-600 text-white hover:bg-green-700"
                            : isRejected
                            ? "bg-red-600 text-white hover:bg-red-700"
                            : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                        }`}
                      >
                        {isApproved ? (
                          <span className="flex items-center">
                            <CheckCircle className="w-4 h-4 mr-2" />
                            Approved
                          </span>
                        ) : isRejected ? (
                          <span className="flex items-center">
                            <XCircle className="w-4 h-4 mr-2" />
                            Rejected
                          </span>
                        ) : (
                          "Review"
                        )}
                      </button>
                    </div>

                    {/* Assessment Details */}
                    <div className="p-4 space-y-3">
                      {/* Clause Text */}
                      <div>
                        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                          Clause Text
                        </label>
                        <p className="mt-1 text-sm text-gray-700 bg-gray-50 p-3 rounded border border-gray-200">
                          {assessment.clause_text}
                        </p>
                      </div>

                      {/* Risk Rationale */}
                      <div>
                        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                          Risk Rationale
                        </label>
                        <p className="mt-1 text-sm text-gray-700 bg-yellow-50 p-3 rounded border border-yellow-200">
                          {assessment.rationale}
                        </p>
                      </div>

                      {/* Impact Assessment */}
                      <div>
                        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                          Impact Assessment
                        </label>
                        <p className="mt-1 text-sm text-gray-700 bg-blue-50 p-3 rounded border border-blue-200">
                          {assessment.impact_assessment}
                        </p>
                      </div>

                      {/* Policy References */}
                      <div className="flex flex-wrap gap-2">
                        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                          Policy References:
                        </label>
                        {assessment.policy_refs.map((ref, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded"
                          >
                            {ref}
                          </span>
                        ))}
                      </div>

                      {/* Comments */}
                      <div>
                        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center mb-2">
                          <MessageSquare className="w-3 h-3 mr-1" />
                          Your Comments (Optional)
                        </label>
                        <textarea
                          className="input text-sm"
                          rows={2}
                          placeholder="Add any notes or concerns about this risk assessment..."
                          value={clauseComments[assessment.clause_id] || ""}
                          onChange={(e) =>
                            setClauseComments({
                              ...clauseComments,
                              [assessment.clause_id]: e.target.value,
                            })
                          }
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Approval Section */}
          <div className="card bg-gradient-to-r from-primary-50 to-blue-50 border-2 border-primary-200">
            <div className="flex items-center mb-4">
              <Shield className="w-6 h-6 text-primary-600 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900">
                Risk Gate Approval
              </h3>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                <p className="font-semibold mb-2">Review Summary:</p>
                <div className="space-y-1">
                  <p>✓ {approvedClauses.size} clauses approved</p>
                  {rejectedClauses.size > 0 && (
                    <p>✗ {rejectedClauses.size} clauses rejected</p>
                  )}
                  <p className="text-gray-600">{pendingCount} pending review</p>
                </div>
              </div>
              {submitError && (
                <div className="text-sm text-red-600 mr-4">{submitError}</div>
              )}
              <button
                onClick={() => void handleSubmitApproval()}
                disabled={!allDecisionsMade || submitLoading}
                className="btn-primary flex items-center text-lg py-3 px-6"
              >
                <CheckCircle className={`w-5 h-5 mr-2 ${submitLoading ? "animate-spin" : ""}`} />
                {submitLoading ? "Submitting…" : "Submit Risk Approval"}
              </button>
            </div>
          </div>
        </>
      )}

      {/* Approval Complete */}
      {approvalComplete && (
        <div className="card bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200">
          <div className="flex items-center mb-4">
            <CheckCircle className="w-8 h-8 text-green-600 mr-3" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Risk Gate Approved!
              </h3>
              <p className="text-sm text-gray-600">
                The run can now proceed to the next stage
              </p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg mb-4">
            <p className="text-sm font-semibold text-gray-700 mb-2">
              Approval Summary:
            </p>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Approved</p>
                <p className="text-2xl font-bold text-green-600">
                  {approvedClauses.size}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Rejected</p>
                <p className="text-2xl font-bold text-red-600">
                  {rejectedClauses.size}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Total</p>
                <p className="text-2xl font-bold text-gray-900">
                  {totalClauses}
                </p>
              </div>
            </div>
          </div>
          <div className="flex space-x-3">
            <Link
              href={`/run/${selectedRun}`}
              className="btn-primary flex items-center"
            >
              <ArrowRight className="w-4 h-4 mr-2" />
              Continue to Final Approval
            </Link>
            <Link href="/reports" className="btn-secondary flex items-center">
              View Reports
            </Link>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!assessments && !assessmentsLoading && !assessmentError && (
        <div className="card text-center py-12">
          <Shield className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-gray-600 mb-2">No run selected</p>
          <p className="text-sm text-gray-500">
            Select a pending run from the list above to begin risk approval
          </p>
        </div>
      )}
    </div>
  );
}
