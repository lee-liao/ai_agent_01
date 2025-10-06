"use client"
import { useEffect, useState } from 'react'
import { api } from '../../../lib/api'

export default function RunDetail({ params }: { params: { id: string } }) {
	const runId = params.id
	const [run, setRun] = useState<any | null>(null)
	const refresh = async () => {
		const data = await api.getRun(runId)
		setRun(data)
	}
	useEffect(() => { refresh() }, [runId])
	return (
		<main style={{ padding: 24 }}>
			<h2>Run Detail</h2>
			<p><b>run_id:</b> {runId}</p>
			{run && (
				<>
					<p><b>doc_id:</b> {run.doc_id} &nbsp; <b>agent_path:</b> {run.agent_path} &nbsp; <b>score:</b> {run.score}</p>
					<h3>Timeline</h3>
					<ol>
						{(run.history||[]).map((h:any,i:number)=>(<li key={i}><b>{h.step}</b> – {h.agent} – {h.status}</li>))}
					</ol>
					<h3>Assessments</h3>
					<table>
						<thead><tr><th>Clause</th><th>Risk</th><th>Rationale</th><th>Policy Refs</th></tr></thead>
						<tbody>
							{(run.assessments||[]).map((a:any)=>(<tr key={a.clause_id}><td>{a.clause_id}</td><td>{a.risk_level}</td><td>{a.rationale}</td><td>{(a.policy_refs||[]).join(', ')}</td></tr>))}
						</tbody>
					</table>
					<h3>Proposals</h3>
					<ul>
						{(run.proposals||[]).map((p:any,i:number)=>(<li key={i}><b>{p.clause_id}</b> [{p.variant}]: {p.edited_text}</li>))}
					</ul>
				</>
			)}
		</main>
	)
}
