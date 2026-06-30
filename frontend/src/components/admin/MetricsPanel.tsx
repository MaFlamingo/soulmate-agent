import React from 'react';
import type { DashboardData } from '../../types';

interface Props {
  data: DashboardData;
}

export const MetricsPanel: React.FC<Props> = ({ data }) => {
  return (
    <div className="space-y-6">
      {/* Agent metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.agents.map((agent) => (
          <div key={agent.name} className="card">
            <h3 className="font-semibold text-gray-800 mb-3">{agent.name}</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">成功率</span>
                <span className="font-medium text-green-600">{agent.success_rate}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">P95 延迟</span>
                <span className="font-medium">{agent.latency_p95_ms.toFixed(0)}ms</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">今日Token</span>
                <span className="font-medium">{(agent.tokens_consumed_today / 1000).toFixed(1)}K</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">请求总数</span>
                <span className="font-medium">{agent.total_requests}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* System info */}
      <div className="card">
        <h3 className="font-semibold text-gray-800 mb-3">🖥 系统概览</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
          <div>
            <span className="text-gray-500">总用户数</span>
            <p className="text-lg font-bold">{data.system.total_users}</p>
          </div>
          <div>
            <span className="text-gray-500">总对话数</span>
            <p className="text-lg font-bold">{data.system.total_conversations}</p>
          </div>
          <div>
            <span className="text-gray-500">总匹配数</span>
            <p className="text-lg font-bold">{data.system.total_matches}</p>
          </div>
          <div>
            <span className="text-gray-500">向量库</span>
            <p className="text-lg font-bold">{data.system.vector_store_count}</p>
          </div>
          <div>
            <span className="text-gray-500">运行时间</span>
            <p className="text-lg font-bold">{(data.system.uptime_seconds / 3600).toFixed(1)}h</p>
          </div>
        </div>
      </div>
    </div>
  );
};
