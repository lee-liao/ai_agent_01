import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8011';

// Test questions for variety
const TEST_QUESTIONS = [
  'How to handle bedtime resistance?',
  'My child refuses to eat vegetables. What should I do?',
  'How can I help my child manage tantrums?',
  'What are good screen time limits for toddlers?',
  'How do I handle sibling conflicts?',
  'My child is having trouble sleeping. Any advice?',
  'How to encourage picky eaters?',
  'What are age-appropriate chores for preschoolers?',
];

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || '15m',
  thresholds: {
    http_req_failed: ['rate<0.01'], // Failure rate < 1%
    http_req_duration: ['p(95)<2500'], // p95 latency < 2.5s
  },
};

export default function () {
  // Health check
  const health = http.get(`${BASE_URL}/healthz`);
  check(health, { 'health 200': (r) => r.status === 200 });

  // Start session
  const name = `Parent_${Math.floor(Math.random() * 1e6)}`;
  const start = http.post(
    `${BASE_URL}/api/coach/start`,
    JSON.stringify({ parent_name: name }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  check(start, { 'start 200': (r) => r.status === 200 });

  const session_id = (start.json() || {}).session_id;
  if (!session_id) {
    return;
  }

  // Select a random question for variety
  const question = TEST_QUESTIONS[Math.floor(Math.random() * TEST_QUESTIONS.length)];
  
  // SSE endpoint - matches what the frontend uses
  // GET /api/coach/stream/{session_id}?question=...
  const sseUrl = `${BASE_URL}/api/coach/stream/${session_id}?question=${encodeURIComponent(question)}`;
  
  // Make SSE request (streaming HTTP GET)
  // IMPORTANT: k6's http.get() will wait for the HTTP response to complete
  // For SSE, this means it waits until the server closes the connection
  // (which happens when the generator finishes after sending 'done: true')
  // The timeout ensures we don't wait forever if something goes wrong
  const params = {
    headers: {
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
    },
    timeout: '30s', // 30 second timeout - enough for LLM responses, but prevents hanging
    tags: { name: 'sse_stream' },
  };
  
  // This call BLOCKS until the SSE stream completes (connection closes)
  // The duration includes the time to receive the entire stream
  const sseResponse = http.get(sseUrl, params);
  
  // Check SSE response
  check(sseResponse, {
    'sse status 200': (r) => r.status === 200,
    'sse has content': (r) => r.body && r.body.length > 0,
    'sse has data events': (r) => {
      // SSE format: "data: {...}\n\n"
      // Check if response contains SSE data format
      return r.body.includes('data:') || r.body.length > 0;
    },
  });
  
  // Parse SSE response to find completion
  // SSE format: "data: {json}\n\n"
  let streamComplete = false;
  if (sseResponse.body) {
    // Split by double newlines (SSE event separator)
    const events = sseResponse.body.split('\n\n').filter(e => e.trim());
    for (const event of events) {
      // Extract data line (SSE format: "data: {...}")
      const dataMatch = event.match(/^data:\s*(.+)$/m);
      if (dataMatch) {
        try {
          const data = JSON.parse(dataMatch[1]);
          // Check for completion signal
          if (data.done === true || data.type === 'refusal' || data.type === 'hitl_queued') {
            streamComplete = true;
            break;
          }
        } catch (e) {
          // Ignore JSON parse errors
        }
      }
    }
  }
  
  check(streamComplete, {
    'stream completed': () => streamComplete,
  });

  // Random sleep between 1-3 seconds to simulate realistic user behavior
  sleep(1 + Math.random() * 2);
}
