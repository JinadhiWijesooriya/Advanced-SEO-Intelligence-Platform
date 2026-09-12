import React, { useEffect, useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginForm } from './components/auth/LoginForm';
import { RegisterForm } from './components/auth/RegisterForm';
import { ProjectList } from './components/projects/ProjectList';
import { ProjectModal } from './components/projects/ProjectModal';
import { CrawlMonitor } from './components/crawl/CrawlMonitor';
import { PageList } from './components/pages/PageList';
import { IssueList } from './components/issues/IssueList';
import { ProjectDashboard } from './components/dashboard/ProjectDashboard';
import { NotificationBell } from './components/notifications/NotificationBell';
import { 
  fetchSystemHealth, 
  fetchProjects, 
  createProject, 
  updateProject, 
  deleteProject,
  startCrawl
} from './services/api';
import type { HealthResponse, Project, ProjectCreateInput, CrawlJob } from './services/api';
import { 
  Activity, 
  CheckCircle2, 
  Server, 
  RefreshCw, 
  ShieldCheck, 
  LogOut,
  Globe,
  ArrowLeft,
  AlertTriangle,
  FileSearch,
  BarChart3
} from 'lucide-react';

const DashboardContent: React.FC = () => {
  const { user, isAuthenticated, logout, loading: authLoading } = useAuth();
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [pingTime, setPingTime] = useState<number | null>(null);

  // Projects state
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState<boolean>(false);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  // Crawl & Selected Project Page/Issues/Dashboard State
  const [activeCrawlJob, setActiveCrawlJob] = useState<CrawlJob | null>(null);
  const [selectedProjectForPages, setSelectedProjectForPages] = useState<Project | null>(null);
  const [selectedProjectForIssues, setSelectedProjectForIssues] = useState<Project | null>(null);
  const [selectedProjectForDashboard, setSelectedProjectForDashboard] = useState<Project | null>(null);

  const checkBackendHealth = async () => {
    setLoadingHealth(true);
    const start = performance.now();
    try {
      const data = await fetchSystemHealth();
      const end = performance.now();
      setPingTime(Math.round(end - start));
      setHealth(data);
    } catch (err) {
      console.error('Health check error:', err);
      setHealth(null);
    } finally {
      setLoadingHealth(false);
    }
  };

  const loadUserProjects = async () => {
    if (!isAuthenticated) return;
    setLoadingProjects(true);
    try {
      const data = await fetchProjects();
      setProjects(data);
    } catch (err) {
      console.error('Failed to load user projects:', err);
    } finally {
      setLoadingProjects(false);
    }
  };

  useEffect(() => {
    checkBackendHealth();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadUserProjects();
    } else {
      setProjects([]);
      setActiveCrawlJob(null);
      setSelectedProjectForPages(null);
      setSelectedProjectForIssues(null);
    }
  }, [isAuthenticated]);

  const handleSaveProject = async (data: ProjectCreateInput, id?: number) => {
    if (id) {
      await updateProject(id, data);
    } else {
      await createProject(data);
    }
    await loadUserProjects();
  };

  const handleDeleteProject = async (id: number) => {
    try {
      await deleteProject(id);
      if (selectedProjectForPages?.id === id) {
        setSelectedProjectForPages(null);
      }
      await loadUserProjects();
    } catch (err) {
      console.error('Failed to delete project:', err);
    }
  };

  const handleStartCrawl = async (projectId: number) => {
    try {
      const crawl = await startCrawl(projectId);
      setActiveCrawlJob(crawl);
      const proj = projects.find((p) => p.id === projectId) || null;
      setSelectedProjectForPages(proj);
      setSelectedProjectForIssues(null);
      setSelectedProjectForDashboard(null);
    } catch (err) {
      console.error('Failed to start crawl:', err);
    }
  };

  const handleViewIssues = (proj: Project) => {
    setSelectedProjectForIssues(proj);
    setSelectedProjectForPages(null);
    setSelectedProjectForDashboard(null);
  };

  const handleViewPages = (proj: Project) => {
    setSelectedProjectForPages(proj);
    setSelectedProjectForIssues(null);
    setSelectedProjectForDashboard(null);
  };

  const handleViewDashboard = (proj: Project) => {
    setSelectedProjectForDashboard(proj);
    setSelectedProjectForPages(null);
    setSelectedProjectForIssues(null);
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-10 h-10 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
          <p className="text-xs text-slate-400 font-medium">Verifying Session Security...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-blue-600 to-indigo-500 rounded-xl shadow-lg shadow-blue-500/20">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-white tracking-wide">SEO Intelligence Platform</h1>
              <p className="text-xs text-slate-400">Phase 10 • AI Intelligence Suite</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs">
              <span className={`w-2 h-2 rounded-full ${health?.status === 'online' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`}></span>
              <span className="text-slate-300 font-medium">{health?.status === 'online' ? 'System Operational' : 'System Offline'}</span>
            </div>

            {isAuthenticated && user ? (
              <div className="flex items-center space-x-3">
                <NotificationBell />
                <div className="flex items-center space-x-3 bg-slate-800/80 border border-slate-700/80 rounded-xl px-3.5 py-1.5">
                <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold shadow-md">
                  {user.email.charAt(0).toUpperCase()}
                </div>
                <div className="text-left hidden sm:block">
                  <p className="text-xs font-semibold text-white leading-tight">{user.email}</p>
                  <p className="text-[10px] text-slate-400 capitalize">{user.role} Account</p>
                </div>
                <button
                  onClick={logout}
                  title="Sign Out"
                  className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors ml-1"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
              </div>
            ) : (
              <div className="flex items-center space-x-2 bg-slate-800/60 p-1 rounded-xl border border-slate-700/60 text-xs">
                <button
                  onClick={() => setAuthMode('login')}
                  className={`px-3 py-1 rounded-lg transition-all font-medium ${authMode === 'login' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}
                >
                  Login
                </button>
                <button
                  onClick={() => setAuthMode('register')}
                  className={`px-3 py-1 rounded-lg transition-all font-medium ${authMode === 'register' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'}`}
                >
                  Register
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-10 space-y-10">
        {!isAuthenticated ? (
          <div className="py-8 flex flex-col items-center justify-center space-y-8">
            <div className="text-center max-w-2xl space-y-3">
              <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium">
                <ShieldCheck className="w-4 h-4" />
                <span>Crawler & Storage Engine Active</span>
              </div>
              <h2 className="text-3xl font-extrabold text-white sm:text-4xl tracking-tight">
                Secure Access Portal
              </h2>
              <p className="text-slate-400 text-sm">
                Authenticate your user account to access project configuration, crawling tools, and automated SEO reports.
              </p>
            </div>

            {authMode === 'login' ? (
              <LoginForm onSwitchToRegister={() => setAuthMode('register')} />
            ) : (
              <RegisterForm onSwitchToLogin={() => setAuthMode('login')} />
            )}
          </div>
        ) : (
          <>
            {/* Hero Banner */}
            <div className="relative rounded-2xl overflow-hidden bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800/80 p-8 shadow-2xl">
              <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-3">
                  <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-medium">
                    <AlertTriangle className="w-4 h-4 text-violet-400" />
                    <span>Phase 10: AI Intelligence Suite Active</span>
                  </div>
                  <h2 className="text-3xl font-extrabold text-white tracking-tight">
                    SEO Analysis & Issue Management
                  </h2>
                  <p className="text-slate-400 text-sm max-w-2xl">
                    Automatically analyze crawled pages with modular rule engines — detecting technical errors, on-page gaps, thin content, broken links, missing ALT attributes, and site-wide duplicate content.
                  </p>
                </div>

                <button 
                  onClick={checkBackendHealth}
                  disabled={loadingHealth}
                  className="flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-all shadow-lg hover:shadow-blue-500/25 active:scale-95 disabled:opacity-50 self-start md:self-center"
                >
                  <RefreshCw className={`w-4 h-4 ${loadingHealth ? 'animate-spin' : ''}`} />
                  <span>Verify Crawler Health</span>
                </button>
              </div>
            </div>

            {/* System Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 flex flex-col justify-between hover:border-slate-700 transition-colors">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="p-3 bg-blue-500/10 rounded-lg text-blue-400">
                      <Globe className="w-6 h-6" />
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {projects.length} {projects.length === 1 ? 'Project' : 'Projects'}
                    </span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-white">Target Projects</h3>
                    <p className="text-xs text-slate-400 mt-1">Configured website domains</p>
                  </div>
                </div>
                <div className="mt-6 pt-4 border-t border-slate-800/80 text-xs text-slate-400 flex justify-between">
                  <span>Owner: {user?.email}</span>
                  <span className="text-blue-400 font-mono">User ID #{user?.id}</span>
                </div>
              </div>

              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 flex flex-col justify-between hover:border-slate-700 transition-colors">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="p-3 bg-indigo-500/10 rounded-lg text-indigo-400">
                      <Server className="w-6 h-6" />
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Online
                    </span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-white">FastAPI Crawler API</h3>
                    <p className="text-xs text-slate-400 mt-1">BackgroundTasks Execution</p>
                  </div>
                </div>
                <div className="mt-6 pt-4 border-t border-slate-800/80 text-xs text-slate-400 flex justify-between">
                  <span>Latency: {pingTime !== null ? `${pingTime}ms` : 'N/A'}</span>
                  <span className="text-indigo-400 font-mono">/api/v1/crawls</span>
                </div>
              </div>

              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 flex flex-col justify-between hover:border-slate-700 transition-colors">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="p-3 bg-violet-500/10 rounded-lg text-violet-400">
                      <FileSearch className="w-6 h-6" />
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">
                      Issues Engine
                    </span>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg text-white">SEO Rule Engine</h3>
                    <p className="text-xs text-slate-400 mt-1">5 Analyzer Modules Active</p>
                  </div>
                </div>
                <div className="mt-6 pt-4 border-t border-slate-800/80 text-xs text-slate-400 flex justify-between">
                  <span>13 SEO rules</span>
                  <span className="text-violet-400 font-mono">seo_issues table</span>
                </div>
              </div>
            </div>

            {/* Live Crawl Monitor */}
            {activeCrawlJob && (
              <CrawlMonitor
                crawlJob={activeCrawlJob}
                onCrawlUpdated={(updated) => setActiveCrawlJob(updated)}
              />
            )}

            {/* Selected Project Dashboard / Pages / Issues View or Projects List */}
            {selectedProjectForDashboard ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between bg-slate-900/40 p-4 rounded-xl border border-slate-800">
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => setSelectedProjectForDashboard(null)}
                      className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center space-x-1.5 text-xs font-semibold"
                    >
                      <ArrowLeft className="w-4 h-4" />
                      <span>Back to Projects</span>
                    </button>
                    <div>
                      <h3 className="font-bold text-lg text-white">
                        SEO Audit Dashboard: {selectedProjectForDashboard.name}
                      </h3>
                      <p className="text-xs text-slate-400 font-mono">
                        {selectedProjectForDashboard.target_url}
                      </p>
                    </div>
                  </div>
                </div>

                <ProjectDashboard
                  project={selectedProjectForDashboard}
                  onViewIssues={handleViewIssues}
                  onViewPages={handleViewPages}
                  onTriggerCrawl={handleStartCrawl}
                />
              </div>
            ) : selectedProjectForPages ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between bg-slate-900/40 p-4 rounded-xl border border-slate-800">
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => setSelectedProjectForPages(null)}
                      className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <div>
                      <h3 className="font-bold text-lg text-white">
                        Crawled Pages: {selectedProjectForPages.name}
                      </h3>
                      <p className="text-xs text-slate-400 font-mono">
                        {selectedProjectForPages.target_url}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleViewDashboard(selectedProjectForPages)}
                      className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all active:scale-95"
                    >
                      <BarChart3 className="w-3.5 h-3.5" />
                      <span>Audit Dashboard</span>
                    </button>
                    <button
                      onClick={() => handleViewIssues(selectedProjectForPages)}
                      className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold shadow-md transition-all active:scale-95"
                    >
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>View SEO Issues</span>
                    </button>
                    <button
                      onClick={() => handleStartCrawl(selectedProjectForPages.id)}
                      className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition-all active:scale-95"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Re-Crawl Website</span>
                    </button>
                  </div>
                </div>

                <PageList projectId={selectedProjectForPages.id} />
              </div>
            ) : selectedProjectForIssues ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between bg-slate-900/40 p-4 rounded-xl border border-slate-800">
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => setSelectedProjectForIssues(null)}
                      className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                    >
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <div>
                      <h3 className="font-bold text-lg text-white">
                        SEO Issues: {selectedProjectForIssues.name}
                      </h3>
                      <p className="text-xs text-slate-400 font-mono">
                        {selectedProjectForIssues.target_url}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleViewDashboard(selectedProjectForIssues)}
                      className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all active:scale-95"
                    >
                      <BarChart3 className="w-3.5 h-3.5" />
                      <span>Audit Dashboard</span>
                    </button>
                    <button
                      onClick={() => handleStartCrawl(selectedProjectForIssues.id)}
                      className="flex items-center space-x-2 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition-all active:scale-95"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Re-Crawl & Re-Analyze</span>
                    </button>
                  </div>
                </div>

                <IssueList projectId={selectedProjectForIssues.id} />
              </div>
            ) : (
              <ProjectList
                projects={projects}
                loading={loadingProjects}
                onOpenCreateModal={() => {
                  setEditingProject(null);
                  setIsModalOpen(true);
                }}
                onEditProject={(project) => {
                  setEditingProject(project);
                  setIsModalOpen(true);
                }}
                onDeleteProject={handleDeleteProject}
                onStartCrawl={handleStartCrawl}
                onViewPages={handleViewPages}
                onViewIssues={handleViewIssues}
                onViewDashboard={handleViewDashboard}
              />
            )}

            {/* Project Modal (Create/Edit) */}
            <ProjectModal
              isOpen={isModalOpen}
              onClose={() => setIsModalOpen(false)}
              onSave={handleSaveProject}
              projectToEdit={editingProject}
            />

            {/* Development Roadmap Status */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-6">
              <div>
                <h3 className="font-bold text-xl text-white">Development Roadmap Status</h3>
                <p className="text-xs text-slate-400 mt-1">Incremental Phase Execution</p>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/60 border border-emerald-500/30">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-semibold text-sm text-white">Phase 1: Foundation</h4>
                      <p className="text-xs text-slate-400">Monorepo setup, FastAPI backend, React + TypeScript + Tailwind frontend, SQLite database schema.</p>
                    </div>
                  </div>
                  <span className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-medium border border-emerald-500/20">Completed</span>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/60 border border-emerald-500/30">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-semibold text-sm text-white">Phase 2: Authentication</h4>
                      <p className="text-xs text-slate-400">User Registration, Login, JWT Tokens, Password Hashing, Protected Routes.</p>
                    </div>
                  </div>
                  <span className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-medium border border-emerald-500/20">Completed</span>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/60 border border-emerald-500/30">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-semibold text-sm text-white">Phase 3: Projects & SSRF Protection</h4>
                      <p className="text-xs text-slate-400">Create website projects, crawl limits, crawl depth, project settings, URL validation & SSRF protection.</p>
                    </div>
                  </div>
                  <span className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-medium border border-emerald-500/20">Completed</span>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/60 border border-emerald-500/30">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-semibold text-sm text-white">Phase 4: Basic Crawler & Page Storage</h4>
                      <p className="text-xs text-slate-400">Single-worker crawler, URL discovery, status codes, title, meta description, links, images & storage.</p>
                    </div>
                  </div>
                  <span className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-medium border border-emerald-500/20">Completed</span>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/60 border border-emerald-500/30">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-semibold text-sm text-white">Phase 5: Modular SEO Analysis Engine</h4>
                      <p className="text-xs text-slate-400">Technical, on-page, content, link & image rule analyzers, duplicate detection, issue management dashboard.</p>
                    </div>
                  </div>
                  <span className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-medium border border-emerald-500/20">Completed</span>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/60 border border-emerald-500/30">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-semibold text-sm text-white">Phase 6: SEO Scoring Engine & Analytics Dashboard</h4>
                      <p className="text-xs text-slate-400">Transparent weighted scoring (Technical 25%, On-Page 25%, Content 20%, Links 15%, Performance 10%, Mobile 5%), health grade A-F, radar diagnostics, and priority actionable recommendations.</p>
                    </div>
                  </div>
                  <span className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-medium border border-emerald-500/20">Completed</span>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/60 border border-emerald-500/30">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-semibold text-sm text-white">Phase 7: Background Jobs & Distributed Processing</h4>
                      <p className="text-xs text-slate-400">Celery distributed crawl tasks, Redis broker integration, crawl_tasks per-URL tracking, exponential backoff retries, and live worker queue activity drawer.</p>
                    </div>
                  </div>
                  <span className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-medium border border-emerald-500/20">Completed</span>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/60 border border-emerald-500/30">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-semibold text-sm text-white">Phase 8: Historical Snapshots, Competitor Intelligence & Scheduled Audits</h4>
                      <p className="text-xs text-slate-400">Immutable audit snapshots with score trend tracking, multi-domain competitor benchmarking, and Celery Beat scheduled recurring scan automation.</p>
                    </div>
                  </div>
                  <span className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-medium border border-emerald-500/20">Completed</span>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/60 border border-emerald-500/30">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-semibold text-sm text-white">Phase 9: Reports, Notifications & Intelligence Suite</h4>
                      <p className="text-xs text-slate-400">PDF/CSV/JSON report generation via ReportLab, in-app notification bell with crawl-complete alerts, competitor benchmarking UI, audit history charts, and scheduled scan configuration panel.</p>
                    </div>
                  </div>
                  <span className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full font-medium border border-emerald-500/20">Completed</span>
                </div>

                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-800/60 border border-violet-500/30">
                  <div className="flex items-center space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-violet-400" />
                    <div>
                      <h4 className="font-semibold text-sm text-white">Phase 10: AI Intelligence Suite (Current)</h4>
                      <p className="text-xs text-slate-400">Rule-based AI recommendation engine with optional OpenAI enrichment, content gap analysis (thin content, heading issues, keyword cannibalization), structured JSON logging with rotating file handler, 6 new test modules, Celery Beat scheduler, and Docker resource limits.</p>
                    </div>
                  </div>
                  <span className="text-xs px-3 py-1 bg-violet-500/10 text-violet-400 rounded-full font-medium border border-violet-500/20">Active</span>
                </div>
              </div>
            </div>
          </>
        )}
      </main>

      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>Advanced SEO Intelligence Platform • Modular SEO Analysis Engine v1.0.0</p>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
};

export default App;
