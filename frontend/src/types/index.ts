// ── Chat ──
export interface ChatSession {
  session_id: number;
  greeting_message: string;
  phase: string;
  user_id?: number;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
}

export interface ExtractedTag {
  type: string;
  category?: string;
  sub_category?: string;
  value?: unknown;
  weight: number;
  confidence: number;
  source_quote?: string;
  tentative: boolean;
}

export interface ProfileUpdate {
  added_interests: Record<string, unknown>[];
  updated_personality?: Record<string, number>;
  updated_social_need?: Record<string, string>;
  new_version?: number;
}

export interface SendMessageResponse {
  message_id: number;
  role: string;
  content: string;
  phase: string;
  extracted_tags: ExtractedTag[];
  profile_updates?: ProfileUpdate;
  tokens_used: number;
  latency_ms: number;
}

// ── Profile ──
export interface ProfileData {
  user_id: number;
  version: number;
  static_attrs: Record<string, string>;
  interests: InterestItem[];
  personality: PersonalityScores;
  social_need: SocialNeed;
  preferences: ProfilePreferences;
  low_confidence_tags: InterestItem[];
  conversation_summary?: string;
  created_at?: string;
  updated_at?: string;
}

export interface InterestItem {
  category: string;
  sub_category: string;
  weight: number;
  confidence: number;
  source: string;
  source_quote?: string;
}

export interface PersonalityScores {
  openness: number;
  extraversion: number;
  conscientiousness: number;
}

export interface SocialNeed {
  buddy_type?: string;
  schedule?: string;
  ideal_group_size?: string;
}

export interface ProfilePreferences {
  hard_constraints: Record<string, unknown>[];
  soft_preferences: Record<string, string>;
}

export interface ProfileVersion {
  version: number;
  snapshot: Record<string, unknown>;
  change_reason?: string;
  created_at: string;
}

// ── Match ──
export interface MatchCandidate {
  match_id: number;
  candidate_id: number;
  candidate_name: string;
  total_score: number;
  rank: number;
  shared_interests: string[];
  score_breakdown: ScoreBreakdown;
  brief_reason: string;
}

export interface ScoreBreakdown {
  interest_score: number;
  personality_score: number;
  social_score: number;
  rule_bonus: number;
  detail: Record<string, unknown>;
}

export interface MatchResult {
  request_id: number;
  candidates: MatchCandidate[];
  total_candidates_searched: number;
  filters_applied: string[];
  latency_ms: number;
}

export interface MatchDetail {
  match_id: number;
  user_id: number;
  candidate_id: number;
  candidate_name: string;
  total_score: number;
  rank: number;
  score_breakdown: ScoreBreakdown;
  explanation: string;
  shared_interests: string[];
  complementary_traits: string[];
  icebreakers: IceBreaker[];
  created_at?: string;
}

export interface IceBreaker {
  id: number;
  style: string;
  content: string;
  activity_suggestion?: string;
  selected: boolean;
  created_at?: string;
}

export interface MatchHistoryItem {
  match_id: number;
  candidate_name: string;
  total_score: number;
  rank: number;
  accepted?: boolean;
  created_at: string;
}

// ── Admin ──
export interface AgentMetrics {
  name: string;
  qps: number;
  latency_p95_ms: number;
  success_rate: number;
  tokens_consumed_today: number;
  total_requests: number;
  error_count: number;
}

export interface SystemInfo {
  total_users: number;
  total_conversations: number;
  total_matches: number;
  vector_store_count: number;
  uptime_seconds: number;
}

export interface DashboardData {
  agents: AgentMetrics[];
  system: SystemInfo;
}

export interface MatchingRule {
  id: number;
  name: string;
  rule_type: string;
  config: Record<string, unknown>;
  priority: number;
  enabled: boolean;
  description?: string;
}
