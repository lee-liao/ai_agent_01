"use client"
import { useState } from 'react'
import { api } from '../../lib/api'

export default function RunPage() {
	const [runId, setRunId] = useState<string>("")
	const [loading, setLoading] = useState(false)
	return (
		<main style={{ padding: 24 }}>
			<h2>Run Orchestrator</h2>
			<button disabled={loading} onClick={async () => {
				setLoading(true)
				try {
					const res = await api.run({ doc_id: 'nda' })
					setRunId(res.run_id)
				} finally {
					setLoading(false)
				}
			}}>
				{loading ? 'Starting...' : 'Start Run'}
			</button>
			{runId && <p>Run started: <b>{runId}</b></p>}
		</main>
	)
}
