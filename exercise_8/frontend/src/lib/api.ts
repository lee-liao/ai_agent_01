import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8004'

export const apiClient = axios.create({
	baseURL: API_BASE_URL,
	timeout: 20000,
	headers: { 'Content-Type': 'application/json' },
})

export const api = {
	health: () => apiClient.get('/health').then(r => r.data),
	run: (payload: { doc_id?: string; scope?: string; options?: any }) => apiClient.post('/api/run', payload).then(r => r.data),
	getBlackboard: (runId: string) => apiClient.get(`/api/blackboard/${runId}`).then(r => r.data),
	riskApprove: (payload: { run_id: string; items: Array<{ clause_id: string; risk_override?: string; comments?: string }> }) => apiClient.post('/api/hitl/risk-approve', payload).then(r => r.data),
	finalApprove: (payload: { run_id: string; note?: string }) => apiClient.post('/api/hitl/final-approve', payload).then(r => r.data),
	exportRedline: (runId: string, format: 'md'|'docx'='md') => apiClient.post('/api/export/redline', null, { params: { run_id: runId, format } }).then(r => r.data),
	replay: (runId: string) => apiClient.get(`/api/replay/${runId}`).then(r => r.data),
	reportSLOs: () => apiClient.get('/api/report/slos').then(r => r.data),
}
