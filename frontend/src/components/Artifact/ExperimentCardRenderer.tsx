import React, { useState } from 'react';
import {
  FlaskConical,
  Target,
  Clock,
  AlertOctagon,
  Sparkles,
  Quote,
  Copy,
  Check,
  Download,
  Share2
} from 'lucide-react';

interface ExperimentCardRendererProps {
  data: any;
}

export const ExperimentCardRenderer: React.FC<ExperimentCardRendererProps> = ({ data }) => {
  const [copied, setCopied] = useState(false);

  if (!data) {
    return (
      <div className="p-8 text-center text-slate-400">
        No experiment card data found.
      </div>
    );
  }

  const {
    title = 'Growth Experiment Card',
    hypothesis = '',
    target_metric = '',
    secondary_metrics = [],
    test_plan = [],
    risks_and_invalidation = [],
    expected_impact = 'High',
    grounding_source = {},
  } = data;

  const handleCopyMarkdown = () => {
    const md = `
# 🧪 Growth Experiment Card: ${title}

## Hypothesis
${hypothesis}

## Target Metric
- **Primary Metric:** \`${target_metric}\`
${secondary_metrics.map((m: string) => `- Secondary: ${m}`).join('\n')}

## 1-Week Sprint Test Plan
${test_plan.map((step: any) => `- **${step.day_range}:** ${step.action}`).join('\n')}

## Risks & Invalidation Criteria
${risks_and_invalidation.map((r: string) => `- ⚠️ ${r}`).join('\n')}

## Impact & Grounding
- **Expected Impact:** ${expected_impact}
- **Source:** ${grounding_source.guest || 'Guest'} (*${grounding_source.episode || 'Episode'}*)
> "${grounding_source.quote_or_concept || ''}"
    `.trim();

    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto p-6 bg-[#0f172a] rounded-2xl border border-slate-800 shadow-2xl text-slate-200 font-sans">
      {/* Card Header */}
      <div className="flex items-start justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-lenny-500/20 border border-lenny-500/40 flex items-center justify-center text-lenny-400 shadow-inner">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded bg-lenny-500/20 text-lenny-400">
                Growth Experiment Card
              </span>
              <span className="text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                1-Week Sprint Ready
              </span>
            </div>
            <h2 className="text-lg font-bold text-white mt-1 leading-snug">
              {title}
            </h2>
          </div>
        </div>

        <button
          onClick={handleCopyMarkdown}
          className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold flex items-center gap-1.5 transition border border-slate-700"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied MD' : 'Copy Card'}</span>
        </button>
      </div>

      {/* Section 1: Hypothesis */}
      <div className="space-y-2">
        <label className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Core Hypothesis</span>
        </label>
        <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 to-slate-900/90 border border-slate-800/90 text-sm font-medium leading-relaxed text-amber-200/90 shadow-sm">
          {hypothesis}
        </div>
      </div>

      {/* Section 2: Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Target Metric */}
        <div className="p-4 rounded-xl bg-[#162035] border border-slate-800 space-y-1.5">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-emerald-400" />
            <span>Target Metric (Primary)</span>
          </label>
          <div className="text-base font-mono font-bold text-emerald-300">
            {target_metric}
          </div>
          <div className="text-[11px] text-slate-400">
            The single north-star number targeted to shift this sprint.
          </div>
        </div>

        {/* Secondary / Guardrails */}
        <div className="p-4 rounded-xl bg-[#162035] border border-slate-800 space-y-1.5">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <AlertOctagon className="w-3.5 h-3.5 text-slate-400" />
            <span>Secondary & Guardrails</span>
          </label>
          <div className="space-y-1">
            {secondary_metrics.length > 0 ? (
              secondary_metrics.map((m: string, i: number) => (
                <span
                  key={i}
                  className="inline-block px-2 py-0.5 mr-1.5 mb-1 rounded bg-slate-800 text-slate-300 text-xs font-mono"
                >
                  {m}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-500">Standard retention & churn guardrails</span>
            )}
          </div>
        </div>
      </div>

      {/* Section 3: 1-Week Test Plan Timeline */}
      <div className="space-y-3">
        <label className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-lenny-400" />
          <span>1-Week Sprint Execution Plan</span>
        </label>
        <div className="space-y-2">
          {test_plan.map((step: any, idx: number) => (
            <div
              key={idx}
              className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition"
            >
              <span className="px-2 py-1 rounded bg-lenny-500/20 text-lenny-400 font-mono text-xs font-bold shrink-0">
                {step.day_range}
              </span>
              <p className="text-xs text-slate-300 leading-relaxed font-medium">
                {step.action}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Section 4: Risks & Invalidation */}
      <div className="space-y-2">
        <label className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
          <span>Risks & Invalidation Criteria</span>
        </label>
        <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-900/30 space-y-1.5">
          {risks_and_invalidation.map((risk: string, idx: number) => (
            <div key={idx} className="flex items-start gap-2 text-xs text-rose-200/90 leading-relaxed">
              <span className="text-rose-400">•</span>
              <span>{risk}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Section 5: Grounding Source Attribution */}
      <div className="p-4 rounded-xl bg-[#131d31] border border-slate-800 space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-400 font-semibold">
          <span className="flex items-center gap-1.5">
            <Quote className="w-3.5 h-3.5 text-lenny-400" />
            <span>Transcript Grounding Source</span>
          </span>
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
            Impact: {expected_impact}
          </span>
        </div>
        <div className="text-xs text-slate-300">
          <span className="font-bold text-white">{grounding_source.guest}</span>
          <span className="text-slate-400"> — {grounding_source.episode}</span>
        </div>
        {grounding_source.quote_or_concept && (
          <div className="text-xs italic text-slate-400 bg-[#0a0f1d] p-3 rounded-lg border border-slate-800/80 font-mono">
            "{grounding_source.quote_or_concept}"
          </div>
        )}
      </div>
    </div>
  );
};
