import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { ChatPage } from './pages/ChatPage';
import { MatchPage } from './pages/MatchPage';
import { ProfilePage } from './pages/ProfilePage';
import { AdminPage } from './pages/AdminPage';

const navItems = [
  { to: '/', label: '💬 对话', end: true },
  { to: '/match', label: '🎯 匹配' },
  { to: '/profile', label: '👤 画像' },
  { to: '/admin', label: '⚙️ 管理' },
];

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="flex flex-col h-screen">
        {/* Top-level navigation */}
        <nav className="bg-white border-b border-gray-200 px-6 py-3 hidden">
          <div className="flex gap-4">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `text-sm font-medium px-3 py-1.5 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Page content */}
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/match" element={<MatchPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;
