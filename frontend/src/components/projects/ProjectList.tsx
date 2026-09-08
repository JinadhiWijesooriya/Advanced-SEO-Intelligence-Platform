import React from 'react';
import type { Project } from '../../services/api';
import { 
  Globe, 
  Layers, 
  FileText, 
  Bot, 
  ShieldCheck, 
  Plus, 
  Pencil, 
  Trash2, 
  ExternalLink,
  Calendar,
  Play,
  List,
  AlertTriangle,
  BarChart3
} from 'lucide-react';

interface ProjectListProps {
  projects: Project[];
  loading: boolean;
  onOpenCreateModal: () => void;
  onEditProject: (project: Project) => void;
  onDeleteProject: (id: number) => void;
  onStartCrawl: (projectId: number) => void;
  onViewPages: (project: Project) => void;
  onViewIssues: (project: Project) => void;
  onViewDashboard: (project: Project) => void;
}

export const ProjectList: React.FC<ProjectListProps> = ({
  projects,
  loading,
  onOpenCreateModal,
  onEditProject,
  onDeleteProject,
  onStartCrawl,
  onViewPages,
  onViewIssues,
  onViewDashboard,
}) => {
  if (loading) {
    return (
      <div className="py-16 flex flex-col items-center justify-center space-y-4 bg-slate-900/40 border border-slate-800 rounded-2xl">
        <div className="w-8 h-8 border-3 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
        <p className="text-xs text-slate-400 font-medium">Loading website projects...</p>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="relative rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center flex flex-col items-center justify-center space-y-4">
        <div className="p-4 bg-blue-500/10 rounded-2xl text-blue-400 ring-1 ring-blue-500/20">
          <Globe className="w-8 h-8" />
        </div>
        <div className="max-w-md space-y-1">
          <h3 className="text-lg font-bold text-white">No SEO Target Projects Yet</h3>
          <p className="text-xs text-slate-400">
            Configure your target website domain and set crawler limits to start performing technical SEO audits.
          </p>
        </div>
        <button
          onClick={onOpenCreateModal}
          className="mt-2 inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/25 transition-all active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>Configure First Project</span>
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold text-white tracking-tight">Active Website Projects</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {projects.length} target {projects.length === 1 ? 'domain' : 'domains'} configured with SSRF validation
          </p>
        </div>
        <button
          onClick={onOpenCreateModal}
          className="inline-flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/20 transition-all active:scale-95 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Target Project</span>
        </button>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project) => (
          <div
            key={project.id}
            className="group relative bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between hover:border-slate-700 hover:bg-slate-900/80 transition-all shadow-xl space-y-5"
          >
            {/* Top Bar */}
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="p-2.5 bg-blue-500/10 rounded-xl text-blue-400 border border-blue-500/20">
                  <Globe className="w-5 h-5" />
                </div>
                <div className="flex items-center space-x-1 opacity-80 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => onEditProject(project)}
                    title="Edit Project Settings"
                    className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`Are you sure you want to delete project "${project.name}"?`)) {
                        onDeleteProject(project.id);
                      }
                    }}
                    title="Delete Project"
                    className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Title & Target URL */}
              <div>
                <h4 className="font-bold text-base text-white group-hover:text-blue-400 transition-colors line-clamp-1">
                  {project.name}
                </h4>
                <a
                  href={project.target_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1 text-xs font-mono text-slate-400 hover:text-blue-300 mt-1 truncate max-w-full"
                >
                  <span className="truncate">{project.target_url}</span>
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                </a>
              </div>

              {/* Badges / Crawl Config */}
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80 text-xs">
                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/60">
                  <div className="flex items-center space-x-1 text-slate-400 text-[10px]">
                    <FileText className="w-3 h-3 text-blue-400" />
                    <span>Max Pages</span>
                  </div>
                  <p className="font-bold text-slate-200 mt-0.5 font-mono">{project.max_crawl_pages}</p>
                </div>

                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/60">
                  <div className="flex items-center space-x-1 text-slate-400 text-[10px]">
                    <Layers className="w-3 h-3 text-indigo-400" />
                    <span>Max Depth</span>
                  </div>
                  <p className="font-bold text-slate-200 mt-0.5 font-mono">{project.max_crawl_depth}</p>
                </div>
              </div>

              {/* User agent & Robots.txt */}
              <div className="space-y-1.5 text-[11px] text-slate-400">
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-1">
                    <Bot className="w-3 h-3 text-amber-400" />
                    <span>User-Agent</span>
                  </span>
                  <span className="font-mono text-slate-300 truncate max-w-[140px]" title={project.custom_user_agent}>
                    {project.custom_user_agent}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-1">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                    <span>Robots.txt</span>
                  </span>
                  <span className={`font-semibold ${project.respect_robots_txt ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {project.respect_robots_txt ? 'Enforced' : 'Ignored'}
                  </span>
                </div>
              </div>
            </div>

            {/* Crawl Actions & Card Footer */}
            <div className="space-y-2.5 pt-3 border-t border-slate-800/80">
              <button
                onClick={() => onViewDashboard(project)}
                className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white text-xs font-bold shadow-md shadow-indigo-500/20 transition-all active:scale-[0.98]"
                title="View SEO Intelligence Dashboard & Score"
              >
                <BarChart3 className="w-3.5 h-3.5" />
                <span>SEO Intelligence Dashboard</span>
              </button>

              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => onStartCrawl(project.id)}
                  className="flex items-center justify-center space-x-1.5 py-2 px-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition-all active:scale-95"
                  title="Start Crawl Audit"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Crawl</span>
                </button>

                <button
                  onClick={() => onViewPages(project)}
                  className="flex items-center justify-center space-x-1.5 py-2 px-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
                  title="View Crawled Pages"
                >
                  <List className="w-3.5 h-3.5" />
                  <span>Pages</span>
                </button>

                <button
                  onClick={() => onViewIssues(project)}
                  className="flex items-center justify-center space-x-1.5 py-2 px-2 rounded-xl bg-violet-700/80 hover:bg-violet-600 text-white text-xs font-semibold transition-all active:scale-95"
                  title="View SEO Issues"
                >
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Issues</span>
                </button>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <div className="flex items-center space-x-1">
                  <Calendar className="w-3 h-3 text-slate-400" />
                  <span>{new Date(project.created_at).toLocaleDateString()}</span>
                </div>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium text-[10px]">
                  SSRF Validated
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
