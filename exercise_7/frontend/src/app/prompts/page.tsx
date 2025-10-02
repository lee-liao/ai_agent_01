"use client"

import React, { useEffect, useState } from 'react'
import { api, PromptVersion, apiClient } from '@/lib/api'
import { parseDiff, Diff, Hunk } from 'react-diff-view'
import 'react-diff-view/style/index.css'

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<{id: string, variables: any}[]>([])
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
  const [editingVariables, setEditingVariables] = useState(false)
  const [variablesJson, setVariablesJson] = useState('')
  // State variables for prompt template editing
  const [editingVersion, setEditingVersion] = useState<PromptVersion | null>(null)
  const [editTemplate, setEditTemplate] = useState('')
  const [editChangelog, setEditChangelog] = useState('')
  const [editMode, setEditMode] = useState<'create' | 'edit' | null>(null)

  useEffect(() => {
    if (strategy === 'fixed') {
      setAbAltVersion(undefined)
      setTrafficSplit(0)
    }
  }, [strategy])

  useEffect(() => {
    refreshPrompts().catch(() => {})
  }, [])

  async function refreshPrompts() {
    const res = await api.listPrompts()
    setPrompts(res.prompts || [])
    
    // Set default variables JSON if prompt exists
    const currentPrompt = res.prompts?.find((p: any) => p.id === promptId)
    if (currentPrompt) {
      setVariablesJson(JSON.stringify(currentPrompt.variables ?? [], null, 2))
    }
  }

  async function refresh() {
    if (!promptId) return
    const res = await api.listPromptVersions(promptId)
    setVersions(res.versions || [])
    
    // Get prompt variables
    try {
      const promptRes = await api.getPrompt(promptId)
      setVariablesJson(JSON.stringify(promptRes.variables ?? [], null, 2))
    } catch (e) {
      // Prompt not found, set empty variables
      setVariablesJson(JSON.stringify([], null, 2))
    }
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
      await refreshPrompts() // Refresh the prompts list in case a new one was created
    } finally {
      setLoading(false)
    }
  }

  // Function to open the edit modal for creating a new version
  function openCreateModal() {
    console.log('openCreateModal called');
    setEditMode('create')
    setEditingVersion(null)
    setEditTemplate('')
    setEditChangelog('')
  }

  // Function to open the edit modal for editing an existing version
  function openEditModal(version: PromptVersion) {
    console.log('openEditModal called with version:', version);
    setEditMode('edit')
    setEditingVersion(version)
    setEditTemplate(version.template)
    setEditChangelog(version.changelog || '')
  }

  // Function to save the edited or new version
  async function saveVersion() {
    console.log('Save function called with state:', { editMode, editingVersion, editTemplate, editChangelog });
    
    if (!editTemplate) {
      alert('Template is required')
      return
    }

    setLoading(true)
    try {
      if (editMode === 'create') {
        console.log('Creating new version with data:', { 
          promptId, 
          template: editTemplate, 
          changelog: editChangelog,
          created_by: 'instructor' 
        });
        
        await api.createPromptVersion(promptId, { 
          template: editTemplate, 
          changelog: editChangelog, 
          created_by: 'instructor' 
        })
      } else if (editMode === 'edit' && editingVersion) {
        console.log('Updating existing version with data:', { 
          promptId, 
          version: editingVersion.version,
          template: editTemplate,
          changelog: editChangelog
        });
        
        await api.updatePromptVersion(promptId, editingVersion.version, {
          template: editTemplate,
          changelog: editChangelog
        })
      } else {
        console.log('Unexpected state - neither creating nor editing');
        alert('Unexpected state - neither creating nor editing')
        return
      }
      
      // Close the modal and refresh the data
      setEditMode(null)
      setEditingVersion(null)
      await refresh()
      await refreshPrompts()
    } catch (error) {
      console.error('Failed to save version:', error)
      alert('Failed to save version')
    } finally {
      setLoading(false)
    }
  }

  // Function to delete a version
  async function deleteVersion(versionId: number) {
    if (!confirm(`Are you sure you want to delete version ${versionId}? This action cannot be undone.`)) {
      return;
    }
    
    try {
      await api.deletePromptVersion(promptId, versionId)
      await refresh() // Refresh the versions list after deletion
      alert(`Version ${versionId} deleted successfully`)
    } catch (error) {
      console.error('Failed to delete version:', error)
      alert('Failed to delete version')
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

  const updateVariables = async () => {
    if (!promptId) return
    try {
      const parsed = JSON.parse(variablesJson)
      // Wrap the parsed data in a variables object
      await api.updatePromptVariables(promptId, { variables: parsed })
      setEditingVariables(false)
      refresh()
    } catch (e) {
      console.error('Failed to parse or update variables:', e)
      alert('Failed to parse or update variables')
    }
  }

  function handlePromptIdChange(e: React.ChangeEvent<HTMLSelectElement>) {
    setPromptId(e.target.value)
  }

  function handlePromptIdInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    setPromptId(e.target.value)
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

      <div className="p-4 border border-black rounded bg-white space-y-3">
        <div className="flex gap-3 items-end">
          <label className="flex-1">
            <span className="text-sm text-black">Prompt ID</span>
            <select 
              value={promptId} 
              onChange={(e) => setPromptId(e.target.value)}
              className="w-full border border-black rounded p-2 text-black"
            >
              {prompts.map((prompt: any) => (
                <option key={prompt.id} value={prompt.id}>
                  {prompt.id}
                </option>
              ))}
            </select>
          </label>
          <button onClick={refresh} className="px-3 py-2 bg-black text-white rounded">Refresh</button>
        </div>

        {/* Variables Editor */}
        <div className="flex gap-3 items-end">
          <label className="flex-1">
            <span className="text-sm text-black">Prompt Variables</span>
            <div className="relative">
              <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm text-gray-800 max-h-32 overflow-y-auto min-h-[128px] whitespace-pre-wrap break-words">
                {variablesJson}
              </pre>
              <button 
                onClick={() => setEditingVariables(true)}
                className="absolute top-2 right-2 px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 z-10"
              >
                Edit
              </button>
            </div>
          </label>
        </div>
      </div>

      <div className="p-4 border border-black rounded bg-white space-y-3">
        <div>
          <div className="flex justify-between items-center mb-2">
            <h2 className="font-medium text-black">Versions</h2>
            <div className="flex gap-2">
              <button 
                onClick={openCreateModal}
                className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
              >
                New
              </button>
              <button 
                onClick={compareVersions} 
                disabled={selectedVersions.length !== 2} 
                className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50"
              >
                Compare ({selectedVersions.length}/2)
              </button>
            </div>
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
                  <th className="p-2 text-black">Actions</th>
                </tr>
              </thead>
              <tbody>
                {versions.map(v => (
                  <tr key={v.version} className="border-t border-black">
                    <td className="p-2 text-black">
                      <input 
                        type="checkbox" 
                        checked={selectedVersions.includes(v.version)} 
                        onChange={() => handleVersionSelect(v.version)} 
                      />
                    </td>
                    <td className="p-2 text-black">{v.version}</td>
                    <td className="p-2 text-black">{v.stats ? `${(v.stats.success_rate * 100).toFixed(1)}%` : 'N/A'}</td>
                    <td className="p-2 text-black">{v.stats ? `${v.stats.avg_cost.toFixed(6)}` : 'N/A'}</td>
                    <td className="p-2 text-black">
                      <button 
                        onClick={() => setViewTemplate(v.template)} 
                        className="text-blue-600 hover:underline"
                      >
                        View
                      </button>
                    </td>
                    <td className="p-2 text-black">{v.created_at}</td>
                    <td className="p-2 text-black">{v.changelog}</td>
                    <td className="p-2 text-black">
                      <div className="flex gap-2">
                        <button 
                          onClick={() => openEditModal(v)}
                          className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
                        >
                          Edit
                        </button>
                        <button 
                          onClick={() => deleteVersion(v.version)}
                          className="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {editingVariables && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg shadow-xl w-full max-w-2xl border border-gray-300">
            <h2 className="text-xl font-bold mb-2 text-gray-800">Edit Prompt Variables</h2>
            <textarea
              value={variablesJson}
              onChange={(e) => setVariablesJson(e.target.value)}
              className="w-full h-64 font-mono text-sm p-2 border border-gray-300 rounded"
              placeholder='{ "variables": [ { "name": "variable_name", "type": "string", "required": true } ] }'
            />
            <div className="flex justify-end gap-2 mt-4">
              <button 
                onClick={() => setEditingVariables(false)}
                className="px-4 py-2 bg-gray-300 text-black rounded"
              >
                Cancel
              </button>
              <button 
                onClick={updateVariables}
                className="px-4 py-2 bg-black text-white rounded"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {viewTemplate && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg shadow-xl w-full max-w-2xl border border-gray-300">
            <h2 className="text-xl font-bold mb-2 text-gray-800">Prompt Template</h2>
            <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm text-gray-800 border border-gray-200">{viewTemplate}</pre>
            <button onClick={() => setViewTemplate(null)} className="mt-4 px-4 py-2 bg-black text-white rounded self-end">Close</button>
          </div>
        </div>
      )}

      {diff && diffInfo && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg shadow-xl w-full max-w-4xl h-3/4 flex flex-col border border-gray-300">
            <h2 className="text-xl font-bold mb-2 text-gray-800">Comparing v{diffInfo.v1} and v{diffInfo.v2}</h2>
            <div className="flex-grow overflow-auto">
              {diff.map(renderFile)}
            </div>
            <button onClick={() => setDiff(null)} className="mt-4 px-4 py-2 bg-black text-white rounded self-end">Close</button>
          </div>
        </div>
      )}

      {/* Edit Prompt Version Modal */}
      {editMode !== null ? (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg shadow-xl w-full max-w-2xl border border-gray-300">
            <h2 className="text-xl font-bold mb-2 text-gray-800">
              {editMode === 'create' ? 'Create New Version' : `Edit Version ${editingVersion?.version}`}
            </h2>
            <label className="block mb-3">
              <span className="text-sm text-black">Template</span>
              <textarea 
                className="w-full border border-black rounded p-2 h-40 text-black" 
                value={editTemplate} 
                onChange={e => setEditTemplate(e.target.value)} 
              />
            </label>
            <label className="block mb-3">
              <span className="text-sm text-black">Changelog</span>
              <input 
                className="w-full border border-black rounded p-2 text-black" 
                value={editChangelog} 
                onChange={e => setEditChangelog(e.target.value)} 
              />
            </label>
            <div className="flex justify-end gap-2">
              <button 
                onClick={() => {
                  setEditMode(null)
                  setEditingVersion(null)
                }}
                className="px-4 py-2 bg-gray-300 text-black rounded"
              >
                Cancel
              </button>
              <button 
                disabled={loading || !editTemplate}
                onClick={saveVersion}
                className="px-4 py-2 bg-black text-white rounded disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Version'}
              </button>
            </div>
          </div>
        </div>
      ) : null}

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