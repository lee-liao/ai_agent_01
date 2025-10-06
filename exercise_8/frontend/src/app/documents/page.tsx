"use client"
import { useEffect, useState } from 'react'
import { api } from '../../lib/api'

export default function DocumentsPage() {
	const [docs, setDocs] = useState<any[]>([])
	const [file, setFile] = useState<File | null>(null)
	const refresh = async () => {
		const list = await api.listDocs()
		setDocs(list)
	}
	useEffect(() => { refresh() }, [])
	return (
		<main style={{ padding: 24 }}>
			<h2>Documents</h2>
			<input type="file" onChange={e => setFile(e.target.files?.[0] || null)} />
			<button disabled={!file} onClick={async () => {
				if (!file) return
				await api.uploadDoc(file)
				setFile(null)
				await refresh()
			}}>Upload</button>
			<ul>
				{docs.map((d:any) => (<li key={d.doc_id}>{d.name} <code>{d.doc_id}</code></li>))}
			</ul>
		</main>
	)
}
