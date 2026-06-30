import React from 'react';
import type { MatchCandidate } from '../../types';
import { MatchCard } from './MatchCard';

interface Props {
  candidates: MatchCandidate[];
  onSelectMatch: (matchId: number) => void;
}

export const MatchList: React.FC<Props> = ({ candidates, onSelectMatch }) => {
  if (candidates.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-4xl mb-4">🔍</div>
        <h3 className="text-lg font-semibold text-gray-700 mb-2">暂无匹配结果</h3>
        <p className="text-sm text-gray-500">完成画像采集后，点击匹配按钮开始寻找搭子</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-bold mb-4">为您找到 {candidates.length} 位潜在搭子</h2>
      <div className="space-y-4">
        {candidates.map((c, i) => (
          <MatchCard
            key={c.match_id || i}
            candidate={c}
            rank={c.rank || i + 1}
            onClick={onSelectMatch}
          />
        ))}
      </div>
    </div>
  );
};
