"use client"

import React, { useEffect, useState } from 'react'
import { api, PromptVersion, apiClient } from '@/lib/api'
import { parseDiff, Diff, Hunk } from 'react-diff-view'
import 'react-diff-view/style/index.css'

export default function PromptsPage() {
  const [promptId, setPromptId] = useState('agent_planner')
  const [versions, setVersions] = useState<PromptVersion[]>([])
  const [template, setTemplate] = useState('')
  const [changelog, setChangelog] = useState('')
  const [strategy, setStrategy] = useState<'fixed' | 'ab'>('fixed')
  const [activeVersion, setActiveVersion] = useState<number | undefined>(undefined)
  const [abAltVersion, setAbAltVersion] = useState<number | undefined>(undefined)
  const [trafficSplit, setTrafficSplit] = useState<number>(10)
  const [loading, setLoading] = useState(false)
  const [selectedVersions, setSelectedVersions] = useState<number[]>([])
  const [diff, setDiff] = useState<any[] | null>(null)
  const [diffInfo, setDiffInfo] = useState<{v1: number, v2: number} | null>(null)
  const [viewTemplate, setViewTemplate] = useState<string | null>(null)

  useEffect(() => {
    if (strategy === 'fixed') {
      setAbAltVersion(undefined)
      setTrafficSplit(0)
    }
  }, [strategy])

  async function refresh() {
    if (!promptId) return
    const [versionsRes, statsRes] = await Promise.all([
      api.listPromptVersions(promptId),
      api.getPromptStats(promptId),
    ])
    console.log("versionsRes:", versionsRes)
    console.log("statsRes:", statsRes)
    const statsMap = new Map(statsRes.stats.map((s: any) => [s.version, s]))
    setVersions(versionsRes.versions.map(v => ({ ...v, stats: statsMap.get(v.version) })))
  }

  useEffect(() => {
    refresh().catch(() => {})
  }, [promptId])

  async function createVersion() {
    setLoading(true)
    try {
      await api.createPromptVersion(promptId, { template, changelog, created_by: 'instructor' })
      setTemplate('')
      setChangelog('')
      await refresh()
    } finally {
      setLoading(false)
    }
  }

  async function deploy() {
    const maxVersion = versions.length > 0 ? Math.max(...versions.map(v => v.version)) : 0

    if (strategy === 'fixed') {
      if (!activeVersion) {
        alert('Please select an active version for the fixed strategy.')
        return
      }
      if (activeVersion > maxVersion) {
        alert(`Active version cannot be greater than the maximum available version (${maxVersion}).`)
        return
      }
    } else if (strategy === 'ab') {
      if (!activeVersion || !abAltVersion) {
        alert('Please select both active and alt versions for A/B strategy.')
        return
      }
      if (activeVersion > maxVersion || abAltVersion > maxVersion) {
        alert(`Active or Alt version cannot be greater than the maximum available version (${maxVersion}).`)
        return
      }
      if (activeVersion === abAltVersion) {
        alert('Active version and Alt version cannot be the same.')
        return
      }
    }

    setLoading(true)
    try {
      const data = {
        env: 'development',
        strategy,
        active_version: activeVersion,
        ab_alt_version: abAltVersion,
        traffic_split: strategy === 'ab' ? trafficSplit : 0,
      }
      await api.deployPrompt(promptId, data)
      alert('Deploy updated')
    } finally {
      setLoading(false)
    }
  }

  function handleVersionSelect(version: number) {
    setSelectedVersions(prev => {
      if (prev.includes(version)) {
        return prev.filter(v => v !== version)
      } else if (prev.length < 2) {
        return [...prev, version]
      }
      return prev
    })
  }

  async function compareVersions() {
    if (selectedVersions.length !== 2) return
    const [v1, v2] = selectedVersions.sort((a, b) => a - b)
    const diffResult = await api.getPromptDiff(promptId, v1, v2)
    const patch = `--- a/v${v1}.txt
+++ b/v${v2}.txt
@@ -1,1 +1,1 @@
- ${diffResult.v1.template || ''}
+ ${diffResult.v2.template || ''}`
    const files = parseDiff(patch)
    setDiff(files)
    setDiffInfo({v1, v2})
  }

  const renderFile = ({ oldRevision, newRevision, type, hunks }: any) => (
    <Diff key={oldRevision + '-' + newRevision} viewType="split" diffType={type} hunks={hunks}>
      {hunks => hunks.map(hunk => <Hunk key={hunk.content} hunk={hunk} />)}
    </Diff>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-black">Prompt Management</h1>

      {viewTemplate && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg shadow-xl w-full max-w-2xl">
            <h2 className="text-xl font-bold mb-2 text-gray-800">Prompt Template</h2>
            <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm text-gray-800">{viewTemplate}</pre>
            <button onClick={() => setViewTemplate(null)} className="mt-4 px-4 py-2 bg-black text-white rounded self-end">Close</button>
          </div>
        </div>
      )}

      {diff && diffInfo && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg shadow-xl w-full max-w-4xl h-3/4 flex flex-col">
            <h2 className="text-xl font-bold mb-2 text-gray-800">Comparing v{diffInfo.v1} and v{diffInfo.v2}</h2>
            <div className="flex-grow overflow-auto">
              {diff.map(renderFile)}
            </div>
            <button onClick={() => setDiff(null)} className="mt-4 px-4 py-2 bg-black text-white rounded self-end">Close</button>
          </div>
        </div>
      )}

      <div className="p-4 border border-black rounded bg-white space-y-3">
        <div className="flex gap-3 items-end">
          <label className="flex-1">
            <span className="text-sm text-black">Prompt ID</span>
            <input className="w-full border border-black rounded p-2 text-black" value={promptId} onChange={e => setPromptId(e.target.value)} />
          </label>
          <button onClick={refresh} className="px-3 py-2 bg-black text-white rounded">Refresh</button>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="font-medium text-black">Versions</h2>
            <button onClick={compareVersions} disabled={selectedVersions.length !== 2} className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50">Compare ({selectedVersions.length}/2)</button>
          </div>
          <div className="max-h-72 overflow-auto border border-black rounded">
            <table className="w-full text-left text-sm">
              <thead className="bg-white border-b border-black">
                <tr>
                  <th className="p-2 text-black"></th>
                  <th className="p-2 text-black">Version</th>
                  <th className="p-2 text-black">Success Rate</th>
                  <th className="p-2 text-black">Avg Cost</th>
                  <th className="p-2 text-black">Template</th>
                  <th className="p-2 text-black">Created</th>
                  <th className="p-2 text-black">Changelog</th>
                </tr>
              </thead>
              <tbody>
                {versions.map(v => (
                  <tr key={v.version} className="border-t border-black">
                    <td className="p-2 text-black"><input type="checkbox" checked={selectedVersions.includes(v.version)} onChange={() => handleVersionSelect(v.version)} /></td>
                    <td className="p-2 text-black">{v.version}</td>
                    <td className="p-2 text-black">{v.stats ? `${(v.stats.success_rate * 100).toFixed(1)}%` : 'N/A'}</td>
                    <td className="p-2 text-black">{v.stats ? `${v.stats.avg_cost.toFixed(6)}` : 'N/A'}</td>
                    <td className="p-2 text-black"><button onClick={() => setViewTemplate(v.template)} className="text-blue-600 hover:underline">View</button></td>
                    <td className="p-2 text-black">{v.created_at}</td>
                    <td className="p-2 text-black">{v.changelog}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="p-4 border border-black rounded bg-white space-y-3">
        <h2 className="font-medium text-black">Create New Version</h2>
        <label className="block">
          <span className="text-sm text-black">Template</span>
          <textarea className="w-full border border-black rounded p-2 h-40 text-black" value={template} onChange={e => setTemplate(e.target.value)} />
        </label>
        <label className="block">
          <span className="text-sm text-black">Changelog</span>
          <input className="w-full border border-black rounded p-2 text-black" value={changelog} onChange={e => setChangelog(e.target.value)} />
        </label>
        <button disabled={loading || !template} onClick={createVersion} className="px-4 py-2 bg-black text-white rounded disabled:opacity-50">Create Version</button>
      </div>

      <div className="p-4 border border-black rounded bg-white space-y-3">
        <h2 className="font-medium text-black">Deploy</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <label className="block">
            <span className="text-sm text-black">Strategy</span>
            <select className="w-full border border-black rounded p-2 text-black" value={strategy} onChange={e => setStrategy(e.target.value as any)}>
              <option value="fixed">fixed</option>
              <option value="ab">ab</option>
            </select>
          </label>
          <label className="block">
            <span className="text-sm text-black">Active Version</span>
            <input type="number" className="w-full border border-black rounded p-2 text-black" value={activeVersion ?? ''} onChange={e => setActiveVersion(e.target.value ? parseInt(e.target.value) : undefined)} />
          </label>
          {strategy === 'ab' && (
            <>
              <label className="block">
                <span className="text-sm text-black">Alt Version</span>
                <input type="number" className="w-full border border-black rounded p-2 text-black" value={abAltVersion ?? ''} onChange={e => setAbAltVersion(e.target.value ? parseInt(e.target.value) : undefined)} />
              </label>
              <label className="block">
                <span className="text-sm text-black">Traffic %</span>
                <input type="number" className="w-full border border-black rounded p-2 text-black" value={trafficSplit} onChange={e => setTrafficSplit(parseInt(e.target.value || '0'))} />
              </label>
            </>
          )}
        </div>
        <button disabled={loading} onClick={deploy} className="px-4 py-2 bg-black text-white rounded disabled:opacity-50">Update Deploy</button>
      </div>
    </div>
  )
}