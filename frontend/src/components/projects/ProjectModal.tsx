import React, { useState, useEffect } from 'react';
import type { Project, ProjectCreateInput } from '../../services/api';
import { validateTargetUrl } from '../../services/api';
import { 
  X, 
  ShieldCheck, 
  ShieldAlert, 
  Globe, 
  Layers, 
  FileText, 
  Bot, 
  CheckCircle2, 
  AlertTriangle,
  Loader2
} from 'lucide-react';

interface ProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (projectData: ProjectCreateInput, id?: number) => Promise<void>;
  projectToEdit?: Project | null;
}

export const ProjectModal: React.FC<ProjectModalProps> = ({
  isOpen,
  onClose,
  onSave,
  projectToEdit,
}) => {
  const [name, setName] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [maxCrawlPages, setMaxCrawlPages] = useState(100);
  const [maxCrawlDepth, setMaxCrawlDepth] = useState(3);
  const [customUserAgent, setCustomUserAgent] = useState('SEOIntelligenceBot/1.0');
  const [respectRobotsTxt, setRespectRobotsTxt] = useState(true);

  // SSRF Live Validation state
  const [validatingUrl, setValidatingUrl] = useState(false);
  const [urlValidationState, setUrlValidationState] = useState<{
    isValid: boolean | null;
    error: string | null;
    normalizedUrl: string | null;
  }>({ isValid: null, error: null, normalizedUrl: null });

  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (projectToEdit) {
      setName(projectToEdit.name);
      setTargetUrl(projectToEdit.target_url);
      setMaxCrawlPages(projectToEdit.max_crawl_pages);
      setMaxCrawlDepth(projectToEdit.max_crawl_depth);
      setCustomUserAgent(projectToEdit.custom_user_agent);
      setRespectRobotsTxt(projectToEdit.respect_robots_txt);
      setUrlValidationState({ isValid: true, error: null, normalizedUrl: projectToEdit.target_url });
    } else {
      setName('');
      setTargetUrl('');
      setMaxCrawlPages(100);
      setMaxCrawlDepth(3);
      setCustomUserAgent('SEOIntelligenceBot/1.0');
      setRespectRobotsTxt(true);
      setUrlValidationState({ isValid: null, error: null, normalizedUrl: null });
    }
    setFormError(null);
  }, [projectToEdit, isOpen]);

  // Debounced SSRF URL Validation
  useEffect(() => {
    if (!targetUrl.trim()) {
      setUrlValidationState({ isValid: null, error: null, normalizedUrl: null });
      return;
    }

    const timer = setTimeout(async () => {
      setValidatingUrl(true);
      try {
        const res = await validateTargetUrl(targetUrl);
        setUrlValidationState({
          isValid: res.is_valid,
          error: res.error || null,
          normalizedUrl: res.normalized_url || null,
        });
      } catch (err: any) {
        setUrlValidationState({
          isValid: false,
          error: 'Failed to contact validation server.',
          normalizedUrl: null,
        });
      } finally {
        setValidatingUrl(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [targetUrl]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!name.trim()) {
      setFormError('Please enter a project name.');
      return;
    }

    if (!targetUrl.trim()) {
      setFormError('Please enter a target URL.');
      return;
    }

    if (urlValidationState.isValid === false) {
      setFormError(`Cannot save project: SSRF Security Violation (${urlValidationState.error})`);
      return;
    }

    setSubmitting(true);
    try {
      await onSave(
        {
          name: name.trim(),
          target_url: targetUrl.trim(),
          max_crawl_pages: maxCrawlPages,
          max_crawl_depth: maxCrawlDepth,
          custom_user_agent: customUserAgent.trim(),
          respect_robots_txt: respectRobotsTxt,
        },
        projectToEdit?.id
      );
      onClose();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to save project. Please check fields.';
      setFormError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-blue-500/10 rounded-xl text-blue-400">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">
                {projectToEdit ? 'Edit Website Project' : 'Configure New SEO Target'}
              </h3>
              <p className="text-xs text-slate-400">Target Domain & SSRF Crawl Boundaries</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-6 flex-1">
          {formError && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Action Required</p>
                <p className="mt-0.5">{formError}</p>
              </div>
            </div>
          )}

          {/* Project Name */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-300">
              Project Name <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. My E-Commerce Store"
              required
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
            />
          </div>

          {/* Target URL with live SSRF protection */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold text-slate-300">
                Target Website URL <span className="text-rose-400">*</span>
              </label>
              <span className="text-[11px] text-slate-400 flex items-center space-x-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>SSRF Guard Active</span>
              </span>
            </div>
            <div className="relative">
              <input
                type="text"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="https://example.com"
                required
                className={`w-full bg-slate-950 border rounded-xl pl-4 pr-10 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none transition-colors ${
                  urlValidationState.isValid === true
                    ? 'border-emerald-500/50 focus:border-emerald-500'
                    : urlValidationState.isValid === false
                    ? 'border-rose-500/50 focus:border-rose-500'
                    : 'border-slate-800 focus:border-blue-500'
                }`}
              />
              <div className="absolute right-3 top-3 flex items-center">
                {validatingUrl ? (
                  <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                ) : urlValidationState.isValid === true ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : urlValidationState.isValid === false ? (
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                ) : null}
              </div>
            </div>

            {/* Live SSRF Validation Status Banner */}
            {validatingUrl && (
              <p className="text-[11px] text-slate-400 flex items-center space-x-1">
                <span>Checking IP, DNS & loopback restriction...</span>
              </p>
            )}
            {!validatingUrl && urlValidationState.isValid === true && (
              <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>
                  Target URL is safe. Normalized: <strong className="font-mono">{urlValidationState.normalizedUrl}</strong>
                </span>
              </div>
            )}
            {!validatingUrl && urlValidationState.isValid === false && (
              <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-start space-x-2">
                <ShieldAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="block font-semibold">SSRF Protection Triggered!</strong>
                  <span>{urlValidationState.error}</span>
                </div>
              </div>
            )}
          </div>

          {/* Crawl Parameters Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
            {/* Max Pages */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span className="flex items-center space-x-1.5">
                  <FileText className="w-3.5 h-3.5 text-blue-400" />
                  <span>Max Crawl Pages</span>
                </span>
                <span className="text-blue-400 font-mono font-bold">{maxCrawlPages}</span>
              </label>
              <input
                type="range"
                min="10"
                max="2000"
                step="10"
                value={maxCrawlPages}
                onChange={(e) => setMaxCrawlPages(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <p className="text-[10px] text-slate-500">Maximum URLs audited per run (10 - 2,000)</p>
            </div>

            {/* Max Crawl Depth */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span className="flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Max Crawl Depth</span>
                </span>
                <span className="text-indigo-400 font-mono font-bold">{maxCrawlDepth}</span>
              </label>
              <input
                type="range"
                min="1"
                max="10"
                step="1"
                value={maxCrawlDepth}
                onChange={(e) => setMaxCrawlDepth(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
              <p className="text-[10px] text-slate-500">Link depth distance from root domain (1 - 10)</p>
            </div>
          </div>

          {/* User Agent & Robots.txt */}
          <div className="space-y-4 pt-2 border-t border-slate-800/80">
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
                <Bot className="w-3.5 h-3.5 text-amber-400" />
                <span>Custom Crawler User-Agent</span>
              </label>
              <input
                type="text"
                value={customUserAgent}
                onChange={(e) => setCustomUserAgent(e.target.value)}
                placeholder="SEOIntelligenceBot/1.0"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-slate-100 placeholder-slate-600 font-mono focus:outline-none focus:border-amber-500 transition-colors"
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800">
              <div>
                <p className="text-xs font-semibold text-slate-200">Respect Robots.txt Directives</p>
                <p className="text-[10px] text-slate-400">Strictly adhere to target site crawler block rules</p>
              </div>
              <button
                type="button"
                onClick={() => setRespectRobotsTxt(!respectRobotsTxt)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  respectRobotsTxt ? 'bg-emerald-600' : 'bg-slate-800'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    respectRobotsTxt ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 flex items-center justify-end space-x-3 bg-slate-900/80">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || urlValidationState.isValid === false}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/25 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {submitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <span>{projectToEdit ? 'Save Changes' : 'Create Project'}</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
