import React, { useState, FormEvent } from 'react';
import { Message } from '@/types';
import { MessageCard } from '@/components/chat/MessageCard';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Paperclip, Send } from 'lucide-react';

type ChatPanelProps = {
  onRegenerate?: () => void;
  messages: Message[];
  onSend: (content: string) => void;
  isLoading: boolean;
  selectedModelName: string;
};

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  onSend,
  isLoading,
  selectedModelName, onRegenerate,
}) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSend(input.trim());
    setInput('');
  };

  return (
    <section className="flex flex-col h-full bg-white dark:bg-primary/90 border-r border-gray-700">
      {/* Header showing selected model */}
      <div className="p-2 bg-white dark:bg-gray-800 border-b border-gray-300 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-300 flex items-center">
        <span className="font-medium">Model:</span> <span className="ml-2 text-accentBlue">{selectedModelName}</span>
          {onRegenerate && (
            <button
              type="button"
              onClick={onRegenerate}
              className="ml-auto p-2 text-accentRed hover:text-white transition text-sm"
            >
              Regenerate
            </button>
          )}
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.map((msg) => (
          <MessageCard key={msg.id} message={msg} />
        ))}
        {isLoading && <LoadingSpinner />}
        {/* Empty state */}
        {messages.length === 0 && !isLoading && (
          <p className="text-center text-gray-500 mt-8">Start a conversation by typing below…</p>
        )}
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="flex items-center p-2 border-t border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800">
        <button
          type="button"
          className="p-2 text-gray-400 hover:text-white transition"
          aria-label="Add attachment"
        >
          <Paperclip size={20} />
        </button>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something..."
          rows={1}
          className="flex-1 resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded px-3 py-2 focus:outline-none mx-2"
        />
        <button
          type="submit"
          className="p-2 text-accentBlue hover:text-white transition"
          aria-label="Send message"
        >
          <Send size={20} />
        </button>
      </form>
    </section>
  );
};
