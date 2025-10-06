"use client"
import { useState } from 'react'
import { api } from '../../lib/api'

export default function RiskGate() {
	const [runId, setRunId] = useState<string>("")
	const [bb, setBb] = useState<any | null>(null)
	const refresh = async () => {
		if (!runId) return
		const data = await api.getBlackboard(runId)
		setBb(data)
	}
	const approveAll = async () => {
		if (!bb) return
		const items = (bb.assessments||[]).map((a: any) => ({ clause_id: a.clause_id }))
		await api.riskApprove({ run_id: runId, items })
		await refresh()
	}
	return (
		<main style={{ padding: 24 }}>
			<h2>Risk Gate</h2>
			<input placeholder="run_id" value={runId} onChange={e => setRunId(e.target.value)} />
			<button onClick={refresh}>Refresh</button>
			{bb && (
				<>
					<table>
						<thead>
							<tr><th>Clause</th><th>Risk</th><th>Rationale</th><th>Policy Refs</th></tr>
						</thead>
						<tbody>
							{(bb.assessments||[]).map((a: any) => (
								<tr key={a.clause_id}><td>{a.clause_id}</td><td>{a.risk_level}</td><td>{a.rationale}</td><td>{(a.policy_refs||[]).join(', ')}</td></tr>
							))}
						</tbody>
					</table>
					<button onClick={approveAll}>Approve All</button>
				</>
			)}
		</main>
	)
}
