import React from 'react';
import type { MatchCandidate } from '../../types';

interface Props {
  candidate: MatchCandidate;
  rank: number;
  onClick: (matchId: number) => void;
}

const scoreColor = (score: number): string => {
  if (score >= 80) return 'text-green-600 bg-green-50';
  if (score >= 60) return 'text-blue-600 bg-blue-50';
  return 'text-gray-500 bg-gray-50';
};

export const MatchCard: React.FC<Props> = ({ candidate, rank, onClick }) => {
  const sc = scoreColor(candidate.total_score);

  return (
    <div
      className="card hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onClick(candidate.match_id)}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-gray-400">#{rank}</span>
          <div>
            <h3 className="font-semibold text-gray-800">
              {candidate.candidate_name || `用户${candidate.candidate_id}`}
            </h3>
            <p className="text-xs text-gray-500">{candidate.brief_reason}</p>
          </div>
        </div>
        <div className={`px-3 py-1.5 rounded-full font-bold text-sm ${sc}`}>
          {candidate.total_score}%
        </div>
      </div>

      {/* Shared interests */}
      {candidate.shared_interests.length > 0 && (
        <div className="flex flex-wrap gap-1">
          <span className="text-xs text-gray-500">共同:</span>
          {candidate.shared_interests.map((interest, i) => (
            <span key={i} className="tag tag-interest text-xs">
              {interest}
            </span>
          ))}
        </div>
      )}

      {/* Score bars */}
      <div className="mt-3 space-y-1">
        <ScoreRow label="兴趣" value={candidate.score_breakdown.interest_score} max={50} color="bg-green-500" />
        <ScoreRow label="性格" value={candidate.score_breakdown.personality_score} max={30} color="bg-purple-500" />
        <ScoreRow label="需求" value={candidate.score_breakdown.social_score} max={20} color="bg-blue-500" />
      </div>
    </div>
  );
};

const ScoreRow: React.FC<{ label: string; value: number; max: number; color: string }> = ({
  label,
  value,
  max,
  color,
}) => (
  <div className="flex items-center gap-2 text-xs">
    <span className="text-gray-500 w-8">{label}</span>
    <div className="score-bar flex-1 h-1.5">
      <div
        className={`score-bar-fill h-1.5 ${color}`}
        style={{ width: `${(value / max * 100).toFixed(0)}%` }}
      />
    </div>
    <span className="text-gray-400 w-12 text-right">
      {value.toFixed(0)}/{max}
    </span>
  </div>
);
