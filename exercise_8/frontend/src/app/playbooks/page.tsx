"use client"
import { useEffect, useState } from 'react'
import { api } from '../../lib/api'

export default function PlaybooksPage() {
	const [pbs, setPbs] = useState<any[]>([])
	const [name, setName] = useState('')
	const [rules, setRules] = useState('{"liability_cap":"12 months fees"}')
	const refresh = async () => {
		const list = await api.listPlaybooks()
		setPbs(list)
	}
	useEffect(() => { refresh() }, [])
	return (
		<main style={{ padding: 24 }}>
			<h2>Playbooks</h2>
			<input placeholder="name" value={name} onChange={e => setName(e.target.value)} />
			<textarea placeholder="rules (JSON)" value={rules} onChange={e => setRules(e.target.value)} />
			<button onClick={async () => {
				try { await api.createPlaybook(name, JSON.parse(rules)) } catch { return }
				setName('')
				await refresh()
			}}>Create</button>
			<ul>
				{pbs.map((p:any) => (
					<li key={p.playbook_id}>{p.name} <code>{p.playbook_id}</code> <button onClick={async () => { await api.deletePlaybook(p.playbook_id); await refresh() }}>Delete</button></li>
				))}
			</ul>
		</main>
	)
}
