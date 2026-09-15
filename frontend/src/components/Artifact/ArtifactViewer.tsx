import React, { useState } from 'react';
import {
  X,
  Code,
  Eye,
  Copy,
  Check,
  Download,
  Maximize2,
  Minimize2,
  Shield,
  FileText,
  FlaskConical
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArtifactData } from '../../types';
import { ExperimentCardRenderer } from './ExperimentCardRenderer';

interface ArtifactViewerProps {
  artifact: ArtifactData | null;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifact,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'preview' | 'source'>('preview');
  const [copied, setCopied] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  if (!artifact) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext =
      artifact.artifact_type === 'html'
        ? 'html'
        : artifact.artifact_type === 'growth_experiment'
        ? 'json'
        : 'md';
    const blob = new Blob([artifact.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.title.replace(/\s+/g, '_').toLowerCase()}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Safe Sandboxed HTML Document Wrapper with strict CSP
  const buildSandboxedHtml = (rawHtml: string) => {
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' https://cdn.jsdelivr.net; script-src 'unsafe-inline'; img-src data: https:;">
          <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
          <style>
            body { background: #0f172a; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 1.5rem; }
          </style>
        </head>
        <body>
          ${rawHtml}
        </body>
      </html>
    `;
  };

  return (
    <div
      className={`bg-[#0d1424] border-l border-slate-800 flex flex-col transition-all duration-300 ${
        isFullscreen
          ? 'fixed inset-0 z-50 w-screen h-screen'
          : 'w-full lg:w-[48%] h-full shrink-0'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-[#090e1a]/90">
        <div className="flex items-center gap-2.5 truncate">
          <div className="p-1.5 rounded-lg bg-lenny-500/20 text-lenny-400">
            {artifact.artifact_type === 'growth_experiment' ? (
              <FlaskConical className="w-4 h-4" />
            ) : (
              <FileText className="w-4 h-4" />
            )}
          </div>
          <div className="truncate">
            <h3 className="text-xs font-bold text-white truncate">
              {artifact.title}
            </h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                Type: {artifact.artifact_type}
              </span>
              <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-mono">
                <Shield className="w-2.5 h-2.5" /> Sandboxed
              </span>
            </div>
          </div>
        </div>

        {/* Tab & Action Controls */}
        <div className="flex items-center gap-1.5 shrink-0">
          {/* Preview / Source Switcher */}
          <div className="flex items-center bg-slate-900 rounded-lg p-0.5 border border-slate-800">
            <button
              onClick={() => setActiveTab('preview')}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold flex items-center gap-1 transition ${
                activeTab === 'preview'
                  ? 'bg-lenny-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3 h-3" />
              <span>Preview</span>
            </button>
            <button
              onClick={() => setActiveTab('source')}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold flex items-center gap-1 transition ${
                activeTab === 'source'
                  ? 'bg-lenny-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code className="w-3 h-3" />
              <span>Source</span>
            </button>
          </div>

          {/* Copy */}
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
            title="Copy artifact content"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>

          {/* Download */}
          <button
            onClick={handleDownload}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
            title="Download artifact file"
          >
            <Download className="w-4 h-4" />
          </button>

          {/* Fullscreen */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>

          {/* Close */}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
            title="Close Artifact Viewer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Artifact Content View */}
      <div className="flex-1 overflow-y-auto p-6 bg-[#080d1a]">
        {activeTab === 'source' ? (
          <pre className="p-4 bg-slate-950 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {artifact.content}
          </pre>
        ) : artifact.artifact_type === 'growth_experiment' ? (
          <ExperimentCardRenderer data={artifact.structured_data} />
        ) : artifact.artifact_type === 'html' ? (
          <div className="h-full min-h-[500px] rounded-xl overflow-hidden border border-slate-800 bg-[#0f172a]">
            <iframe
              title={artifact.title}
              sandbox="allow-scripts"
              srcDoc={buildSandboxedHtml(artifact.content)}
              className="w-full h-full min-h-[500px] border-0"
            />
          </div>
        ) : (
          /* Markdown (Ship 30 for 30 Essay) */
          <div className="max-w-3xl mx-auto p-6 bg-[#0f172a] rounded-2xl border border-slate-800 text-slate-200 shadow-xl space-y-4">
            <div className="prose prose-invert prose-lenny max-w-none text-sm leading-relaxed">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {artifact.content}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
