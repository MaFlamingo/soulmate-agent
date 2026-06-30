import { useState, useCallback } from 'react';
import type { MatchCandidate, MatchDetail, IceBreaker } from '../types';
import * as api from '../api/client';

export function useMatch() {
  const [candidates, setCandidates] = useState<MatchCandidate[]>([]);
  const [matchDetail, setMatchDetail] = useState<MatchDetail | null>(null);
  const [icebreakers, setIcebreakers] = useState<IceBreaker[]>([]);
  const [loading, setLoading] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);

  const requestMatch = useCallback(async (k: number = 5) => {
    setLoading(true);
    setMatchError(null);
    try {
      const result = await api.requestMatch(undefined, k);
      setCandidates(result.candidates);
      return result;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '匹配请求失败';
      setMatchError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const viewMatchDetail = useCallback(async (matchId: number) => {
    setLoading(true);
    try {
      const detail = await api.getMatchDetail(matchId);
      setMatchDetail(detail);
      setIcebreakers(detail.icebreakers || []);
      return detail;
    } catch (err) {
      console.error('Failed to get match detail:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const generateIcebreakers = useCallback(async (matchId: number) => {
    try {
      const result = await api.generateIcebreakers(matchId);
      setIcebreakers(result.icebreakers);
      return result.icebreakers;
    } catch (err) {
      console.error('Failed to generate icebreakers:', err);
      return [];
    }
  }, []);

  const submitFeedback = useCallback(async (matchId: number, accepted: boolean) => {
    try {
      await api.submitFeedback(matchId, accepted);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  }, []);

  return {
    candidates,
    matchDetail,
    icebreakers,
    loading,
    matchError,
    requestMatch,
    viewMatchDetail,
    generateIcebreakers,
    submitFeedback,
  };
}
