import React from 'react';
import { Plus, MessageSquare, Bot, Settings, BarChart2, Monitor, Zap } from 'lucide-react';
import { useToast } from '@/context/ToastContext';

type SidebarProps = {
  chats: { id: string; title: string }[];
  selectedChatId: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  currentModel: { id: string; name: string };
};

export const Sidebar: React.FC<SidebarProps> = ({
  chats,
  selectedChatId,
  onSelectChat,
  onNewChat,
  currentModel,
}) => {
  const { addToast } = useToast();

  const handleNewChat = () => {
    onNewChat();
    addToast('Started a new chat', 'success');
  };

  return (
    <aside className="flex flex-col w-64 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 border-r border-gray-300 dark:border-gray-800 p-4 overflow-y-auto">
      {/* Logo */}
      <div className="flex items-center mb-6">
        <Zap className="text-accentRed mr-2" size={28} />
        <span className="text-xl font-bold">HallUGuard</span>
      </div>

      {/* Nav items */}
      <nav className="flex-1 space-y-2">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center space-x-2 p-2 rounded hover:bg-gray-300 dark:hover:bg-gray-800 transition"
        >
          <Plus size={20} />
          <span>New Chat</span>
        </button>
        <div className="mt-4">
          <h3 className="text-sm uppercase text-gray-400 mb-2">History</h3>
          {chats.length === 0 && (
            <p className="text-xs text-gray-500">No chats yet</p>
          )}
          {chats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => onSelectChat(chat.id)}
              className={`w-full text-left text-sm p-2 rounded hover:bg-gray-300 dark:hover:bg-gray-800 transition ${
                chat.id === selectedChatId ? 'bg-gray-800' : ''
              }`}
            >
              {chat.title}
            </button>
          ))}
        </div>
      </nav>

      {/* Bottom status */}
      <div className="mt-6 pt-4 border-t border-gray-800">
        <div className="flex items-center space-x-2">
          <Bot size={16} className="text-accentBlue" />
          <span className="text-xs">{currentModel.name}</span>
        </div>
        <div className="flex items-center space-x-2 mt-2">
          <Monitor size={16} className="text-green-500" />
          <span className="text-xs">Online</span>
        </div>
      </div>
    </aside>
  );
};
