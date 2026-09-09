import React, { useEffect, useState } from 'react';
import { fetchSchedule, upsertSchedule } from '../../services/api';
import type { ScheduledScan } from '../../services/api';
import { Clock, Calendar, RefreshCw, CheckCircle2, AlertCircle, Power } from 'lucide-react';

interface Props {
  projectId: number;
}

type Frequency = 'daily' | 'weekly' | 'monthly';

const FREQ_OPTIONS: { value: Frequency; label: string; desc: string; icon: string }[] = [
  { value: 'daily', label: 'Daily', desc: 'Runs every 24 hours', icon: '⚡' },
  { value: 'weekly', label: 'Weekly', desc: 'Runs every 7 days', icon: '📅' },
  { value: 'monthly', label: 'Monthly', desc: 'Runs every 30 days', icon: '🗓️' },
];

function formatNextRun(iso: string | null): string {
  if (!iso) return 'Not scheduled';
  const date = new Date(iso);
  const now = new Date();
  const diff = date.getTime() - now.getTime();
  if (diff < 0) return 'Due now';
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(hours / 24);
  if (days > 0) return `in ${days} day${days !== 1 ? 's' : ''}`;
  if (hours > 0) return `in ${hours} hour${hours !== 1 ? 's' : ''}`;
  return `in < 1 hour`;
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

export const SchedulePanel: React.FC<Props> = ({ projectId }) => {
  const [schedule, setSchedule] = useState<ScheduledScan | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form state
  const [frequency, setFrequency] = useState<Frequency>('weekly');
  const [enabled, setEnabled] = useState(true);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await fetchSchedule(projectId);
      setSchedule(s);
      if (s) {
        setFrequency(s.frequency as Frequency);
        setEnabled(s.enabled);
      }
    } catch {
      setError('Failed to load schedule.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [projectId]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(false);
    try {
      const updated = await upsertSchedule(projectId, {
        frequency,
        enabled,
        project_id: projectId,
      });
      setSchedule(updated);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to save schedule.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <div className="w-8 h-8 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-indigo-500/10 rounded-lg">
          <Clock className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h3 className="font-bold text-white">Automated Scan Schedule</h3>
          <p className="text-xs text-slate-400">Configure recurring SEO audits for this project</p>
        </div>
      </div>

      {/* Current Status Card */}
      {schedule && (
        <div className={`rounded-2xl p-5 border ${schedule.enabled ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-slate-800/40 border-slate-700'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-2.5 h-2.5 rounded-full ${schedule.enabled ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
              <span className={`text-sm font-semibold ${schedule.enabled ? 'text-emerald-400' : 'text-slate-400'}`}>
                {schedule.enabled ? 'Schedule Active' : 'Schedule Disabled'}
              </span>
            </div>
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium border ${
              schedule.enabled
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-slate-700 text-slate-400 border-slate-600'
            }`}>
              {schedule.frequency.charAt(0).toUpperCase() + schedule.frequency.slice(1)}
            </span>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-slate-500 mb-1">Next Run</p>
              <p className="text-sm font-medium text-white">{formatDate(schedule.next_run_at)}</p>
              <p className="text-xs text-indigo-400 mt-0.5">{formatNextRun(schedule.next_run_at)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1">Last Run</p>
              <p className="text-sm font-medium text-white">{formatDate(schedule.last_run_at)}</p>
            </div>
          </div>
        </div>
      )}

      {!schedule && (
        <div className="bg-slate-800/40 border border-dashed border-slate-700 rounded-2xl p-5 text-center">
          <Calendar className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-400">No schedule configured yet.</p>
          <p className="text-xs text-slate-500 mt-1">Set one below to enable automated audits.</p>
        </div>
      )}

      {/* Configuration */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-5">
        <h4 className="text-sm font-semibold text-white">Configure Schedule</h4>

        {/* Frequency Selector */}
        <div className="space-y-2">
          <label className="text-xs text-slate-400 font-medium">Scan Frequency</label>
          <div className="grid grid-cols-3 gap-3">
            {FREQ_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setFrequency(opt.value)}
                className={`p-4 rounded-xl border text-left transition-all ${
                  frequency === opt.value
                    ? 'bg-indigo-500/15 border-indigo-500/40 shadow-lg shadow-indigo-500/10'
                    : 'bg-slate-800/40 border-slate-700 hover:border-slate-600'
                }`}
              >
                <span className="text-lg">{opt.icon}</span>
                <p className={`text-sm font-bold mt-1.5 ${frequency === opt.value ? 'text-indigo-400' : 'text-white'}`}>
                  {opt.label}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">{opt.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Enable Toggle */}
        <div className="flex items-center justify-between p-4 bg-slate-800/40 rounded-xl border border-slate-700">
          <div className="flex items-center gap-3">
            <Power className={`w-4 h-4 ${enabled ? 'text-emerald-400' : 'text-slate-500'}`} />
            <div>
              <p className="text-sm font-medium text-white">Enable Automated Scans</p>
              <p className="text-xs text-slate-400 mt-0.5">
                {enabled ? 'Scans will run automatically on schedule' : 'No automatic scans will run'}
              </p>
            </div>
          </div>
          <button
            onClick={() => setEnabled(!enabled)}
            className={`relative w-11 h-6 rounded-full transition-all duration-300 ${enabled ? 'bg-emerald-500' : 'bg-slate-600'}`}
          >
            <span
              className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-300 ${enabled ? 'translate-x-[22px]' : 'translate-x-0.5'}`}
            />
          </button>
        </div>

        {/* Feedback */}
        {error && (
          <div className="flex items-center gap-2 text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl px-3 py-2.5 text-xs">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            {error}
          </div>
        )}
        {success && (
          <div className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-3 py-2.5 text-xs">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            Schedule saved successfully!
          </div>
        )}

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all disabled:opacity-50 active:scale-[0.98] flex items-center justify-center gap-2"
        >
          {saving ? (
            <><RefreshCw className="w-4 h-4 animate-spin" /> Saving…</>
          ) : (
            <><CheckCircle2 className="w-4 h-4" /> {schedule ? 'Update Schedule' : 'Enable Schedule'}</>
          )}
        </button>
      </div>
    </div>
  );
};
