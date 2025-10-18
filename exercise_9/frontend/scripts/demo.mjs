// Demo script (Node) to automate a sample run via the backend API
// - Uploads sample docs
// - Starts a run for the high-value doc
// - Auto-approves HITL if required
// - Prints frontend export viewer URLs

import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const UI_BASE = process.env.UI_BASE_URL || 'http://localhost:3000';

async function uploadDocument(filePath, name) {
  const abs = resolve(filePath);
  const buf = await readFile(abs);
  const blob = new Blob([buf], { type: 'text/plain' });
  const form = new FormData();
  form.append('file', blob, name);
  const resp = await fetch(`${API_BASE}/api/documents/upload`, { method: 'POST', body: form });
  if (!resp.ok) throw new Error(`Upload failed: ${resp.status}`);
  return resp.json();
}

async function startRun(docId) {
  const resp = await fetch(`${API_BASE}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ doc_id: docId })
  });
  if (!resp.ok) throw new Error(`Start run failed: ${resp.status}`);
  return resp.json();
}

async function getRun(runId) {
  const resp = await fetch(`${API_BASE}/api/run/${runId}`);
  if (!resp.ok) throw new Error(`Get run failed: ${resp.status}`);
  return resp.json();
}

async function listHITL() {
  const resp = await fetch(`${API_BASE}/api/hitl/queue`);
  if (!resp.ok) throw new Error(`Get HITL queue failed: ${resp.status}`);
  return resp.json();
}

async function approveHITL(hitlId) {
  const resp = await fetch(`${API_BASE}/api/hitl/${hitlId}/respond`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hitl_id: hitlId, decisions: [{ item_id: 'approve_all', decision: 'approve' }] })
  });
  if (!resp.ok) throw new Error(`Approve HITL failed: ${resp.status}`);
  return resp.json();
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  try {
    console.log('Uploading sample documents...');
    const baseDir = resolve(process.cwd(), '../../');
    const high = await uploadDocument(resolve(baseDir, 'data/sample_documents/high_value_test.md'), 'high_value_test.md');
    const base = await uploadDocument(resolve(baseDir, 'data/sample_documents/pii_baseline_test.md'), 'pii_baseline_test.md');
    const ctx  = await uploadDocument(resolve(baseDir, 'data/sample_documents/context_pii_test.md'), 'context_pii_test.md');
    console.log('Uploaded:', high.name, base.name, ctx.name);

    console.log('Starting review run for high-value doc...');
    const runStart = await startRun(high.doc_id);
    const runId = runStart.run_id;
    console.log('Run ID:', runId);

    // initial wait
    await sleep(1500);

    const deadline = Date.now() + 30000; // 30s timeout
    while (Date.now() < deadline) {
      const run = await getRun(runId);
      console.log('Status:', run.status);
      if (run.status === 'awaiting_hitl') {
        const queue = await listHITL();
        const item = (queue || []).find(q => q.run_id === runId);
        if (item) {
          console.log('Approving HITL:', item.hitl_id);
          await approveHITL(item.hitl_id);
          await sleep(1000);
        }
      } else if (run.status === 'completed' || run.status === 'failed') {
        console.log('Final status:', run.status);
        console.log('UI Redline:', `${UI_BASE}/export/${runId}/redline`);
        console.log('UI Final:  ', `${UI_BASE}/export/${runId}/final`);
        return;
      }
      await sleep(2000);
    }
    console.warn('Timed out waiting for completion. Check /review and /hitl manually.');
  } catch (err) {
    console.error('Demo failed:', err);
    process.exitCode = 1;
  }
}

main();

