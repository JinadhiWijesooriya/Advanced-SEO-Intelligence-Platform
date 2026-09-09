import React, { useEffect, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { fetchAuditHistory } from '../../services/api';
import type { AuditSnapshot } from '../../services/api';
import { TrendingUp, BarChart3, RefreshCw, AlertCircle } from 'lucide-react';

interface Props {
  projectId: number;
}

const GRADE_MAP: Record<string, string> = {
  A: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  B: 'bg-lime-500/10 text-lime-400 border-lime-500/20',
  C: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  D: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  F: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
};

function getGrade(score: number): string {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-3 shadow-xl text-xs space-y-1">
      <p className="text-slate-300 font-semibold mb-2">{label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }} />
          <span className="text-slate-400 capitalize">{p.dataKey.replace('_score', '')}:</span>
          <span className="text-white font-mono">{p.value?.toFixed(1)}</span>
        </div>
      ))}
    </div>
  );
};

export const HistoryView: React.FC<Props> = ({ projectId }) => {
  const [snapshots, setSnapshots] = useState<AuditSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAuditHistory(projectId);
      setSnapshots(data);
    } catch {
      setError('Failed to load audit history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [projectId]);

  const chartData = [...snapshots]
    .reverse()
    .map((s, i) => ({
      audit: `#${i + 1}`,
      date: formatDate(s.created_at),
      overall_score: s.overall_score,
      technical_score: s.technical_score,
      content_score: s.content_score,
      link_score: s.link_score,
    }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-3 text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl p-4">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  if (snapshots.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center space-y-3">
        <div className="p-4 bg-slate-800/60 rounded-2xl">
          <TrendingUp className="w-10 h-10 text-slate-600" />
        </div>
        <p className="text-slate-400 text-sm">No audit history yet.</p>
        <p className="text-slate-500 text-xs max-w-xs">Run your first crawl to start tracking score trends over time.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-violet-500/10 rounded-lg">
            <TrendingUp className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h3 className="font-bold text-white">Score Evolution</h3>
            <p className="text-xs text-slate-400">{snapshots.length} audit{snapshots.length !== 1 ? 's' : ''} recorded</p>
          </div>
        </div>
        <button
          onClick={load}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Chart */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
            <defs>
              {[
                { key: 'overall_score', color: '#6366f1' },
                { key: 'technical_score', color: '#22d3ee' },
                { key: 'content_score', color: '#a78bfa' },
                { key: 'link_score', color: '#34d399' },
              ].map(({ key, color }) => (
                <linearGradient key={key} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.2} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="audit" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
            {[
              { key: 'overall_score', color: '#6366f1', label: 'Overall' },
              { key: 'technical_score', color: '#22d3ee', label: 'Technical' },
              { key: 'content_score', color: '#a78bfa', label: 'Content' },
              { key: 'link_score', color: '#34d399', label: 'Links' },
            ].map(({ key, color }) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={color}
                fill={`url(#grad-${key})`}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Snapshot Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-semibold text-white">Audit History</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left px-5 py-3 text-slate-400 font-medium">#</th>
                <th className="text-left px-3 py-3 text-slate-400 font-medium">Date</th>
                <th className="text-right px-3 py-3 text-slate-400 font-medium">Score</th>
                <th className="text-right px-3 py-3 text-slate-400 font-medium">Grade</th>
                <th className="text-right px-3 py-3 text-slate-400 font-medium">Pages</th>
                <th className="text-right px-3 py-3 text-slate-400 font-medium">Issues</th>
                <th className="text-right px-3 py-3 text-slate-400 font-medium text-rose-400">Critical</th>
                <th className="text-right px-5 py-3 text-slate-400 font-medium text-orange-400">High</th>
              </tr>
            </thead>
            <tbody>
              {[...snapshots].reverse().map((snap, idx) => {
                const grade = getGrade(snap.overall_score);
                return (
                  <tr key={snap.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                    <td className="px-5 py-3 text-slate-500 font-mono">#{idx + 1}</td>
                    <td className="px-3 py-3 text-slate-300">{formatDate(snap.created_at)}</td>
                    <td className="px-3 py-3 text-right font-bold text-white font-mono">{snap.overall_score.toFixed(1)}</td>
                    <td className="px-3 py-3 text-right">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold border ${GRADE_MAP[grade] || ''}`}>
                        {grade}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-right text-slate-300">{snap.page_count}</td>
                    <td className="px-3 py-3 text-right text-slate-300">{snap.issue_count}</td>
                    <td className="px-3 py-3 text-right text-rose-400 font-medium">{snap.critical_issues}</td>
                    <td className="px-5 py-3 text-right text-orange-400 font-medium">{snap.high_issues}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
