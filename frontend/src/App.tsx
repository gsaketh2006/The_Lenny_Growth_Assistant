import React, { useState, useEffect } from 'react';
import { SessionSidebar } from './components/Sidebar/SessionSidebar';
import { ChatContainer } from './components/Chat/ChatContainer';
import { ArtifactViewer } from './components/Artifact/ArtifactViewer';
import { SettingsModal } from './components/Settings/SettingsModal';
import {
  fetchSessions,
  fetchSession,
  createSession,
  deleteSession,
  fetchProviders,
  selectProvider,
  fetchHealth,
  streamChat,
  fetchCurrentUser,
  logoutUser,
  getAuthToken,
  restoreStoredCustomProviders
} from './services/api';
import { SessionSummary, ProviderInfo, HealthStatus, Message, ArtifactData, User } from './types';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [settingsTab, setSettingsTab] = useState<'engine' | 'account'>('engine');
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeArtifact, setActiveArtifact] = useState<ArtifactData | null>(null);
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('ollama');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);

  // Load initial data & check active user session
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      // 1. Restore any saved custom LLM providers to backend runtime
      await restoreStoredCustomProviders();

      // 2. Check logged-in user if token exists
      if (getAuthToken()) {
        try {
          const user = await fetchCurrentUser();
          setCurrentUser(user);
        } catch (e) {
          console.log('No active user session');
        }
      }

      // 3. Fetch user-scoped sessions, providers & system health
      const [sessList, provList, healthData] = await Promise.all([
        fetchSessions(),
        fetchProviders(),
        fetchHealth(),
      ]);
      setSessions(sessList);
      setProviders(provList);
      setHealth(healthData);


      const activeProv = provList.find((p) => p.is_active);
      if (activeProv) {
        setSelectedProvider(activeProv.id);
      }

      if (sessList.length > 0) {
        handleSelectSession(sessList[0].id);
      }
    } catch (e) {
      console.error('Error loading initial data:', e);
    }
  };

  const handleAuthSuccess = async (user: User) => {
    setCurrentUser(user);
    try {
      const sessList = await fetchSessions();
      setSessions(sessList);
      if (sessList.length > 0) {
        handleSelectSession(sessList[0].id);
      } else {
        setActiveSessionId(null);
        setMessages([]);
        setActiveArtifact(null);
      }
    } catch (e) {
      console.error('Error refreshing sessions after login:', e);
    }
  };

  const handleLogout = async () => {
    logoutUser();
    setCurrentUser(null);
    try {
      const sessList = await fetchSessions();
      setSessions(sessList);
      if (sessList.length > 0) {
        handleSelectSession(sessList[0].id);
      } else {
        setActiveSessionId(null);
        setMessages([]);
        setActiveArtifact(null);
      }
    } catch (e) {
      setSessions([]);
      setActiveSessionId(null);
      setMessages([]);
      setActiveArtifact(null);
    }
  };


  const refreshProviders = async () => {
    try {
      const provList = await fetchProviders();
      setProviders(provList);
    } catch (e) {
      console.error('Error refreshing providers:', e);
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    try {
      setActiveSessionId(sessionId);
      const sessData = await fetchSession(sessionId);
      const mappedMessages: Message[] = (sessData.messages || []).map((m: any) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        skill_used: m.skill_used,
        routing_rationale: m.routing_rationale,
        confidence_level: m.confidence_level,
        confidence_score: m.confidence_score,
        citations: m.citations || [],
        artifact: m.artifact || undefined,
        created_at: m.created_at,
      }));
      setMessages(mappedMessages);

      // If session has an artifact, open the latest one
      if (sessData.artifacts && sessData.artifacts.length > 0) {
        const latest = sessData.artifacts[sessData.artifacts.length - 1];
        setActiveArtifact(latest);
      } else {
        setActiveArtifact(null);
      }
    } catch (e) {
      console.error('Error selecting session:', e);
    }
  };

  const handleNewChat = async () => {
    try {
      const newSess = await createSession('New Conversation');
      setActiveSessionId(newSess.id);
      setMessages([]);
      setActiveArtifact(null);
      const updated = await fetchSessions();
      setSessions(updated);
    } catch (e) {
      console.error('Error creating new session:', e);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      const updated = await fetchSessions();
      setSessions(updated);
      if (activeSessionId === sessionId) {
        if (updated.length > 0) {
          handleSelectSession(updated[0].id);
        } else {
          setActiveSessionId(null);
          setMessages([]);
          setActiveArtifact(null);
        }
      }
    } catch (e) {
      console.error('Error deleting session:', e);
    }
  };

  const handleSelectProvider = async (providerId: string) => {
    try {
      setSelectedProvider(providerId);
      await selectProvider(providerId);
      const provList = await fetchProviders();
      setProviders(provList);
    } catch (e) {
      console.error('Error switching provider:', e);
    }
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isStreaming) return;

    // Append User Message to UI
    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    // Prepare placeholder Assistant Message
    const assistantIndex = messages.length + 1;
    let assistantContent = '';

    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: '',
        isStreaming: true,
      },
    ]);

    await streamChat(text, activeSessionId || undefined, selectedProvider, {
      onSessionInit: (sessId) => {
        if (!activeSessionId) {
          setActiveSessionId(sessId);
          fetchSessions().then(setSessions);
        }
      },
      onRouting: (data) => {
        setMessages((prev) => {
          const copy = [...prev];
          if (copy[assistantIndex]) {
            copy[assistantIndex].skill_used = data.skill;
            copy[assistantIndex].routing_rationale = data.rationale;
          }
          return copy;
        });
      },
      onGrounding: (data) => {
        setMessages((prev) => {
          const copy = [...prev];
          if (copy[assistantIndex]) {
            copy[assistantIndex].confidence_level = data.confidence_level;
            copy[assistantIndex].confidence_score = data.confidence_score;
            copy[assistantIndex].citations = data.citations;
          }
          return copy;
        });
      },
      onToken: (token) => {
        assistantContent += token;
        setMessages((prev) => {
          const copy = [...prev];
          if (copy[assistantIndex]) {
            copy[assistantIndex].content = assistantContent;
          }
          return copy;
        });
      },
      onArtifact: (art) => {
        setActiveArtifact(art);
        setMessages((prev) => {
          const copy = [...prev];
          if (copy[assistantIndex]) {
            copy[assistantIndex].artifact = art;
          }
          return copy;
        });
      },
      onError: (err) => {
        setMessages((prev) => {
          const copy = [...prev];
          if (copy[assistantIndex]) {
            copy[assistantIndex].content = `⚠️ ${err}`;
          }
          return copy;
        });
        setIsStreaming(false);
      },
      onDone: () => {
        setIsStreaming(false);
        setMessages((prev) => {
          const copy = [...prev];
          if (copy[assistantIndex]) {
            copy[assistantIndex].isStreaming = false;
          }
          return copy;
        });
        fetchSessions().then(setSessions);
      },
    });
  };

  return (
    <div className="flex h-screen w-screen bg-[#0b0f19] text-slate-100 overflow-hidden font-sans">
      {/* Left Sidebar */}
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        providers={providers}
        health={health}
        selectedProvider={selectedProvider}
        onSelectProvider={handleSelectProvider}
        onOpenSettings={(tab) => {
          setSettingsTab(tab || 'engine');
          setIsSettingsOpen(true);
        }}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      {/* Center Chat View */}
      <ChatContainer
        messages={messages}
        onSendMessage={handleSendMessage}
        isStreaming={isStreaming}
        onOpenArtifact={(art) => setActiveArtifact(art)}
        activeArtifact={activeArtifact}
        selectedProvider={selectedProvider}
      />

      {/* Right Artifact Viewer (when active) */}
      {activeArtifact && (
        <ArtifactViewer
          artifact={activeArtifact}
          onClose={() => setActiveArtifact(null)}
        />
      )}

      {/* Unified Settings & Account Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        providers={providers}
        selectedProvider={selectedProvider}
        onProviderChanged={(prov) => setSelectedProvider(prov)}
        onRefreshProviders={refreshProviders}
        currentUser={currentUser}
        onAuthSuccess={handleAuthSuccess}
        onLogout={handleLogout}
        initialTab={settingsTab}
      />
    </div>
  );
}

export default App;

