"use client"
import { useEffect, useState } from 'react'
import { api } from '../../lib/api'
import Link from 'next/link'

export default function RunPage() {
	const [docs, setDocs] = useState<any[]>([])
	const [pbs, setPbs] = useState<any[]>([])
	const [docId, setDocId] = useState<string>('')
	const [agentPath, setAgentPath] = useState<string>('manager_worker')
	const [playbookId, setPlaybookId] = useState<string>('')
	const [runId, setRunId] = useState<string>('')
	const [loading, setLoading] = useState(false)
	useEffect(() => { (async () => { setDocs(await api.listDocs()); setPbs(await api.listPlaybooks()) })() }, [])
	return (
		<main style={{ padding: 24 }}>
			<h2>Run Orchestrator</h2>
			<div>
				<label>Document: </label>
				<select value={docId} onChange={e=>setDocId(e.target.value)}>
					<option value="">(choose)</option>
					{docs.map(d => <option key={d.doc_id} value={d.doc_id}>{d.name}</option>)}
				</select>
			</div>
			<div>
				<label>Agent Path: </label>
				<select value={agentPath} onChange={e=>setAgentPath(e.target.value)}>
					<option value="manager_worker">Manager–Worker</option>
					<option value="planner_executor">Planner–Executor</option>
					<option value="reviewer_referee">Reviewer/Referee</option>
				</select>
			</div>
			<div>
				<label>Playbook: </label>
				<select value={playbookId} onChange={e=>setPlaybookId(e.target.value)}>
					<option value="">(none)</option>
					{pbs.map(p => <option key={p.playbook_id} value={p.playbook_id}>{p.name}</option>)}
				</select>
			</div>
			<button disabled={loading} onClick={async () => {
				setLoading(true)
				try {
					const res = await api.run({ doc_id: docId || undefined, agent_path: agentPath, playbook_id: playbookId || undefined })
					setRunId(res.run_id)
				} finally {
					setLoading(false)
				}
			}}>
				{loading ? 'Starting...' : 'Start Run'}
			</button>
			{runId && <p>Run started: <b>{runId}</b> – <Link href={`/run/${runId}`}>View Details</Link></p>}
		</main>
	)
}
