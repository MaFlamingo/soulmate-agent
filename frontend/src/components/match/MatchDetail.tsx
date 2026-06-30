import React, { useEffect } from 'react';
import type { MatchDetail as MatchDetailType, IceBreaker } from '../../types';

interface Props {
  detail: MatchDetailType;
  icebreakers: IceBreaker[];
  onGenerateIcebreaker: (matchId: number) => void;
  onAccept: (matchId: number) => void;
  onBack: () => void;
}

const styleIcons: Record<string, string> = {
  humorous: '😄',
  formal: '🤝',
  warm: '💝',
};

const styleLabels: Record<string, string> = {
  humorous: '幽默型',
  formal: '正式型',
  warm: '温暖型',
};

export const MatchDetailView: React.FC<Props> = ({
  detail,
  icebreakers,
  onGenerateIcebreaker,
  onAccept,
  onBack,
}) => {
  useEffect(() => {
    if (icebreakers.length === 0) {
      onGenerateIcebreaker(detail.match_id);
    }
  }, []);

  const { score_breakdown: sb } = detail;

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="text-primary-600 hover:text-primary-800 text-sm mb-2">
        ← 返回列表
      </button>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">匹配详情 #{detail.rank}</h2>
          <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full font-bold text-lg">
            {detail.total_score}%
          </span>
        </div>

        {/* Score breakdown */}
        <h3 className="font-semibold text-sm text-gray-600 mb-3">📊 评分分解</h3>
        <div className="space-y-2 mb-4">
          <ScoreBar label="兴趣相似度" value={sb.interest_score} max={50} color="bg-green-500" />
          <ScoreBar label="性格契合度" value={sb.personality_score} max={30} color="bg-purple-500" />
          <ScoreBar label="需求匹配度" value={sb.social_score} max={20} color="bg-blue-500" />
        </div>

        {/* Explanation */}
        {detail.explanation && (
          <div className="bg-blue-50 rounded-lg p-4 mb-4">
            <h3 className="font-semibold text-sm text-blue-800 mb-2">💡 推荐理由</h3>
            <p className="text-sm text-blue-900 leading-relaxed">{detail.explanation}</p>
          </div>
        )}

        {/* Shared interests & complementary */}
        <div className="flex flex-wrap gap-4 text-sm">
          {detail.shared_interests.length > 0 && (
            <div>
              <span className="text-gray-500">共同兴趣: </span>
              {detail.shared_interests.map((s, i) => (
                <span key={i} className="tag tag-interest mr-1">{s}</span>
              ))}
            </div>
          )}
          {detail.complementary_traits.length > 0 && (
            <div>
              <span className="text-gray-500">互补特质: </span>
              {detail.complementary_traits.map((t, i) => (
                <span key={i} className="tag tag-personality mr-1">{t}</span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Icebreakers */}
      <div className="card">
        <h3 className="font-semibold text-gray-800 mb-4">💬 选择破冰方式</h3>
        {icebreakers.length === 0 ? (
          <div className="text-center py-8">
            <div className="inline-flex gap-1 mb-2">
              <span className="typing-dot inline-block w-2 h-2 bg-gray-400 rounded-full" />
              <span className="typing-dot inline-block w-2 h-2 bg-gray-400 rounded-full" />
              <span className="typing-dot inline-block w-2 h-2 bg-gray-400 rounded-full" />
            </div>
            <p className="text-sm text-gray-500">正在生成破冰话术...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {icebreakers.map((ib) => (
              <div
                key={ib.id}
                className="border border-gray-200 rounded-xl p-4 hover:border-primary-300 hover:shadow-sm transition-all cursor-pointer"
              >
                <div className="text-2xl mb-2">
                  {styleIcons[ib.style] || '💬'} <span className="text-sm font-medium text-gray-700">{styleLabels[ib.style] || ib.style}</span>
                </div>
                <p className="text-sm text-gray-700 mb-3 leading-relaxed">{ib.content}</p>
                {ib.activity_suggestion && (
                  <div className="bg-green-50 rounded-lg p-2 text-xs text-green-800">
                    🎯 {ib.activity_suggestion}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Accept button */}
        <div className="mt-6 flex gap-3 justify-center">
          <button className="btn-secondary" onClick={onBack}>
            稍后再说
          </button>
          <button className="btn-primary" onClick={() => onAccept(detail.match_id)}>
            👍 接受匹配，发送破冰消息
          </button>
        </div>
      </div>
    </div>
  );
};

const ScoreBar: React.FC<{ label: string; value: number; max: number; color: string }> = ({
  label,
  value,
  max,
  color,
}) => (
  <div className="flex items-center gap-3">
    <span className="text-sm text-gray-600 w-24">{label}</span>
    <div className="score-bar flex-1">
      <div
        className={`score-bar-fill ${color}`}
        style={{ width: `${(value / max * 100).toFixed(0)}%` }}
      />
    </div>
    <span className="text-sm text-gray-500 w-16 text-right">
      {value.toFixed(0)} / {max}
    </span>
  </div>
);
