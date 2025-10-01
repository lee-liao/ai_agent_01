"use client"
import React, { useState } from 'react'
import { api } from '@/lib/api'

export default function AgentConsolePage() {
  const [query, setQuery] = useState('what is the price of x?')
  const [failRate, setFailRate] = useState(0.35)
  const [budgetUsd, setBudgetUsd] = useState(0.05)
  const [model, setModel] = useState('gpt-4o-mini')
  const [injectTimeoutMs, setInjectTimeoutMs] = useState(0)
  const [cacheHitRate, setCacheHitRate] = useState(0.7)

  const [traceId, setTraceId] = useState<string>('')
  const [spans, setSpans] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  async function runTask() {
    setLoading(true)
    try {
      const overrides = {
        fail_rate: Number(failRate),
        budget_usd: Number(budgetUsd),
        model,
        inject_timeout_ms: Number(injectTimeoutMs),
        cache_hit_rate: Number(cacheHitRate),
      }
      const res = await api.agentsRun(query, overrides)
      const newTraceId = res.trace_id
      setTraceId(newTraceId)
      // poll once after a short delay
      setTimeout(async () => {
        const t = await api.getTrace(newTraceId)
        setSpans(t.spans || [])
      }, 800)
    } finally {
      setLoading(false)
    }
  }

  async function refreshTrace() {
    if (!traceId) return
    const t = await api.getTrace(traceId)
    setSpans(t.spans || [])
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-black">Agent Console</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-3 p-4 border border-black rounded-md bg-white">
          <h2 className="font-medium text-black">Run Controls</h2>
          <label className="block">
            <span className="text-sm text-black">Query</span>
            <input className="w-full border border-black rounded p-2 text-black" value={query} onChange={e => setQuery(e.target.value)} />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-sm text-black">FAIL_RATE</span>
              <input type="number" step="0.01" className="w-full border border-black rounded p-2 text-black" value={failRate} onChange={e => setFailRate(parseFloat(e.target.value))} />
            </label>
            <label className="block">
              <span className="text-sm text-black">BUDGET_USD</span>
              <input type="number" step="0.01" className="w-full border border-black rounded p-2 text-black" value={budgetUsd} onChange={e => setBudgetUsd(parseFloat(e.target.value))} />
            </label>
            <label className="block">
              <span className="text-sm text-black">MODEL</span>
              <input className="w-full border border-black rounded p-2 text-black" value={model} onChange={e => setModel(e.target.value)} />
            </label>
            <label className="block">
              <span className="text-sm text-black">INJECT_TIMEOUT_MS</span>
              <input type="number" className="w-full border border-black rounded p-2 text-black" value={injectTimeoutMs} onChange={e => setInjectTimeoutMs(parseInt(e.target.value || '0'))} />
            </label>
            <label className="block">
              <span className="text-sm text-black">CACHE_HIT_RATE</span>
              <input type="number" step="0.01" className="w-full border border-black rounded p-2 text-black" value={cacheHitRate} onChange={e => setCacheHitRate(parseFloat(e.target.value))} />
            </label>
          </div>

          <div className="flex items-center gap-3">
            <button onClick={runTask} disabled={loading} className="px-4 py-2 bg-black text-white rounded disabled:opacity-50">Run Plan</button>
            <button onClick={refreshTrace} className="px-4 py-2 bg-black text-white rounded">Refresh Trace</button>
          </div>
        </div>

        <div className="space-y-2 p-4 border border-black rounded-md bg-white">
          <h2 className="font-medium text-black">Trace</h2>
          <div className="text-sm text-black">Trace ID: <span className="font-mono text-black">{traceId || '-'}</span></div>
          <div className="max-h-96 overflow-auto border border-black rounded">
            <table className="w-full text-left text-sm">
              <thead className="bg-white border-b border-black">
                <tr>
                  <th className="p-2 text-black">Span</th>
                  <th className="p-2 text-black">Parent</th>
                  <th className="p-2 text-black">Name</th>
                  <th className="p-2 text-black">Tool</th>
                  <th className="p-2 text-black">Latency(ms)</th>
                  <th className="p-2 text-black">Retry</th>
                  <th className="p-2 text-black">Err</th>
                </tr>
              </thead>
              <tbody>
                {spans.map((s: any) => (
                  <tr key={s.span_id} className="border-t border-black">
                    <td className="p-2 font-mono text-xs text-black">{s.span_id.slice(0,8)}</td>
                    <td className="p-2 font-mono text-xs text-black">{s.parent_span_id ? s.parent_span_id.slice(0,8) : '-'}</td>
                    <td className="p-2 text-black">{s.name}</td>
                    <td className="p-2 text-black">{s.attributes?.tool_name || '-'}</td>
                    <td className="p-2 text-black">{s.attributes?.latency_ms ?? '-'}</td>
                    <td className="p-2 text-black">{s.attributes?.retry_count ?? 0}</td>
                    <td className="p-2 text-red-600">{s.attributes?.error_code || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}