import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { TopBar } from '@/components/TopBar';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { AnalysisPanel } from '@/components/analysis/AnalysisPanel';
import { ToastProvider } from '@/context/ToastContext';
import { sendMessage } from '@/services/api';
import type { AIModel, Chat, Message, AnalysisReport } from '@/types';

// Utility to generate simple IDs
const genId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;

const AVAILABLE_MODELS: AIModel[] = [
  { id: 'gpt-4o', name: 'GPT‑4o' },
  { id: 'gemini', name: 'Gemini' },
  { id: 'claude', name: 'Claude' },
  { id: 'chatgpt', name: 'ChatGPT' },
];

const App: React.FC = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<string>(AVAILABLE_MODELS[0].id);
  const [isLoading, setIsLoading] = useState(false);

  // Load persisted chats from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('halluguard-chats');
    if (stored) {
      try {
        const parsed: Chat[] = JSON.parse(stored);
        setChats(parsed);
        if (parsed.length > 0) setSelectedChatId(parsed[0].id);
      } catch {
        // ignore malformed data
      }
    }
  }, []);

  // Persist chats on change
  useEffect(() => {
    localStorage.setItem('halluguard-chats', JSON.stringify(chats));
  }, [chats]);

  const currentChat = chats.find((c) => c.id === selectedChatId) ?? null;
  const selectedModel = AVAILABLE_MODELS.find((m) => m.id === selectedModelId) ?? AVAILABLE_MODELS[0];

  const createNewChat = useCallback(() => {
    const newChat: Chat = {
      id: genId(),
      title: 'New Chat',
      modelId: selectedModelId,
      messages: [],
    };
    setChats((prev) => [newChat, ...prev]);
    setSelectedChatId(newChat.id);
  }, [selectedModelId]);

  const selectChat = (id: string) => {
    setSelectedChatId(id);
    const chat = chats.find((c) => c.id === id);
    if (chat) setSelectedModelId(chat.modelId);
  };

  const handleModelChange = (modelId: string) => {
    setSelectedModelId(modelId);
    if (currentChat) {
      // Update model associated with current chat
      setChats((prev) =>
        prev.map((c) => (c.id === currentChat.id ? { ...c, modelId } : c))
      );
    }
  };

  const handleSend = async (content: string) => {
    if (!selectedChatId) return;
    const userMsg: Message = {
      id: genId(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    // Add user message optimistically
    setChats((prev) =>
      prev.map((c) => (c.id === selectedChatId ? { ...c, messages: [...c.messages, userMsg] } : c))
    );
    setIsLoading(true);
    try {
      const resp = await sendMessage(selectedChatId, selectedModelId, content);
      const assistantMsg: Message = {
        id: genId(),
        role: 'assistant',
        content: resp.answer,
        timestamp: new Date().toISOString(),
      };
      const updatedChat: Chat = {
        ...currentChat!,
        messages: [...currentChat!.messages, assistantMsg],
        analysis: resp.analysis,
      };
      setChats((prev) => prev.map((c) => (c.id === selectedChatId ? updatedChat : c)));
    } catch (e) {
      console.error(e);
      // Minimal error handling – toast could be added via context if needed
    } finally {
      setIsLoading(false);
    }
  };

    // Regenerate the last assistant response using the previous user message
  const handleRegenerate = async () => {
    if (!selectedChatId || !currentChat) return;
    // Find the most recent user message
    const lastUserMsg = [...currentChat.messages].reverse().find((m) => m.role === 'user');
    if (!lastUserMsg) return;
    setIsLoading(true);
    try {
      const resp = await sendMessage(selectedChatId, selectedModelId, lastUserMsg.content);
      const newAssistantMsg: Message = {
        id: genId(),
        role: 'assistant',
        content: resp.answer,
        timestamp: new Date().toISOString(),
      };
      // Replace the previous assistant message (assumed to be the last one)
      const updatedMessages = currentChat.messages.slice(0, -1).concat(newAssistantMsg);
      const updatedChat: Chat = { ...currentChat, messages: updatedMessages, analysis: resp.analysis };
      setChats((prev) => prev.map((c) => (c.id === selectedChatId ? updatedChat : c)));
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  // Theme handling – stored in localStorage
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('halluguard-theme');
    return saved ? saved === 'dark' : true; // default dark
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('halluguard-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  const toggleTheme = () => setIsDark((prev) => !prev);

  return (
    <ToastProvider>
      <div className={`flex h-screen overflow-hidden \${isDark ? 'bg-primary text-white' : 'bg-white text-gray-900'}`}>
        <Sidebar
          chats={chats.map((c) => ({ id: c.id, title: c.title }))}
          selectedChatId={selectedChatId}
          onSelectChat={selectChat}
          onNewChat={createNewChat}
          currentModel={selectedModel}
        />
        <div className="flex flex-col flex-1">
          <TopBar
            models={AVAILABLE_MODELS}
            selectedModelId={selectedModelId}
            onModelChange={handleModelChange}
            onToggleTheme={toggleTheme}
            isDark={isDark}
          />
          <div className="grid flex-1 overflow-hidden grid-cols-1 lg:grid-cols-2">
            <ChatPanel
              messages={currentChat?.messages ?? []}
              onSend={handleSend}
              isLoading={isLoading}
              selectedModelName={selectedModel.name}
              onRegenerate={handleRegenerate}
            />
            <AnalysisPanel analysis={currentChat?.analysis ?? null} isLoading={isLoading} />
          </div>
        </div>
      </div>
    </ToastProvider>


  );
};

export default App;
