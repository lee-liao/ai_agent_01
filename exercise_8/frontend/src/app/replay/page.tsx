"use client"
import { useState } from 'react'
import { api } from '../../lib/api'

export default function ReplayPage() {
	const [runId, setRunId] = useState<string>("")
	const [newId, setNewId] = useState<string>("")
	return (
		<main style={{ padding: 24 }}>
			<h2>Replay</h2>
			<input placeholder="run_id" value={runId} onChange={e => setRunId(e.target.value)} />
			<button onClick={async () => {
				const res = await api.replay(runId)
				setNewId(res.run_id)
			}}>Replay</button>
			{newId && <p>Replayed to: {newId}</p>}
		</main>
	)
}
