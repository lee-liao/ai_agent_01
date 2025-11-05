'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import hitlAPI, { HITLCase } from '@/lib/hitlApi';
import { ArrowLeft, Send, AlertCircle, Clock, CheckCircle2, RefreshCw } from 'lucide-react';

export default function HITLCasePage() {
  const params = useParams();
  const router = useRouter();
  const hitlId = params.id as string;
  
  const [caseItem, setCaseItem] = useState<HITLCase | null>(null);
  const [reply, setReply] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadCase = async () => {
    try {
      setLoading(true);
      const item = await hitlAPI.getCase(hitlId);
      setCaseItem(item);
    } catch (error) {
      console.error('Failed to load case:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (hitlId) {
      loadCase();
    }
  }, [hitlId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reply.trim() || !caseItem) return;

    try {
      setSubmitting(true);
      await hitlAPI.submitReply(hitlId, reply);
      // Reload case to show updated status
      await loadCase();
      setReply('');
      // Optionally redirect back to queue
      setTimeout(() => {
        router.push('/hitl/queue');
      }, 2000);
    } catch (error) {
      console.error('Failed to submit reply:', error);
      alert('Failed to submit reply. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const getPriorityBadge = (priority: string) => {
    if (priority === 'high') {
      return (
        <span className="px-3 py-1 text-sm font-bold bg-red-100 text-red-800 rounded-full">
          HIGH PRIORITY
        </span>
      );
    }
    return (
      <span className="px-3 py-1 text-sm font-bold bg-yellow-100 text-yellow-800 rounded-full">
        MEDIUM PRIORITY
      </span>
    );
  };

  const getCategoryBadge = (category: string) => {
    const colors: Record<string, string> = {
      crisis: 'bg-red-200 text-red-900',
      pii: 'bg-orange-200 text-orange-900',
      medical: 'bg-blue-200 text-blue-900',
      therapy: 'bg-purple-200 text-purple-900',
      legal: 'bg-gray-200 text-gray-900'
    };
    
    return (
      <span className={`px-3 py-1 text-sm font-semibold rounded-full ${colors[category] || 'bg-gray-200 text-gray-900'}`}>
        {category.toUpperCase()}
      </span>
    );
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        </div>
      </div>
    );
  }

  if (!caseItem) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <p className="text-gray-500">Case not found</p>
            <button
              onClick={() => router.push('/hitl/queue')}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Back to Queue
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => router.push('/hitl/queue')}
          className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Queue
        </button>

        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Case Details</h1>
              <div className="flex items-center gap-2 mb-2">
                {getPriorityBadge(caseItem.priority)}
                {getCategoryBadge(caseItem.category)}
              </div>
              <p className="text-sm text-gray-500">
                Status: <span className="font-semibold">{caseItem.status}</span>
              </p>
            </div>
          </div>

          <div className="border-t pt-4 mb-4">
            <h2 className="font-semibold text-gray-900 mb-2">User Message</h2>
            <p className="text-gray-700 bg-gray-50 p-4 rounded-lg">
              {caseItem.user_message}
            </p>
          </div>

          <div className="border-t pt-4 mb-4">
            <h2 className="font-semibold text-gray-900 mb-2">Timeline</h2>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>Created: {formatTime(caseItem.created_at)}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>Updated: {formatTime(caseItem.updated_at)}</span>
              </div>
              {caseItem.resolved_at && (
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span>Resolved: {formatTime(caseItem.resolved_at)}</span>
                </div>
              )}
            </div>
          </div>

          <div className="border-t pt-4">
            <h2 className="font-semibold text-gray-900 mb-2">Session ID</h2>
            <p className="text-sm text-gray-600 font-mono">{caseItem.session_id}</p>
          </div>
        </div>

        {/* Conversation History */}
        {caseItem.conversation_history && caseItem.conversation_history.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="font-semibold text-gray-900 mb-4">Conversation History</h2>
            <div className="space-y-3">
              {caseItem.conversation_history.map((msg, idx) => (
                <div key={idx} className="border-l-2 border-blue-200 pl-4">
                  <div className="text-xs text-gray-500 mb-1">{msg.role}</div>
                  <p className="text-gray-700">{msg.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Mentor Reply Form */}
        {caseItem.status !== 'resolved' ? (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Submit Response</h2>
            <form onSubmit={handleSubmit}>
              <textarea
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                placeholder="Enter your response to the parent..."
                className="w-full h-32 p-3 border rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Your response will be sent to the parent's chat session.
                </p>
                <button
                  type="submit"
                  disabled={!reply.trim() || submitting}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {submitting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Submit Response
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <h2 className="font-semibold text-green-900">Case Resolved</h2>
            </div>
            {caseItem.mentor_reply && (
              <div className="mt-4">
                <p className="text-sm font-semibold text-green-900 mb-2">Mentor Response:</p>
                <p className="text-green-800 bg-white p-4 rounded-lg">
                  {caseItem.mentor_reply}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

