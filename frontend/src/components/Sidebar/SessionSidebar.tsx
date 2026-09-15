import React from 'react';
import {
  MessageSquarePlus,
  MessageSquare,
  Trash2,
  Cpu,
  Settings,
  LogIn,
  LogOut,
  User as UserIcon,
  ShieldCheck,
  ChevronRight,
  Database
} from 'lucide-react';
import { SessionSummary, ProviderInfo, HealthStatus, User } from '../../types';

interface SessionSidebarProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  providers: ProviderInfo[];
  health: HealthStatus | null;
  selectedProvider: string;
  onSelectProvider: (provider: string) => void;
  onOpenSettings: (initialTab?: 'engine' | 'account') => void;
  currentUser: User | null;
  onLogout: () => void;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  providers,
  health,
  selectedProvider,
  onSelectProvider,
  onOpenSettings,
  currentUser,
  onLogout,
}) => {
  const currentProviderObj = providers.find((p) => p.id === selectedProvider);

  return (
    <aside className="w-72 bg-[#0d1424] border-r border-slate-800/80 flex flex-col h-full shrink-0 select-none">
      {/* App Branding */}
      <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-lenny-500 to-amber-600 flex items-center justify-center text-lg shadow-lg shadow-lenny-500/20">
            🎙️
          </div>
          <div>
            <h1 className="font-bold text-sm text-white leading-tight">
              The Lenny Assistant
            </h1>
            <p className="text-[11px] text-slate-400 font-medium">
              Growth Intelligence
            </p>
          </div>
        </div>

        <button
          onClick={() => onOpenSettings('engine')}
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
          title="Settings & Models"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full py-2.5 px-4 rounded-xl bg-lenny-600 hover:bg-lenny-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-md shadow-lenny-500/20 transition-all hover:scale-[1.01] active:scale-[0.99]"
        >
          <MessageSquarePlus className="w-4 h-4" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Sessions History List */}
      <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1">
        <div className="px-2 py-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
          Conversations ({sessions.length})
        </div>

        {sessions.length === 0 ? (
          <div className="px-3 py-6 text-center text-xs text-slate-500">
            No active conversations. Start one above!
          </div>
        ) : (
          sessions.map((sess) => {
            const isActive = sess.id === activeSessionId;
            return (
              <div
                key={sess.id}
                onClick={() => onSelectSession(sess.id)}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                  isActive
                    ? 'bg-slate-800/90 text-white font-medium border border-slate-700 shadow-sm'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-lenny-400' : 'text-slate-500'}`} />
                  <span className="truncate">{sess.title}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(sess.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 rounded transition"
                  title="Delete conversation"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Bottom Controls */}
      <div className="p-3 border-t border-slate-800/80 bg-[#090e1a]/80 space-y-2.5">
        {/* Model Card */}
        <button
          onClick={() => onOpenSettings('engine')}
          className="w-full p-2.5 rounded-xl bg-[#131b2e] hover:bg-[#18233c] border border-slate-800 hover:border-slate-700 text-left transition flex items-center justify-between group"
        >
          <div className="flex items-center gap-2 min-w-0">
            <Cpu className="w-4 h-4 text-lenny-400 shrink-0" />
            <div className="min-w-0">
              <div className="text-xs font-semibold text-white truncate">
                {currentProviderObj?.name || selectedProvider}
              </div>
              <div className="text-[10px] text-slate-400 truncate font-mono">
                {currentProviderObj?.current_model || 'default'}
              </div>
            </div>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300 transition shrink-0" />
        </button>

        {/* User Account Bar */}
        {currentUser ? (
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-800/50 border border-slate-800 text-xs">
            <div
              onClick={() => onOpenSettings('account')}
              className="flex items-center gap-2 min-w-0 cursor-pointer"
            >
              <div className="w-6 h-6 rounded-lg bg-lenny-500/20 text-lenny-400 flex items-center justify-center font-bold text-[11px] shrink-0">
                {currentUser.full_name ? currentUser.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="min-w-0">
                <div className="font-medium text-slate-200 truncate flex items-center gap-1 text-[11px]">
                  <span className="truncate">{currentUser.full_name || 'Account'}</span>
                  <ShieldCheck className="w-3 h-3 text-emerald-400 shrink-0" />
                </div>
              </div>
            </div>
            <button
              onClick={onLogout}
              className="p-1 text-slate-400 hover:text-rose-400 rounded transition shrink-0"
              title="Sign Out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => onOpenSettings('account')}
            className="w-full p-2 rounded-xl bg-slate-800/40 hover:bg-slate-800/70 border border-slate-800 text-left transition flex items-center justify-between text-xs text-slate-300"
          >
            <div className="flex items-center gap-2">
              <UserIcon className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-[11px]">Sign In / Register</span>
            </div>
            <LogIn className="w-3 h-3 text-slate-400" />
          </button>
        )}

        {/* Knowledge Base Status */}
        <div className="pt-1 flex items-center justify-between text-[10px] text-slate-500">
          <span className="flex items-center gap-1">
            <Database className="w-3 h-3" />
            {health?.transcripts_indexed_count !== undefined
              ? `${health.transcripts_indexed_count} chunks indexed`
              : 'Knowledge Base Ready'}
          </span>
          <span className="text-emerald-500 font-medium">● Online</span>
        </div>
      </div>
    </aside>
  );
};

