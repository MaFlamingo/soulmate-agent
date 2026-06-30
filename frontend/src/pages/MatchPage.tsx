import React, { useState, useEffect } from 'react';
import { MatchList } from '../components/match/MatchList';
import { MatchDetailView } from '../components/match/MatchDetail';
import { useMatch } from '../hooks/useMatch';
import type { MatchDetail as MatchDetailType } from '../types';

export const MatchPage: React.FC = () => {
  const {
    candidates,
    matchDetail,
    icebreakers,
    loading,
    matchError,
    requestMatch,
    viewMatchDetail,
    generateIcebreakers,
    submitFeedback,
  } = useMatch();

  const [showDetail, setShowDetail] = useState(false);

  // Trigger matching on mount
  useEffect(() => {
    requestMatch(5);
  }, []);

  const handleSelectMatch = async (matchId: number) => {
    await viewMatchDetail(matchId);
    setShowDetail(true);
  };

  const handleBack = () => {
    setShowDetail(false);
  };

  const handleAccept = async (matchId: number) => {
    await submitFeedback(matchId, true);
    alert('✅ 匹配已接受！破冰消息已发送给候选人。');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-800">
            {showDetail ? '候选人详情' : '🎯 匹配结果'}
          </h1>
          <button
            onClick={() => requestMatch(5)}
            disabled={loading}
            className="btn-primary text-sm"
          >
            {loading ? '匹配中...' : '🔄 重新匹配'}
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-8">
        {matchError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-700 text-sm">{matchError}</p>
            <p className="text-red-500 text-xs mt-1">请先完成画像采集对话后再尝试匹配。</p>
          </div>
        )}

        {loading && !showDetail && (
          <div className="text-center py-12">
            <div className="inline-flex gap-1 mb-3">
              <span className="typing-dot inline-block w-3 h-3 bg-primary-500 rounded-full" />
              <span className="typing-dot inline-block w-3 h-3 bg-primary-500 rounded-full" />
              <span className="typing-dot inline-block w-3 h-3 bg-primary-500 rounded-full" />
            </div>
            <p className="text-gray-500">正在为你寻找最佳搭子...</p>
          </div>
        )}

        {!loading && showDetail && matchDetail && (
          <MatchDetailView
            detail={matchDetail}
            icebreakers={icebreakers}
            onGenerateIcebreaker={generateIcebreakers}
            onAccept={handleAccept}
            onBack={handleBack}
          />
        )}

        {!loading && !showDetail && (
          <MatchList candidates={candidates} onSelectMatch={handleSelectMatch} />
        )}
      </main>
    </div>
  );
};
