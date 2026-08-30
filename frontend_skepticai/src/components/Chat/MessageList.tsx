import React, { useEffect, useRef, useState } from 'react';
import { 
  User, 
  Sparkles, 
  Copy, 
  Check, 
  RotateCw, 
  ThumbsUp, 
  ThumbsDown, 
  ShieldAlert, 
  ShieldCheck, 
  AlertTriangle,
  FileText,
  Image as ImageIcon,
  ExternalLink,
  ChevronRight,
  Eye
} from 'lucide-react';
import { ChatMessage, AttachedFile } from '../../types.ts';
import { MarkdownMessage } from './MarkdownMessage.tsx';
import { AVAILABLE_MODELS } from '../../constants/models.ts';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onRegenerate: (messageId: string) => void;
  onFeedback: (messageId: string, feedback: 'like' | 'dislike') => void;
  onInspectAnalysis: (messageId: string) => void;
  activeAnalysisMessageId: string | null;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading,
  onRegenerate,
  onFeedback,
  onInspectAnalysis,
  activeAnalysisMessageId
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Auto-scroll on new messages or loading updates
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleCopy = async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  };

  const getModelBadge = (modelId?: string) => {
    const model = AVAILABLE_MODELS.find(m => m.id === modelId) || AVAILABLE_MODELS[0];
    return (
      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/60">
        {model.name}
      </span>
    );
  };

  const renderStatusPill = (message: ChatMessage) => {
    if (!message.analysis) return null;
    const { status, confidence, flaggedFindingsCount } = message.analysis;

    if (status === 'verified') {
      return (
        <button
          type="button"
          onClick={() => onInspectAnalysis(message.id)}
          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold transition cursor-pointer"
          title="Click to view detailed analysis"
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>{Math.round(confidence * 100)}% Verified</span>
          <ChevronRight className="w-3 h-3 opacity-60" />
        </button>
      );
    }

    if (status === 'mostly_reliable') {
      return (
        <button
          type="button"
          onClick={() => onInspectAnalysis(message.id)}
          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 text-xs font-semibold transition cursor-pointer"
          title="Click to view detailed analysis"
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>{Math.round(confidence * 100)}% Mostly Reliable</span>
          {flaggedFindingsCount && flaggedFindingsCount > 0 ? (
            <span className="px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 text-[10px]">
              {flaggedFindingsCount} note
            </span>
          ) : null}
        </button>
      );
    }

    if (status === 'partially_reliable') {
      return (
        <button
          type="button"
          onClick={() => onInspectAnalysis(message.id)}
          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-semibold transition cursor-pointer"
          title="Click to view detailed analysis"
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          <span>{Math.round(confidence * 100)}% Partially Reliable</span>
          <span className="px-1.5 py-0.2 rounded bg-amber-500/30 text-amber-200 text-[10px]">
            {flaggedFindingsCount} flagged
          </span>
        </button>
      );
    }

    if (status === 'potential_hallucination') {
      return (
        <button
          type="button"
          onClick={() => onInspectAnalysis(message.id)}
          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-red-500/15 hover:bg-red-500/25 text-red-400 border border-red-500/40 text-xs font-bold transition cursor-pointer animate-pulse"
          title="Warning: Potential hallucinations detected. Click to inspect."
        >
          <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
          <span>Potential Hallucination ({Math.round(confidence * 100)}%)</span>
          <span className="px-1.5 py-0.2 rounded bg-red-600 text-white text-[10px]">
            {flaggedFindingsCount} issues
          </span>
        </button>
      );
    }

    return null;
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 max-w-4xl mx-auto w-full">
      {messages.map((message) => {
        const isUser = message.role === 'user';
        const isActiveReport = activeAnalysisMessageId === message.id;

        return (
          <div
            key={message.id}
            id={`message-bubble-${message.id}`}
            className={`flex flex-col group ${isUser ? 'items-end' : 'items-start'}`}
          >
            {/* Message header info */}
            <div className={`flex items-center gap-2 mb-1.5 px-1 text-xs text-gray-400 ${isUser ? 'flex-row-reverse' : ''}`}>
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                isUser ? 'bg-gray-800 text-gray-300' : 'bg-gradient-to-br from-blue-600 to-red-600 text-white font-black text-[10px] shadow-sm'
              }`}>
                {isUser ? <User className="w-3.5 h-3.5" /> : 'SA'}
              </div>
              <span className="font-semibold text-gray-200">
                {isUser ? 'You' : 'SkepticAI'}
              </span>
              {!isUser && getModelBadge(message.modelId)}
              <span className="text-[11px] text-gray-500">{message.timestamp}</span>

              {/* Status pill on AI messages */}
              {!isUser && renderStatusPill(message)}
            </div>

            {/* Message Body Box */}
            <div
              className={`relative max-w-[92%] sm:max-w-[85%] rounded-2xl p-4 transition-all shadow-md ${
                isUser
                  ? 'bg-blue-600 text-white rounded-tr-none'
                  : `bg-[#111114] border text-gray-200 rounded-tl-none ${
                      isActiveReport
                        ? 'border-blue-500/60 ring-1 ring-blue-500/30'
                        : 'border-gray-800/80 hover:border-gray-700'
                    }`
              }`}
            >
              {/* If user attached files */}
              {isUser && message.attachments && message.attachments.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2.5 pb-2 border-b border-blue-400/30">
                  {message.attachments.map(att => (
                    <div
                      key={att.id}
                      className="flex items-center gap-1 px-2 py-0.5 rounded bg-blue-700/60 border border-blue-400/30 text-[11px] text-blue-100"
                    >
                      {att.type.startsWith('image/') ? (
                        <ImageIcon className="w-3 h-3 text-blue-200" />
                      ) : (
                        <FileText className="w-3 h-3 text-blue-200" />
                      )}
                      <span className="max-w-[130px] truncate">{att.name}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Message text / markdown */}
              {isUser ? (
                <p className="whitespace-pre-wrap text-sm sm:text-[15px] leading-relaxed font-normal">
                  {message.content}
                </p>
              ) : (
                <div className="text-sm sm:text-[15px]">
                  <MarkdownMessage content={message.content} />
                </div>
              )}

              {/* Bottom Action Toolbar for AI message */}
              {!isUser && (
                <div className="mt-3 pt-2.5 border-t border-gray-800/80 flex items-center justify-between text-gray-500 text-xs gap-2 flex-wrap">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      id={`copy-msg-${message.id}`}
                      onClick={() => handleCopy(message.id, message.content)}
                      className="hover:text-blue-400 transition cursor-pointer text-xs flex items-center gap-1"
                      title="Copy response text"
                    >
                      {copiedId === message.id ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-[11px] text-emerald-400">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span className="text-[11px] hidden sm:inline">Copy</span>
                        </>
                      )}
                    </button>

                    <button
                      type="button"
                      id={`regen-msg-${message.id}`}
                      onClick={() => onRegenerate(message.id)}
                      disabled={isLoading}
                      className="hover:text-blue-400 transition cursor-pointer text-xs flex items-center gap-1"
                      title="Regenerate response and re-verify"
                    >
                      <RotateCw className="w-3.5 h-3.5" />
                      <span className="text-[11px] hidden sm:inline">Regenerate</span>
                    </button>

                    <div className="h-3 w-px bg-gray-800" />

                    <button
                      type="button"
                      id={`like-msg-${message.id}`}
                      onClick={() => onFeedback(message.id, 'like')}
                      className={`hover:text-blue-400 transition cursor-pointer ${
                        message.feedback === 'like' ? 'text-emerald-400' : 'text-gray-500'
                      }`}
                      title="Good response"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>

                    <button
                      type="button"
                      id={`dislike-msg-${message.id}`}
                      onClick={() => onFeedback(message.id, 'dislike')}
                      className={`hover:text-red-400 transition cursor-pointer ${
                        message.feedback === 'dislike' ? 'text-red-400' : 'text-gray-500'
                      }`}
                      title="Poor response or factual inaccuracies"
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Analysis panel shortcut */}
                  {message.analysis && (
                    <button
                      type="button"
                      id={`inspect-analysis-${message.id}`}
                      onClick={() => onInspectAnalysis(message.id)}
                      className={`px-2.5 py-1 rounded text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                        message.analysis.status === 'potential_hallucination'
                          ? 'bg-red-500/15 text-red-400 hover:bg-red-500/25 border border-red-500/30'
                          : 'bg-gray-900 text-blue-400 hover:bg-gray-800 border border-gray-800'
                      }`}
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect Report</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}

      <div ref={bottomRef} />
    </div>
  );
};
