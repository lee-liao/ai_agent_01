import Link from 'next/link'
export default function Page() {
	return (
		<main style={{ padding: 24 }}>
			<h1>Exercise 8 – HITL Orchestrator</h1>
			<ul>
				<li><Link href="/hitl">Risk Gate</Link></li>
				<li><Link href="/finalize">Final Gate</Link></li>
				<li><Link href="/run">Run</Link></li>
				<li><Link href="/replay">Replay</Link></li>
				<li><Link href="/reports">Reports</Link></li>
			</ul>
		</main>
	)
}
