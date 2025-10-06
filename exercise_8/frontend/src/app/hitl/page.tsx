"use client"
import { useEffect, useState } from 'react'

export default function RiskGate() {
	const [runId, setRunId] = useState<string>("")
	const [items, setItems] = useState<any[]>([])
	return (
		<main style={{ padding: 24 }}>
			<h2>Risk Gate</h2>
			<p>Approve/Downgrade/Request rework at risk gate (stub).</p>
			<input placeholder="run_id" value={runId} onChange={e => setRunId(e.target.value)} />
			<button>Refresh</button>
			<table>
				<thead>
					<tr><th>Clause</th><th>Risk</th><th>Rationale</th><th>Policy Refs</th><th>Action</th></tr>
				</thead>
				<tbody>
					{items.map((it, i) => (
						<tr key={i}><td>{it.clause_id}</td><td>{it.risk}</td><td>{it.rationale}</td><td>{(it.policy_refs||[]).join(', ')}</td><td><button>Approve</button></td></tr>
					))}
				</tbody>
			</table>
		</main>
	)
}
