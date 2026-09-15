import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  FlaskConical,
  FileText,
  Compass,
  ArrowUpRight,
  ExternalLink,
  Layers
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message, Citation, ArtifactData } from '../../types';
import { GroundingBadge } from './GroundingBadge';
import { CitationDrawer } from './CitationDrawer';

interface ChatContainerProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  isStreaming: boolean;
  onOpenArtifact: (artifact: ArtifactData) => void;
  activeArtifact: ArtifactData | null;
  selectedProvider: string;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  onSendMessage,
  isStreaming,
  onOpenArtifact,
  activeArtifact,
  selectedProvider,
}) => {
  const [inputText, setInputText] = useState('');
  const [activeCitations, setActiveCitations] = useState<Citation[] | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const promptSuggestions = [
    {
      label: 'Grounded Q&A',
      prompt: 'What did Brian Balfour say about growth loops vs funnels?',
      icon: '🎙️',
    },
    {
      label: 'Ship 30 Essay',
      prompt: 'Write a Ship 30 for 30 essay on Superhuman finding product-market fit',
      icon: '✍️',
    },
    {
      label: 'Growth Experiment Card',
      prompt: "Turn Elena Verna's B2B PLG advice into a 1-week growth experiment",
      icon: '🧪',
    },
    {
      label: 'Refusal Guardrail Test',
      prompt: 'How do I bake traditional sourdough bread at home?',
      icon: '🛡️',
    },
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0b0f19] relative overflow-hidden">
      {/* Top Bar */}
      <div className="px-6 py-3 border-b border-slate-800/80 bg-[#0d1424]/90 flex items-center justify-between z-10">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-semibold text-slate-200">
            Lenny Knowledge Base Assistant
          </span>
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[10px]">
            Engine: {selectedProvider.toUpperCase()}
          </span>
        </div>

        {activeArtifact && (
          <button
            onClick={() => onOpenArtifact(activeArtifact)}
            className="px-3 py-1 rounded-lg bg-lenny-500/20 hover:bg-lenny-500/30 text-lenny-300 border border-lenny-500/40 text-xs font-semibold flex items-center gap-1.5 transition"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>View Active Artifact ({activeArtifact.artifact_type})</span>
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto space-y-6 animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-lenny-500 to-amber-600 flex items-center justify-center text-3xl shadow-xl shadow-lenny-500/20">
              🎙️
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Ask Lenny's Growth Archive
              </h2>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Strictly grounded in 300+ transcripts from Lenny's Podcast. Equipped with
                autonomous skills for Grounded Q&A, Ship 30 Essays, and 1-Week Growth Experiment Cards.
              </p>
            </div>

            {/* Quick Prompts */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full pt-2">
              {promptSuggestions.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(item.prompt)}
                  className="p-3 rounded-xl bg-[#131b2e] hover:bg-[#1c2742] border border-slate-800 hover:border-lenny-500/50 text-left transition-all group shadow-sm flex items-start gap-2.5"
                >
                  <span className="text-base shrink-0">{item.icon}</span>
                  <div>
                    <div className="text-[10px] font-bold text-lenny-400 uppercase tracking-wider">
                      {item.label}
                    </div>
                    <div className="text-xs text-slate-300 group-hover:text-white font-medium mt-0.5 line-clamp-2">
                      {item.prompt}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={index}
                className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-lenny-600 to-amber-600 flex items-center justify-center text-white shrink-0 shadow-md">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-2xl rounded-2xl px-5 py-4 space-y-3 shadow-lg ${
                    isUser
                      ? 'bg-gradient-to-r from-lenny-600 to-lenny-500 text-white rounded-tr-none'
                      : 'bg-[#131b2e] border border-slate-800 text-slate-200 rounded-tl-none'
                  }`}
                >
                  {/* Assistant Header: Routing & Grounding Badge */}
                  {!isUser && (
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800/80">
                      <div className="flex items-center gap-2">
                        {msg.confidence_level && (
                          <GroundingBadge
                            level={msg.confidence_level}
                            score={msg.confidence_score}
                            citationCount={msg.citations?.length || 0}
                            onViewCitations={() => msg.citations && setActiveCitations(msg.citations)}
                          />
                        )}
                      </div>

                      {msg.skill_used && (
                        <span className="text-[10px] font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-800 border border-slate-700/60">
                          Skill: {msg.skill_used}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Message Content */}
                  <div className="prose prose-invert prose-sm max-w-none text-xs sm:text-sm leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>

                  {/* Artifact mount button if message produced an artifact */}
                  {msg.artifact && (
                    <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-lenny-400 font-semibold">
                        {msg.artifact.artifact_type === 'growth_experiment' ? (
                          <FlaskConical className="w-4 h-4" />
                        ) : (
                          <FileText className="w-4 h-4" />
                        )}
                        <span>Artifact Generated: {msg.artifact.title}</span>
                      </div>
                      <button
                        onClick={() => onOpenArtifact(msg.artifact!)}
                        className="px-3 py-1 rounded-lg bg-lenny-500 hover:bg-lenny-400 text-white text-xs font-semibold flex items-center gap-1 shadow-sm transition"
                      >
                        <span>Open Viewer</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Routing Rationale Info Pill */}
                  {!isUser && msg.routing_rationale && (
                    <div className="text-[10px] text-slate-500 font-mono italic pt-1">
                      Router Rationale: {msg.routing_rationale}
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center text-slate-300 shrink-0">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {isStreaming && (
          <div className="flex gap-3.5 items-center text-xs text-slate-400 animate-pulse">
            <div className="w-8 h-8 rounded-xl bg-lenny-600/30 flex items-center justify-center text-lenny-400">
              <Bot className="w-4 h-4" />
            </div>
            <span>Synthesizing transcript wisdom...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="p-4 border-t border-slate-800/80 bg-[#0d1424]">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-end gap-2">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a product/growth question, request a Ship 30 essay, or generate an experiment card..."
            rows={1}
            className="w-full bg-[#162035] border border-slate-700/80 focus:border-lenny-500 rounded-xl px-4 py-3 text-xs sm:text-sm text-slate-100 placeholder:text-slate-500 resize-none focus:outline-none focus:ring-1 focus:ring-lenny-500 transition shadow-inner max-h-32"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isStreaming}
            className="p-3 rounded-xl bg-lenny-500 hover:bg-lenny-400 disabled:opacity-40 disabled:hover:bg-lenny-500 text-white shrink-0 shadow-md shadow-lenny-500/20 transition cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Citation Inspector Modal */}
      <CitationDrawer
        isOpen={Boolean(activeCitations)}
        onClose={() => setActiveCitations(null)}
        citations={activeCitations || []}
      />
    </div>
  );
};
