"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { exportFinal } from "@/lib/api";

export default function FinalExportPage() {
  const params = useParams<{ run_id: string }>();
  const runId = params?.run_id as string;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const resp = await exportFinal(runId);
        setData(resp);
      } catch (e: any) {
        setError(e?.message || "Failed to load final export");
      } finally {
        setLoading(false);
      }
    };
    if (runId) load();
  }, [runId]);

  const handleCopy = async () => {
    if (data?.content) {
      await navigator.clipboard.writeText(data.content);
      alert("Final document copied to clipboard");
    }
  };

  const handleDownload = () => {
    if (!data?.content) return;
    const blob = new Blob([data.content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `run_${runId}_final.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-4 text-gray-800">Final Document</h1>
      <p className="text-sm text-gray-600 mb-6">Run ID: {runId}</p>

      {loading && (
        <div className="bg-white rounded-lg shadow p-6">Loading final document...</div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded p-4">{error}</div>
      )}

      {data && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3 items-center">
            <button onClick={handleCopy} className="bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700">
              Copy
            </button>
            <button onClick={handleDownload} className="bg-gray-700 text-white px-3 py-2 rounded text-sm hover:bg-gray-800">
              Download
            </button>
            <a href={`/export/${runId}/redline`} className="ml-auto text-sm text-blue-700 hover:underline">
              View Redline →
            </a>
          </div>
          <div className="bg-white rounded-lg shadow p-4 overflow-auto">
            <div className="text-xs text-gray-600 mb-2">
              Redactions Applied: <strong>{data.redactions_applied}</strong> · Risk Level: <strong>{data.risk_level}</strong>
            </div>
            <pre className="whitespace-pre-wrap text-sm">{data.content}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

