import React, { useState, useRef, useEffect, ChangeEvent, KeyboardEvent } from 'react';
import { Paperclip, Send, X, FileText, Image as ImageIcon, File, Loader2, Sparkles } from 'lucide-react';
import { AttachedFile, ModelId } from '../../types.ts';
import { ModelSelector } from './ModelSelector.tsx';

interface ChatInputProps {
  onSendMessage: (content: string, modelId: ModelId, attachments: AttachedFile[]) => void;
  isLoading: boolean;
  selectedModelId: ModelId;
  onSelectModel: (modelId: ModelId) => void;
  enterToSend?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  selectedModelId,
  onSelectModel,
  enterToSend = true
}) => {
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<AttachedFile[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea based on input height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      if (enterToSend && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newAttachments: AttachedFile[] = [];
    Array.from(files).forEach((file) => {
      // Basic size limit check: 15MB
      if (file.size > 15 * 1024 * 1024) {
        alert(`File "${file.name}" exceeds the 15MB size limit.`);
        return;
      }

      newAttachments.push({
        id: `att-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
        name: file.name,
        size: file.size,
        type: file.type || 'application/octet-stream',
        uploadedAt: new Date().toISOString()
      });
    });

    setAttachments(prev => [...prev, ...newAttachments]);
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments(prev => prev.filter(a => a.id !== id));
  };

  const handleSubmit = () => {
    const trimmed = input.trim();
    if ((!trimmed && attachments.length === 0) || isLoading) return;

    onSendMessage(trimmed, selectedModelId, attachments);
    setInput('');
    setAttachments([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const getFileIcon = (type: string, name: string) => {
    if (type.startsWith('image/')) return <ImageIcon className="w-3.5 h-3.5 text-blue-400" />;
    if (type.includes('pdf') || name.endsWith('.pdf')) return <FileText className="w-3.5 h-3.5 text-red-400" />;
    if (type.includes('word') || name.endsWith('.docx') || name.endsWith('.doc')) return <FileText className="w-3.5 h-3.5 text-blue-300" />;
    if (type.includes('text') || name.endsWith('.txt')) return <FileText className="w-3.5 h-3.5 text-emerald-400" />;
    return <File className="w-3.5 h-3.5 text-slate-400" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const isSubmitDisabled = (!input.trim() && attachments.length === 0) || isLoading;

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4 pt-2 bg-gradient-to-t from-[#050505] via-[#050505] to-transparent">
      <div className="relative rounded-2xl bg-[#111111] border border-gray-700/80 shadow-2xl shadow-blue-900/10 focus-within:border-blue-500 transition-colors">
        {/* Attachment chips preview */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 p-3 pb-0 border-b border-gray-800/80">
            {attachments.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-gray-800 border border-gray-700 text-xs text-gray-200 shadow-sm"
              >
                {getFileIcon(file.type, file.name)}
                <span className="max-w-[150px] truncate font-medium">{file.name}</span>
                <span className="text-[10px] text-gray-400">({formatFileSize(file.size)})</span>
                <button
                  type="button"
                  onClick={() => removeAttachment(file.id)}
                  className="p-0.5 rounded hover:bg-gray-700 text-gray-400 hover:text-red-400 transition cursor-pointer ml-1"
                  title="Remove attachment"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Text Input Area */}
        <div className="p-3.5 pb-2.5 flex flex-col">
          <textarea
            ref={textareaRef}
            id="chat-message-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask SkepticAI anything, or paste text/claims to verify..."
            rows={1}
            disabled={isLoading}
            className="w-full bg-transparent text-white placeholder-gray-500 text-sm sm:text-[15px] resize-none outline-none max-h-48 overflow-y-auto leading-relaxed"
          />

          {/* Controls Bar at bottom of input box */}
          <div className="flex items-center justify-between pt-2.5 border-t border-gray-800/80 mt-1 gap-2 flex-wrap sm:flex-nowrap">
            {/* Left Action: Attachments */}
            <div className="flex items-center gap-1.5">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                multiple
                accept=".pdf,.txt,.doc,.docx,image/*"
                className="hidden"
                id="file-attachment-input"
              />
              <button
                type="button"
                id="attach-file-button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition cursor-pointer flex items-center gap-1.5 text-xs font-medium"
                title="Attach PDF, TXT, DOCX, or Image"
              >
                <Paperclip className="w-4 h-4" />
                <span className="hidden sm:inline">Attach</span>
              </button>
            </div>

            {/* Middle Action: Model Selector */}
            <div className="flex items-center gap-2">
              <ModelSelector
                selectedModelId={selectedModelId}
                onSelectModel={onSelectModel}
              />
            </div>

            {/* Right Action: Send Button */}
            <div className="flex items-center gap-1.5 ml-auto">
              <button
                type="button"
                id="send-message-button"
                onClick={handleSubmit}
                disabled={isSubmitDisabled}
                className={`flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-150 cursor-pointer ${
                  isSubmitDisabled
                    ? 'bg-gray-800 text-gray-500 cursor-not-allowed opacity-60'
                    : 'bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/50 active:scale-95'
                }`}
                title={isLoading ? 'Generating response & analyzing claims...' : 'Send message (Enter)'}
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin text-blue-200" />
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-1.5" />
                    <span>Send</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between px-2 pt-1 text-[11px] text-gray-500">
        <span className="hidden sm:inline">
          Press <kbd className="px-1 py-0.5 rounded bg-gray-900 text-gray-400 font-mono text-[10px] border border-gray-800">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-gray-900 text-gray-400 font-mono text-[10px] border border-gray-800">Shift+Enter</kbd> for newline
        </span>
        <span className="ml-auto flex items-center gap-1 text-gray-500">
          <Sparkles className="w-3 h-3 text-blue-400" />
          Factual claims are cross-referenced in real-time
        </span>
      </div>
    </div>
  );
};
