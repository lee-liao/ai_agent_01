"use client"
import { useEffect, useState } from 'react'
import { api } from '../../lib/api'

export default function ReportsPage() {
	const [data, setData] = useState<any>(null)
	useEffect(() => {
		api.reportSLOs().then(setData).catch(() => setData(null))
	}, [])
	return (
		<main style={{ padding: 24 }}>
			<h2>Reports</h2>
			{data ? (
				<ul>
					<li>P50 latency: {data.p50_ms} ms</li>
					<li>P95 latency: {data.p95_ms} ms</li>
					<li>Reviewer pass-rate: {Math.round((data.reviewer_pass_rate||0)*100)}%</li>
					<li>Cost: ${data.cost_usd}</li>
				</ul>
			) : (
				<p>Loading…</p>
			)}
		</main>
	)
}
