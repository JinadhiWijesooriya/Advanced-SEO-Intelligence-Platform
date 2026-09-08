import React, { useEffect, useState } from 'react';
import type { CrawlJob, CrawlTask } from '../../services/api';
import { getCrawlStatus, stopCrawl, fetchCrawlTasks } from '../../services/api';
import { 
  Activity, 
  Square, 
  CheckCircle2, 
  AlertOctagon, 
  Clock, 
  Loader2, 
  FileCheck2,
  FileX2,
  Layers,
  ChevronDown,
  ChevronUp,
  Server,
  AlertCircle
} from 'lucide-react';

interface CrawlMonitorProps {
  crawlJob: CrawlJob;
  onCrawlUpdated: (updatedJob: CrawlJob) => void;
}

export const CrawlMonitor: React.FC<CrawlMonitorProps> = ({ crawlJob, onCrawlUpdated }) => {
  const [stopping, setStopping] = useState(false);
  const [showTaskQueue, setShowTaskQueue] = useState(false);
  const [tasks, setTasks] = useState<CrawlTask[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);

  const loadTasks = async () => {
    try {
      setLoadingTasks(true);
      const res = await fetchCrawlTasks(crawlJob.id, { page_size: 20 });
      setTasks(res.tasks);
    } catch (err) {
      console.error('Failed to load crawl tasks:', err);
    } finally {
      setLoadingTasks(false);
    }
  };

  useEffect(() => {
    if (crawlJob.status !== 'running' && crawlJob.status !== 'pending') {
      if (showTaskQueue) {
        loadTasks();
      }
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await getCrawlStatus(crawlJob.id);
        onCrawlUpdated(updated);
        if (showTaskQueue) {
          const taskRes = await fetchCrawlTasks(crawlJob.id, { page_size: 20 });
          setTasks(taskRes.tasks);
        }
      } catch (err) {
        console.error('Failed to poll crawl status:', err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [crawlJob.id, crawlJob.status, onCrawlUpdated, showTaskQueue]);

  const handleToggleTasks = () => {
    const nextState = !showTaskQueue;
    setShowTaskQueue(nextState);
    if (nextState) {
      loadTasks();
    }
  };

  const handleStop = async () => {
    setStopping(true);
    try {
      const stopped = await stopCrawl(crawlJob.id);
      onCrawlUpdated(stopped);
    } catch (err) {
      console.error('Failed to stop crawl:', err);
    } finally {
      setStopping(false);
    }
  };

  const percent = crawlJob.total_urls > 0 
    ? Math.min(100, Math.round((crawlJob.processed_urls / crawlJob.total_urls) * 100))
    : 0;

  const isLive = crawlJob.status === 'running' || crawlJob.status === 'pending';

  return (
    <div className="relative rounded-2xl bg-slate-900/90 border border-slate-800 p-6 shadow-2xl space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className={`p-3 rounded-xl border ${
            isLive ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' :
            crawlJob.status === 'completed' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
            crawlJob.status === 'stopped' ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' :
            'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}>
            {isLive ? <Loader2 className="w-6 h-6 animate-spin" /> :
             crawlJob.status === 'completed' ? <CheckCircle2 className="w-6 h-6" /> :
             crawlJob.status === 'stopped' ? <Square className="w-6 h-6" /> :
             <AlertOctagon className="w-6 h-6" />}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-lg font-extrabold text-white tracking-tight">
                Crawl Job Audit #{crawlJob.id}
              </h3>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
                isLive ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse' :
                crawlJob.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                crawlJob.status === 'stopped' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                'bg-rose-500/20 text-rose-400 border border-rose-500/30'
              }`}>
                {crawlJob.status}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {isLive ? 'Celery / Background worker processing website URLs & extracting technical SEO tags...' :
               crawlJob.status === 'completed' ? 'Audit complete. All discovered URLs parsed.' :
               crawlJob.status === 'stopped' ? 'Crawl execution halted by user.' :
               'Crawl run encountered an error.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-center">
          <button
            onClick={handleToggleTasks}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-semibold transition-colors"
          >
            <Server className="w-3.5 h-3.5 text-indigo-400" />
            <span>Worker Queue</span>
            {showTaskQueue ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {isLive && (
            <button
              onClick={handleStop}
              disabled={stopping}
              className="flex items-center justify-center space-x-2 px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 text-xs font-semibold transition-all active:scale-95 disabled:opacity-50"
            >
              {stopping ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />}
              <span>Stop Crawl</span>
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar Container */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold">
          <span className="text-slate-300 flex items-center space-x-1.5">
            <Activity className="w-4 h-4 text-blue-400" />
            <span>Audit Discovery Progress</span>
          </span>
          <span className="text-blue-400 font-mono font-bold text-sm">{percent}%</span>
        </div>
        <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden p-0.5 border border-slate-800">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isLive ? 'bg-gradient-to-r from-blue-600 to-indigo-500 animate-pulse' :
              crawlJob.status === 'completed' ? 'bg-emerald-500' :
              crawlJob.status === 'stopped' ? 'bg-amber-500' : 'bg-rose-500'
            }`}
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 border-t border-slate-800/80">
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[11px]">
            <FileCheck2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Processed URLs</span>
          </div>
          <p className="text-lg font-bold text-white mt-1 font-mono">{crawlJob.processed_urls}</p>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[11px]">
            <Layers className="w-3.5 h-3.5 text-blue-400" />
            <span>Discovered Queue</span>
          </div>
          <p className="text-lg font-bold text-white mt-1 font-mono">{crawlJob.total_urls}</p>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[11px]">
            <FileX2 className="w-3.5 h-3.5 text-rose-400" />
            <span>Failed Crawls</span>
          </div>
          <p className="text-lg font-bold text-white mt-1 font-mono">{crawlJob.failed_urls}</p>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <div className="flex items-center space-x-1.5 text-slate-400 text-[11px]">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            <span>Started At</span>
          </div>
          <p className="text-xs font-semibold text-slate-200 mt-1 font-mono truncate">
            {new Date(crawlJob.started_at).toLocaleTimeString()}
          </p>
        </div>
      </div>

      {/* Expandable Worker Queue Activity Drawer */}
      {showTaskQueue && (
        <div className="pt-4 border-t border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Server className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                Distributed Task Queue Activity ({tasks.length})
              </h4>
            </div>
            {loadingTasks && <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-400" />}
          </div>

          {tasks.length === 0 ? (
            <p className="text-xs text-slate-400 py-3 text-center bg-slate-950/40 rounded-xl">
              No tasks currently dispatched in the queue.
            </p>
          ) : (
            <div className="max-h-60 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 flex items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-0.5 truncate flex-1">
                    <p className="font-mono text-slate-200 truncate">{task.url}</p>
                    {task.error_message && (
                      <p className="text-[11px] text-rose-400 flex items-center space-x-1 truncate">
                        <AlertCircle className="w-3 h-3 flex-shrink-0" />
                        <span className="truncate">{task.error_message}</span>
                      </p>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <span className="text-[10px] text-slate-400 font-mono">
                      Try {task.attempts}
                    </span>
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                        task.status === 'completed'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : task.status === 'in_progress'
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse'
                          : task.status === 'failed'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}
                    >
                      {task.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
