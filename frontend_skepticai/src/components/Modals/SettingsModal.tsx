import React, { useState } from 'react';
import { 
  X, 
  Moon, 
  Sun, 
  Laptop, 
  Sliders, 
  ShieldCheck, 
  Database, 
  Trash2, 
  Check, 
  Download,
  User,
  LogOut,
  Sparkles
} from 'lucide-react';
import { UserProfile, UserSettings, ModelId } from '../../types.ts';
import { AVAILABLE_MODELS } from '../../constants/models.ts';
import { logout } from '../../services/apiService.ts';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: UserSettings;
  onUpdateSettings: (newSettings: Partial<UserSettings>) => void;
  userProfile: UserProfile;
  onSignOut: () => void;
  onClearHistory: () => void;
  conversationsJsonString: string;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onUpdateSettings,
  userProfile,
  onSignOut,
  onClearHistory,
  conversationsJsonString
}) => {
  const [activeTab, setActiveTab] = useState<'appearance' | 'chat' | 'analysis' | 'account' | 'data'>('appearance');
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [copiedExport, setCopiedExport] = useState(false);

  if (!isOpen) return null;

  const handleExport = () => {
    const blob = new Blob([conversationsJsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `skepticai-conversations-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setCopiedExport(true);
    setTimeout(() => setCopiedExport(false), 2500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-2xl rounded-2xl bg-[#141416] border border-gray-800 shadow-2xl overflow-hidden flex flex-col md:flex-row max-h-[85vh] text-gray-200">
        {/* Mobile / Desktop Close */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-3 right-3 p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition cursor-pointer z-10"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Sidebar navigation tabs */}
        <div className="w-full md:w-52 bg-[#0c0c0e] p-4 border-b md:border-b-0 md:border-r border-gray-800 flex md:flex-col gap-1 overflow-x-auto">
          <div className="hidden md:block text-xs font-bold uppercase tracking-wider text-gray-400 px-3 py-2">
            Settings
          </div>

          <button
            type="button"
            onClick={() => setActiveTab('appearance')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition cursor-pointer text-left whitespace-nowrap ${
              activeTab === 'appearance' ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30' : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Moon className="w-4 h-4" />
            <span>Appearance</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('chat')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition cursor-pointer text-left whitespace-nowrap ${
              activeTab === 'chat' ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30' : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Sliders className="w-4 h-4" />
            <span>Chat Preferences</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('analysis')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition cursor-pointer text-left whitespace-nowrap ${
              activeTab === 'analysis' ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30' : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Analysis Report</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('account')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition cursor-pointer text-left whitespace-nowrap ${
              activeTab === 'account' ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30' : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <User className="w-4 h-4" />
            <span>Account</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('data')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition cursor-pointer text-left whitespace-nowrap ${
              activeTab === 'data' ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30' : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>Data & Privacy</span>
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {/* Appearance Tab */}
          {activeTab === 'appearance' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white">Interface Theme</h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Select your preferred color scheme for SkepticAI.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => onUpdateSettings({ theme: 'dark' })}
                  className={`p-3.5 rounded-xl border flex flex-col items-center gap-2 cursor-pointer transition ${
                    settings.theme === 'dark'
                      ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                      : 'bg-black/40 border-gray-800 text-gray-400 hover:border-gray-700'
                  }`}
                >
                  <Moon className="w-5 h-5" />
                  <span className="text-xs font-semibold">Dark (Default)</span>
                </button>

                <button
                  type="button"
                  onClick={() => onUpdateSettings({ theme: 'light' })}
                  className={`p-3.5 rounded-xl border flex flex-col items-center gap-2 cursor-pointer transition ${
                    settings.theme === 'light'
                      ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                      : 'bg-black/40 border-gray-800 text-gray-400 hover:border-gray-700'
                  }`}
                >
                  <Sun className="w-5 h-5" />
                  <span className="text-xs font-semibold">Light</span>
                </button>

                <button
                  type="button"
                  onClick={() => onUpdateSettings({ theme: 'system' })}
                  className={`p-3.5 rounded-xl border flex flex-col items-center gap-2 cursor-pointer transition ${
                    settings.theme === 'system'
                      ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                      : 'bg-black/40 border-gray-800 text-gray-400 hover:border-gray-700'
                  }`}
                >
                  <Laptop className="w-5 h-5" />
                  <span className="text-xs font-semibold">System</span>
                </button>
              </div>

              <div className="p-3 rounded-xl bg-black/40 border border-gray-800/80 text-xs text-gray-300">
                <span className="font-semibold text-blue-400">Visual Palette:</span> Professional dark theme using refined high-contrast surfaces (#0a0a0a / #141416), blue badges, and red contradiction warnings.
              </div>
            </div>
          )}

          {/* Chat Tab */}
          {activeTab === 'chat' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white">Chat Preferences</h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Configure default model and input interaction behavior.
                </p>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1.5">
                    Default AI Model
                  </label>
                  <select
                    value={settings.defaultModel}
                    onChange={(e) => onUpdateSettings({ defaultModel: e.target.value as ModelId })}
                    className="w-full p-2.5 rounded-xl bg-black/40 border border-gray-800 text-xs text-white focus:border-blue-500 outline-none"
                  >
                    {AVAILABLE_MODELS.map(m => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({m.provider})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-black/40 border border-gray-800">
                  <div>
                    <div className="text-xs font-semibold text-white">Enter to Send</div>
                    <div className="text-[11px] text-gray-400">
                      Pressing Enter sends the message; Shift+Enter creates a new line.
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.enterToSend}
                    onChange={(e) => onUpdateSettings({ enterToSend: e.target.checked })}
                    className="rounded border-gray-700 bg-gray-900 text-blue-600 focus:ring-0 cursor-pointer w-4 h-4"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Analysis Report Tab */}
          {activeTab === 'analysis' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white">Verification & Hallucination Settings</h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Tune the hallucination detection pipeline and report display.
                </p>
              </div>

              <div className="space-y-2.5">
                <div className="flex items-center justify-between p-3 rounded-xl bg-black/40 border border-gray-800">
                  <div>
                    <div className="text-xs font-semibold text-white">Enable Right-Side Analysis Panel</div>
                    <div className="text-[11px] text-gray-400">
                      Displays confidence gauge and flagged findings beside chat.
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.enableAnalysisReport}
                    onChange={(e) => onUpdateSettings({ enableAnalysisReport: e.target.checked })}
                    className="rounded border-gray-700 bg-gray-900 text-blue-600 focus:ring-0 cursor-pointer w-4 h-4"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-black/40 border border-gray-800">
                  <div>
                    <div className="text-xs font-semibold text-white">Show Numerical Confidence Scores</div>
                    <div className="text-[11px] text-gray-400">
                      Include calibrated % metrics alongside qualitative statuses.
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.showConfidenceScores}
                    onChange={(e) => onUpdateSettings({ showConfidenceScores: e.target.checked })}
                    className="rounded border-gray-700 bg-gray-900 text-blue-600 focus:ring-0 cursor-pointer w-4 h-4"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-black/40 border border-gray-800">
                  <div>
                    <div className="text-xs font-semibold text-white">Include Citation Evidence Snippets</div>
                    <div className="text-[11px] text-gray-400">
                      Retrieve and display verbatim knowledge graph passages.
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.showEvidenceSources}
                    onChange={(e) => onUpdateSettings({ showEvidenceSources: e.target.checked })}
                    className="rounded border-gray-700 bg-gray-900 text-blue-600 focus:ring-0 cursor-pointer w-4 h-4"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Account Tab */}
          {activeTab === 'account' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white">User Account</h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Manage your researcher credentials and active session.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-black/40 border border-gray-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center font-bold text-sm">
                    {userProfile.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white">{userProfile.name}</div>
                    <div className="text-[11px] text-gray-400">{userProfile.email}</div>
                    <div className="text-[10px] text-blue-400 mt-0.5">{userProfile.role}</div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={async () => {
                    await logout();
                    onSignOut();
                    onClose();
                  }}
                  className="px-3 py-1.5 rounded-lg bg-red-950/40 hover:bg-red-900/60 border border-red-500/30 text-red-300 text-xs font-semibold transition cursor-pointer flex items-center gap-1.5"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}

          {/* Data & Privacy Tab */}
          {activeTab === 'data' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white">Data Management</h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Export or wipe local conversation logs and audit reports.
                </p>
              </div>

              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-black/40 border border-gray-800 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-semibold text-white">Export All Conversations</div>
                    <div className="text-[11px] text-gray-400">
                      Download complete chat logs with claim verification metadata as JSON.
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleExport}
                    className="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-white text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 shrink-0"
                  >
                    {copiedExport ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400">Exported</span>
                      </>
                    ) : (
                      <>
                        <Download className="w-3.5 h-3.5" />
                        <span>Export JSON</span>
                      </>
                    )}
                  </button>
                </div>

                <div className="p-3.5 rounded-xl bg-red-950/20 border border-red-500/30 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-semibold text-red-300">Clear Chat History</div>
                    <div className="text-[11px] text-gray-400">
                      Permanently delete all stored chats and analysis records.
                    </div>
                  </div>
                  {showClearConfirm ? (
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          onClearHistory();
                          setShowClearConfirm(false);
                          onClose();
                        }}
                        className="px-2.5 py-1 rounded bg-red-600 hover:bg-red-500 text-white text-xs font-bold transition cursor-pointer"
                      >
                        Confirm Delete
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowClearConfirm(false)}
                        className="px-2 py-1 rounded bg-gray-800 text-gray-300 text-xs hover:bg-gray-700 transition cursor-pointer"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setShowClearConfirm(true)}
                      className="px-3 py-1.5 rounded-lg bg-red-600/20 hover:bg-red-600/40 border border-red-500/40 text-red-300 text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 shrink-0"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Clear All</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
