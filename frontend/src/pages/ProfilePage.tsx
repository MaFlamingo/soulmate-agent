import React from 'react';
import { useProfile } from '../hooks/useProfile';
import { ProfileCard } from '../components/profile/ProfileCard';
import type { PersonalityScores } from '../types';

export const ProfilePage: React.FC = () => {
  const { profile, loading, refreshProfile } = useProfile();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-800">👤 我的画像</h1>
          <button onClick={refreshProfile} className="btn-secondary text-sm">
            🔄 刷新
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8 space-y-6">
        <ProfileCard profile={profile} loading={loading} />

        {profile && (
          <>
            {/* Personality Radar (text-based for simplicity) */}
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-4">🧠 性格详情</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <PersonalityDetail
                  label="开放性"
                  value={profile.personality.openness}
                  description="对新体验的好奇和接受程度"
                  highLabel="探索者"
                  lowLabel="务实者"
                />
                <PersonalityDetail
                  label="外向性"
                  value={profile.personality.extraversion}
                  description="社交活跃度和能量来源"
                  highLabel="社交达人"
                  lowLabel="独处充电"
                />
                <PersonalityDetail
                  label="尽责性"
                  value={profile.personality.conscientiousness}
                  description="计划性和自律程度"
                  highLabel="规划者"
                  lowLabel="随性派"
                />
              </div>
            </div>

            {/* Version info */}
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-2">📋 画像信息</h3>
              <div className="text-sm text-gray-600 space-y-1">
                <p>版本: v{profile.version}</p>
                <p>兴趣标签: {profile.interests.length} 个</p>
                <p>低置信度标签: {profile.low_confidence_tags.length} 个</p>
                {profile.conversation_summary && (
                  <p>摘要: {profile.conversation_summary}</p>
                )}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

const PersonalityDetail: React.FC<{
  label: string;
  value: number;
  description: string;
  highLabel: string;
  lowLabel: string;
}> = ({ label, value, description, highLabel, lowLabel }) => (
  <div className="text-center p-4 bg-gray-50 rounded-xl">
    <h4 className="font-semibold text-gray-800 mb-1">{label}</h4>
    <div className="text-3xl font-bold text-primary-600 my-2">
      {(value * 100).toFixed(0)}%
    </div>
    <div className="flex justify-between text-xs text-gray-400 mb-2">
      <span>{lowLabel}</span>
      <span>{highLabel}</span>
    </div>
    <div className="score-bar mb-2">
      <div
        className="score-bar-fill bg-primary-500"
        style={{ width: `${(value * 100).toFixed(0)}%` }}
      />
    </div>
    <p className="text-xs text-gray-500">{description}</p>
  </div>
);
