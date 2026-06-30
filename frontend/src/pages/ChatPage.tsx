import React, { useEffect, useRef } from 'react';
import { ChatBubble } from '../components/chat/ChatBubble';
import { ChatInput } from '../components/chat/ChatInput';
import { ProfileCard } from '../components/profile/ProfileCard';
import { useChat } from '../hooks/useChat';
import { useProfile } from '../hooks/useProfile';
import { useNavigate } from 'react-router-dom';

export const ChatPage: React.FC = () => {
  const {
    messages,
    phase,
    loading,
    profileUpdates,
    matchingReady,
    startSession,
    sendMessage,
  } = useChat();

  const { profile, refreshProfile } = useProfile();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Start session on mount
  useEffect(() => {
    startSession();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Refresh profile when updates come in
  useEffect(() => {
    if (profileUpdates) {
      refreshProfile();
    }
  }, [profileUpdates]);

  const phaseLabels: Record<string, string> = {
    greeting: '👋 问候',
    interest_gathering: '🎯 了解兴趣',
    interest_deepening: '🔍 深入探索',
    personality_probing: '🧠 了解性格',
    social_need_clarification: '📋 明确需求',
    confirmation_loop: '✅ 确认画像',
    ready_to_match: '🚀 准备匹配',
  };

  return (
    <div className="flex h-screen">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-800">SoulMate-Agent</h1>
            <p className="text-xs text-gray-500">
              {phaseLabels[phase] || phase} · {messages.length} 条消息
            </p>
          </div>
          {matchingReady && (
            <button
              onClick={() => navigate('/match')}
              className="btn-accent animate-pulse"
            >
              🚀 开始匹配
            </button>
          )}
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="max-w-3xl mx-auto">
            {messages.map((msg) => (
              <ChatBubble
                key={msg.id}
                role={msg.role}
                content={msg.content}
                extractedTags={msg.extractedTags}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <ChatInput onSend={sendMessage} disabled={loading} />
      </div>

      {/* Profile sidebar */}
      <aside className="w-80 border-l border-gray-200 bg-gray-50 p-4 overflow-y-auto hidden lg:block">
        <ProfileCard profile={profile} loading={loading} />
        {profileUpdates && (
          <div className="mt-3 text-xs text-green-600">
            ✅ 画像已更新 (v{profileUpdates.new_version})
          </div>
        )}
      </aside>
    </div>
  );
};
