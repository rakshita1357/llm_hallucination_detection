import React, { useState, useMemo } from 'react';
import { 
  Plus, 
  Search, 
  MessageSquare, 
  MoreVertical, 
  Edit3, 
  Trash2, 
  Settings, 
  LogOut, 
  LogIn, 
  ChevronLeft, 
  ChevronRight, 
  X, 
  ShieldCheck, 
  User,
  PanelLeftClose,
  PanelLeft,
  Sparkles
} from 'lucide-react';
import { ChatConversation, UserProfile } from '../../types.ts';
import { BrandLogo } from '../BrandLogo.tsx';

interface SidebarProps {
  conversations: ChatConversation[];
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onRenameChat: (id: string, currentTitle: string) => void;
  onDeleteChat: (id: string, title: string) => void;
  userProfile: UserProfile;
  onOpenSettings: () => void;
  onOpenAuth: (mode?: 'signin' | 'signup') => void;
  onSignOut: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeChatId,
  onSelectChat,
  onNewChat,
  onRenameChat,
  onDeleteChat,
  userProfile,
  onOpenSettings,
  onOpenAuth,
  onSignOut,
  isCollapsed,
  onToggleCollapse,
  isMobileOpen,
  onCloseMobile
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);

  // Group conversations by date intervals
  const groupedConversations = useMemo(() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterday = today - 86400000;
    const prev7Days = today - 86400000 * 7;

    const filtered = conversations.filter(c => 
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.messages.some(m => m.content.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const groups: {
      today: ChatConversation[];
      yesterday: ChatConversation[];
      prev7Days: ChatConversation[];
      older: ChatConversation[];
    } = {
      today: [],
      yesterday: [],
      prev7Days: [],
      older: []
    };

    filtered.forEach(chat => {
      const chatTime = new Date(chat.createdAt || chat.updatedAt).getTime();
      if (chatTime >= today) {
        groups.today.push(chat);
      } else if (chatTime >= yesterday) {
        groups.yesterday.push(chat);
      } else if (chatTime >= prev7Days) {
        groups.prev7Days.push(chat);
      } else {
        groups.older.push(chat);
      }
    });

    return groups;
  }, [conversations, searchQuery]);

  const renderChatGroup = (title: string, items: ChatConversation[]) => {
    if (items.length === 0) return null;

    return (
      <div className="space-y-1 mb-3">
        <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-gray-500">
          {title}
        </div>
        <div className="space-y-0.5">
          {items.map((chat) => {
            const isActive = chat.id === activeChatId;
            const isMenuOpen = activeMenuId === chat.id;

            return (
              <div
                key={chat.id}
                id={`chat-item-${chat.id}`}
                className="relative group"
                onMouseLeave={() => setActiveMenuId(null)}
              >
                <button
                  type="button"
                  onClick={() => {
                    onSelectChat(chat.id);
                    onCloseMobile();
                  }}
                  className={`w-full text-left px-3 py-2 rounded text-xs flex items-center gap-2 transition-colors cursor-pointer ${
                    isActive
                      ? 'bg-blue-900/20 text-blue-400 border-l-2 border-blue-500 font-medium'
                      : 'text-gray-400 hover:bg-white/5 hover:text-gray-200 border-l-2 border-transparent'
                  }`}
                >
                  <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-blue-400' : 'text-gray-500'}`} />
                  <span className="truncate flex-1">{chat.title}</span>
                </button>

                {/* Actions button (Rename, Delete) */}
                <div className={`absolute right-1.5 top-1.5 flex items-center ${
                  isActive || isMenuOpen ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                } transition-opacity`}>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveMenuId(activeMenuId === chat.id ? null : chat.id);
                    }}
                    className="p-1 rounded text-gray-500 hover:text-gray-200 hover:bg-gray-800 transition cursor-pointer"
                    title="Options"
                  >
                    <MoreVertical className="w-3.5 h-3.5" />
                  </button>

                  {/* Dropdown Menu */}
                  {isMenuOpen && (
                    <div className="absolute right-0 top-full mt-1 z-30 w-32 rounded-lg bg-[#1a1a1e] border border-gray-800 shadow-xl p-1 space-y-0.5 text-xs text-gray-200 backdrop-blur-md">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveMenuId(null);
                          onRenameChat(chat.id, chat.title);
                        }}
                        className="w-full px-2.5 py-1.5 rounded hover:bg-white/10 flex items-center gap-2 text-left cursor-pointer"
                      >
                        <Edit3 className="w-3.5 h-3.5 text-gray-400" />
                        <span>Rename</span>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveMenuId(null);
                          onDeleteChat(chat.id, chat.title);
                        }}
                        className="w-full px-2.5 py-1.5 rounded hover:bg-red-950/50 text-red-400 flex items-center gap-2 text-left cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        <span>Delete</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const hasAnyChats = 
    groupedConversations.today.length > 0 || 
    groupedConversations.yesterday.length > 0 || 
    groupedConversations.prev7Days.length > 0 || 
    groupedConversations.older.length > 0;

  const content = (
    <div className="flex flex-col h-full bg-[#141416] text-gray-300 border-r border-blue-900/30 select-none">
      {/* Top Header */}
      <div className="p-3.5 border-b border-blue-900/20 flex items-center justify-between">
        {!isCollapsed && <BrandLogo size="sm" />}
        {isCollapsed && (
          <button
            type="button"
            onClick={onToggleCollapse}
            className="mx-auto p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition cursor-pointer"
            title="Expand Sidebar"
          >
            <PanelLeft className="w-5 h-5 text-blue-400" />
          </button>
        )}

        <div className="flex items-center gap-1">
          {!isCollapsed && (
            <button
              type="button"
              onClick={onToggleCollapse}
              className="hidden lg:flex p-1.5 rounded text-gray-400 hover:text-white hover:bg-white/5 transition cursor-pointer"
              title="Collapse Sidebar"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          )}

          {/* Close mobile button */}
          <button
            type="button"
            onClick={onCloseMobile}
            className="lg:hidden p-1.5 rounded text-gray-400 hover:text-white hover:bg-white/5 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {!isCollapsed ? (
        <>
          {/* New Chat Button */}
          <div className="p-3">
            <button
              type="button"
              id="new-chat-button"
              onClick={() => {
                onNewChat();
                onCloseMobile();
              }}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-2 text-sm font-medium flex items-center justify-center gap-2 shadow-md transition-colors cursor-pointer group"
            >
              <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform" />
              <span>New Chat</span>
            </button>
          </div>

          {/* Search Input */}
          <div className="px-3 pb-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                id="search-chats-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search chats..."
                className="w-full pl-8 pr-3 py-1.5 rounded-md bg-black/40 border border-gray-800 text-xs text-gray-300 placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-2 text-gray-500 hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          {/* Chat History List */}
          <div className="flex-1 overflow-y-auto px-2 py-1 scrollbar-thin">
            {hasAnyChats ? (
              <>
                {renderChatGroup('Today', groupedConversations.today)}
                {renderChatGroup('Yesterday', groupedConversations.yesterday)}
                {renderChatGroup('Previous 7 Days', groupedConversations.prev7Days)}
                {renderChatGroup('Older', groupedConversations.older)}
              </>
            ) : (
              <div className="text-center py-8 px-4 text-xs text-gray-500 space-y-1">
                {searchQuery ? (
                  <p>No chats matching "{searchQuery}"</p>
                ) : (
                  <>
                    <MessageSquare className="w-6 h-6 mx-auto text-gray-600 mb-2" />
                    <p className="font-semibold text-gray-400">No chat history yet</p>
                    <p className="text-[11px] text-gray-500">Start a new conversation to verify AI claims.</p>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Footer controls: Settings + User Profile */}
          <div className="p-3 border-t border-blue-900/20 space-y-2 bg-[#141416]">
            <button
              type="button"
              id="sidebar-settings-button"
              onClick={onOpenSettings}
              className="w-full px-3 py-1.5 rounded text-xs font-medium text-gray-400 hover:bg-white/5 hover:text-white transition flex items-center justify-between cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <Settings className="w-4 h-4 text-gray-400" />
                <span>Settings</span>
              </div>
              <span className="text-[10px] text-gray-500 px-1.5 py-0.5 rounded bg-black/40 border border-gray-800">
                v1.0
              </span>
            </button>

            {/* Profile / Login Block */}
            {userProfile.isLoggedIn ? (
              <div className="p-2 bg-black/30 rounded-lg flex items-center justify-between gap-2 border border-gray-800/50 text-xs">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-8 h-8 rounded bg-blue-500 text-white flex items-center justify-center font-bold text-xs shrink-0">
                    {userProfile.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="font-bold text-white truncate text-xs">
                      {userProfile.name}
                    </div>
                    <div className="text-[10px] text-gray-500 truncate">
                      {userProfile.role}
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={onSignOut}
                  className="p-1.5 rounded text-gray-500 hover:text-red-400 hover:bg-white/5 transition cursor-pointer"
                  title="Sign Out"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => onOpenAuth('signin')}
                className="w-full py-2 px-3 rounded-lg bg-black/40 hover:bg-white/5 text-blue-400 text-xs font-semibold border border-gray-800 transition flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In / Profile</span>
              </button>
            )}
          </div>
        </>
      ) : (
        /* Collapsed Icon-Only View */
        <div className="flex-1 flex flex-col items-center py-4 space-y-3">
          <button
            type="button"
            onClick={onNewChat}
            className="p-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition shadow cursor-pointer"
            title="New Chat"
          >
            <Plus className="w-4 h-4" />
          </button>

          <div className="w-8 h-px bg-gray-800 my-1" />

          <button
            type="button"
            onClick={onOpenSettings}
            className="p-2.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition cursor-pointer"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          <div className="mt-auto pb-2">
            <button
              type="button"
              onClick={() => userProfile.isLoggedIn ? onOpenSettings() : onOpenAuth('signin')}
              className="w-8 h-8 rounded bg-blue-500 text-white flex items-center justify-center font-bold text-xs cursor-pointer"
              title={userProfile.isLoggedIn ? userProfile.name : 'Sign In'}
            >
              {userProfile.isLoggedIn ? userProfile.name.slice(0, 2).toUpperCase() : <User className="w-4 h-4" />}
            </button>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <div className={`hidden lg:block h-full transition-all duration-200 shrink-0 ${
        isCollapsed ? 'w-16' : 'w-64 xl:w-72'
      }`}>
        {content}
      </div>

      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex animate-in fade-in duration-150">
          <div
            className="fixed inset-0 bg-black/75 backdrop-blur-sm"
            onClick={onCloseMobile}
          />
          <div className="relative w-72 max-w-[85vw] h-full shadow-2xl z-10 animate-in slide-in-from-left duration-200">
            {content}
          </div>
        </div>
      )}
    </>
  );
};
