import React, { useState, useEffect, useMemo } from 'react';
import { 
  ChatConversation, 
  ChatMessage, 
  ModelId, 
  UserSettings, 
  UserProfile, 
  AttachedFile, 
  AnalysisReportData 
} from './types.ts';
import { storageService, DEFAULT_SETTINGS, DEFAULT_USER } from './services/storageService.ts';
import { sendChatMessage } from './services/apiService.ts';
import { AVAILABLE_MODELS, DEFAULT_MODEL_ID } from './constants/models.ts';
import { Sidebar } from './components/Sidebar/Sidebar.tsx';
import { ChatHeader } from './components/Chat/ChatHeader.tsx';
import { MessageList } from './components/Chat/MessageList.tsx';
import { ChatInput } from './components/Chat/ChatInput.tsx';
import { EmptyState } from './components/Chat/EmptyState.tsx';
import { AnalysisPanel } from './components/AnalysisPanel/AnalysisPanel.tsx';
import { AuthModal } from './components/Modals/AuthModal.tsx';
import { SettingsModal } from './components/Modals/SettingsModal.tsx';
import { RenameModal } from './components/Modals/RenameModal.tsx';
import { DeleteModal } from './components/Modals/DeleteModal.tsx';

export default function App() {
  // Application State
  const [conversations, setConversations] = useState<ChatConversation[]>(() => storageService.getConversations());
  const [activeChatId, setActiveChatId] = useState<string | null>(() => storageService.getActiveChatId() || 'chat-today-01');
  const [settings, setSettings] = useState<UserSettings>(() => storageService.getSettings());
  const [userProfile, setUserProfile] = useState<UserProfile>(() => storageService.getUserProfile());
  const [selectedModelId, setSelectedModelId] = useState<ModelId>(settings.defaultModel || DEFAULT_MODEL_ID);

  // Execution & Step Animation State
  const [isLoading, setIsLoading] = useState(false);
  const [currentAnalysisStep, setCurrentAnalysisStep] = useState<number>(0);
  const [activeAnalysisMessageId, setActiveAnalysisMessageId] = useState<string | null>(null);

  // Layout & Responsive States
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isAnalysisPanelOpen, setIsAnalysisPanelOpen] = useState(true);

  // Modals
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'signin' | 'signup'>('signin');
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [renameChatTarget, setRenameChatTarget] = useState<{ id: string; title: string } | null>(null);
  const [deleteChatTarget, setDeleteChatTarget] = useState<{ id: string; title: string } | null>(null);

  // Sync active conversation
  const activeConversation = useMemo(() => {
    return conversations.find(c => c.id === activeChatId) || null;
  }, [conversations, activeChatId]);

  // Find currently active message to display in the Analysis Report
  const currentAnalysisData = useMemo<AnalysisReportData | null>(() => {
    if (!activeConversation) return null;

    if (activeAnalysisMessageId) {
      const msg = activeConversation.messages.find(m => m.id === activeAnalysisMessageId);
      if (msg && msg.analysis) return msg.analysis;
    }

    // Default to the latest assistant message that contains analysis
    const assistantMessages = activeConversation.messages.filter(m => m.role === 'assistant' && m.analysis);
    if (assistantMessages.length > 0) {
      return assistantMessages[assistantMessages.length - 1].analysis || null;
    }

    return null;
  }, [activeConversation, activeAnalysisMessageId]);

  // Flagged issues count in current report
  const flaggedCount = currentAnalysisData?.findings?.length || 0;
  const hasFlaggedIssues = flaggedCount > 0;

  // Persist conversation updates
  useEffect(() => {
    storageService.saveConversations(conversations);
  }, [conversations]);

  useEffect(() => {
    storageService.setActiveChatId(activeChatId);
  }, [activeChatId]);

  useEffect(() => {
    storageService.saveSettings(settings);
    // Apply Theme
    const root = document.documentElement;
    if (settings.theme === 'light') {
      root.classList.remove('dark');
      root.classList.add('light');
    } else if (settings.theme === 'dark') {
      root.classList.remove('light');
      root.classList.add('dark');
    } else {
      // System
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('dark', isDark);
      root.classList.toggle('light', !isDark);
    }
  }, [settings]);

  useEffect(() => {
    storageService.saveUserProfile(userProfile);
  }, [userProfile]);

  // Handle Model Selection
  const handleSelectModel = (modelId: ModelId) => {
    setSelectedModelId(modelId);
    if (activeConversation) {
      setConversations(prev => prev.map(c => c.id === activeConversation.id ? { ...c, modelId } : c));
    }
  };

  // Start New Chat
  const handleNewChat = () => {
    setActiveChatId(null);
    setActiveAnalysisMessageId(null);
    setIsMobileSidebarOpen(false);
  };

  // Select Existing Chat
  const handleSelectChat = (id: string) => {
    setActiveChatId(id);
    const chat = conversations.find(c => c.id === id);
    if (chat) {
      setSelectedModelId(chat.modelId);
      // Pick latest assistant message
      const latestAi = [...chat.messages].reverse().find(m => m.role === 'assistant' && m.analysis);
      if (latestAi) {
        setActiveAnalysisMessageId(latestAi.id);
      } else {
        setActiveAnalysisMessageId(null);
      }
    }
  };

  // Rename Chat
  const handleSaveRename = (newTitle: string) => {
    if (!renameChatTarget) return;
    setConversations(prev => prev.map(c => 
      c.id === renameChatTarget.id ? { ...c, title: newTitle, updatedAt: new Date().toISOString() } : c
    ));
    setRenameChatTarget(null);
  };

  // Delete Chat
  const handleConfirmDelete = () => {
    if (!deleteChatTarget) return;
    const remaining = conversations.filter(c => c.id !== deleteChatTarget.id);
    setConversations(remaining);
    if (activeChatId === deleteChatTarget.id) {
      setActiveChatId(remaining.length > 0 ? remaining[0].id : null);
      setActiveAnalysisMessageId(null);
    }
    setDeleteChatTarget(null);
  };

  // Send Message workflow
  const handleSendMessage = async (
    prompt: string, 
    modelId: ModelId, 
    attachments: AttachedFile[] = []
  ) => {
    if (isLoading) return;

    let targetChatId = activeChatId;
    let currentMessages: ChatMessage[] = [];

    const userMessage: ChatMessage = {
      id: `msg-user-${Date.now()}`,
      role: 'user',
      content: prompt,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      attachments
    };

    // If starting a brand new conversation
    if (!targetChatId || !conversations.some(c => c.id === targetChatId)) {
      const generatedTitle = prompt.length > 35 ? `${prompt.slice(0, 35)}...` : prompt || 'New Fact Check';
      const newChat: ChatConversation = {
        id: `chat-${Date.now()}`,
        title: generatedTitle,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        modelId,
        messages: [userMessage]
      };
      setConversations(prev => [newChat, ...prev]);
      setActiveChatId(newChat.id);
      targetChatId = newChat.id;
      currentMessages = [userMessage];
    } else {
      // Append user message to existing conversation
      setConversations(prev => prev.map(c => {
        if (c.id === targetChatId) {
          currentMessages = [...c.messages, userMessage];
          return {
            ...c,
            updatedAt: new Date().toISOString(),
            messages: currentMessages
          };
        }
        return c;
      }));
    }

    // Begin Loading & Stepped Verification Pipeline
    setIsLoading(true);
    setCurrentAnalysisStep(0);

    try {
      const result = await sendChatMessage(
        prompt,
        modelId,
        attachments,
        currentMessages,
        settings.customBackendUrl,
        settings.useLiveBackend,
        (step) => {
          setCurrentAnalysisStep(step);
        }
      );

      const assistantMessage: ChatMessage = {
        id: `msg-ai-${Date.now()}`,
        role: 'assistant',
        modelId,
        content: result.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        analysisStatus: 'completed',
        analysis: result.analysis
      };

      setConversations(prev => prev.map(c => {
        if (c.id === targetChatId) {
          return {
            ...c,
            updatedAt: new Date().toISOString(),
            messages: [...c.messages, assistantMessage]
          };
        }
        return c;
      }));

      // Focus on this new analysis
      setActiveAnalysisMessageId(assistantMessage.id);

      // If hallucination detected or settings require, ensure right panel is open
      if (result.analysis.status === 'potential_hallucination' || settings.enableAnalysisReport) {
        setIsAnalysisPanelOpen(true);
      }
    } catch (err) {
      console.error('Error generating chat message:', err);
      const errorMessage: ChatMessage = {
        id: `msg-err-${Date.now()}`,
        role: 'assistant',
        modelId,
        content: 'An error occurred while connecting to the verification engine. Please check your network or custom backend endpoint.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        analysisStatus: 'unavailable',
        analysis: {
          confidence: 0,
          status: 'analysis_unavailable',
          findings: []
        }
      };

      setConversations(prev => prev.map(c => {
        if (c.id === targetChatId) {
          return {
            ...c,
            messages: [...c.messages, errorMessage]
          };
        }
        return c;
      }));
    } finally {
      setIsLoading(false);
    }
  };

  // Regenerate Response
  const handleRegenerate = async (messageId: string) => {
    if (!activeConversation || isLoading) return;
    const msgIndex = activeConversation.messages.findIndex(m => m.id === messageId);
    if (msgIndex === -1) return;

    // Find the prompt that triggered this response
    const priorUserMsg = activeConversation.messages.slice(0, msgIndex).reverse().find(m => m.role === 'user');
    if (!priorUserMsg) return;

    // Remove old AI response and re-send
    const prunedMessages = activeConversation.messages.filter(m => m.id !== messageId);
    setConversations(prev => prev.map(c => c.id === activeConversation.id ? { ...c, messages: prunedMessages } : c));

    await handleSendMessage(priorUserMsg.content, selectedModelId, priorUserMsg.attachments);
  };

  // Message Feedback
  const handleFeedback = (messageId: string, feedback: 'like' | 'dislike') => {
    if (!activeConversation) return;
    setConversations(prev => prev.map(c => {
      if (c.id === activeConversation.id) {
        return {
          ...c,
          messages: c.messages.map(m => {
            if (m.id === messageId) {
              return {
                ...m,
                feedback: m.feedback === feedback ? null : feedback
              };
            }
            return m;
          })
        };
      }
      return c;
    }));
  };

  // Inspect analysis for specific message
  const handleInspectAnalysis = (messageId: string) => {
    setActiveAnalysisMessageId(messageId);
    setIsAnalysisPanelOpen(true);
  };

  // Theme switch shortcut
  const handleToggleTheme = () => {
    const nextTheme = settings.theme === 'dark' ? 'light' : 'dark';
    setSettings(prev => ({ ...prev, theme: nextTheme }));
  };

  return (
    <div className={`flex h-screen w-screen overflow-hidden ${
      settings.theme === 'light' ? 'bg-gray-100 text-gray-900' : 'bg-[#0c0c0e] text-gray-100'
    }`}>
      {/* 1. LEFT SIDEBAR (Collapsible, Drawer on mobile) */}
      <Sidebar
        conversations={conversations}
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onRenameChat={(id, title) => setRenameChatTarget({ id, title })}
        onDeleteChat={(id, title) => setDeleteChatTarget({ id, title })}
        userProfile={userProfile}
        onOpenSettings={() => setIsSettingsModalOpen(true)}
        onOpenAuth={(mode) => {
          setAuthModalMode(mode || 'signin');
          setIsAuthModalOpen(true);
        }}
        onSignOut={() => setUserProfile({ ...DEFAULT_USER, isLoggedIn: false })}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        isMobileOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      {/* 2. CENTER CHAT AREA (Receives majority of screen width) */}
      <main className="flex-1 flex flex-col min-w-0 h-full relative overflow-hidden bg-[#0a0a0a]">
        <ChatHeader
          chatTitle={activeConversation ? activeConversation.title : 'New Chat'}
          selectedModelId={selectedModelId}
          onSelectModel={handleSelectModel}
          onToggleSidebarMobile={() => setIsMobileSidebarOpen(true)}
          isAnalysisOpen={isAnalysisPanelOpen}
          onToggleAnalysis={() => setIsAnalysisPanelOpen(!isAnalysisPanelOpen)}
          hasFlaggedIssues={hasFlaggedIssues}
          flaggedCount={flaggedCount}
          theme={settings.theme}
          onToggleTheme={handleToggleTheme}
          onRenameTitle={() => {
            if (activeConversation) {
              setRenameChatTarget({ id: activeConversation.id, title: activeConversation.title });
            }
          }}
          onResetChat={handleNewChat}
        />

        {/* Messages or Empty State */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {activeConversation && activeConversation.messages.length > 0 ? (
            <MessageList
              messages={activeConversation.messages}
              isLoading={isLoading}
              onRegenerate={handleRegenerate}
              onFeedback={handleFeedback}
              onInspectAnalysis={handleInspectAnalysis}
              activeAnalysisMessageId={activeAnalysisMessageId}
            />
          ) : (
            <EmptyState
              onSelectPrompt={(prompt, model) => {
                if (model) setSelectedModelId(model);
                handleSendMessage(prompt, model || selectedModelId);
              }}
            />
          )}

          {/* Fixed Input at Bottom */}
          <ChatInput
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            selectedModelId={selectedModelId}
            onSelectModel={handleSelectModel}
            enterToSend={settings.enterToSend}
          />
        </div>
      </main>

      {/* 3. RIGHT-SIDE ANALYSIS REPORT PANEL (Noticeably smaller, secondary verification layer) */}
      {isAnalysisPanelOpen && (
        <>
          {/* Desktop / Tablet docked sidebar */}
          <div className="hidden md:block w-80 lg:w-96 shrink-0 h-full">
            <AnalysisPanel
              analysisData={currentAnalysisData}
              isLoading={isLoading}
              currentStep={currentAnalysisStep}
              onClose={() => setIsAnalysisPanelOpen(false)}
            />
          </div>

          {/* Mobile slide-over drawer / bottom sheet */}
          <div className="md:hidden fixed inset-0 z-40 flex justify-end">
            <div
              className="fixed inset-0 bg-black/70 backdrop-blur-sm animate-in fade-in"
              onClick={() => setIsAnalysisPanelOpen(false)}
            />
            <div className="relative w-full max-w-sm h-full shadow-2xl z-10 animate-in slide-in-from-right duration-200">
              <AnalysisPanel
                analysisData={currentAnalysisData}
                isLoading={isLoading}
                currentStep={currentAnalysisStep}
                onClose={() => setIsAnalysisPanelOpen(false)}
                isMobile={true}
              />
            </div>
          </div>
        </>
      )}

      {/* MODALS */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onLogin={(profile) => setUserProfile(profile)}
        initialMode={authModalMode}
      />

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        settings={settings}
        onUpdateSettings={(newSettings) => setSettings(prev => ({ ...prev, ...newSettings }))}
        userProfile={userProfile}
        onSignOut={() => setUserProfile({ ...DEFAULT_USER, isLoggedIn: false })}
        onClearHistory={() => {
          storageService.clearAllData();
          setConversations([]);
          setActiveChatId(null);
          setActiveAnalysisMessageId(null);
        }}
        conversationsJsonString={JSON.stringify(conversations, null, 2)}
      />

      <RenameModal
        isOpen={!!renameChatTarget}
        currentTitle={renameChatTarget?.title || ''}
        onClose={() => setRenameChatTarget(null)}
        onSave={handleSaveRename}
      />

      <DeleteModal
        isOpen={!!deleteChatTarget}
        chatTitle={deleteChatTarget?.title || ''}
        onClose={() => setDeleteChatTarget(null)}
        onConfirm={handleConfirmDelete}
      />
    </div>
  );
}
