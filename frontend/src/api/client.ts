import axios from 'axios';
import type {
  ChatSession, Message, SendMessageResponse,
  ProfileData, ProfileVersion,
  MatchResult, MatchDetail, MatchHistoryItem, IceBreaker,
  DashboardData, MatchingRule,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Default user ID for demo
const DEFAULT_USER = 1;

// ── Chat API ──

export async function createSession(userId?: number): Promise<ChatSession> {
  const { data } = await api.post('/chat/sessions', { user_id: userId || DEFAULT_USER });
  return data;
}

export async function sendMessage(sessionId: number, content: string): Promise<SendMessageResponse> {
  const { data } = await api.post(`/chat/sessions/${sessionId}/messages`, { content });
  return data;
}

export async function getSession(sessionId: number): Promise<{
  id: number; user_id: number; state: Record<string, unknown>;
  status: string; messages: Message[];
}> {
  const { data } = await api.get(`/chat/sessions/${sessionId}`);
  return data;
}

export async function listSessions(userId?: number): Promise<{ items: Record<string, unknown>[] }> {
  const { data } = await api.get('/chat/sessions', {
    params: { user_id: userId || DEFAULT_USER },
  });
  return data;
}

// ── Profile API ──

export async function getMyProfile(userId?: number): Promise<ProfileData> {
  const { data } = await api.get('/profile/me', { params: { user_id: userId || DEFAULT_USER } });
  return data;
}

export async function getProfileVersions(userId?: number): Promise<ProfileVersion[]> {
  const { data } = await api.get('/profile/me/versions', {
    params: { user_id: userId || DEFAULT_USER },
  });
  return data;
}

export async function getProfileVersion(version: number, userId?: number): Promise<ProfileVersion> {
  const { data } = await api.get(`/profile/me/versions/${version}`, {
    params: { user_id: userId || DEFAULT_USER },
  });
  return data;
}

export async function exportProfile(userId?: number): Promise<Record<string, unknown>> {
  const { data } = await api.post('/profile/me/export', null, {
    params: { user_id: userId || DEFAULT_USER },
  });
  return data;
}

// ── Match API ──

export async function requestMatch(userId?: number, k: number = 5): Promise<MatchResult> {
  const { data } = await api.post('/match/request', {
    user_id: userId || DEFAULT_USER,
    k,
  });
  return data;
}

export async function getMatchResults(userId?: number, limit: number = 20, offset: number = 0): Promise<{
  items: MatchHistoryItem[]; total: number;
}> {
  const { data } = await api.get('/match/results', {
    params: { user_id: userId || DEFAULT_USER, limit, offset },
  });
  return data;
}

export async function getMatchDetail(matchId: number): Promise<MatchDetail> {
  const { data } = await api.get(`/match/${matchId}`);
  return data;
}

export async function submitFeedback(matchId: number, accepted: boolean, feedbackText?: string): Promise<void> {
  await api.post(`/match/${matchId}/feedback`, { accepted, feedback_text: feedbackText });
}

export async function generateIcebreakers(matchId: number): Promise<{
  match_id: number; icebreakers: IceBreaker[];
}> {
  const { data } = await api.post(`/match/${matchId}/icebreaker`);
  return data;
}

// ── Admin API ──

export async function getDashboard(): Promise<DashboardData> {
  const { data } = await api.get('/admin/dashboard');
  return data;
}

export async function listRules(): Promise<MatchingRule[]> {
  const { data } = await api.get('/admin/rules');
  return data;
}

export async function updateRule(ruleId: number, updates: Record<string, unknown>): Promise<MatchingRule> {
  const { data } = await api.put(`/admin/rules/${ruleId}`, updates);
  return data;
}

export async function listUsers(page: number = 1): Promise<{ items: Record<string, unknown>[]; total: number }> {
  const { data } = await api.get('/admin/users', { params: { page } });
  return data;
}

export async function getAuditLogs(params: Record<string, unknown> = {}): Promise<{ items: Record<string, unknown>[] }> {
  const { data } = await api.get('/admin/audit-logs', { params });
  return data;
}
