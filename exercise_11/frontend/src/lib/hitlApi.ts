import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8011';

export interface HITLCase {
  hitl_id: string;
  session_id: string;
  category: string;
  priority: 'high' | 'medium';
  status: 'pending' | 'in_progress' | 'resolved';
  user_message: string;
  conversation_history: Array<{ role: string; text: string; timestamp?: string }>;
  created_at: string;
  updated_at: string;
  mentor_reply?: string;
  resolved_at?: string;
}

export const hitlAPI = {
  async getQueue(status: 'pending' | 'in_progress' | 'resolved' = 'pending') {
    const res = await axios.get(`${API_URL}/api/hitl/queue`, {
      params: { status }
    });
    return res.data.items as HITLCase[];
  },

  async getCase(hitlId: string) {
    const res = await axios.get(`${API_URL}/api/hitl/${hitlId}`);
    return res.data as HITLCase;
  },

  async submitReply(hitlId: string, mentorReply: string) {
    const res = await axios.post(`${API_URL}/api/hitl/${hitlId}/reply`, {
      mentor_reply: mentorReply
    });
    return res.data;
  },

  async getSessionReplies(sessionId: string) {
    const res = await axios.get(`${API_URL}/api/hitl/session/${sessionId}/replies`);
    return res.data.replies as HITLCase[];
  }
};

export default hitlAPI;

