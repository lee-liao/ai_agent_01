"use client"

import React, { useEffect, useState } from 'react'
import { api, PromptVersion, apiClient } from '@/lib/api'
import { parseDiff, Diff, Hunk } from 'react-diff-view'
import 'react-diff-view/style/index.css'

export default function PromptsPage() {
  const [promptId, setPromptId] = useState('agent_planner')
  const [prompts, setPrompts] = useState<{id: string, variables: any}[]>([])
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
  // State for current deployment information
  const [currentDeployment, setCurrentDeployment] = useState<any>(null)
  // State for test prompts tab
  const [activeTab, setActiveTab] = useState<'versions' | 'deploy' | 'test'>('versions')
  const [promptVariables, setPromptVariables] = useState<any[]>([])
  const [variableInputs, setVariableInputs] = useState<Record<string, string>>({})
  const [callCount, setCallCount] = useState(0)
  const [responses, setResponses] = useState<any[]>([])
  const [testLoading, setTestLoading] = useState(false)
  const [warning, setWarning] = useState<string | null>(null)

  useEffect(() => {
    if (strategy === 'fixed') {
      setAbAltVersion(undefined)
      setTrafficSplit(0)
    }
  }, [strategy])

  useEffect(() => {
    refreshPrompts().then(() => {
      refresh().catch(() => {})
    }).catch(() => {})
  }, []);

  useEffect(() => {
    refresh().catch(error => {
      console.error('Failed to refresh data for prompt:', promptId, error);
    });
  }, [promptId]);

  async function refreshPrompts() {
    const res = await api.listPrompts()
    setPrompts(res.prompts || [])
    
    // Only set default variables JSON if prompt exists and variablesJson is empty
    const currentPrompt = res.prompts?.find((p: any) => p.id === promptId)
    if (currentPrompt && !variablesJson) {
      setVariablesJson(JSON.stringify(currentPrompt.variables ?? [], null, 2))
    }
  }

  async function refresh() {
    if (!promptId) return
    
    // Get prompt versions
    let versionsData = []
    try {
      const res = await api.listPromptVersions(promptId)
      versionsData = res.versions || []
      setVersions(versionsData)
    } catch (e) {
      console.error('Error getting prompt versions:', e);
      setVersions([])
    }
    
    // Get prompt stats
    try {
      const statsRes = await api.getPromptStats(promptId)
      const statsMap = {}
      if (statsRes.stats) {
        statsRes.stats.forEach(stat => {
          statsMap[stat.version] = stat
        })
      }
      
      // Merge stats with versions
      const versionsWithStats = versionsData.map(version => ({
        ...version,
        stats: statsMap[version.version] || null
      }))
      
      setVersions(versionsWithStats)
    } catch (e) {
      console.error('Error getting prompt stats:', e);
    }
    
    // Get prompt variables
    try {
      const promptRes = await api.getPrompt(promptId)
      setVariablesJson(JSON.stringify(promptRes.variables ?? [], null, 2))
      setPromptVariables(promptRes.variables ?? [])
      // Initialize variable inputs with empty values
      const initialInputs: Record<string, string> = {};
      (promptRes.variables ?? []).forEach((variable: any) => {
        initialInputs[variable.name] = ''
      })
      setVariableInputs(initialInputs)
    } catch (e) {
      console.error('Error getting prompt variables:', e);
      // Only set to empty array if it's a 404 error
      // For other errors, keep the previous value
    }
    
    // Get current deployment
    try {
      const deployment = await api.getCurrentDeployment(promptId, 'development')
      setCurrentDeployment(deployment)
      setStrategy(deployment.strategy as 'fixed' | 'ab')
      setActiveVersion(deployment.active_version)
      setAbAltVersion(deployment.ab_alt_version || undefined)
      setTrafficSplit(deployment.traffic_split || 0)
    } catch (e) {
      console.error('Error getting deployment:', e);
      // No deployment found
      setCurrentDeployment(null)
    }
  }

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
    setEditMode('create')
    setEditingVersion(null)
    setEditTemplate('')
    setEditChangelog('')
  }

  // Function to open the edit modal for editing an existing version
  function openEditModal(version: PromptVersion) {
    setEditMode('edit')
    setEditingVersion(version)
    setEditTemplate(version.template)
    setEditChangelog(version.changelog || '')
  }

  // Function to save the edited or new version
  async function saveVersion() {
    
    if (!editTemplate) {
      alert('Template is required')
      return
    }

    setLoading(true)
    try {
      if (editMode === 'create') {
        await api.createPromptVersion(promptId, { 
          template: editTemplate, 
          changelog: editChangelog, 
          created_by: 'instructor' 
        })
      } else if (editMode === 'edit' && editingVersion) {
        await api.updatePromptVersion(promptId, editingVersion.version, {
          template: editTemplate,
          changelog: editChangelog
        })
      } else {
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
      // Refresh deployment information
      await refresh()
    } finally {
      setLoading(false)
    }
  }

  // Function to handle prompt testing
  async function handleTestSubmit() {
    // Validate required variables
    const missingRequired = promptVariables.filter(
      variable => variable.required && (!variableInputs[variable.name] || variableInputs[variable.name].trim() === '')
    );
    
    if (missingRequired.length > 0) {
      alert(`Please fill in the required variables: ${missingRequired.map(v => v.name).join(', ')}`);
      return;
    }

    setTestLoading(true);
    
    try {
      // Get current deployment
      const deployment = await api.getCurrentDeployment(promptId, 'development');
      
      // For A/B testing, we need to call both versions
      let versionsToTest = [];
      
      if (deployment.strategy === 'ab') {
        versionsToTest = [deployment.active_version, deployment.ab_alt_version];
      } else {
        versionsToTest = [deployment.active_version];
      }
      
      // Get versions details
      const versionsRes = await api.listPromptVersions(promptId);
      const versionDetails = versionsRes.versions;
      
      // Track responses
      const newResponses = [];
      
      // Process each version
      for (const versionNum of versionsToTest) {
        const version = versionDetails.find(v => v.version === versionNum);
        if (!version) continue;
        
        // Parse template to extract system and inputs parts
        const template = version.template;
        const systemMatch = template.match(/System:\s*(.+?)(?=\s*Inputs:|$)/i);
        const inputsMatch = template.match(/Inputs:\s*(.+)/i);
        
        const systemPrompt = systemMatch ? systemMatch[1].trim() : '';
        let userPrompt = inputsMatch ? inputsMatch[1].trim() : '';
        
        // Replace variables in user prompt
        Object.entries(variableInputs).forEach(([key, value]) => {
          userPrompt = userPrompt.replace(new RegExp(`{${key}}`, 'g'), value);
        });
        
        // Actually call the LLM endpoint
        try {
          const response = await api.executePrompt({
            prompt_id: promptId,
            env: 'development',
            variables: variableInputs,
            version: versionNum  // Specify the version to test
          });
          
          newResponses.push({
            callId: callCount + newResponses.length + 1,
            version: versionNum,
            content: response.response,
            cost: response.cost
          });
        } catch (error) {
          console.error('Error calling LLM:', error);
          // Fallback to simulated response in case of error
          const simulatedResponse = {
            role: 'assistant',
            content: `This is a simulated response for version ${versionNum} with system prompt: "${systemPrompt}" and user input: "${userPrompt}". In a real implementation, this would be the actual LLM response.`
          };
          
          const simulatedCost = Math.random() * 0.0001;
          
          newResponses.push({
            callId: callCount + newResponses.length + 1,
            version: versionNum,
            content: simulatedResponse.content,
            cost: simulatedCost
          });
        }
        
        // Commented out the previous simulation code
        // // For now, we'll simulate the LLM call since there's no direct endpoint
        // // In a real implementation, this would call an LLM API endpoint
        // const simulatedResponse = {
        //   role: 'assistant',
        //   content: `This is a simulated response for version ${versionNum} with system prompt: "${systemPrompt}" and user input: "${userPrompt}". In a real implementation, this would be the actual LLM response.`
        // };
        // 
        // // Simulate cost (in a real implementation, this would come from the LLM API)
        // const simulatedCost = Math.random() * 0.0001;
        // 
        // // Log the call
        // // Note: We would need an endpoint to actually call the LLM and log the results
        // // For now, we'll just simulate this process
        // 
        // newResponses.push({
        //   callId: callCount + newResponses.length + 1,
        //   version: versionNum,
        //   content: simulatedResponse.content,
        //   cost: simulatedCost
        // });
        // 
        // // Log to database (in a real implementation)
        // // await api.logPromptCall({
        // //   prompt_version_id: version.id,
        // //   success: true,
        // //   cost: simulatedCost
        // // });
      }
      
      // Update state
      setResponses(prev => [...newResponses, ...prev]);
      setCallCount(prev => prev + newResponses.length);
      
      // Check for pricing warning in A/B testing
      if (deployment.strategy === 'ab' && versionDetails.length >= 2) {
        const activeVersionDetail = versionDetails.find(v => v.version === deployment.active_version);
        const altVersionDetail = versionDetails.find(v => v.version === deployment.ab_alt_version);
        
        if (activeVersionDetail?.stats && altVersionDetail?.stats) {
          const activeCost = activeVersionDetail.stats.avg_cost;
          const altCost = altVersionDetail.stats.avg_cost;
          
          if (altCost > activeCost * 1.05) {
            setWarning('The deployed prompt version will be rolled back to strategy \'fix\'');
          } else {
            setWarning(null);
          }
        }
      }
    } catch (error) {
      console.error('Error testing prompt:', error);
      alert('Error testing prompt. Check console for details.');
    } finally {
      setTestLoading(false);
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
          <button onClick={refresh} className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Refresh</button>
        </div>

        {/* Variables Editor */}
        <div className="flex gap-3 items-end">
          <label className="flex-1">
            <span className="text-sm text-black">Prompt Variables</span>
            <div className="relative">
              <pre 
                onClick={() => setEditingVariables(true)}
                className="bg-blue-50 p-4 rounded overflow-auto text-sm text-gray-800 max-h-32 overflow-y-auto min-h-[128px] whitespace-pre-wrap break-words cursor-pointer hover:bg-blue-100 border border-blue-200"
              >
                {variablesJson}
              </pre>
            </div>
          </label>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'versions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('versions')}
          >
            Versions
          </button>
          <button
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'deploy'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('deploy')}
          >
            Deployment
          </button>
          <button
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'test'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('test')}
          >
            Test Prompts
          </button>
        </nav>
      </div>

      {/* Versions Tab */}
      {activeTab === 'versions' && (
        <div className="p-4 border border-black rounded bg-white space-y-3">
          <div>
            <div className="flex justify-between items-center mb-2">
              <h2 className="font-medium text-black">Versions</h2>
              <div className="flex gap-2">
                <button 
                  onClick={openCreateModal}
                  className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  New
                </button>
                <button 
                  onClick={compareVersions} 
                  disabled={selectedVersions.length !== 2} 
                  className="px-3 py-1 bg-blue-500 text-white rounded disabled:opacity-50 hover:bg-blue-600"
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
                            className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
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
      )}

      {/* Deployment Tab */}
      {activeTab === 'deploy' && (
        <div className="p-4 border border-black rounded bg-white space-y-3">
          <h2 className="font-medium text-black">Deployment</h2>
          {currentDeployment && (
            <div className="bg-blue-50 p-3 rounded border border-blue-200">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2 text-sm">
                <div>
                  <span className="text-gray-600">Strategy:</span>
                  <span className="ml-2 font-medium">{currentDeployment.strategy}</span>
                </div>
                <div>
                  <span className="text-gray-600">Active Version:</span>
                  <span className="ml-2 font-medium">{currentDeployment.active_version}</span>
                </div>
                {currentDeployment.strategy === 'ab' && (
                  <>
                    <div>
                      <span className="text-gray-600">Alt Version:</span>
                      <span className="ml-2 font-medium">{currentDeployment.ab_alt_version}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Traffic Split:</span>
                      <span className="ml-2 font-medium">{currentDeployment.traffic_split}%</span>
                    </div>
                  </>
                )}
                <div>
                  <span className="text-gray-600">Last Updated:</span>
                  <span className="ml-2 font-medium">
                    {new Date(currentDeployment.updated_at).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          )}
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
          <button disabled={loading} onClick={deploy} className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50 hover:bg-blue-600">Update Deploy</button>
        </div>
      )}

      {/* Test Prompts Tab */}
      {activeTab === 'test' && (
        <div className="p-4 border border-black rounded bg-white space-y-6">
          <h2 className="font-medium text-black">Test Prompts</h2>
          
          {warning && (
            <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative" role="alert">
              <strong className="font-bold">Warning: </strong>
              <span className="block sm:inline">{warning}</span>
            </div>
          )}
          
          {/* Variable Inputs */}
          <div className="space-y-4">
            <h3 className="font-medium text-black">Prompt Variables</h3>
            {promptVariables.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {promptVariables.map((variable) => (
                  <div key={variable.name} className="space-y-1">
                    <label className="block text-sm font-medium text-gray-700">
                      {variable.name} {variable.required && <span className="text-red-500">*</span>}
                      <span className="block text-xs font-normal text-gray-500">{variable.description}</span>
                    </label>
                    <input
                      type="text"
                      value={variableInputs[variable.name] || ''}
                      onChange={(e) => setVariableInputs(prev => ({
                        ...prev,
                        [variable.name]: e.target.value
                      }))}
                      className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm ${
                        variable.required ? 'border-red-300' : 'border-gray-300'
                      }`}
                      placeholder={variable.description}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No variables defined for this prompt.</p>
            )}
          </div>
          
          {/* Submit Section */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm text-gray-600">
                Calls made: {callCount}
              </span>
            </div>
            <button
              disabled={testLoading}
              onClick={handleTestSubmit}
              className="px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50 hover:bg-green-700 flex items-center"
            >
              {testLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Testing...
                </>
              ) : (
                'Test Prompt'
              )}
            </button>
          </div>
          
          {/* Responses */}
          {responses.length > 0 && (
            <div className="space-y-4">
              <h3 className="font-medium text-black">Responses</h3>
              <div className="max-h-96 overflow-y-auto border border-gray-200 rounded">
                {responses.map((response, index) => (
                  <div key={index} className="border-b border-gray-200 p-4 hover:bg-gray-50">
                    <div className="flex justify-between">
                      <div className="font-medium text-gray-900">
                        Call #{response.callId} - Version {response.version}
                      </div>
                      <div className="text-sm text-gray-500">
                        Cost: ${response.cost.toFixed(6)}
                      </div>
                    </div>
                    <div className="mt-2">
                      <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-100 p-2 rounded">
                        {response.content}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

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
                className="px-4 py-2 bg-gray-300 text-black rounded hover:bg-gray-400"
              >
                Cancel
              </button>
              <button 
                onClick={updateVariables}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
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
            <button onClick={() => setViewTemplate(null)} className="mt-4 px-4 py-2 bg-blue-500 text-white rounded self-end hover:bg-blue-600">Close</button>
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
            <button onClick={() => setDiff(null)} className="mt-4 px-4 py-2 bg-blue-500 text-white rounded self-end hover:bg-blue-600">Close</button>
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
                className="px-4 py-2 bg-gray-300 text-black rounded hover:bg-gray-400"
              >
                Cancel
              </button>
              <button 
                disabled={loading || !editTemplate}
                onClick={saveVersion}
                className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50 hover:bg-blue-600"
              >
                {loading ? 'Saving...' : 'Save Version'}
              </button>
            </div>
          </div>
        </div>
      ) : null}

    </div>
  )
}