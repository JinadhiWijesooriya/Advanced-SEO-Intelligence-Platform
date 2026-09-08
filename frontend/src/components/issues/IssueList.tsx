import React, { useEffect, useState, useCallback } from 'react';
import {
  fetchProjectIssues,
  fetchIssueSummary,
  updateIssueStatus,
} from '../../services/api';
import type {
  SEOIssue,
  SEOIssueListResponse,
  IssueSummaryResponse,
} from '../../services/api';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  Search,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Globe,
  ShieldAlert,
  FileText,
  Link2,
  Image as ImageIcon,
  Zap,
  CheckCircle2,
  EyeOff,
  RotateCcw,
  ExternalLink,
} from 'lucide-react';

// ─── Types ──────────────────────────────────────────────────────────────────

type SeverityKey = 'critical' | 'high' | 'medium' | 'low';
type CategoryKey = 'all' | 'technical' | 'onpage' | 'content' | 'link' | 'image' | 'performance';
type StatusKey = 'open' | 'resolved' | 'ignored' | 'all';

// ─── Constants ───────────────────────────────────────────────────────────────

const SEVERITY_CONFIG: Record<SeverityKey, { label: string; color: string; bg: string; border: string; dot: string }> = {
  critical: {
    label: 'Critical',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    dot: 'bg-red-500',
  },
  high: {
    label: 'High',
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    dot: 'bg-orange-500',
  },
  medium: {
    label: 'Medium',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    dot: 'bg-amber-500',
  },
  low: {
    label: 'Low',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
    dot: 'bg-blue-500',
  },
};

const CATEGORY_CONFIG: Record<Exclude<CategoryKey, 'all'>, { label: string; icon: React.ReactNode }> = {
  technical: { label: 'Technical', icon: <ShieldAlert className="w-4 h-4" /> },
  onpage: { label: 'On-Page', icon: <FileText className="w-4 h-4" /> },
  content: { label: 'Content', icon: <Globe className="w-4 h-4" /> },
  link: { label: 'Links', icon: <Link2 className="w-4 h-4" /> },
  image: { label: 'Images', icon: <ImageIcon className="w-4 h-4" /> },
  performance: { label: 'Performance', icon: <Zap className="w-4 h-4" /> },
};

// ─── Severity Badge ──────────────────────────────────────────────────────────

const SeverityBadge: React.FC<{ severity: SeverityKey }> = ({ severity }) => {
  const cfg = SEVERITY_CONFIG[severity];
  const Icon =
    severity === 'critical' ? AlertCircle :
    severity === 'high' ? AlertTriangle :
    severity === 'medium' ? Info :
    CheckCircle;

  return (
    <span className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${cfg.bg} ${cfg.color} border ${cfg.border}`}>
      <Icon className="w-3 h-3" />
      <span>{cfg.label}</span>
    </span>
  );
};

// ─── Summary Cards ────────────────────────────────────────────────────────────

interface SummaryCardsProps {
  summary: IssueSummaryResponse;
}

const SummaryCards: React.FC<SummaryCardsProps> = ({ summary }) => {
  const cards = [
    {
      label: 'Critical',
      count: summary.by_severity.critical,
      cfg: SEVERITY_CONFIG.critical,
      icon: <AlertCircle className="w-5 h-5" />,
    },
    {
      label: 'High',
      count: summary.by_severity.high,
      cfg: SEVERITY_CONFIG.high,
      icon: <AlertTriangle className="w-5 h-5" />,
    },
    {
      label: 'Medium',
      count: summary.by_severity.medium,
      cfg: SEVERITY_CONFIG.medium,
      icon: <Info className="w-5 h-5" />,
    },
    {
      label: 'Low',
      count: summary.by_severity.low,
      cfg: SEVERITY_CONFIG.low,
      icon: <CheckCircle className="w-5 h-5" />,
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map(({ label, count, cfg, icon }) => (
        <div
          key={label}
          className={`relative overflow-hidden rounded-xl p-5 border ${cfg.border} ${cfg.bg} backdrop-blur-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-lg`}
        >
          {/* Background gradient glow */}
          <div className={`absolute top-0 right-0 w-20 h-20 rounded-full opacity-10 blur-xl ${cfg.dot}`} />
          <div className={`${cfg.color} mb-3`}>{icon}</div>
          <p className="text-3xl font-extrabold text-white tabular-nums">{count.toLocaleString()}</p>
          <p className={`text-xs font-semibold mt-1 ${cfg.color}`}>{label} Severity</p>
        </div>
      ))}
    </div>
  );
};

// ─── Category Tabs ────────────────────────────────────────────────────────────

interface CategoryTabsProps {
  active: CategoryKey;
  summary: IssueSummaryResponse;
  onChange: (cat: CategoryKey) => void;
}

const CategoryTabs: React.FC<CategoryTabsProps> = ({ active, summary, onChange }) => {
  const tabs: { key: CategoryKey; label: string; count?: number; icon?: React.ReactNode }[] = [
    { key: 'all', label: 'All Issues', count: summary.total_open },
    ...Object.entries(CATEGORY_CONFIG).map(([key, { label, icon }]) => ({
      key: key as CategoryKey,
      label,
      count: summary.by_category[key as keyof typeof summary.by_category],
      icon,
    })),
  ];

  return (
    <div className="flex flex-wrap gap-2">
      {tabs.map(({ key, label, count, icon }) => (
        <button
          key={key}
          id={`issue-tab-${key}`}
          onClick={() => onChange(key)}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all duration-200 ${
            active === key
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/25'
              : 'bg-slate-800/70 text-slate-400 hover:text-white hover:bg-slate-700/70 border border-slate-700/50'
          }`}
        >
          {icon && <span>{icon}</span>}
          <span>{label}</span>
          {count !== undefined && (
            <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
              active === key ? 'bg-white/20 text-white' : 'bg-slate-700 text-slate-300'
            }`}>
              {count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
};

// ─── Issue Row ────────────────────────────────────────────────────────────────

interface IssueRowProps {
  issue: SEOIssue;
  onStatusChange: (issueId: number, newStatus: 'open' | 'resolved' | 'ignored') => Promise<void>;
}

const IssueRow: React.FC<IssueRowProps> = ({ issue, onStatusChange }) => {
  const [expanded, setExpanded] = useState(false);
  const [updating, setUpdating] = useState(false);

  const handleStatusChange = async (newStatus: 'open' | 'resolved' | 'ignored') => {
    setUpdating(true);
    try {
      await onStatusChange(issue.id, newStatus);
    } finally {
      setUpdating(false);
    }
  };

  const categoryMeta = CATEGORY_CONFIG[issue.category as keyof typeof CATEGORY_CONFIG];
  const isOpen = issue.status === 'open';
  const isResolved = issue.status === 'resolved';

  return (
    <div className={`rounded-xl border transition-all duration-200 ${
      isResolved
        ? 'bg-emerald-500/5 border-emerald-500/20 opacity-70'
        : issue.status === 'ignored'
        ? 'bg-slate-800/30 border-slate-700/30 opacity-50'
        : 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600/70'
    }`}>
      {/* Header Row */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-4 flex items-start justify-between gap-4 group"
      >
        <div className="flex items-start gap-3 flex-1 min-w-0">
          {/* Severity dot */}
          <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${SEVERITY_CONFIG[issue.severity]?.dot || 'bg-slate-500'}`} />

          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <SeverityBadge severity={issue.severity as SeverityKey} />

              {/* Category badge */}
              {categoryMeta && (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-slate-700/60 text-slate-300 text-[11px] font-medium border border-slate-600/40">
                  {categoryMeta.icon}
                  <span>{categoryMeta.label}</span>
                </span>
              )}

              {/* Rule code */}
              <span className="font-mono text-[11px] text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                {issue.code}
              </span>

              {/* Status badge */}
              {!isOpen && (
                <span className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${
                  isResolved
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25'
                    : 'bg-slate-600/40 text-slate-400 border border-slate-600/40'
                }`}>
                  {issue.status}
                </span>
              )}
            </div>

            <p className="text-sm text-slate-200 leading-snug font-medium pr-4 truncate group-hover:text-white transition-colors">
              {issue.message}
            </p>

            {issue.page_url && (
              <p className="text-[11px] text-slate-500 font-mono mt-1.5 truncate">
                {issue.page_url}
              </p>
            )}
          </div>
        </div>

        <div className="flex-shrink-0 flex items-center gap-2">
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors" />
          )}
        </div>
      </button>

      {/* Expanded Detail */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-slate-700/50 pt-4">
          {/* Recommendation */}
          <div className="bg-slate-900/60 rounded-lg p-4 border border-slate-700/40">
            <p className="text-xs font-semibold text-indigo-300 mb-1.5 uppercase tracking-wide">Recommended Fix</p>
            <p className="text-sm text-slate-300 leading-relaxed">{issue.recommendation}</p>
          </div>

          {/* Affected URL */}
          {issue.page_url && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Affected URL:</span>
              <a
                href={issue.page_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-mono truncate transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                {issue.page_url}
                <ExternalLink className="w-3 h-3 flex-shrink-0" />
              </a>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-2 pt-1">
            {issue.status !== 'resolved' && (
              <button
                id={`issue-resolve-${issue.id}`}
                onClick={() => handleStatusChange('resolved')}
                disabled={updating}
                className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 text-xs font-semibold border border-emerald-600/30 transition-all active:scale-95 disabled:opacity-50"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Mark Resolved</span>
              </button>
            )}

            {issue.status !== 'ignored' && (
              <button
                id={`issue-ignore-${issue.id}`}
                onClick={() => handleStatusChange('ignored')}
                disabled={updating}
                className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-slate-700/50 hover:bg-slate-600/50 text-slate-400 text-xs font-semibold border border-slate-600/40 transition-all active:scale-95 disabled:opacity-50"
              >
                <EyeOff className="w-3.5 h-3.5" />
                <span>Ignore</span>
              </button>
            )}

            {issue.status !== 'open' && (
              <button
                id={`issue-reopen-${issue.id}`}
                onClick={() => handleStatusChange('open')}
                disabled={updating}
                className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-500/15 hover:bg-indigo-500/30 text-indigo-400 text-xs font-semibold border border-indigo-500/25 transition-all active:scale-95 disabled:opacity-50"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reopen</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Main IssueList Component ─────────────────────────────────────────────────

interface IssueListProps {
  projectId: number;
}

export const IssueList: React.FC<IssueListProps> = ({ projectId }) => {
  const [summary, setSummary] = useState<IssueSummaryResponse | null>(null);
  const [issueData, setIssueData] = useState<SEOIssueListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [activeCategory, setActiveCategory] = useState<CategoryKey>('all');
  const [activeSeverity, setActiveSeverity] = useState<string>('');
  const [activeStatus, setActiveStatus] = useState<StatusKey>('open');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const PAGE_SIZE = 20;

  const loadData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);

    try {
      const [summaryData, issuesData] = await Promise.all([
        fetchIssueSummary(projectId),
        fetchProjectIssues(projectId, {
          category: activeCategory !== 'all' ? activeCategory : undefined,
          severity: activeSeverity || undefined,
          status: activeStatus !== 'all' ? activeStatus : undefined,
          search: searchQuery || undefined,
          page: currentPage,
          page_size: PAGE_SIZE,
        }),
      ]);
      setSummary(summaryData);
      setIssueData(issuesData);
    } catch (err) {
      console.error('Failed to load SEO issues:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [projectId, activeCategory, activeSeverity, activeStatus, searchQuery, currentPage]);

  useEffect(() => {
    setCurrentPage(1);
  }, [activeCategory, activeSeverity, activeStatus, searchQuery]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStatusChange = async (issueId: number, newStatus: 'open' | 'resolved' | 'ignored') => {
    await updateIssueStatus(issueId, newStatus);
    await loadData(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Analyzing SEO Issues…</p>
        </div>
      </div>
    );
  }

  const totalPages = issueData ? Math.ceil(issueData.total / PAGE_SIZE) : 1;
  const hasSummary = summary && (summary.total_open + summary.total_resolved + summary.total_ignored) > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-white">SEO Issue Dashboard</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {summary ? `${summary.total_open} open · ${summary.total_resolved} resolved · ${summary.total_ignored} ignored` : 'No analysis data yet'}
          </p>
        </div>
        <button
          id="issues-refresh-btn"
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition-all active:scale-95 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* No issues state */}
      {!hasSummary ? (
        <div className="flex flex-col items-center justify-center py-16 bg-slate-800/30 rounded-xl border border-slate-700/50 border-dashed">
          <div className="w-16 h-16 rounded-full bg-slate-700/50 flex items-center justify-center mb-4">
            <CheckCircle2 className="w-8 h-8 text-emerald-400" />
          </div>
          <h4 className="text-lg font-bold text-white mb-1">No SEO Issues Found</h4>
          <p className="text-sm text-slate-400 text-center max-w-sm">
            Run a crawl job on this project to automatically analyze pages and surface SEO issues.
          </p>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <SummaryCards summary={summary!} />

          {/* Status Filter Tabs (Open / Resolved / Ignored / All) */}
          <div className="flex gap-2">
            {(['open', 'resolved', 'ignored', 'all'] as StatusKey[]).map((s) => (
              <button
                key={s}
                id={`status-tab-${s}`}
                onClick={() => setActiveStatus(s)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all capitalize ${
                  activeStatus === s
                    ? 'bg-slate-600 text-white'
                    : 'bg-slate-800/50 text-slate-400 hover:text-white border border-slate-700/50'
                }`}
              >
                {s}
                {summary && (
                  <span className="ml-1.5 text-[10px] opacity-70">
                    ({s === 'open' ? summary.total_open : s === 'resolved' ? summary.total_resolved : s === 'ignored' ? summary.total_ignored : summary.total_open + summary.total_resolved + summary.total_ignored})
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Category Filter Tabs */}
          <CategoryTabs
            active={activeCategory}
            summary={summary!}
            onChange={(cat) => setActiveCategory(cat)}
          />

          {/* Search and Severity filter */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                id="issues-search-input"
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search issues by message or code…"
                className="w-full pl-9 pr-4 py-2.5 bg-slate-800/70 border border-slate-700/60 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500/40 transition-all"
              />
            </div>

            <select
              id="severity-filter"
              value={activeSeverity}
              onChange={(e) => setActiveSeverity(e.target.value)}
              className="px-4 py-2.5 bg-slate-800/70 border border-slate-700/60 rounded-xl text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500/40 transition-all appearance-none cursor-pointer"
            >
              <option value="">All Severities</option>
              <option value="critical">🔴 Critical</option>
              <option value="high">🟠 High</option>
              <option value="medium">🟡 Medium</option>
              <option value="low">🔵 Low</option>
            </select>
          </div>

          {/* Issues List */}
          <div className="space-y-3">
            {!issueData || issueData.issues.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 bg-slate-800/30 rounded-xl border border-slate-700/40 border-dashed">
                <Search className="w-8 h-8 text-slate-600 mb-3" />
                <p className="text-sm text-slate-400">No issues match the current filters.</p>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between text-xs text-slate-500 px-1">
                  <span>
                    Showing {Math.min((currentPage - 1) * PAGE_SIZE + 1, issueData.total)}–
                    {Math.min(currentPage * PAGE_SIZE, issueData.total)} of {issueData.total} issues
                  </span>
                </div>

                {issueData.issues.map((issue) => (
                  <IssueRow
                    key={issue.id}
                    issue={issue}
                    onStatusChange={handleStatusChange}
                  />
                ))}

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2 pt-4">
                    <button
                      id="issues-prev-page"
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 border border-slate-700 disabled:opacity-40 transition-all"
                    >
                      ← Prev
                    </button>
                    <span className="text-xs text-slate-500">
                      Page {currentPage} of {totalPages}
                    </span>
                    <button
                      id="issues-next-page"
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 border border-slate-700 disabled:opacity-40 transition-all"
                    >
                      Next →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default IssueList;
