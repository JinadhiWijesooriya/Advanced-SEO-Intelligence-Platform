import React, { useEffect, useState } from 'react';
import {
  fetchCompetitors, addCompetitor, deleteCompetitor, auditCompetitor
} from '../../services/api';
import type { Competitor, Project } from '../../services/api';
import {
  Globe, Plus, Trash2, Play, RefreshCw, AlertCircle, X,
  Target, Award
} from 'lucide-react';

interface Props {
  project: Project;
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-slate-500 text-xs">N/A</span>;
  const color = score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-yellow-400' : 'text-rose-400';
  return <span className={`font-bold font-mono text-sm ${color}`}>{score.toFixed(1)}</span>;
}

function GradeBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-slate-500 text-xs font-bold">—</span>;
  const grade = score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F';
  const cls = score >= 80 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    : score >= 60 ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
    : 'bg-rose-500/10 text-rose-400 border-rose-500/20';
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-bold border ${cls}`}>{grade}</span>
  );
}

export const CompetitorView: React.FC<Props> = ({ project }) => {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [auditing, setAuditing] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);

  // Add form state
  const [form, setForm] = useState({ name: '', domain: '', target_url: '' });
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setCompetitors(await fetchCompetitors(project.id));
    } catch {
      setError('Failed to load competitors.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [project.id]);

  const handleAdd = async () => {
    setFormError('');
    if (!form.name.trim()) { setFormError('Name is required.'); return; }
    if (!form.target_url.trim()) { setFormError('URL is required.'); return; }
    try {
      new URL(form.target_url);
    } catch {
      setFormError('Please enter a valid URL (e.g. https://example.com)');
      return;
    }
    setSaving(true);
    try {
      const domain = form.domain.trim() || new URL(form.target_url).hostname;
      await addCompetitor({ name: form.name, domain, target_url: form.target_url, project_id: project.id });
      setShowModal(false);
      setForm({ name: '', domain: '', target_url: '' });
      await load();
    } catch (e: any) {
      setFormError(e?.response?.data?.detail || 'Failed to add competitor.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    setDeleting(id);
    try {
      await deleteCompetitor(id);
      setCompetitors(prev => prev.filter(c => c.id !== id));
    } catch {
      setError('Failed to delete competitor.');
    } finally {
      setDeleting(null);
    }
  };

  const handleAudit = async (id: number) => {
    setAuditing(id);
    try {
      await auditCompetitor(id);
      await load();
    } catch {
      setError('Failed to trigger audit.');
    } finally {
      setAuditing(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-500/10 rounded-lg">
            <Target className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="font-bold text-white">Competitor Benchmark</h3>
            <p className="text-xs text-slate-400">{competitors.length} competitor{competitors.length !== 1 ? 's' : ''} tracked</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={load}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all shadow-md active:scale-95"
          >
            <Plus className="w-4 h-4" />
            Add Competitor
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl p-4 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-8 h-8 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
        </div>
      ) : competitors.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center space-y-3 border border-dashed border-slate-700 rounded-2xl">
          <div className="p-4 bg-slate-800/60 rounded-2xl">
            <Globe className="w-10 h-10 text-slate-600" />
          </div>
          <p className="text-slate-400 text-sm font-medium">No competitors tracked yet</p>
          <p className="text-slate-500 text-xs max-w-xs">Add competitor domains to benchmark your SEO performance side-by-side.</p>
          <button
            onClick={() => setShowModal(true)}
            className="mt-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl transition-all"
          >
            Add First Competitor
          </button>
        </div>
      ) : (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
          {/* Your project row */}
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-700 bg-indigo-500/5">
            <div className="flex items-center gap-3">
              <Award className="w-4 h-4 text-indigo-400" />
              <div>
                <p className="text-sm font-bold text-white">{project.name} <span className="text-indigo-400 text-xs font-normal ml-1">(Your Site)</span></p>
                <p className="text-xs text-slate-400 font-mono">{project.target_url}</p>
              </div>
            </div>
          </div>

          {/* Competitors */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/40">
                  <th className="text-left px-5 py-3 text-slate-400 font-medium">Competitor</th>
                  <th className="text-left px-3 py-3 text-slate-400 font-medium">Domain</th>
                  <th className="text-right px-3 py-3 text-slate-400 font-medium">Score</th>
                  <th className="text-right px-3 py-3 text-slate-400 font-medium">Grade</th>
                  <th className="text-right px-3 py-3 text-slate-400 font-medium">Pages</th>
                  <th className="text-right px-3 py-3 text-slate-400 font-medium">Issues</th>
                  <th className="text-right px-5 py-3 text-slate-400 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {competitors.map(comp => (
                  <tr key={comp.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                    <td className="px-5 py-3.5">
                      <p className="font-semibold text-white">{comp.name}</p>
                    </td>
                    <td className="px-3 py-3.5">
                      <span className="text-slate-400 font-mono">{comp.domain}</span>
                    </td>
                    <td className="px-3 py-3.5 text-right">
                      <ScoreBadge score={comp.latest_score} />
                    </td>
                    <td className="px-3 py-3.5 text-right">
                      <GradeBadge score={comp.latest_score} />
                    </td>
                    <td className="px-3 py-3.5 text-right text-slate-300">
                      {comp.latest_page_count ?? <span className="text-slate-500">—</span>}
                    </td>
                    <td className="px-3 py-3.5 text-right text-slate-300">
                      {comp.latest_issue_count ?? <span className="text-slate-500">—</span>}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleAudit(comp.id)}
                          disabled={auditing === comp.id}
                          title="Run Benchmark Audit"
                          className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors disabled:opacity-50"
                        >
                          {auditing === comp.id
                            ? <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            : <Play className="w-3.5 h-3.5" />
                          }
                        </button>
                        <button
                          onClick={() => handleDelete(comp.id)}
                          disabled={deleting === comp.id}
                          title="Remove Competitor"
                          className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors disabled:opacity-50"
                        >
                          {deleting === comp.id
                            ? <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            : <Trash2 className="w-3.5 h-3.5" />
                          }
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Competitor Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-white text-lg">Add Competitor</h4>
                <p className="text-xs text-slate-400 mt-0.5">Track a rival domain for SEO benchmarking</p>
              </div>
              <button
                onClick={() => { setShowModal(false); setFormError(''); setForm({ name: '', domain: '', target_url: '' }); }}
                className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {formError && (
              <div className="flex items-center gap-2 text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2 text-xs">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                {formError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1.5">Competitor Name *</label>
                <input
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Ahrefs, SEMrush"
                  className="w-full bg-slate-800 border border-slate-700 text-white text-sm rounded-xl px-4 py-2.5 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition placeholder-slate-500"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1.5">Target URL *</label>
                <input
                  value={form.target_url}
                  onChange={e => {
                    const url = e.target.value;
                    setForm(f => ({
                      ...f,
                      target_url: url,
                      domain: f.domain || (() => { try { return new URL(url).hostname; } catch { return ''; } })()
                    }));
                  }}
                  placeholder="https://competitor.com"
                  className="w-full bg-slate-800 border border-slate-700 text-white text-sm rounded-xl px-4 py-2.5 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition placeholder-slate-500 font-mono"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 font-medium block mb-1.5">Domain <span className="text-slate-600">(auto-detected)</span></label>
                <input
                  value={form.domain}
                  onChange={e => setForm(f => ({ ...f, domain: e.target.value }))}
                  placeholder="competitor.com"
                  className="w-full bg-slate-800 border border-slate-700 text-white text-sm rounded-xl px-4 py-2.5 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition placeholder-slate-500 font-mono"
                />
              </div>
            </div>

            <div className="flex gap-3 pt-1">
              <button
                onClick={() => { setShowModal(false); setFormError(''); setForm({ name: '', domain: '', target_url: '' }); }}
                className="flex-1 py-2.5 rounded-xl border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 text-sm font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAdd}
                disabled={saving}
                className="flex-1 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold transition-all disabled:opacity-50 active:scale-95"
              >
                {saving ? 'Adding…' : 'Add Competitor'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
