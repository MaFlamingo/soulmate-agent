import React, { useState, useRef, useEffect } from 'react';

interface Props {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<Props> = ({ onSend, disabled }) => {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, [disabled]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput('');
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="说说你的兴趣爱好吧..."
          rows={2}
          disabled={disabled}
          className="input-field resize-none flex-1"
          maxLength={2000}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="btn-primary px-6 py-2.5"
        >
          {disabled ? (
            <span className="flex items-center gap-2">
              <span className="typing-dot inline-block w-1.5 h-1.5 bg-white rounded-full" />
              <span className="typing-dot inline-block w-1.5 h-1.5 bg-white rounded-full" />
              <span className="typing-dot inline-block w-1.5 h-1.5 bg-white rounded-full" />
            </span>
          ) : (
            '发送'
          )}
        </button>
      </div>
      <p className="text-xs text-gray-400 text-center mt-2">
        Enter 发送 · Shift+Enter 换行
      </p>
    </div>
  );
};
