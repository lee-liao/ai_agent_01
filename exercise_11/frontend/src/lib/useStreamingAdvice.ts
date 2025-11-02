/**
 * Hook for streaming advice using Server-Sent Events (SSE)
 * Usage in coach chat page
 */

import { useState, useCallback } from 'react';

interface Citation {
  source: string;
  url: string;
}

interface StreamingState {
  isStreaming: boolean;
  currentText: string;
  citations: Citation[];
  error: string | null;
}

export function useStreamingAdvice(apiUrl: string) {
  const [state, setState] = useState<StreamingState>({
    isStreaming: false,
    currentText: '',
    citations: [],
    error: null,
  });

  const streamAdvice = useCallback(
    (sessionId: string, question: string, onComplete: (text: string, citations: Citation[], isRefusal?: boolean) => void) => {
      setState({
        isStreaming: true,
        currentText: '',
        citations: [],
        error: null,
      });

      const encodedQuestion = encodeURIComponent(question);
      const eventSource = new EventSource(
        `${apiUrl}/api/coach/stream/${sessionId}?question=${encodedQuestion}`
      );

      let fullText = '';
      let finalCitations: Citation[] = [];
      let isRefusal = false;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'refusal') {
            // Handle refusal message
            isRefusal = true;
            onComplete('', [], true);
            setState({
              isStreaming: false,
              currentText: '',
              citations: [],
              error: null,
            });
            eventSource.close();
          } else if (data.chunk) {
            // Accumulate streaming text
            fullText += data.chunk;
            setState((prev) => ({
              ...prev,
              currentText: fullText,
            }));
          } else if (data.done) {
            // Stream complete
            finalCitations = data.citations || [];
            onComplete(fullText, finalCitations, isRefusal);
            setState({
              isStreaming: false,
              currentText: '',
              citations: finalCitations,
              error: null,
            });
            eventSource.close();
          }
        } catch (err) {
          console.error('Error parsing SSE data:', err);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: 'Connection error. Please try again.',
        }));
        eventSource.close();
        onComplete(fullText || 'Error streaming response', [], false);
      };

      // Cleanup function
      return () => {
        eventSource.close();
      };
    },
    [apiUrl]
  );

  return {
    ...state,
    streamAdvice,
  };
}

