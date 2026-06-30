import React from 'react';
import type { ExtractedTag } from '../../types';

interface Props {
  role: 'user' | 'assistant';
  content: string;
  extractedTags?: ExtractedTag[];
}

const tagColors: Record<string, string> = {
  interest: 'bg-green-100 text-green-700',
  personality: 'bg-purple-100 text-purple-700',
  social_need: 'bg-blue-100 text-blue-700',
};

export const ChatBubble: React.FC<Props> = ({ role, content, extractedTags }) => {
  return (
    <div className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs opacity-70 font-medium">
            {role === 'user' ? '😊 我' : '🤖 SoulMate'}
          </span>
        </div>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>

        {/* Extracted tags (show on assistant messages) */}
        {extractedTags && extractedTags.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200/50">
            <p className="text-xs text-gray-500 mb-1">🔍 已识别:</p>
            <div className="flex flex-wrap gap-1">
              {extractedTags.map((tag, i) => (
                <span
                  key={i}
                  className={`tag text-xs ${tagColors[tag.type] || 'bg-gray-100 text-gray-600'} ${tag.tentative ? 'border border-dashed border-yellow-400' : ''}`}
                  title={tag.source_quote ? `来源: "${tag.source_quote}"` : undefined}
                >
                  {tag.sub_category || tag.category || tag.value}
                  {tag.tentative && ' †'}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
