import { useState, useCallback, useRef } from 'react';
import type { ExtractedTag, ProfileUpdate } from '../types';
import * as api from '../api/client';

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  extractedTags?: ExtractedTag[];
}

export function useChat() {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [phase, setPhase] = useState<string>('greeting');
  const [loading, setLoading] = useState(false);
  const [profileUpdates, setProfileUpdates] = useState<ProfileUpdate | null>(null);
  const [matchingReady, setMatchingReady] = useState(false);
  const msgIdRef = useRef(0);

  const startSession = useCallback(async () => {
    setLoading(true);
    try {
      const session = await api.createSession();
      setSessionId(session.session_id);
      setPhase(session.phase);
      msgIdRef.current += 1;
      setMessages([{
        id: msgIdRef.current,
        role: 'assistant',
        content: session.greeting_message,
      }]);
    } catch (err) {
      console.error('Failed to start session:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!sessionId) return;

    msgIdRef.current += 1;
    const userMsg: ChatMessage = { id: msgIdRef.current, role: 'user', content };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await api.sendMessage(sessionId, content);
      msgIdRef.current += 1;
      const assistantMsg: ChatMessage = {
        id: msgIdRef.current,
        role: 'assistant',
        content: response.content,
        extractedTags: response.extracted_tags,
      };
      setMessages(prev => [...prev, assistantMsg]);
      setPhase(response.phase);
      setProfileUpdates(response.profile_updates || null);

      // Check if matching is suggested
      if (response.phase === 'ready_to_match' || response.phase === 'confirmation_loop') {
        setMatchingReady(true);
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      msgIdRef.current += 1;
      setMessages(prev => [...prev, {
        id: msgIdRef.current,
        role: 'assistant',
        content: '抱歉，消息发送失败，请重试。',
      }]);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  return {
    sessionId,
    messages,
    phase,
    loading,
    profileUpdates,
    matchingReady,
    startSession,
    sendMessage,
  };
}
