import React, { useEffect, useState, useCallback } from 'react';
import {
  fetchAIRecommendations,
  fetchContentGaps,
  regenerateAIRecommendations,
} from '../../services/api';
import type {
  AIRecommendationsResponse,
  AISuggestion,
  ContentGapReportResponse,
  ContentGap,
} from '../../services/api';
import {
  Brain,
  Zap,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Lightbulb,
  TrendingUp,
  FileText,
  Link2,
  Image as ImageIcon,
  Settings,
  Target,
  Sparkles,
} from 'lucide-react';

interface AIRecommendationsPanelProps {
  projectId: number;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

const PRIORITY_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; border: string; icon: React.ReactNode }
> = {
  critical: {
    label: 'Critical Impact',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    icon: <AlertTriangle className="w-4 h-4 text-red-400" />,
  },
  high: {
    label: 'High Impact',
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    icon: <TrendingUp className="w-4 h-4 text-orange-400" />,
  },
  medium: {
    label: 'Medium Impact',
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    icon: <Lightbulb className="w-4 h-4 text-yellow-400" />,
  },
  quick_win: {
    label: 'Quick Win',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
  },
};

const CATEGORY_ICON: Record<string, React.ReactNode> = {
  technical: <Settings className="w-4 h-4" />,
  onpage: <FileText className="w-4 h-4" />,
  content: <Lightbulb className="w-4 h-4" />,
  link: <Link2 className="w-4 h-4" />,
  image: <ImageIcon className="w-4 h-4" />,
  performance: <Zap className="w-4 h-4" />,
};

const GAP_SEVERITY_CONFIG: Record<string, { color: string; bg: string; border: string }> = {
  high: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
  medium: { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
  low: { color: 'text-slate-400', bg: 'bg-slate-700/40', border: 'border-slate-700' },
};

// ─── Suggestion Card ─────────────────────────────────────────────────────────

const SuggestionCard: React.FC<{ suggestion: AISuggestion }> = ({
  suggestion,
}) => {
  const [expanded, setExpanded] = useState(false);
  const cfg = PRIORITY_CONFIG[suggestion.priority] ?? PRIORITY_CONFIG.medium;
  const catIcon = CATEGORY_ICON[suggestion.category] ?? <Target className="w-4 h-4" />;

  return (
    <div
      className={`rounded-xl border ${cfg.border} bg-slate-900/60 overflow-hidden
        transition-all duration-200 hover:border-opacity-60`}
    >
      {/* Header */}
      <button
        className="w-full text-left p-5 flex items-start justify-between gap-4 group"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <div className="flex items-start gap-4 min-w-0">
          {/* Priority badge */}
          <div
            className={`flex-shrink-0 w-8 h-8 rounded-lg ${cfg.bg} flex items-center justify-center mt-0.5`}
          >
            {cfg.icon}
          </div>

          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span
                className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.color} border ${cfg.border}`}
              >
                {cfg.label}
              </span>
              <span className="flex items-center gap-1 text-xs text-slate-400 px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700">
                {catIcon}
                <span className="capitalize">{suggestion.category}</span>
              </span>
              {suggestion.ai_enhanced && (
                <span className="flex items-center gap-1 text-xs text-violet-400 px-2 py-0.5 rounded-full bg-violet-500/10 border border-violet-500/20">
                  <Sparkles className="w-3 h-3" />
                  AI Enhanced
                </span>
              )}
            </div>
            <h4 className="font-semibold text-white text-sm leading-snug">{suggestion.title}</h4>
            <p className="text-xs text-slate-400 mt-1">{suggestion.impact_estimate}</p>
          </div>
        </div>

        <div className="flex-shrink-0 text-slate-500 group-hover:text-slate-300 transition-colors mt-1">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded body */}
      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-slate-800/80 pt-4">
          {/* Description */}
          <p className="text-sm text-slate-300 leading-relaxed">{suggestion.description}</p>

          {/* Action */}
          <div className="rounded-lg bg-blue-500/5 border border-blue-500/20 p-4">
            <p className="text-xs font-semibold text-blue-400 mb-1.5 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5" /> Recommended Action
            </p>
            <p className="text-sm text-slate-300 leading-relaxed">{suggestion.action}</p>
          </div>

          {/* OpenAI detail */}
          {suggestion.ai_enhanced && suggestion.openai_detail && (
            <div className="rounded-lg bg-violet-500/5 border border-violet-500/20 p-4">
              <p className="text-xs font-semibold text-violet-400 mb-1.5 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" /> AI Expert Insight
              </p>
              <p className="text-sm text-slate-300 leading-relaxed">{suggestion.openai_detail}</p>
            </div>
          )}

          {/* Affected URLs */}
          {suggestion.affected_urls.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-400 mb-2">
                Affected Pages ({suggestion.affected_pages})
              </p>
              <ul className="space-y-1">
                {suggestion.affected_urls.slice(0, 5).map((url) => (
                  <li
                    key={url}
                    className="flex items-center gap-2 text-xs text-slate-400 font-mono bg-slate-800/60 px-3 py-1.5 rounded-lg"
                  >
                    <ExternalLink className="w-3 h-3 flex-shrink-0 text-slate-500" />
                    <span className="truncate">{url}</span>
                  </li>
                ))}
                {suggestion.affected_pages > 5 && (
                  <li className="text-xs text-slate-500 px-3">
                    + {suggestion.affected_pages - 5} more pages
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Content Gap Card ─────────────────────────────────────────────────────────

const ContentGapCard: React.FC<{ gap: ContentGap }> = ({ gap }) => {
  const [expanded, setExpanded] = useState(false);
  const cfg = GAP_SEVERITY_CONFIG[gap.severity] ?? GAP_SEVERITY_CONFIG.medium;

  return (
    <div className={`rounded-xl border ${cfg.border} bg-slate-900/60 overflow-hidden`}>
      <button
        className="w-full text-left p-5 flex items-start justify-between gap-4"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-start gap-3 min-w-0">
          <div
            className={`flex-shrink-0 w-8 h-8 rounded-lg ${cfg.bg} flex items-center justify-center mt-0.5`}
          >
            <Target className={`w-4 h-4 ${cfg.color}`} />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span
                className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.color} border ${cfg.border}`}
              >
                {gap.severity.toUpperCase()}
              </span>
              <span className="text-xs text-slate-500">{gap.affected_count} pages</span>
            </div>
            <h4 className="font-semibold text-white text-sm">{gap.title}</h4>
            <p className="text-xs text-slate-400 mt-1 line-clamp-2">{gap.description}</p>
          </div>
        </div>
        <div className="flex-shrink-0 text-slate-500 mt-1">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-4 border-t border-slate-800/80 pt-4">
          <div className="rounded-lg bg-indigo-500/5 border border-indigo-500/20 p-4">
            <p className="text-xs font-semibold text-indigo-400 mb-1.5 flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5" /> Recommendation
            </p>
            <p className="text-sm text-slate-300 leading-relaxed">{gap.recommendation}</p>
          </div>
          {gap.pages.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-400 mb-2">
                Sample Affected Pages
              </p>
              <ul className="space-y-1">
                {gap.pages.slice(0, 5).map((p) => (
                  <li
                    key={p.url}
                    className="flex items-center justify-between gap-2 text-xs bg-slate-800/60 px-3 py-1.5 rounded-lg"
                  >
                    <span className="font-mono text-slate-400 truncate">{p.url}</span>
                    <span className="text-slate-500 flex-shrink-0">{p.detail}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ─── Main Panel ───────────────────────────────────────────────────────────────

export const AIRecommendationsPanel: React.FC<AIRecommendationsPanelProps> = ({ projectId }) => {
  const [recData, setRecData] = useState<AIRecommendationsResponse | null>(null);
  const [gapData, setGapData] = useState<ContentGapReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<'recommendations' | 'content_gaps'>('recommendations');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [rec, gap] = await Promise.all([
        fetchAIRecommendations(projectId),
        fetchContentGaps(projectId),
      ]);
      setRecData(rec);
      setGapData(gap);
    } catch (err) {
      setError('Failed to load AI analysis. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      const [rec, gap] = await Promise.all([
        regenerateAIRecommendations(projectId),
        fetchContentGaps(projectId),
      ]);
      setRecData(rec);
      setGapData(gap);
    } catch (err) {
      console.error('Regenerate failed:', err);
    } finally {
      setRegenerating(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="relative">
          <div className="w-14 h-14 rounded-full bg-violet-500/10 border border-violet-500/30 flex items-center justify-center">
            <Brain className="w-7 h-7 text-violet-400" />
          </div>
          <div className="absolute -top-1 -right-1 w-4 h-4 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
        </div>
        <p className="text-sm text-slate-400 font-medium">Running AI Analysis…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-8 text-center space-y-3">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto" />
        <p className="text-sm text-red-300">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs font-medium transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const suggestions = recData?.suggestions ?? [];
  const gaps = gapData?.gaps ?? [];
  const isOpenAI = recData?.ai_mode === 'openai';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-violet-500/10 border border-violet-500/20">
              <Brain className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <h3 className="font-bold text-lg text-white leading-tight">AI SEO Intelligence</h3>
              <p className="text-xs text-slate-400">
                {isOpenAI ? (
                  <span className="flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-violet-400" />
                    Powered by OpenAI GPT
                  </span>
                ) : (
                  'Rule-based analysis engine'
                )}
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500
            text-white text-xs font-semibold transition-all shadow-lg hover:shadow-violet-500/20
            active:scale-95 disabled:opacity-50 self-start sm:self-center"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
          Re-analyse
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{suggestions.length}</p>
          <p className="text-xs text-slate-400 mt-1">Recommendations</p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-red-400">
            {suggestions.filter((s) => s.priority === 'critical').length}
          </p>
          <p className="text-xs text-slate-400 mt-1">Critical</p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-indigo-400">{gapData?.total_pages_analyzed ?? 0}</p>
          <p className="text-xs text-slate-400 mt-1">Pages Analysed</p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-emerald-400">
            {gapData?.content_health_score ?? 100}
          </p>
          <p className="text-xs text-slate-400 mt-1">Content Health</p>
        </div>
      </div>

      {/* View tabs */}
      <div className="flex items-center bg-slate-800/60 p-1 rounded-xl border border-slate-700/60 w-fit">
        <button
          onClick={() => setActiveView('recommendations')}
          className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeView === 'recommendations'
              ? 'bg-violet-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Recommendations ({suggestions.length})
        </button>
        <button
          onClick={() => setActiveView('content_gaps')}
          className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeView === 'content_gaps'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          Content Gaps ({gaps.length})
        </button>
      </div>

      {/* Recommendations list */}
      {activeView === 'recommendations' && (
        <div className="space-y-3">
          {suggestions.length === 0 ? (
            <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-10 text-center space-y-3">
              <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
              <p className="font-semibold text-emerald-300">No open issues — site looks great!</p>
              <p className="text-xs text-slate-400">
                Run a fresh crawl after making content changes to get updated recommendations.
              </p>
            </div>
          ) : (
            suggestions.map((s) => (
              <SuggestionCard key={s.id} suggestion={s} />
            ))
          )}
        </div>
      )}

      {/* Content gaps list */}
      {activeView === 'content_gaps' && (
        <div className="space-y-3">
          {/* Summary stats */}
          {gapData && gapData.total_pages_analyzed > 0 && (
            <div className="grid grid-cols-3 gap-3 mb-2">
              <div className="bg-red-500/5 border border-red-500/15 rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-red-400">{gapData.thin_content_count}</p>
                <p className="text-xs text-slate-400 mt-0.5">Thin Content</p>
              </div>
              <div className="bg-yellow-500/5 border border-yellow-500/15 rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-yellow-400">{gapData.missing_h1_count}</p>
                <p className="text-xs text-slate-400 mt-0.5">Missing H1</p>
              </div>
              <div className="bg-orange-500/5 border border-orange-500/15 rounded-xl p-3 text-center">
                <p className="text-xl font-bold text-orange-400">{gapData.cannibalization_clusters}</p>
                <p className="text-xs text-slate-400 mt-0.5">Cannibal. Clusters</p>
              </div>
            </div>
          )}

          {gaps.length === 0 ? (
            <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-10 text-center space-y-3">
              <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
              <p className="font-semibold text-emerald-300">
                {gapData?.total_pages_analyzed === 0
                  ? 'Run a crawl first to analyse content gaps.'
                  : 'No content gaps detected — excellent content health!'}
              </p>
            </div>
          ) : (
            gaps.map((g) => <ContentGapCard key={g.id} gap={g} />)
          )}
        </div>
      )}
    </div>
  );
};
