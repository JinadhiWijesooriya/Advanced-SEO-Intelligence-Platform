import React, { useEffect, useState } from 'react';
import {
  fetchProjectSEOSummary,
  recalculateProjectScores,
} from '../../services/api';
import type { Project, ProjectSEOSummary } from '../../services/api';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip,
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  ShieldCheck,
  Globe,
  FileText,
  Layers,
  ArrowRight,
  HelpCircle,
  ExternalLink,
} from 'lucide-react';

interface ProjectDashboardProps {
  project: Project;
  onViewIssues: (project: Project) => void;
  onViewPages: (project: Project) => void;
  onTriggerCrawl: (projectId: number) => void;
}

export const ProjectDashboard: React.FC<ProjectDashboardProps> = ({
  project,
  onViewIssues,
  onViewPages,
  onTriggerCrawl,
}) => {
  const [summary, setSummary] = useState<ProjectSEOSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchProjectSEOSummary(project.id);
      setSummary(data);
    } catch (err: unknown) {
      console.error('Failed to load SEO summary:', err);
      setError('Could not load SEO summary metrics.');
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    try {
      setRefreshing(true);
      const data = await recalculateProjectScores(project.id);
      setSummary(data);
    } catch (err: unknown) {
      console.error('Failed to recalculate scores:', err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, [project.id]);

  if (loading) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 flex flex-col items-center justify-center space-y-4">
        <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
        <p className="text-sm text-slate-400 font-medium">Computing SEO Intelligence Metrics...</p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="bg-slate-900/60 border border-rose-900/40 rounded-2xl p-8 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <p className="text-slate-300 font-medium">{error || 'No audit summary found.'}</p>
        <button
          onClick={loadSummary}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  // Health color palette
  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A':
        return { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30', ring: '#10b981' };
      case 'B':
        return { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30', ring: '#3b82f6' };
      case 'C':
        return { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30', ring: '#f59e0b' };
      case 'D':
        return { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30', ring: '#f97316' };
      default:
        return { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/30', ring: '#f43f5e' };
    }
  };

  const gradeStyle = getGradeColor(summary.health_grade);

  // Radar chart data for Category Scores
  const radarData = [
    { subject: 'Technical', score: summary.category_scores.technical, fullMark: 100 },
    { subject: 'On-Page', score: summary.category_scores.onpage, fullMark: 100 },
    { subject: 'Content', score: summary.category_scores.content, fullMark: 100 },
    { subject: 'Links', score: summary.category_scores.link, fullMark: 100 },
    { subject: 'Performance', score: summary.category_scores.performance, fullMark: 100 },
  ];

  const categoryList = [
    { name: 'Technical SEO', key: 'technical', weight: '25%', score: summary.category_scores.technical, desc: 'HTTP status, canonical tags, HTTPS, server response' },
    { name: 'On-Page SEO', key: 'onpage', weight: '25%', score: summary.category_scores.onpage, desc: 'Title tags, meta descriptions, H1 headers, duplicate tags' },
    { name: 'Content Quality', key: 'content', weight: '20%', score: summary.category_scores.content, desc: 'Word count sufficiency, thin content detection' },
    { name: 'Links & Navigation', key: 'link', weight: '15%', score: summary.category_scores.link, desc: 'Internal link health, broken link detection' },
    { name: 'Performance Signals', key: 'performance', weight: '10%', score: summary.category_scores.performance, desc: 'Response latency thresholds, page delivery speed' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-indigo-500/20 text-white">
            <Globe className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-bold text-white tracking-wide">{project.name}</h2>
              <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                Audit #{summary.crawl_job_id ?? 'N/A'}
              </span>
            </div>
            <a
              href={project.target_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-slate-400 hover:text-indigo-400 transition-colors flex items-center space-x-1 mt-0.5 font-mono"
            >
              <span>{project.target_url}</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleRecalculate}
            disabled={refreshing}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-all active:scale-95 disabled:opacity-50"
            title="Recalculate scores from current issue findings"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Recalculate</span>
          </button>
          <button
            onClick={() => onViewPages(project)}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-all active:scale-95"
          >
            <FileText className="w-3.5 h-3.5 text-blue-400" />
            <span>Pages ({summary.audited_pages})</span>
          </button>
          <button
            onClick={() => onViewIssues(project)}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold shadow-md transition-all active:scale-95"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Issues ({summary.issue_counts.total})</span>
          </button>
          <button
            onClick={() => onTriggerCrawl(project.id)}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-md transition-all active:scale-95"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Run Audit Crawl</span>
          </button>
        </div>
      </div>

      {/* Main Score & Distribution Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Overall SEO Score Gauge Card */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-xl relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Overall SEO Score
            </span>
            <span
              className={`text-xs font-bold px-2.5 py-1 rounded-full border ${gradeStyle.bg} ${gradeStyle.text} ${gradeStyle.border}`}
            >
              Grade {summary.health_grade}
            </span>
          </div>

          {/* Central Circular Display */}
          <div className="my-6 flex flex-col items-center justify-center">
            <div className="relative w-44 h-44 flex items-center justify-center">
              {/* Outer SVG Ring */}
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  stroke="#1e293b"
                  strokeWidth="12"
                  fill="transparent"
                />
                <circle
                  cx="80"
                  cy="80"
                  r="70"
                  stroke={gradeStyle.ring}
                  strokeWidth="12"
                  fill="transparent"
                  strokeDasharray={440}
                  strokeDashoffset={440 - (440 * summary.overall_score) / 100}
                  strokeLinecap="round"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              {/* Central Text */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-4xl font-extrabold text-white tracking-tight">
                  {summary.overall_score}
                </span>
                <span className="text-xs text-slate-400 font-medium mt-0.5">out of 100</span>
              </div>
            </div>
          </div>

          {/* Page Distribution Bar */}
          <div className="space-y-2 pt-4 border-t border-slate-800/80">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span>Audited URL Distribution</span>
              <span className="font-semibold text-slate-200">{summary.audited_pages} Pages</span>
            </div>
            <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden flex">
              <div
                style={{
                  width: `${summary.audited_pages ? (summary.page_health.healthy / summary.audited_pages) * 100 : 0}%`,
                }}
                className="bg-emerald-500 h-full"
                title={`Healthy (>=80): ${summary.page_health.healthy}`}
              />
              <div
                style={{
                  width: `${summary.audited_pages ? (summary.page_health.warning / summary.audited_pages) * 100 : 0}%`,
                }}
                className="bg-amber-500 h-full"
                title={`Warning (60-79): ${summary.page_health.warning}`}
              />
              <div
                style={{
                  width: `${summary.audited_pages ? (summary.page_health.critical / summary.audited_pages) * 100 : 0}%`,
                }}
                className="bg-rose-500 h-full"
                title={`Critical (<60): ${summary.page_health.critical}`}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 pt-1">
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Healthy ({summary.page_health.healthy})</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                <span>Warning ({summary.page_health.warning})</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                <span>Critical ({summary.page_health.critical})</span>
              </span>
            </div>
          </div>
        </div>

        {/* Category Strength Radar Chart */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Category Radar
            </span>
            <span className="text-xs text-slate-400">Benchmark: 100 max</span>
          </div>

          <div className="h-64 w-full flex items-center justify-center my-auto">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 9 }} />
                <Radar
                  name="SEO Score"
                  dataKey="score"
                  stroke="#6366f1"
                  fill="#6366f1"
                  fillOpacity={0.4}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-center space-x-2">
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            <span>Weighted audit score across all crawled HTML documents</span>
          </div>
        </div>

        {/* Severity Metrics & Action Cards */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Issue Breakdown
            </span>
            <span className="text-xs font-semibold text-slate-300">
              {summary.issue_counts.total} Total Findings
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Critical */}
            <div
              onClick={() => onViewIssues(project)}
              className="bg-rose-500/10 border border-rose-500/20 hover:border-rose-500/40 p-4 rounded-xl cursor-pointer transition-all hover:scale-[1.02]"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-rose-400">Critical</span>
                <AlertCircle className="w-4 h-4 text-rose-400" />
              </div>
              <p className="text-2xl font-extrabold text-white mt-2">
                {summary.issue_counts.by_severity.critical}
              </p>
              <p className="text-[10px] text-rose-300/70 mt-0.5">-25 pts deduction</p>
            </div>

            {/* High */}
            <div
              onClick={() => onViewIssues(project)}
              className="bg-amber-500/10 border border-amber-500/20 hover:border-amber-500/40 p-4 rounded-xl cursor-pointer transition-all hover:scale-[1.02]"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-amber-400">High</span>
                <AlertTriangle className="w-4 h-4 text-amber-400" />
              </div>
              <p className="text-2xl font-extrabold text-white mt-2">
                {summary.issue_counts.by_severity.high}
              </p>
              <p className="text-[10px] text-amber-300/70 mt-0.5">-15 pts deduction</p>
            </div>

            {/* Medium */}
            <div
              onClick={() => onViewIssues(project)}
              className="bg-blue-500/10 border border-blue-500/20 hover:border-blue-500/40 p-4 rounded-xl cursor-pointer transition-all hover:scale-[1.02]"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-blue-400">Medium</span>
                <HelpCircle className="w-4 h-4 text-blue-400" />
              </div>
              <p className="text-2xl font-extrabold text-white mt-2">
                {summary.issue_counts.by_severity.medium}
              </p>
              <p className="text-[10px] text-blue-300/70 mt-0.5">-8 pts deduction</p>
            </div>

            {/* Low */}
            <div
              onClick={() => onViewIssues(project)}
              className="bg-slate-800/60 border border-slate-700/60 hover:border-slate-600 p-4 rounded-xl cursor-pointer transition-all hover:scale-[1.02]"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">Low</span>
                <ShieldCheck className="w-4 h-4 text-slate-400" />
              </div>
              <p className="text-2xl font-extrabold text-white mt-2">
                {summary.issue_counts.by_severity.low}
              </p>
              <p className="text-[10px] text-slate-400 mt-0.5">-3 pts deduction</p>
            </div>
          </div>

          {/* Quick Resolution Stats */}
          <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">Open: {summary.issue_counts.by_status.open}</span>
            <span className="text-emerald-400 font-medium">
              Resolved: {summary.issue_counts.by_status.resolved}
            </span>
            <span className="text-slate-500">Ignored: {summary.issue_counts.by_status.ignored}</span>
          </div>
        </div>
      </div>

      {/* Category Breakdown Progress Bars */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            <h3 className="font-bold text-white text-base">Weighted Category Diagnostics</h3>
          </div>
          <span className="text-xs text-slate-400">Formulated per Section 11 Specification</span>
        </div>

        <div className="space-y-4">
          {categoryList.map((cat) => {
            const scoreColor =
              cat.score >= 80 ? 'bg-emerald-500' : cat.score >= 60 ? 'bg-amber-500' : 'bg-rose-500';
            const badgeColor =
              cat.score >= 80
                ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                : cat.score >= 60
                ? 'text-amber-400 bg-amber-500/10 border-amber-500/20'
                : 'text-rose-400 bg-rose-500/10 border-rose-500/20';

            return (
              <div key={cat.key} className="bg-slate-800/40 border border-slate-800 p-4 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-white text-sm">{cat.name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
                      Weight {cat.weight}
                    </span>
                  </div>
                  <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${badgeColor}`}>
                    {cat.score} / 100
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${scoreColor}`}
                    style={{ width: `${cat.score}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400">{cat.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top Actionable Priority Issues */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <h3 className="font-bold text-white text-base">Top Priority Recommendations</h3>
          </div>
          <button
            onClick={() => onViewIssues(project)}
            className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1 font-medium"
          >
            <span>View all issues</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {summary.top_issues.length === 0 ? (
          <div className="bg-slate-800/30 rounded-xl p-8 text-center text-slate-400 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <span>No critical or high issues detected in latest audit! Great job!</span>
          </div>
        ) : (
          <div className="space-y-3">
            {summary.top_issues.map((item, idx) => (
              <div
                key={idx}
                className="bg-slate-800/40 border border-slate-800/80 hover:border-slate-700 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-colors"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                        item.severity === 'critical'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}
                    >
                      {item.severity}
                    </span>
                    <span className="font-mono text-xs text-slate-300 font-semibold">{item.code}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                      Affects {item.count} page{item.count > 1 ? 's' : ''}
                    </span>
                  </div>
                  <p className="text-xs text-slate-200">{item.message}</p>
                  <p className="text-[11px] text-slate-400">
                    <span className="text-indigo-400 font-medium">Fix:</span> {item.recommendation}
                  </p>
                </div>

                <button
                  onClick={() => onViewIssues(project)}
                  className="self-start md:self-center px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold whitespace-nowrap"
                >
                  Inspect Pages
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
