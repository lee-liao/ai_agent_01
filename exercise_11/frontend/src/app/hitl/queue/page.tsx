'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import hitlAPI, { HITLCase } from '@/lib/hitlApi';
import { AlertCircle, Clock, CheckCircle2, Circle, ArrowRight, RefreshCw } from 'lucide-react';

export default function HITLQueuePage() {
  const router = useRouter();
  const [cases, setCases] = useState<HITLCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'pending' | 'in_progress' | 'resolved'>('pending');

  // Memoize filtered cases and counts to prevent unnecessary recalculations
  const filteredCases = useMemo(() => {
    return cases.filter(c => c.status === filter);
  }, [cases, filter]);

  const counts = useMemo(() => {
    return {
      pending: cases.filter(c => c.status === 'pending').length,
      in_progress: cases.filter(c => c.status === 'in_progress').length,
      resolved: cases.filter(c => c.status === 'resolved').length,
    };
  }, [cases]);

  const loadCases = useCallback(async (showLoading = false) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      const items = await hitlAPI.getQueue(filter);
      // Only update if cases actually changed to prevent unnecessary re-renders
      setCases((prevCases) => {
        // Compare by ID to avoid unnecessary updates
        const prevIds = new Set(prevCases.map(c => c.hitl_id));
        const newIds = new Set(items.map(c => c.hitl_id));
        if (prevIds.size === newIds.size && 
            [...prevIds].every(id => newIds.has(id)) &&
            items.every(item => {
              const prev = prevCases.find(c => c.hitl_id === item.hitl_id);
              return prev && prev.status === item.status && prev.updated_at === item.updated_at;
            })) {
          // No changes, return previous state
          return prevCases;
        }
        return items;
      });
    } catch (error) {
      console.error('Failed to load HITL queue:', error);
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, [filter]);

  // Initial load and when filter changes
  useEffect(() => {
    loadCases(true);
  }, [filter, loadCases]);

  // SSE connection for real-time updates
  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8011';
    const eventSource = new EventSource(`${apiUrl}/api/coach/hitl/events`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Reload cases when new case or case update is received
        if (data.type === 'new_case' || data.type === 'case_updated') {
          // Reload without showing loading spinner (silent update)
          loadCases(false);
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      // EventSource will automatically reconnect
    };

    return () => {
      eventSource.close();
    };
  }, [loadCases]); // Include loadCases in dependencies

  const getPriorityBadge = (priority: string) => {
    if (priority === 'high') {
      return (
        <span className="px-2 py-1 text-xs font-bold bg-red-100 text-red-800 rounded-full">
          HIGH
        </span>
      );
    }
    return (
      <span className="px-2 py-1 text-xs font-bold bg-yellow-100 text-yellow-800 rounded-full">
        MEDIUM
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
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${colors[category] || 'bg-gray-200 text-gray-900'}`}>
        {category.toUpperCase()}
      </span>
    );
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  if (loading && cases.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Mentor Queue</h1>
              <p className="text-gray-600 mt-1">Review and respond to sensitive cases</p>
            </div>
            <button
              onClick={() => loadCases(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {/* Filter Tabs */}
          <div className="flex gap-2 mb-6 border-b">
            <button
              onClick={() => setFilter('pending')}
              className={`px-4 py-2 font-medium ${
                filter === 'pending'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Pending ({counts.pending})
              </div>
            </button>
            <button
              onClick={() => setFilter('in_progress')}
              className={`px-4 py-2 font-medium ${
                filter === 'in_progress'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              In Progress ({counts.in_progress})
            </button>
            <button
              onClick={() => setFilter('resolved')}
              className={`px-4 py-2 font-medium ${
                filter === 'resolved'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                Resolved ({counts.resolved})
              </div>
            </button>
          </div>

          {/* Cases List */}
          {filteredCases.length === 0 ? (
            <div className="text-center py-12">
              <Circle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No {filter} cases</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredCases.map((caseItem) => (
                <div
                  key={caseItem.hitl_id}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => router.push(`/hitl/case/${caseItem.hitl_id}`)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {getPriorityBadge(caseItem.priority)}
                        {getCategoryBadge(caseItem.category)}
                        <span className="text-sm text-gray-500">
                          Session: {caseItem.session_id}
                        </span>
                      </div>
                      <p className="text-gray-900 mb-2 line-clamp-2">
                        {caseItem.user_message}
                      </p>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span>Created: {formatTime(caseItem.created_at)}</span>
                        {caseItem.resolved_at && (
                          <span>Resolved: {formatTime(caseItem.resolved_at)}</span>
                        )}
                      </div>
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

