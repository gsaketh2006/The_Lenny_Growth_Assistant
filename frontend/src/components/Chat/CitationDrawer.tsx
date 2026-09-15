import React from 'react';
import { X, ExternalLink, User, Calendar, Quote } from 'lucide-react';
import { Citation } from '../../types';

interface CitationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  citations: Citation[];
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({
  isOpen,
  onClose,
  citations,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
      <div className="bg-[#131b2e] border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0f172a]">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <span>🎙️</span> Transcript Citations & Grounding Sources
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Verified segments retrieved from Lenny's Podcast archive
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Citations List */}
        <div className="p-6 overflow-y-auto space-y-4">
          {citations.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-6">
              No specific citation segments available for this response.
            </p>
          ) : (
            citations.map((cit, idx) => (
              <div
                key={cit.chunk_id || idx}
                className="p-4 rounded-xl bg-[#1e293b]/70 border border-slate-700/80 hover:border-lenny-500/50 transition-all space-y-2.5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-lenny-500/20 text-lenny-400 text-xs font-mono font-bold">
                        Source #{idx + 1}
                      </span>
                      <span className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        {cit.guest_name}
                      </span>
                    </div>
                    <h4 className="text-xs text-slate-300 font-medium mt-1">
                      {cit.episode_title}
                    </h4>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="px-2 py-1 rounded bg-slate-800 border border-slate-700 text-emerald-400 font-mono text-[11px] font-bold">
                      {Math.round(cit.similarity_score * 100)}% Match
                    </span>
                  </div>
                </div>

                {/* Snippet */}
                <div className="bg-[#0b0f19]/80 rounded-lg p-3 border border-slate-800 text-xs text-slate-300 leading-relaxed font-mono relative">
                  <Quote className="w-3.5 h-3.5 text-slate-600 mb-1" />
                  "{cit.snippet}"
                </div>

                {/* Metadata footer */}
                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                  {cit.publication_date && (
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" /> Published: {cit.publication_date}
                    </span>
                  )}
                  {cit.episode_url && (
                    <a
                      href={cit.episode_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-lenny-400 hover:text-lenny-300 inline-flex items-center gap-1 font-medium transition"
                    >
                      <span>Watch Episode</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-[#0f172a] text-right">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
