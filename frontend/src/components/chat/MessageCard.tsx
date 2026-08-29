import React from 'react';
import { Message } from '@/types';
import { User, Bot, Copy } from 'lucide-react';

type Props = {
  message: Message;
};

export const MessageCard: React.FC<Props> = ({ message }) => {
  const isUser = message.role === 'user';
  const Icon = isUser ? User : Bot;
  const bg = isUser ? 'bg-gray-200 dark:bg-gray-800' : 'bg-white dark:bg-primary/80';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`max-w-[70%] rounded-lg p-3 ${bg} shadow-sm relative`}>
        <div className="flex items-center mb-1">
          <Icon size={14} className="mr-1 text-accentBlue" />
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          {!isUser && (
            <button
              type="button"
              onClick={() => navigator.clipboard.writeText(message.content)}
              className="absolute top-1 right-1 p-1 text-gray-500 dark:text-gray-300 hover:text-white transition"
              aria-label="Copy message"
            >
              <Copy size={14} />
            </button>
          )}
      </div>
    </div>
  );
};
