'use client';

import { useEffect, useMemo, useState } from 'react';
import { useSSE } from '@/hooks/useSSE';

interface SuggestionEvent {
  type: 'text' | 'tool_result' | 'complete';
  content?: string;
  tool?: string;
  result?: any;
  timestamp?: string;
}

export function AISuggestions({ callId }: { callId: string }) {
  const sseUrl = useMemo(() => {
    if (!callId) return '';
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return `${base}/api/stream/suggestions/${callId}`;
  }, [callId]);

  const { data: events, isConnected } = useSSE<SuggestionEvent>(sseUrl);
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    const text = events
      .filter((e) => e.type === 'text' && e.content)
      .map((e) => e.content)
      .join('\n');
    setDisplayedText(text);
  }, [events]);

  if (!callId) return null;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">🤖</span>
        <h3 className="text-lg font-bold text-gray-900">AI Suggestions</h3>
        {isConnected && <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />}
      </div>

      {displayedText ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-blue-900 whitespace-pre-line">
          {displayedText}
        </div>
      ) : (
        <div className="text-sm text-gray-500">Suggestions will appear here during the call.</div>
      )}
    </div>
  );
}

export default AISuggestions;


