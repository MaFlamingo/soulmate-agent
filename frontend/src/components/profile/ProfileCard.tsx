import React from 'react';
import type { ProfileData } from '../../types';

interface Props {
  profile: ProfileData | null;
  loading?: boolean;
}

export const ProfileCard: React.FC<Props> = ({ profile, loading }) => {
  if (loading) {
    return (
      <div className="card animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-24 mb-3" />
        <div className="space-y-2">
          <div className="h-3 bg-gray-100 rounded w-full" />
          <div className="h-3 bg-gray-100 rounded w-3/4" />
          <div className="h-3 bg-gray-100 rounded w-1/2" />
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="card">
        <p className="text-gray-500 text-sm">画像尚未建立，开始对话来构建你的画像吧！</p>
      </div>
    );
  }

  const { interests, personality, social_need, low_confidence_tags } = profile;

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-800">👤 我的画像</h3>
        <span className="text-xs text-gray-400">v{profile.version}</span>
      </div>

      {/* Interests */}
      <div>
        <h4 className="text-xs font-medium text-gray-500 mb-2">🏷 兴趣标签</h4>
        <div className="flex flex-wrap gap-1.5">
          {interests.length === 0 && (
            <span className="text-xs text-gray-400">暂无标签</span>
          )}
          {interests.map((item, i) => (
            <span
              key={i}
              className={`tag tag-interest ${low_confidence_tags.includes(item) ? 'border border-dashed border-yellow-400' : ''}`}
              title={`置信度: ${(item.confidence * 100).toFixed(0)}%`}
            >
              {item.sub_category || item.category}
              {low_confidence_tags.includes(item) && ' †'}
            </span>
          ))}
        </div>
      </div>

      {/* Personality */}
      {personality && (
        <div>
          <h4 className="text-xs font-medium text-gray-500 mb-2">🧠 性格特征</h4>
          <div className="space-y-1.5">
            <PersonalityBar label="开放性" value={personality.openness} color="bg-purple-500" />
            <PersonalityBar label="外向性" value={personality.extraversion} color="bg-blue-500" />
            <PersonalityBar label="尽责性" value={personality.conscientiousness} color="bg-green-500" />
          </div>
        </div>
      )}

      {/* Social Need */}
      {social_need && Object.keys(social_need).length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-gray-500 mb-2">🎯 社交需求</h4>
          <div className="text-xs text-gray-600 space-y-1">
            {social_need.buddy_type && (
              <p>搭子类型: <span className="font-medium">{social_need.buddy_type}</span></p>
            )}
            {social_need.schedule && (
              <p>时间偏好: <span className="font-medium">{social_need.schedule}</span></p>
            )}
          </div>
        </div>
      )}

      {/* Tentative tags note */}
      {low_confidence_tags.length > 0 && (
        <p className="text-xs text-yellow-600 italic">
          † 标记为待确认的标签，继续对话可提高置信度
        </p>
      )}
    </div>
  );
};

const PersonalityBar: React.FC<{ label: string; value: number; color: string }> = ({
  label,
  value,
  color,
}) => (
  <div className="flex items-center gap-2">
    <span className="text-xs text-gray-500 w-10">{label}</span>
    <div className="score-bar flex-1">
      <div
        className={`score-bar-fill ${color}`}
        style={{ width: `${(value * 100).toFixed(0)}%` }}
      />
    </div>
    <span className="text-xs text-gray-400 w-8 text-right">
      {(value * 100).toFixed(0)}%
    </span>
  </div>
);
