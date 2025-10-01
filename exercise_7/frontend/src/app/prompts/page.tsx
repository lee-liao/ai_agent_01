"use client"

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'

export default function PromptsPage() {
  const [promptId, setPromptId] = useState('agent/planner')
  const [versions, setVersions] = useState<any[]>([])
  const [template, setTemplate] = useState('')
  const [changelog, setChangelog] = useState('')
  const [strategy, setStrategy] = useState<'fixed' | 'ab'>('fixed')
  const [activeVersion, setActiveVersion] = useState<number | undefined>(undefined)
  const [abAltVersion, setAbAltVersion] = useState<number | undefined>(undefined)
  const [trafficSplit, setTrafficSplit] = useState<number>(10)
  const [loading, setLoading] = useState(false)

  async function refresh() {
    if (!promptId) return
    const res = await api.listPromptVersions(promptId)
    setVersions(res.versions || [])
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
    setLoading(true)
    try {
      await api.deployPrompt(promptId, {
        env: 'development',
        strategy,
        active_version: activeVersion,
        ab_alt_version: abAltVersion,
        traffic_split: strategy === 'ab' ? trafficSplit : 0,
      })
      alert('Deploy updated')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-black">Prompt Management</h1>

      <div className="p-4 border border-black rounded bg-white space-y-3">
        <div className="flex gap-3 items-end">
          <label className="flex-1">
            <span className="text-sm text-black">Prompt ID</span>
            <input className="w-full border border-black rounded p-2 text-black" value={promptId} onChange={e => setPromptId(e.target.value)} />
          </label>
          <button onClick={refresh} className="px-3 py-2 bg-black text-white rounded">Refresh</button>
        </div>

        <div>
          <h2 className="font-medium mb-2 text-black">Versions</h2>
          <div className="max-h-72 overflow-auto border border-black rounded">
            <table className="w-full text-left text-sm">
              <thead className="bg-white border-b border-black">
                <tr>
                  <th className="p-2 text-black">Version</th>
                  <th className="p-2 text-black">Created</th>
                  <th className="p-2 text-black">Changelog</th>
                </tr>
              </thead>
              <tbody>
                {versions.map(v => (
                  <tr key={v.version} className="border-t border-black">
                    <td className="p-2 text-black">{v.version}</td>
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