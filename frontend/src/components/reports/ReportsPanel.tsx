import React, { useEffect, useState, useCallback } from 'react';
import { createReport, fetchReports, deleteReport, downloadReport } from '../../services/api';
import type { Report } from '../../services/api';
import {
  FileText, FileSpreadsheet, Download, Trash2, RefreshCw,
  AlertCircle, CheckCircle2, Clock, Loader2, FileBadge
} from 'lucide-react';

interface Props {
  projectId: number;
}

const FORMAT_CONFIG = {
  json: {
    label: 'JSON',
    description: 'Machine-readable structured data report',
    icon: <FileText className="w-5 h-5" />,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    buttonBg: 'bg-blue-600 hover:bg-blue-500',
    ext: '.json',
  },
  csv: {
    label: 'CSV',
    description: 'Spreadsheet with pages & issues data',
    icon: <FileSpreadsheet className="w-5 h-5" />,
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
    buttonBg: 'bg-emerald-600 hover:bg-emerald-500',
    ext: '.csv',
  },
  pdf: {
    label: 'PDF',
    description: 'Professional formatted audit report',
    icon: <FileBadge className="w-5 h-5" />,
    color: 'text-rose-400',
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/20',
    buttonBg: 'bg-rose-600 hover:bg-rose-500',
    ext: '.pdf',
  },
};

function StatusBadge({ status }: { status: Report['status'] }) {
  if (status === 'completed') {
    return (
      <span className="flex items-center gap-1 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full text-xs font-medium">
        <CheckCircle2 className="w-3 h-3" /> Ready
      </span>
    );
  }
  if (status === 'pending') {
    return (
      <span className="flex items-center gap-1 text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 px-2 py-0.5 rounded-full text-xs font-medium">
        <Loader2 className="w-3 h-3 animate-spin" /> Generating
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full text-xs font-medium">
      <AlertCircle className="w-3 h-3" /> Failed
    </span>
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

export const ReportsPanel: React.FC<Props> = ({ projectId }) => {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setReports(await fetchReports(projectId));
    } catch {
      setError('Failed to load reports.');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  // Auto-refresh while any report is pending
  useEffect(() => {
    const hasPending = reports.some(r => r.status === 'pending');
    if (!hasPending) return;
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, [reports, load]);

  const handleGenerate = async (format: string) => {
    setGenerating(format);
    setError(null);
    setSuccess(null);
    try {
      await createReport(projectId, format);
      setSuccess(`${format.toUpperCase()} report is being generated…`);
      setTimeout(() => setSuccess(null), 4000);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || `Failed to generate ${format} report.`);
    } finally {
      setGenerating(null);
    }
  };

  const handleDownload = async (report: Report) => {
    setDownloading(report.id);
    setError(null);
    try {
      await downloadReport(report.id);
    } catch {
      setError('Failed to download report.');
    } finally {
      setDownloading(null);
    }
  };

  const handleDelete = async (id: number) => {
    setDeleting(id);
    try {
      await deleteReport(id);
      setReports(prev => prev.filter(r => r.id !== id));
    } catch {
      setError('Failed to delete report.');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-500/10 rounded-lg">
            <FileText className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h3 className="font-bold text-white">SEO Reports</h3>
            <p className="text-xs text-slate-400">Generate and download audit reports in multiple formats</p>
          </div>
        </div>
        <button
          onClick={load}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Generate Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {(Object.entries(FORMAT_CONFIG) as [string, typeof FORMAT_CONFIG.json][]).map(([fmt, cfg]) => (
          <button
            key={fmt}
            onClick={() => handleGenerate(fmt)}
            disabled={!!generating}
            className={`group flex flex-col gap-3 p-5 rounded-2xl border ${cfg.bg} ${cfg.border} hover:scale-[1.02] transition-all active:scale-[0.98] disabled:opacity-50 text-left`}
          >
            <div className="flex items-center justify-between">
              <div className={`${cfg.color}`}>{cfg.icon}</div>
              {generating === fmt ? (
                <Loader2 className="w-4 h-4 text-slate-400 animate-spin" />
              ) : (
                <Download className={`w-4 h-4 ${cfg.color} opacity-0 group-hover:opacity-100 transition-opacity`} />
              )}
            </div>
            <div>
              <p className={`font-bold text-sm ${cfg.color}`}>{cfg.label} Report</p>
              <p className="text-xs text-slate-500 mt-0.5">{cfg.description}</p>
            </div>
            <div className={`w-full py-1.5 rounded-lg text-center text-xs font-semibold text-white ${cfg.buttonBg} transition-colors`}>
              {generating === fmt ? 'Generating…' : `Generate ${cfg.label}`}
            </div>
          </button>
        ))}
      </div>

      {/* Feedback */}
      {error && (
        <div className="flex items-center gap-2 text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-4 py-3 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3 text-sm">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          {success}
        </div>
      )}

      {/* Report History */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-800 flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-semibold text-white">Report History</span>
          <span className="ml-auto text-xs text-slate-500">{reports.length} report{reports.length !== 1 ? 's' : ''}</span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="w-7 h-7 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
          </div>
        ) : reports.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center space-y-2">
            <FileText className="w-8 h-8 text-slate-600" />
            <p className="text-slate-400 text-sm">No reports yet</p>
            <p className="text-slate-500 text-xs">Use the buttons above to generate your first report.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/40">
                  <th className="text-left px-5 py-3 text-slate-400 font-medium">Format</th>
                  <th className="text-left px-3 py-3 text-slate-400 font-medium">Created</th>
                  <th className="text-center px-3 py-3 text-slate-400 font-medium">Status</th>
                  <th className="text-right px-5 py-3 text-slate-400 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map(report => {
                  const cfg = FORMAT_CONFIG[report.format as keyof typeof FORMAT_CONFIG];
                  return (
                    <tr key={report.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2.5">
                          <div className={`p-1.5 rounded-lg ${cfg?.bg || 'bg-slate-800'}`}>
                            <span className={cfg?.color || 'text-slate-400'}>{cfg?.icon}</span>
                          </div>
                          <div>
                            <p className="font-semibold text-white uppercase">{report.format}</p>
                            <p className="text-slate-500">Report #{report.id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-3.5 text-slate-400">{formatDate(report.created_at)}</td>
                      <td className="px-3 py-3.5 text-center">
                        <StatusBadge status={report.status} />
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {report.status === 'completed' && (
                            <button
                              onClick={() => handleDownload(report)}
                              disabled={downloading === report.id}
                              title="Download"
                              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors disabled:opacity-50 font-medium"
                            >
                              {downloading === report.id
                                ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                : <Download className="w-3.5 h-3.5" />
                              }
                              Download
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(report.id)}
                            disabled={deleting === report.id}
                            title="Delete"
                            className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors disabled:opacity-50"
                          >
                            {deleting === report.id
                              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              : <Trash2 className="w-3.5 h-3.5" />
                            }
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
