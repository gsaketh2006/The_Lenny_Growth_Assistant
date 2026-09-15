import React, { useState } from 'react';
import { X, Key, Cpu, ShieldCheck, Check, Sparkles, User as UserIcon, LogOut, ArrowRight, Zap, Globe } from 'lucide-react';
import { ProviderInfo, User } from '../../types';
import { selectProvider, addCustomProvider, loginUser, registerUser } from '../../services/api';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  providers: ProviderInfo[];
  selectedProvider: string;
  onProviderChanged: (providerId: string) => void;
  onRefreshProviders: () => void;
  currentUser: User | null;
  onAuthSuccess: (user: User) => void;
  onLogout: () => void;
  initialTab?: 'engine' | 'account';
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  providers,
  selectedProvider,
  onProviderChanged,
  onRefreshProviders,
  currentUser,
  onAuthSuccess,
  onLogout,
  initialTab = 'engine',
}) => {
  const [activeTab, setActiveTab] = useState<'engine' | 'account'>(initialTab);
  
  // Engine Form State
  const [providerType, setProviderType] = useState<string>(selectedProvider);
  const [apiKey, setApiKey] = useState<string>('');
  const [customModel, setCustomModel] = useState<string>('');
  const [customBaseUrl, setCustomBaseUrl] = useState<string>('');
  const [savingEngine, setSavingEngine] = useState<boolean>(false);
  const [engineSuccessMsg, setEngineSuccessMsg] = useState<string | null>(null);

  // Auth Form State
  const [isRegisterMode, setIsRegisterMode] = useState<boolean>(false);
  const [authEmail, setAuthEmail] = useState<string>('');
  const [authPassword, setAuthPassword] = useState<string>('');
  const [authName, setAuthName] = useState<string>('');
  const [authLoading, setAuthLoading] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);

  if (!isOpen) return null;

  const currentProviderObj = providers.find((p) => p.id === providerType);

  const handleSaveEngine = async () => {
    setSavingEngine(true);
    setEngineSuccessMsg(null);
    try {
      if (providerType === 'groq') {
        const customObj = {
          name: 'Groq Cloud',
          api_type: 'openai_compatible' as const,
          base_url: 'https://api.groq.com/openai/v1',
          model_name: customModel.trim() || 'llama-3.3-70b-versatile',
          api_key: apiKey.trim() || undefined,
        };
        const created = await addCustomProvider(customObj, true);
        await selectProvider(created.id, customObj.model_name, customObj.api_key);
        onProviderChanged(created.id);
      } else if (providerType === 'deepseek') {
        const customObj = {
          name: 'DeepSeek',
          api_type: 'openai_compatible' as const,
          base_url: 'https://api.deepseek.com/v1',
          model_name: customModel.trim() || 'deepseek-chat',
          api_key: apiKey.trim() || undefined,
        };
        const created = await addCustomProvider(customObj, true);
        await selectProvider(created.id, customObj.model_name, customObj.api_key);
        onProviderChanged(created.id);
      } else if (providerType === 'custom') {
        const customObj = {
          name: 'Custom Endpoint',
          api_type: 'openai_compatible' as const,
          base_url: customBaseUrl.trim() || 'http://localhost:1234/v1',
          model_name: customModel.trim() || 'local-model',
          api_key: apiKey.trim() || undefined,
        };
        const created = await addCustomProvider(customObj, true);
        await selectProvider(created.id, customObj.model_name, customObj.api_key);
        onProviderChanged(created.id);
      } else {
        await selectProvider(
          providerType,
          customModel.trim() || undefined,
          apiKey.trim() || undefined
        );
        onProviderChanged(providerType);
      }

      onRefreshProviders();
      setEngineSuccessMsg('Model configuration saved successfully!');
      setTimeout(() => {
        setEngineSuccessMsg(null);
        onClose();
      }, 900);
    } catch (e: any) {
      setEngineSuccessMsg(`Error: ${e.message || 'Failed to save'}`);
    } finally {
      setSavingEngine(false);
    }
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authEmail.trim() || !authPassword.trim()) {
      setAuthError('Please enter both email and password.');
      return;
    }
    setAuthLoading(true);
    setAuthError(null);
    try {
      let res;
      if (isRegisterMode) {
        res = await registerUser({
          email: authEmail.trim(),
          password: authPassword.trim(),
          full_name: authName.trim() || undefined,
        });
      } else {
        res = await loginUser({
          email: authEmail.trim(),
          password: authPassword.trim(),
        });
      }
      onAuthSuccess(res.user);
      onClose();
    } catch (err: any) {
      setAuthError(err.message || 'Authentication failed');
    } finally {
      setAuthLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fade-in font-sans">
      <div className="bg-[#111928] border border-slate-700/80 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden text-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0d1424]">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-white">Settings</h3>
          </div>
          <div className="flex items-center gap-3">
            {/* Tab switchers */}
            <div className="flex bg-[#090e1a] p-1 rounded-xl border border-slate-800 text-xs">
              <button
                onClick={() => setActiveTab('engine')}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  activeTab === 'engine'
                    ? 'bg-lenny-500 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                LLM Engine
              </button>
              <button
                onClick={() => setActiveTab('account')}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  activeTab === 'account'
                    ? 'bg-lenny-500 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Account
              </button>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tab 1: LLM Engine */}
        {activeTab === 'engine' && (
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Choose Model Provider
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'groq', label: 'Groq Cloud', icon: '⚡', desc: 'Fast & Free tier' },
                  { id: 'ollama', label: 'Ollama', icon: '💻', desc: 'Local instance' },
                  { id: 'openai', label: 'OpenAI', icon: '🧠', desc: 'GPT-4o' },
                  { id: 'anthropic', label: 'Anthropic', icon: '✨', desc: 'Claude 3.5' },
                  { id: 'deepseek', label: 'DeepSeek', icon: '🐋', desc: 'DeepSeek-V3' },
                  { id: 'custom', label: 'Custom API', icon: '⚙️', desc: 'Any Base URL' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setProviderType(item.id);
                      if (item.id === 'groq') setCustomModel('llama-3.3-70b-versatile');
                      if (item.id === 'deepseek') setCustomModel('deepseek-chat');
                    }}
                    className={`p-2.5 rounded-xl border text-left transition flex flex-col justify-between ${
                      providerType === item.id || (providerType.startsWith('custom_') && item.id === 'custom')
                        ? 'bg-lenny-500/15 border-lenny-500 text-white shadow-sm'
                        : 'bg-[#0e1626] border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                    }`}
                  >
                    <div className="text-base">{item.icon}</div>
                    <div className="mt-1">
                      <div className="text-xs font-bold leading-tight">{item.label}</div>
                      <div className="text-[10px] text-slate-400 truncate">{item.desc}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Provider Configuration Fields */}
            <div className="bg-[#090e1a] p-4 rounded-xl border border-slate-800 space-y-3">
              {providerType === 'ollama' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Select Installed Local Model
                  </label>
                  <select
                    value={customModel || currentProviderObj?.current_model || ''}
                    onChange={(e) => setCustomModel(e.target.value)}
                    className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500"
                  >
                    {(currentProviderObj?.available_models || ['llama3.1:8b', 'Finetuning:latest', 'Structred_SLM:latest']).map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                  <p className="text-[11px] text-slate-400 mt-1.5">
                    Connects to local Ollama on <code className="text-slate-300 font-mono">http://localhost:11434</code>
                  </p>
                </div>
              )}

              {providerType === 'groq' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Groq API Key
                    </label>
                    <input
                      type="password"
                      placeholder="gsk_..."
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500 font-mono"
                    />
                    <p className="text-[11px] text-slate-400 mt-1">
                      Get a free key from <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer" className="text-lenny-400 hover:underline">console.groq.com</a>
                    </p>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Model Name
                    </label>
                    <input
                      type="text"
                      placeholder="llama-3.3-70b-versatile"
                      value={customModel || 'llama-3.3-70b-versatile'}
                      onChange={(e) => setCustomModel(e.target.value)}
                      className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500 font-mono"
                    />
                  </div>
                </div>
              )}

              {(providerType === 'openai' || providerType === 'anthropic' || providerType === 'deepseek') && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      {providerType.toUpperCase()} API Key
                    </label>
                    <input
                      type="password"
                      placeholder="Paste your API key here..."
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Model Identifier (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder={providerType === 'openai' ? 'gpt-4o' : providerType === 'anthropic' ? 'claude-3-5-sonnet-20241022' : 'deepseek-chat'}
                      value={customModel}
                      onChange={(e) => setCustomModel(e.target.value)}
                      className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500 font-mono"
                    />
                  </div>
                </div>
              )}

              {providerType === 'custom' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      API Base URL
                    </label>
                    <input
                      type="text"
                      placeholder="https://api.together.xyz/v1 or http://localhost:1234/v1"
                      value={customBaseUrl}
                      onChange={(e) => setCustomBaseUrl(e.target.value)}
                      className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Model Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. meta-llama/Llama-3.3-70B-Instruct-Turbo"
                      value={customModel}
                      onChange={(e) => setCustomModel(e.target.value)}
                      className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      API Key (Optional)
                    </label>
                    <input
                      type="password"
                      placeholder="Optional API key"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500 font-mono"
                    />
                  </div>
                </div>
              )}
            </div>

            {engineSuccessMsg && (
              <div className="p-2.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
                <Check className="w-4 h-4" />
                <span>{engineSuccessMsg}</span>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={savingEngine}
                onClick={handleSaveEngine}
                className="px-5 py-2 rounded-xl bg-lenny-600 hover:bg-lenny-500 text-white text-xs font-semibold shadow-md shadow-lenny-500/20 transition flex items-center gap-1.5"
              >
                {savingEngine ? 'Saving...' : 'Apply & Save'}
              </button>
            </div>
          </div>
        )}

        {/* Tab 2: Account */}
        {activeTab === 'account' && (
          <div className="p-6">
            {currentUser ? (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-[#090e1a] border border-slate-800 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-lenny-500/20 text-lenny-400 flex items-center justify-center font-bold text-sm">
                    {currentUser.full_name ? currentUser.full_name.charAt(0).toUpperCase() : 'U'}
                  </div>
                  <div>
                    <div className="text-sm font-bold text-white flex items-center gap-1.5">
                      <span>{currentUser.full_name || 'User'}</span>
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div className="text-xs text-slate-400">{currentUser.email}</div>
                  </div>
                </div>

                <p className="text-xs text-slate-400">
                  You are signed in. Your conversations and artifacts are securely saved in Supabase.
                </p>

                <button
                  type="button"
                  onClick={() => {
                    onLogout();
                    onClose();
                  }}
                  className="w-full py-2.5 rounded-xl border border-rose-500/40 text-rose-400 hover:bg-rose-500/10 text-xs font-semibold transition flex items-center justify-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              </div>
            ) : (
              <form onSubmit={handleAuthSubmit} className="space-y-3.5">
                <div>
                  <h4 className="text-sm font-bold text-white">
                    {isRegisterMode ? 'Create an Account' : 'Sign In to Lenny Assistant'}
                  </h4>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Save and separate your conversation history in Supabase.
                  </p>
                </div>

                {authError && (
                  <div className="p-2.5 rounded-lg bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs">
                    {authError}
                  </div>
                )}

                {isRegisterMode && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Lenny Rachitsky"
                      value={authName}
                      onChange={(e) => setAuthName(e.target.value)}
                      className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="you@company.com"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Password
                  </label>
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    className="w-full bg-[#131b2e] border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lenny-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={authLoading}
                  className="w-full py-2.5 rounded-xl bg-lenny-600 hover:bg-lenny-500 text-white text-xs font-bold transition shadow-md shadow-lenny-500/20 flex items-center justify-center gap-1.5 mt-2"
                >
                  {authLoading ? 'Please wait...' : isRegisterMode ? 'Register Account' : 'Sign In'}
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>

                <div className="text-center pt-1">
                  <button
                    type="button"
                    onClick={() => {
                      setIsRegisterMode(!isRegisterMode);
                      setAuthError(null);
                    }}
                    className="text-xs text-lenny-400 hover:underline"
                  >
                    {isRegisterMode ? 'Already have an account? Sign In' : "Don't have an account? Register"}
                  </button>
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
