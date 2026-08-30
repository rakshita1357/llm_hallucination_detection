import React from 'react';
import { 
  Menu, 
  Activity, 
  Sun, 
  Moon, 
  Share2, 
  ShieldAlert, 
  ShieldCheck, 
  MoreHorizontal, 
  Edit2, 
  RotateCcw,
  Sparkles,
  Layers
} from 'lucide-react';
import { ModelId } from '../../types.ts';
import { ModelSelector } from './ModelSelector.tsx';
import { BrandLogo } from '../BrandLogo.tsx';

interface ChatHeaderProps {
  chatTitle: string;
  selectedModelId: ModelId;
  onSelectModel: (modelId: ModelId) => void;
  onToggleSidebarMobile: () => void;
  isAnalysisOpen: boolean;
  onToggleAnalysis: () => void;
  hasFlaggedIssues?: boolean;
  flaggedCount?: number;
  theme: 'dark' | 'light' | 'system';
  onToggleTheme: () => void;
  onRenameTitle: () => void;
  onResetChat: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  chatTitle,
  selectedModelId,
  onSelectModel,
  onToggleSidebarMobile,
  isAnalysisOpen,
  onToggleAnalysis,
  hasFlaggedIssues = false,
  flaggedCount = 0,
  theme,
  onToggleTheme,
  onRenameTitle,
  onResetChat
}) => {
  return (
    <header className="h-14 border-b border-gray-800 bg-[#050505] px-4 sm:px-6 flex items-center justify-between gap-3 select-none z-20 shrink-0">
      {/* Left side: Mobile menu toggle + Chat Title */}
      <div className="flex items-center gap-2.5 min-w-0">
        <button
          type="button"
          id="mobile-sidebar-toggle"
          onClick={onToggleSidebarMobile}
          className="lg:hidden p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition cursor-pointer"
          title="Open Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 min-w-0">
          <div className="flex items-center gap-1.5 min-w-0 group cursor-pointer" onClick={onRenameTitle}>
            <h1 className="text-xs sm:text-sm font-bold text-white truncate max-w-[140px] sm:max-w-xs md:max-w-md">
              {chatTitle || 'New Conversation'}
            </h1>
            <Edit2 className="w-3 h-3 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
          </div>
        </div>
      </div>

      {/* Center: Model Selector in Header for wide screens */}
      <div className="hidden md:flex items-center">
        <ModelSelector
          selectedModelId={selectedModelId}
          onSelectModel={onSelectModel}
        />
      </div>

      {/* Right side: Action Buttons */}
      <div className="flex items-center gap-2">
        {/* Theme segmented control toggle */}
        <div className="flex bg-gray-900 rounded-lg p-0.5 border border-gray-800 text-xs">
          <button
            type="button"
            onClick={onToggleTheme}
            className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1 cursor-pointer ${
              theme === 'dark' || theme === 'system'
                ? 'bg-gray-800 text-gray-200 shadow-sm font-medium'
                : 'text-gray-500 hover:text-gray-300'
            }`}
            title="Dark Theme"
          >
            <Moon className="w-3.5 h-3.5 text-blue-400" />
            <span className="hidden sm:inline text-[11px]">Dark</span>
          </button>
          <button
            type="button"
            onClick={onToggleTheme}
            className={`px-2.5 py-1 rounded transition-colors flex items-center gap-1 cursor-pointer ${
              theme === 'light'
                ? 'bg-gray-800 text-gray-200 shadow-sm font-medium'
                : 'text-gray-500 hover:text-gray-300'
            }`}
            title="Light Theme"
          >
            <Sun className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden sm:inline text-[11px]">Light</span>
          </button>
        </div>

        {/* Reset Chat button */}
        <button
          type="button"
          id="reset-chat-button"
          onClick={onResetChat}
          className="hidden sm:flex p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition cursor-pointer"
          title="Start fresh message in this chat"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* Toggle Analysis Report Panel Button */}
        <button
          type="button"
          id="toggle-analysis-panel-button"
          onClick={onToggleAnalysis}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer shadow-sm ${
            isAnalysisOpen
              ? hasFlaggedIssues
                ? 'bg-red-600/20 text-red-400 border border-red-500/50'
                : 'bg-blue-600/20 text-blue-400 border border-blue-500/50'
              : hasFlaggedIssues
              ? 'bg-red-600 text-white animate-pulse'
              : 'bg-gray-900 text-gray-300 hover:text-white border border-gray-800'
          }`}
          title="Toggle Hallucination & Confidence Analysis Report"
        >
          {hasFlaggedIssues ? (
            <ShieldAlert className="w-3.5 h-3.5" />
          ) : (
            <Activity className="w-3.5 h-3.5" />
          )}
          <span className="hidden sm:inline">Analysis Report</span>
          {flaggedCount > 0 && (
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] font-black ${
              isAnalysisOpen ? 'bg-red-500 text-white' : 'bg-white text-red-600'
            }`}>
              {flaggedCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
};
