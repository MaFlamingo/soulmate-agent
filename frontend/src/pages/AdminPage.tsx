import React, { useState, useEffect } from 'react';
import { MetricsPanel } from '../components/admin/MetricsPanel';
import type { DashboardData } from '../types';
import * as api from '../api/client';

export const AdminPage: React.FC = () => {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const data = await api.getDashboard();
      setDashboard(data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-800">⚙️ 管理后台</h1>
          <span className="text-sm text-gray-500">SoulMate-Agent v1.0</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {loading ? (
          <div className="card animate-pulse space-y-3">
            <div className="h-4 bg-gray-200 rounded w-32" />
            <div className="h-8 bg-gray-100 rounded w-full" />
          </div>
        ) : dashboard ? (
          <MetricsPanel data={dashboard} />
        ) : (
          <div className="card text-center py-12">
            <p className="text-gray-500">无法加载监控数据</p>
            <button onClick={loadDashboard} className="btn-primary mt-3 text-sm">
              重试
            </button>
          </div>
        )}

        {/* Quick links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a href="/admin/rules" className="card hover:shadow-md transition-shadow">
            <h3 className="font-semibold">📋 匹配规则</h3>
            <p className="text-sm text-gray-500 mt-1">管理硬约束过滤和权重配置</p>
          </a>
          <a href="/admin/users" className="card hover:shadow-md transition-shadow">
            <h3 className="font-semibold">👥 用户管理</h3>
            <p className="text-sm text-gray-500 mt-1">查看和管理用户账号</p>
          </a>
          <a href="/admin/logs" className="card hover:shadow-md transition-shadow">
            <h3 className="font-semibold">📝 审计日志</h3>
            <p className="text-sm text-gray-500 mt-1">查看系统操作记录</p>
          </a>
        </div>
      </main>
    </div>
  );
};
