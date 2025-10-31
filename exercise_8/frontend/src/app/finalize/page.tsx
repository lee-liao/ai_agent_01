"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  Download,
  Eye,
  MessageSquare,
  Clock,
  User,
  ThumbsUp,
  ThumbsDown,
  Edit3,
  ArrowRight,
} from "lucide-react";

import { api } from "../../lib/api";

interface PendingFinalRun {
  run_id: string;
  doc_id?: string;
  doc_name?: string;
  agent_path?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
  total_proposals: number;
  high_risk_resolved: number;
  score: number;
}

interface FinalSummary {
  total_clauses: number;
  high_risk_clauses: number;
  medium_risk_clauses: number;
  low_risk_clauses: number;
  proposals_generated: number;
  estimated_risk_reduction: string;
}

interface FinalMemo {
  executive_summary: string;
  risk_assessment: string;
  recommendations: string[];
}

interface RedlineProposal {
  proposal_id: string;
  clause_id: string;
  clause_heading: string;
  risk_level: string;
  original_text: string;
  proposed_text: string;
  rationale: string;
  policy_refs: string[];
  variant: string;
  reviewer_notes?: string;
}

interface RedlineDetails {
  run_id: string;
  doc_id?: string;
  doc_name?: string;
  agent_path?: string;
  playbook_id?: string;
  status?: string;
  created_at?: string;
  score: number;
  summary: FinalSummary;
  proposals: RedlineProposal[];
  memo: FinalMemo;
}

export default function FinalizePage() {
  const searchParams = useSearchParams();
  const deepLinkRunId = useMemo(() => searchParams?.get("run_id") ?? "", [searchParams]);
  const [pendingRuns, setPendingRuns] = useState<PendingFinalRun[]>([]);
  const [pendingLoading, setPendingLoading] = useState(true);
  const [pendingError, setPendingError] = useState<string | null>(null);

  const [selectedRun, setSelectedRun] = useState<string>("");
  const [redlineDetails, setRedlineDetails] = useState<RedlineDetails | null>(
    null
  );
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState<string | null>(null);

  const [approvalNotes, setApprovalNotes] = useState<string>("");
  const [approvedProposals, setApprovedProposals] = useState<Set<string>>(
    new Set()
  );
  const [rejectedProposals, setRejectedProposals] = useState<Set<string>>(
    new Set()
  );
  const [proposalComments, setProposalComments] = useState<
    Record<string, string>
  >({});

  const [finalApproveError, setFinalApproveError] = useState<string | null>(
    null
  );
  const [submittingApproval, setSubmittingApproval] = useState(false);

  const [showExportOptions, setShowExportOptions] = useState(false);
  const [exportComplete, setExportComplete] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const refreshPendingRuns = async (options?: { preserveSelection?: boolean }) => {
    const preserveSelection = options?.preserveSelection ?? false;
    setPendingLoading(true);
    setPendingError(null);
    try {
      const data: PendingFinalRun[] = await api.listPendingFinalRuns();
      setPendingRuns(data);

      const runStillPending = data.some((item) => item.run_id === selectedRun);
      if (!runStillPending && !preserveSelection) {
        setSelectedRun("");
        setRedlineDetails(null);
        setShowExportOptions(false);
        setExportComplete(false);
      }
    } catch (error) {
      console.error("Failed to load pending final runs", error);
      setPendingError("Unable to load pending final approvals.");
    } finally {
      setPendingLoading(false);
    }
  };

  useEffect(() => {
    void refreshPendingRuns();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLoadRedline = async (runId: string) => {
    setSelectedRun(runId);
    setDetailsLoading(true);
    setDetailsError(null);
    setRedlineDetails(null);
    setShowExportOptions(false);
    setExportComplete(false);
    setFinalApproveError(null);

    try {
      const data: RedlineDetails = await api.getRedlineDetails(runId);
      setRedlineDetails(data);
      const allClauseIds = new Set<string>(
        data.proposals.map((proposal) => proposal.clause_id)
      );
      setApprovedProposals(allClauseIds);
      setRejectedProposals(new Set());
      setProposalComments({});
    } catch (error) {
      console.error("Failed to load redline details", error);
      setDetailsError("Unable to load redline details for this run.");
    } finally {
      setDetailsLoading(false);
    }
  };

  useEffect(() => {
    if (!deepLinkRunId || pendingRuns.length === 0) {
      return;
    }
    if (!pendingRuns.some((run) => run.run_id === deepLinkRunId)) {
      return;
    }
    if (selectedRun === deepLinkRunId) {
      return;
    }
    void handleLoadRedline(deepLinkRunId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deepLinkRunId, pendingRuns]);

  const handleToggleApproval = (proposalId: string) => {
    const newApproved = new Set(approvedProposals);
    const newRejected = new Set(rejectedProposals);

    if (newApproved.has(proposalId)) {
      newApproved.delete(proposalId);
      newRejected.add(proposalId);
    } else if (newRejected.has(proposalId)) {
      newRejected.delete(proposalId);
    } else {
      newApproved.add(proposalId);
    }

    setApprovedProposals(newApproved);
    setRejectedProposals(newRejected);
  };

  const handleApproveAll = async () => {
    if (!selectedRun || !redlineDetails) {
      return;
    }

    setSubmittingApproval(true);
    setFinalApproveError(null);
    setExportError(null);

    try {
      await api.finalApprove({
        run_id: selectedRun,
        approved: Array.from(approvedProposals),
        rejected: Array.from(rejectedProposals),
        note: approvalNotes,
      });

      setShowExportOptions(true);
      setExportComplete(false);
      await refreshPendingRuns({ preserveSelection: true });
    } catch (error) {
      console.error("Final approval failed", error);
      setFinalApproveError("Unable to finalize approval. Please try again.");
    } finally {
      setSubmittingApproval(false);
    }
  };

  const handleExport = async (format: "md" | "docx" | "pdf") => {
    if (!selectedRun) {
      return;
    }

    setExporting(true);
    setExportError(null);

    try {
      await api.exportRedline(selectedRun, format);
      setExportComplete(true);
    } catch (error) {
      console.error("Export failed", error);
      setExportError("Failed to export redlined document.");
    } finally {
      setExporting(false);
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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Final Approval Gate
        </h1>
        <p className="text-gray-600">
          Review and approve redlined contract proposals before export
        </p>
      </div>

      {pendingError && (
        <div className="mb-4 border border-red-200 bg-red-50 text-red-700 px-4 py-3 rounded">
          {pendingError}
        </div>
      )}
      {detailsError && (
        <div className="mb-4 border border-red-200 bg-red-50 text-red-700 px-4 py-3 rounded">
          {detailsError}
        </div>
      )}
      {finalApproveError && (
        <div className="mb-4 border border-red-200 bg-red-50 text-red-700 px-4 py-3 rounded">
          {finalApproveError}
        </div>
      )}
      {exportError && (
        <div className="mb-4 border border-red-200 bg-red-50 text-red-700 px-4 py-3 rounded">
          {exportError}
        </div>
      )}

      <div className="card mb-8">
        <div className="flex items-center mb-6">
          <Clock className="w-6 h-6 text-orange-600 mr-3" />
          <h2 className="text-xl font-semibold text-gray-900">
            Pending Final Approval
          </h2>
        </div>
        <div className="grid grid-cols-1 gap-3">
          {pendingLoading ? (
            <div className="p-4 border-2 border-dashed border-gray-200 rounded-lg text-gray-500 text-sm">
              Loading pending reviews...
            </div>
          ) : pendingRuns.length === 0 ? (
            <div className="p-6 border-2 border-gray-200 rounded-lg text-gray-500 text-sm text-center">
              No runs are awaiting final approval.
            </div>
          ) : (
            pendingRuns.map((review) => {
              const createdAt = review.created_at
                ? new Date(review.created_at).toLocaleTimeString("en-US", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "--";

              return (
                <button
                  key={review.run_id}
                  onClick={() => handleLoadRedline(review.run_id)}
                  className={`flex items-center justify-between p-4 border-2 rounded-lg text-left transition-all ${
                    selectedRun === review.run_id
                      ? "border-primary-500 bg-primary-50"
                      : "border-gray-200 hover:border-primary-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center space-x-4 flex-1">
                    <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">
                        {review.doc_name || "Untitled Document"}
                      </p>
                      <p className="text-xs text-gray-500 font-mono mt-1">
                        {review.run_id}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-6 text-sm">
                    <div className="text-center">
                      <p className="text-gray-600 text-xs">Agent</p>
                      <p className="font-medium text-gray-900">
                        {(review.agent_path || "-").replace("_", "-")}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-600 text-xs">Score</p>
                      <p className="font-semibold text-gray-900">
                        {Math.round(review.score)} / 100
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-gray-600 text-xs">Proposals</p>
                      <p className="font-medium text-gray-900">
                        {review.total_proposals}
                      </p>
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
            })
          )}
        </div>
      </div>

      {selectedRun && detailsLoading && (
        <div className="card text-gray-500 text-sm mb-8">
          Loading redline details...
        </div>
      )}

      {redlineDetails && !detailsLoading && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Total Clauses</p>
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {redlineDetails.summary?.total_clauses ?? 0}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {redlineDetails.summary?.proposals_generated ?? 0} proposals
              </p>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Risk Reduction</p>
                <AlertTriangle className="w-5 h-5 text-green-600" />
              </div>
              <p className="text-3xl font-bold text-green-600">
                {redlineDetails.summary?.estimated_risk_reduction ?? "--"}
              </p>
              <p className="text-sm text-gray-600 mt-1">After redlines</p>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Approval Status</p>
                <CheckCircle className="w-5 h-5 text-orange-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {approvedProposals.size}/{redlineDetails.proposals.length}
              </p>
              <p className="text-sm text-gray-600 mt-1">Approved</p>
            </div>

            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Score</p>
                <ThumbsUp className="w-5 h-5 text-purple-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {Math.round(redlineDetails.score)} / 100
              </p>
              <p className="text-sm text-gray-600 mt-1">Quality rating</p>
            </div>
          </div>

          <div className="card mb-8 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200">
            <div className="flex items-center mb-4">
              <FileText className="w-6 h-6 text-blue-600 mr-3" />
              <h3 className="text-lg font-semibold text-gray-900">
                Executive Summary
              </h3>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Overview</h4>
                <p className="text-sm text-gray-700">
                  {redlineDetails.memo?.executive_summary || "No summary available."}
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">
                  Risk Assessment
                </h4>
                <p className="text-sm text-gray-700">
                  {redlineDetails.memo?.risk_assessment || "No assessment provided."}
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">
                  Recommendations
                </h4>
                <ul className="space-y-1">
                  {(redlineDetails.memo?.recommendations || []).map(
                    (rec, idx) => (
                      <li
                        key={`${redlineDetails.run_id}-rec-${idx}`}
                        className="text-sm text-gray-700 flex items-start"
                      >
                        <span className="text-blue-600 mr-2">•</span>
                        <span>{rec}</span>
                      </li>
                    )
                  )}
                </ul>
              </div>
            </div>
          </div>

          <div className="card mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <Edit3 className="w-6 h-6 text-primary-600 mr-3" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Redline Proposals ({redlineDetails.proposals.length})
                </h2>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    const allIds = new Set<string>(
                      redlineDetails.proposals.map((p) => p.clause_id)
                    );
                    setApprovedProposals(allIds);
                    setRejectedProposals(new Set());
                  }}
                  className="btn-secondary text-sm flex items-center"
                >
                  <ThumbsUp className="w-4 h-4 mr-2" />
                  Approve All
                </button>
                <button
                  onClick={() => {
                    const allIds = new Set<string>(
                      redlineDetails.proposals.map((p) => p.clause_id)
                    );
                    setRejectedProposals(allIds);
                    setApprovedProposals(new Set());
                  }}
                  className="btn-secondary text-sm flex items-center"
                >
                  <ThumbsDown className="w-4 h-4 mr-2" />
                  Reject All
                </button>
              </div>
            </div>

            <div className="space-y-6">
              {redlineDetails.proposals.map((proposal, index) => {
                const isApproved = approvedProposals.has(proposal.clause_id);
                const isRejected = rejectedProposals.has(proposal.clause_id);

                return (
                  <div
                    key={`${proposal.clause_id}-${index}`}
                    className={`border-2 rounded-lg overflow-hidden transition-all ${
                      isApproved
                        ? "border-green-300 bg-green-50"
                        : isRejected
                        ? "border-red-300 bg-red-50"
                        : "border-gray-200"
                    }`}
                  >
                    <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
                      <div className="flex items-center space-x-4 flex-1">
                        <span className="flex-shrink-0 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                          {index + 1}
                        </span>
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h3 className="font-semibold text-gray-900">
                              {proposal.clause_heading}
                            </h3>
                            <span
                              className={`px-2 py-1 text-xs font-semibold rounded border ${getRiskColor(
                                proposal.risk_level
                              )}`}
                            >
                              {proposal.risk_level}
                            </span>
                            <span className="text-xs text-gray-500 font-mono">
                              {proposal.clause_id}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            Variant: {proposal.variant}
                            {proposal.reviewer_notes && ` • Reviewer: ${proposal.reviewer_notes}`}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleToggleApproval(proposal.clause_id)}
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

                    <div className="p-4 space-y-4">
                      <div>
                        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center">
                          <XCircle className="w-3 h-3 mr-1 text-red-600" />
                          Original Text
                        </label>
                        <div className="mt-1 text-sm text-gray-700 bg-red-50 p-3 rounded border border-red-200">
                          {proposal.original_text}
                        </div>
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center">
                          <CheckCircle className="w-3 h-3 mr-1 text-green-600" />
                          Proposed Text
                        </label>
                        <div className="mt-1 text-sm text-gray-700 bg-green-50 p-3 rounded border border-green-200">
                          {proposal.proposed_text}
                        </div>
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                          Rationale
                        </label>
                        <p className="mt-1 text-sm text-gray-700 bg-blue-50 p-3 rounded border border-blue-200">
                          {proposal.rationale}
                        </p>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
                          Policy References:
                        </label>
                        {proposal.policy_refs.map((ref, idx) => (
                          <span
                            key={`${proposal.clause_id}-policy-${idx}`}
                            className="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded"
                          >
                            {ref}
                          </span>
                        ))}
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide flex items-center mb-2">
                          <MessageSquare className="w-3 h-3 mr-1" />
                          Your Comments (Optional)
                        </label>
                        <textarea
                          className="input text-sm"
                          rows={2}
                          placeholder="Add any notes or concerns about this proposal..."
                          value={proposalComments[proposal.clause_id] || ""}
                          onChange={(e) =>
                            setProposalComments({
                              ...proposalComments,
                              [proposal.clause_id]: e.target.value,
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

          {!showExportOptions && (
            <div className="card bg-gradient-to-r from-primary-50 to-blue-50 border-2 border-primary-200">
              <div className="flex items-center mb-4">
                <User className="w-6 h-6 text-primary-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Final Approval Notes
                </h3>
              </div>
              <textarea
                className="input mb-4"
                rows={4}
                placeholder="Add any final notes, instructions, or concerns before approving..."
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
              />
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  <p className="font-semibold mb-1">Review Summary:</p>
                  <p>
                    ✓ {approvedProposals.size} proposals approved
                    {rejectedProposals.size > 0 &&
                      ` • ✗ ${rejectedProposals.size} rejected`}
                  </p>
                </div>
                <button
                  onClick={handleApproveAll}
                  disabled={approvedProposals.size === 0 || submittingApproval}
                  className={`btn-primary flex items-center text-lg py-3 px-6 ${
                    submittingApproval ? "opacity-70 cursor-not-allowed" : ""
                  }`}
                >
                  <CheckCircle className="w-5 h-5 mr-2" />
                  {submittingApproval ? "Approving..." : "Approve & Export"}
                </button>
              </div>
            </div>
          )}

          {showExportOptions && !exportComplete && (
            <div className="card bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200">
              <div className="flex items-center mb-4">
                <Download className="w-6 h-6 text-green-600 mr-3" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Export Redlined Document
                </h3>
              </div>
              <p className="text-sm text-gray-700 mb-4">
                Select format to export the approved redlined contract and
                summary memo:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={() => handleExport("docx")}
                  disabled={exporting}
                  className={`card hover:shadow-lg transition-shadow text-center p-6 ${
                    exporting ? "opacity-70 cursor-not-allowed" : ""
                  }`}
                >
                  <FileText className="w-12 h-12 text-blue-600 mx-auto mb-3" />
                  <p className="font-semibold text-gray-900">Microsoft Word</p>
                  <p className="text-xs text-gray-600 mt-1">.DOCX format</p>
                </button>
                <button
                  onClick={() => handleExport("pdf")}
                  disabled={exporting}
                  className={`card hover:shadow-lg transition-shadow text-center p-6 ${
                    exporting ? "opacity-70 cursor-not-allowed" : ""
                  }`}
                >
                  <FileText className="w-12 h-12 text-red-600 mx-auto mb-3" />
                  <p className="font-semibold text-gray-900">PDF</p>
                  <p className="text-xs text-gray-600 mt-1">
                    Portable Document Format
                  </p>
                </button>
                <button
                  onClick={() => handleExport("md")}
                  disabled={exporting}
                  className={`card hover:shadow-lg transition-shadow text-center p-6 ${
                    exporting ? "opacity-70 cursor-not-allowed" : ""
                  }`}
                >
                  <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                  <p className="font-semibold text-gray-900">Markdown</p>
                  <p className="text-xs text-gray-600 mt-1">.MD format</p>
                </button>
              </div>
            </div>
          )}

          {exportComplete && (
            <div className="card bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200">
              <div className="flex items-center mb-4">
                <CheckCircle className="w-8 h-8 text-green-600 mr-3" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Export Complete!
                  </h3>
                  <p className="text-sm text-gray-600">
                    Your redlined document is ready for download
                  </p>
                </div>
              </div>
              <div className="space-y-3">
                <div className="bg-white p-4 rounded-lg">
                  <p className="text-sm font-semibold text-gray-700 mb-2">
                    Generated Files:
                  </p>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li className="flex items-center justify-between">
                      <span className="flex items-center">
                        <FileText className="w-4 h-4 mr-2 text-blue-600" />
                        Redlined_Document.docx
                      </span>
                      <button className="text-primary-600 hover:text-primary-700 font-medium">
                        Download
                      </button>
                    </li>
                    <li className="flex items-center justify-between">
                      <span className="flex items-center">
                        <FileText className="w-4 h-4 mr-2 text-blue-600" />
                        Summary_Memo.pdf
                      </span>
                      <button className="text-primary-600 hover:text-primary-700 font-medium">
                        Download
                      </button>
                    </li>
                    <li className="flex items-center justify-between">
                      <span className="flex items-center">
                        <FileText className="w-4 h-4 mr-2 text-blue-600" />
                        Decision_Card.csv
                      </span>
                      <button className="text-primary-600 hover:text-primary-700 font-medium">
                        Download
                      </button>
                    </li>
                  </ul>
                </div>
                <div className="flex space-x-3">
                  <Link
                    href={`/run/${redlineDetails.run_id}`}
                    className="btn-primary flex items-center"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View Run Details
                  </Link>
                  <Link href="/reports" className="btn-secondary flex items-center">
                    <ArrowRight className="w-4 h-4 mr-2" />
                    Go to Reports
                  </Link>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {!redlineDetails && !detailsLoading && (
        <div className="card text-center py-12">
          <CheckCircle className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-gray-600 mb-2">No review selected</p>
          <p className="text-sm text-gray-500">
            Select a pending review from the list above to begin final approval
          </p>
        </div>
      )}
    </div>
  );
}
