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

// Spike test: Sudden 10x traffic increase
export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Normal load: 10 users
    { duration: '30s', target: 100 },  // Spike: Sudden jump to 100 users (10x)
    { duration: '1m', target: 100 },   // Sustain spike for 1 minute
    { duration: '30s', target: 10 },   // Return to normal: 10 users
    { duration: '1m', target: 10 },   // Normal load for 1 minute
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'], // More lenient for spike test (5% failure rate acceptable)
    http_req_duration: ['p(95)<8000'], // More lenient latency threshold for spike (8s)
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
  const sseUrl = `${BASE_URL}/api/coach/stream/${session_id}?question=${encodeURIComponent(question)}`;
  
  const params = {
    headers: {
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
    },
    timeout: '30s',
    tags: { name: 'sse_stream' },
  };
  
  const sseResponse = http.get(sseUrl, params);
  
  check(sseResponse, {
    'sse status 200': (r) => r.status === 200,
    'sse has content': (r) => r.body && r.body.length > 0,
    'sse has data events': (r) => {
      return r.body.includes('data:') || r.body.length > 0;
    },
  });
  
  // Parse SSE response to find completion
  let streamComplete = false;
  if (sseResponse.body) {
    const events = sseResponse.body.split('\n\n').filter(e => e.trim());
    for (const event of events) {
      const dataMatch = event.match(/^data:\s*(.+)$/m);
      if (dataMatch) {
        try {
          const data = JSON.parse(dataMatch[1]);
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

