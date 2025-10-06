"use client"
import { useState } from 'react'
import { api } from '../../lib/api'

export default function FinalGate() {
	const [runId, setRunId] = useState<string>("")
	const [note, setNote] = useState<string>("")
	const [artifact, setArtifact] = useState<string>("")
	return (
		<main style={{ padding: 24 }}>
			<h2>Final Redline Gate</h2>
			<input placeholder="run_id" value={runId} onChange={e => setRunId(e.target.value)} />
			<input placeholder="note" value={note} onChange={e => setNote(e.target.value)} />
			<div>
				<button onClick={async () => {
					await api.finalApprove({ run_id: runId, note })
					const res = await api.exportRedline(runId, 'md')
					setArtifact(res.artifact_uri)
				}}>Approve & Export</button>
			</div>
			{artifact && <p>Exported: {artifact}</p>}
		</main>
	)
}
