"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { exportRedline } from "@/lib/api";

export default function RedlineExportPage() {
  const params = useParams<{ run_id: string }>();
  const searchParams = useSearchParams();
  const runId = params?.run_id as string;
  const format = (searchParams?.get("format") as string) || "md";

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const resp = await exportRedline(runId, format);
        setData(resp);
      } catch (e: any) {
        setError(e?.message || "Failed to load redline export");
      } finally {
        setLoading(false);
      }
    };
    if (runId) load();
  }, [runId, format]);

  const handleCopy = async () => {
    if (data?.content) {
      await navigator.clipboard.writeText(data.content);
      alert("Redline copied to clipboard");
    }
  };

  const handleDownload = () => {
    if (!data?.content) return;
    const blob = new Blob([data.content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `run_${runId}_redline.${format}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-4 text-gray-800">Redline Export</h1>
      <p className="text-sm text-gray-600 mb-6">Run ID: {runId}</p>

      {loading && (
        <div className="bg-white rounded-lg shadow p-6">Loading redline...</div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded p-4">{error}</div>
      )}

      {data && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <button onClick={handleCopy} className="bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700">
              Copy
            </button>
            <button onClick={handleDownload} className="bg-gray-700 text-white px-3 py-2 rounded text-sm hover:bg-gray-800">
              Download
            </button>
            <a href={`/export/${runId}/final`} className="ml-auto text-sm text-blue-700 hover:underline">
              View Final Document →
            </a>
          </div>
          <div className="bg-white rounded-lg shadow p-4 overflow-auto">
            <pre className="whitespace-pre-wrap text-sm">{data.content}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

