import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8004'

export const apiClient = axios.create({
	baseURL: API_BASE_URL,
	timeout: 20000,
	headers: { 'Content-Type': 'application/json' },
})

export const api = {
	health: () => apiClient.get('/health').then(r => r.data),
	// Docs
	uploadDoc: (file: File) => {
		const fd = new FormData()
		fd.append('file', file)
		return apiClient.post('/api/docs/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' }}).then(r => r.data)
	},
	listDocs: () => apiClient.get('/api/docs').then(r => r.data),
	getDoc: (docId: string) => apiClient.get(`/api/docs/${docId}`).then(r => r.data),
	// Playbooks
	createPlaybook: (name: string, rules: any) => apiClient.post('/api/playbooks', { name, rules }).then(r => r.data),
	listPlaybooks: () => apiClient.get('/api/playbooks').then(r => r.data),
	getPlaybook: (id: string) => apiClient.get(`/api/playbooks/${id}`).then(r => r.data),
	deletePlaybook: (id: string) => apiClient.delete(`/api/playbooks/${id}`).then(r => r.data),
	// Runs
	run: (payload: { doc_id?: string; agent_path?: string; playbook_id?: string; scope?: string; options?: any }) => apiClient.post('/api/run', payload).then(r => r.data),
	getRun: (runId: string) => apiClient.get(`/api/run/${runId}`).then(r => r.data),
	getBlackboard: (runId: string) => apiClient.get(`/api/blackboard/${runId}`).then(r => r.data),
	listPendingRiskRuns: () => apiClient.get('/api/hitl/pending-runs').then(r => r.data),
	getRiskAssessments: (runId: string) => apiClient.get(`/api/hitl/runs/${runId}/assessments`).then(r => r.data),
	saveRiskGateDecisions: (runId: string, payload: { items: Array<{ clause_id: string; decision: 'approve' | 'reject' | 'review'; comments?: string }> }) =>
		apiClient.post(`/api/hitl/runs/${runId}/decisions`, payload).then(r => r.data),
	riskApprove: (payload: { run_id: string; items: Array<{ clause_id: string; decision: 'approve'|'reject'; risk_override?: string; comments?: string }> }) => apiClient.post('/api/hitl/risk-approve', payload).then(r => r.data),
	listPendingFinalRuns: () => apiClient.get('/api/hitl/final-runs').then(r => r.data),
	getRedlineDetails: (runId: string) => apiClient.get(`/api/hitl/runs/${runId}/redlines`).then(r => r.data),
	finalApprove: (payload: { run_id: string; approved: string[]; rejected: string[]; note?: string }) => apiClient.post('/api/hitl/final-approve', payload).then(r => r.data),
	exportRedline: (runId: string, format: 'md'|'docx'|'pdf'='md') => apiClient.post('/api/export/redline', null, { params: { run_id: runId, format } }).then(r => r.data),
	listRuns: () => apiClient.get('/api/runs').then(r => r.data),
	replayRun: (runId: string, payload?: { agent_path?: string; playbook_id?: string | null }) =>
		apiClient.post(`/api/replay/${runId}`, payload ?? {}).then(r => r.data),
	replayClause: (runId: string, clauseId: string, payload: { prompt?: string; policy_rules?: any }) =>
		apiClient.post(`/api/replay/${runId}/clauses/${clauseId}`, payload ?? {}).then(r => r.data),
	reportSLOs: () => apiClient.get('/api/report/slos').then(r => r.data),
}
