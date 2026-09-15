import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, XCircle, Info } from 'lucide-react';
import { ConfidenceLevel } from '../../types';

interface GroundingBadgeProps {
  level?: ConfidenceLevel;
  score?: number;
  citationCount?: number;
  onViewCitations?: () => void;
  isRefusal?: boolean;
}

export const GroundingBadge: React.FC<GroundingBadgeProps> = ({
  level,
  score,
  citationCount = 0,
  onViewCitations,
  isRefusal,
}) => {
  if (!level) return null;

  const scorePct = score !== undefined ? Math.round(score * 100) : null;

  if (level === 'HIGH') {
    return (
      <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs font-medium">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
        <span>High Grounding</span>
        {scorePct !== null && (
          <span className="text-emerald-400/80 font-mono">({scorePct}%)</span>
        )}
        {citationCount > 0 && onViewCitations && (
          <button
            onClick={onViewCitations}
            className="ml-1 px-1.5 py-0.5 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-200 text-[10px] transition"
          >
            {citationCount} {citationCount === 1 ? 'source' : 'sources'}
          </button>
        )}
      </div>
    );
  }

  if (level === 'MEDIUM') {
    return (
      <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-950/60 border border-amber-500/40 text-amber-300 text-xs font-medium">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
        <span>Medium Grounding</span>
        {scorePct !== null && (
          <span className="text-amber-400/80 font-mono">({scorePct}%)</span>
        )}
        {citationCount > 0 && onViewCitations && (
          <button
            onClick={onViewCitations}
            className="ml-1 px-1.5 py-0.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 text-[10px] transition"
          >
            {citationCount} {citationCount === 1 ? 'source' : 'sources'}
          </button>
        )}
      </div>
    );
  }

  if (level === 'LOW') {
    return (
      <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-orange-950/60 border border-orange-500/40 text-orange-300 text-xs font-medium">
        <ShieldAlert className="w-3.5 h-3.5 text-orange-400" />
        <span>Low Grounding</span>
        {scorePct !== null && (
          <span className="text-orange-400/80 font-mono">({scorePct}%)</span>
        )}
        {citationCount > 0 && onViewCitations && (
          <button
            onClick={onViewCitations}
            className="ml-1 px-1.5 py-0.5 rounded bg-orange-500/20 hover:bg-orange-500/30 text-orange-200 text-[10px] transition"
          >
            {citationCount} sources
          </button>
        )}
      </div>
    );
  }

  // INSUFFICIENT
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-rose-950/80 border border-rose-500/50 text-rose-200 text-xs font-medium shadow-sm">
      <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
      <div>
        <span className="font-semibold text-rose-300">Insufficient Grounding in Archive</span>
        <span className="ml-1 text-rose-300/80 text-[11px] block sm:inline">
          (Honest Refusal Guardrail active — no hallucination)
        </span>
      </div>
    </div>
  );
};
