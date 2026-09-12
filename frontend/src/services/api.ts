import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject JWT Bearer Token if present in localStorage
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('seo_access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  database: string;
  environment: string;
}

export interface User {
  id: number;
  email: string;
  role: string;
  created_at: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
}

export interface Project {
  id: number;
  user_id: number;
  name: string;
  target_url: string;
  max_crawl_pages: number;
  max_crawl_depth: number;
  custom_user_agent: string;
  respect_robots_txt: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateInput {
  name: string;
  target_url: string;
  max_crawl_pages?: number;
  max_crawl_depth?: number;
  custom_user_agent?: string;
  respect_robots_txt?: boolean;
}

export interface ProjectUpdateInput {
  name?: string;
  target_url?: string;
  max_crawl_pages?: number;
  max_crawl_depth?: number;
  custom_user_agent?: string;
  respect_robots_txt?: boolean;
}

export interface UrlValidationResponse {
  url: string;
  is_valid: boolean;
  normalized_url?: string;
  error?: string;
}

export interface CrawlJob {
  id: number;
  project_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped';
  total_urls: number;
  processed_urls: number;
  failed_urls: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface Link {
  id: number;
  source_url: string;
  target_url: string;
  link_type: 'internal' | 'external';
  anchor_text?: string;
  status_code?: number;
  is_broken: boolean;
}

export interface Image {
  id: number;
  url: string;
  alt_text?: string;
  has_alt: boolean;
}

export interface Page {
  id: number;
  project_id: number;
  crawl_job_id: number;
  url: string;
  status_code: number;
  title?: string;
  meta_description?: string;
  canonical_url?: string;
  h1_tags?: string;
  word_count: number;
  response_time_ms: number;
  depth: number;
  content_type?: string;
  crawled_at: string;
}

export interface PageDetail extends Page {
  links: Link[];
  images: Image[];
}

export interface PageListResponse {
  total: number;
  page: number;
  page_size: number;
  pages: Page[];
}

export const fetchSystemHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
};

export const registerUser = async (email: string, password: string): Promise<User> => {
  const response = await apiClient.post<User>('/v1/auth/register', { email, password });
  return response.data;
};

export const loginUser = async (email: string, password: string): Promise<AuthTokenResponse> => {
  const response = await apiClient.post<AuthTokenResponse>('/v1/auth/login', { email, password });
  return response.data;
};

export const fetchCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>('/v1/auth/me');
  return response.data;
};

export const fetchProjects = async (): Promise<Project[]> => {
  const response = await apiClient.get<Project[]>('/v1/projects');
  return response.data;
};

export const createProject = async (data: ProjectCreateInput): Promise<Project> => {
  const response = await apiClient.post<Project>('/v1/projects', data);
  return response.data;
};

export const getProject = async (id: number): Promise<Project> => {
  const response = await apiClient.get<Project>(`/v1/projects/${id}`);
  return response.data;
};

export const updateProject = async (id: number, data: ProjectUpdateInput): Promise<Project> => {
  const response = await apiClient.put<Project>(`/v1/projects/${id}`, data);
  return response.data;
};

export const deleteProject = async (id: number): Promise<void> => {
  await apiClient.delete(`/v1/projects/${id}`);
};

export const validateTargetUrl = async (url: string): Promise<UrlValidationResponse> => {
  const response = await apiClient.post<UrlValidationResponse>('/v1/projects/validate-url', { url });
  return response.data;
};

export const startCrawl = async (projectId: number): Promise<CrawlJob> => {
  const response = await apiClient.post<CrawlJob>(`/v1/projects/${projectId}/crawl`);
  return response.data;
};

export const getCrawlStatus = async (crawlId: number): Promise<CrawlJob> => {
  const response = await apiClient.get<CrawlJob>(`/v1/crawls/${crawlId}`);
  return response.data;
};

export const stopCrawl = async (crawlId: number): Promise<CrawlJob> => {
  const response = await apiClient.post<CrawlJob>(`/v1/crawls/${crawlId}/stop`);
  return response.data;
};

export const fetchProjectPages = async (
  projectId: number,
  params?: { query?: string; status_code?: number; page?: number; page_size?: number }
): Promise<PageListResponse> => {
  const response = await apiClient.get<PageListResponse>(`/v1/projects/${projectId}/pages`, { params });
  return response.data;
};

export const getPageDetails = async (pageId: number): Promise<PageDetail> => {
  const response = await apiClient.get<PageDetail>(`/v1/pages/${pageId}`);
  return response.data;
};

// ─── SEO Issues ────────────────────────────────────────────────────────────

export interface SEOIssue {
  id: number;
  project_id: number;
  page_id: number | null;
  crawl_job_id: number;
  category: 'technical' | 'onpage' | 'content' | 'link' | 'image' | 'performance';
  severity: 'critical' | 'high' | 'medium' | 'low';
  code: string;
  message: string;
  recommendation: string;
  status: 'open' | 'resolved' | 'ignored';
  created_at: string;
  page_url: string | null;
}

export interface SEOIssueListResponse {
  total: number;
  page: number;
  page_size: number;
  issues: SEOIssue[];
}

export interface IssueSeveritySummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface IssueCategorySummary {
  technical: number;
  onpage: number;
  content: number;
  link: number;
  image: number;
  performance: number;
}

export interface IssueSummaryResponse {
  total_open: number;
  total_resolved: number;
  total_ignored: number;
  by_severity: IssueSeveritySummary;
  by_category: IssueCategorySummary;
}

export const fetchProjectIssues = async (
  projectId: number,
  params?: {
    severity?: string;
    category?: string;
    status?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }
): Promise<SEOIssueListResponse> => {
  const response = await apiClient.get<SEOIssueListResponse>(`/v1/projects/${projectId}/issues`, { params });
  return response.data;
};

export const fetchIssueSummary = async (projectId: number): Promise<IssueSummaryResponse> => {
  const response = await apiClient.get<IssueSummaryResponse>(`/v1/projects/${projectId}/issues/summary`);
  return response.data;
};

export const updateIssueStatus = async (
  issueId: number,
  newStatus: 'open' | 'resolved' | 'ignored'
): Promise<SEOIssue> => {
  const response = await apiClient.put<SEOIssue>(`/v1/issues/${issueId}`, { status: newStatus });
  return response.data;
};

// ==========================================
// Phase 6: SEO Scoring & Analytics Dashboard
// ==========================================

export interface CategoryScores {
  technical: number;
  onpage: number;
  content: number;
  link: number;
  performance: number;
  mobile: number;
}

export interface PageHealthSummary {
  healthy: number;
  warning: number;
  critical: number;
}

export interface TopIssueSummary {
  code: string;
  category: string;
  severity: string;
  message: string;
  recommendation: string;
  count: number;
}

export interface ProjectSEOSummary {
  project_id: number;
  crawl_job_id?: number | null;
  crawl_status: string;
  audited_pages: number;
  overall_score: number;
  health_grade: string;
  category_scores: CategoryScores;
  page_health: PageHealthSummary;
  issue_counts: {
    total: number;
    by_severity: IssueSeveritySummary;
    by_category: Record<string, number>;
    by_status: { open: number; resolved: number; ignored: number };
  };
  top_issues: TopIssueSummary[];
}

export interface PageSEOScore {
  id: number;
  page_id: number;
  project_id: number;
  crawl_job_id: number;
  overall_score: number;
  technical_score: number;
  onpage_score: number;
  content_score: number;
  link_score: number;
  performance_score: number;
  mobile_score: number;
  created_at: string;
  url?: string;
}

export const fetchProjectSEOSummary = async (projectId: number): Promise<ProjectSEOSummary> => {
  const response = await apiClient.get<ProjectSEOSummary>(`/v1/projects/${projectId}/seo-summary`);
  return response.data;
};

export const fetchPageSEOScore = async (pageId: number): Promise<PageSEOScore> => {
  const response = await apiClient.get<PageSEOScore>(`/v1/pages/${pageId}/seo`);
  return response.data;
};

export const recalculateProjectScores = async (projectId: number): Promise<ProjectSEOSummary> => {
  const response = await apiClient.post<ProjectSEOSummary>(`/v1/projects/${projectId}/recalculate-scores`);
  return response.data;
};

// =======================================================
// Phase 7: Background Jobs & Distributed Workers (Celery)
// =======================================================

export interface CrawlTask {
  id: number;
  crawl_job_id: number;
  url: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  attempts: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CrawlTaskListResponse {
  tasks: CrawlTask[];
  total: number;
}

export const fetchCrawlTasks = async (
  crawlId: number,
  params?: { status?: string; page?: number; page_size?: number }
): Promise<CrawlTaskListResponse> => {
  const response = await apiClient.get<CrawlTaskListResponse>(`/v1/crawls/${crawlId}/tasks`, { params });
  return response.data;
};

// =====================================================
// Phase 8: Historical Snapshots, Competitors, Schedules
// =====================================================

export interface AuditSnapshot {
  id: number;
  project_id: number;
  crawl_job_id: number;
  overall_score: number;
  technical_score: number;
  onpage_score: number;
  content_score: number;
  link_score: number;
  performance_score: number;
  mobile_score: number;
  issue_count: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
  page_count: number;
  created_at: string;
}

export interface Competitor {
  id: number;
  project_id: number;
  name: string;
  domain: string;
  target_url: string;
  latest_score: number | null;
  latest_page_count: number | null;
  latest_issue_count: number | null;
  latest_crawl_job_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface CompetitorCreateInput {
  name: string;
  domain: string;
  target_url: string;
  project_id: number;
}

export interface ScheduledScan {
  id: number;
  project_id: number;
  frequency: 'daily' | 'weekly' | 'monthly';
  enabled: boolean;
  next_run_at: string | null;
  last_run_at: string | null;
  created_at: string;
}

export interface ScheduledScanInput {
  frequency: 'daily' | 'weekly' | 'monthly';
  enabled: boolean;
  project_id: number;
}

export const fetchAuditHistory = async (projectId: number): Promise<AuditSnapshot[]> => {
  const response = await apiClient.get<AuditSnapshot[]>(`/v1/projects/${projectId}/snapshots`);
  return response.data;
};

export const fetchCompetitors = async (projectId: number): Promise<Competitor[]> => {
  const response = await apiClient.get<Competitor[]>(`/v1/projects/${projectId}/competitors`);
  return response.data;
};

export const addCompetitor = async (data: CompetitorCreateInput): Promise<Competitor> => {
  const response = await apiClient.post<Competitor>(`/v1/projects/${data.project_id}/competitors`, data);
  return response.data;
};

export const deleteCompetitor = async (competitorId: number): Promise<void> => {
  await apiClient.delete(`/v1/competitors/${competitorId}`);
};

export const auditCompetitor = async (competitorId: number): Promise<{ crawl_job_id: number }> => {
  const response = await apiClient.post(`/v1/competitors/${competitorId}/audit`);
  return response.data;
};

export const fetchSchedule = async (projectId: number): Promise<ScheduledScan | null> => {
  try {
    const response = await apiClient.get<ScheduledScan>(`/v1/projects/${projectId}/schedule`);
    return response.data;
  } catch {
    return null;
  }
};

export const upsertSchedule = async (projectId: number, data: ScheduledScanInput): Promise<ScheduledScan> => {
  const response = await apiClient.post<ScheduledScan>(`/v1/projects/${projectId}/schedule`, data);
  return response.data;
};

// =====================================================
// Phase 9: Reports & Notifications
// =====================================================

export interface Report {
  id: number;
  project_id: number;
  crawl_job_id: number | null;
  format: 'json' | 'csv' | 'pdf';
  file_path: string | null;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
}

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  message: string;
  read_at: string | null;
  created_at: string;
}

export const createReport = async (projectId: number, format: string): Promise<Report> => {
  const response = await apiClient.post<Report>(`/v1/projects/${projectId}/reports`, {
    format,
    project_id: projectId,
  });
  return response.data;
};

export const fetchReports = async (projectId: number): Promise<Report[]> => {
  const response = await apiClient.get<Report[]>(`/v1/projects/${projectId}/reports`);
  return response.data;
};

export const deleteReport = async (reportId: number): Promise<void> => {
  await apiClient.delete(`/v1/reports/${reportId}`);
};

export const getReportDownloadUrl = (reportId: number): string => {
  const token = localStorage.getItem('seo_access_token');
  return `${apiClient.defaults.baseURL}/v1/reports/${reportId}/download?token=${token}`;
};

export const downloadReport = async (reportId: number): Promise<void> => {
  const token = localStorage.getItem('seo_access_token');
  const response = await apiClient.get(`/v1/reports/${reportId}/download`, {
    responseType: 'blob',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  const cd = response.headers['content-disposition'] || '';
  const filename = cd.split('filename=')[1]?.replace(/"/g, '') || `report_${reportId}`;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const fetchNotifications = async (unreadOnly = false): Promise<Notification[]> => {
  const response = await apiClient.get<Notification[]>('/v1/notifications', {
    params: { unread_only: unreadOnly },
  });
  return response.data;
};

export const fetchUnreadCount = async (): Promise<number> => {
  const response = await apiClient.get<{ unread_count: number }>('/v1/notifications/unread-count');
  return response.data.unread_count;
};

export const markNotificationRead = async (id: number): Promise<Notification> => {
  const response = await apiClient.put<Notification>(`/v1/notifications/${id}/read`);
  return response.data;
};

export const markAllNotificationsRead = async (): Promise<{ marked_read: number }> => {
  const response = await apiClient.put('/v1/notifications/read-all');
  return response.data;
};

export const deleteNotification = async (id: number): Promise<void> => {
  await apiClient.delete(`/v1/notifications/${id}`);
};

// =====================================================
// Phase 10: AI Intelligence
// =====================================================

export interface AISuggestion {
  id: string;
  category: string;
  priority: 'critical' | 'high' | 'medium' | 'quick_win';
  title: string;
  description: string;
  action: string;
  impact_estimate: string;
  affected_pages: number;
  affected_urls: string[];
  ai_enhanced: boolean;
  openai_detail: string | null;
}

export interface AIRecommendationsResponse {
  project_id: number;
  ai_mode: 'openai' | 'rule-based';
  total_suggestions: number;
  suggestions: AISuggestion[];
}

export interface ContentGapPage {
  url: string;
  detail: string;
}

export interface ContentGap {
  id: string;
  gap_type: string;
  severity: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  recommendation: string;
  affected_count: number;
  pages: ContentGapPage[];
}

export interface ContentGapReportResponse {
  project_id: number;
  total_pages_analyzed: number;
  thin_content_count: number;
  missing_h1_count: number;
  cannibalization_clusters: number;
  content_health_score: number;
  gaps: ContentGap[];
}

export const fetchAIRecommendations = async (
  projectId: number
): Promise<AIRecommendationsResponse> => {
  const response = await apiClient.get<AIRecommendationsResponse>(
    `/v1/projects/${projectId}/ai-recommendations`
  );
  return response.data;
};

export const regenerateAIRecommendations = async (
  projectId: number
): Promise<AIRecommendationsResponse> => {
  const response = await apiClient.post<AIRecommendationsResponse>(
    `/v1/projects/${projectId}/ai-recommendations/regenerate`
  );
  return response.data;
};

export const fetchContentGaps = async (
  projectId: number
): Promise<ContentGapReportResponse> => {
  const response = await apiClient.get<ContentGapReportResponse>(
    `/v1/projects/${projectId}/content-gaps`
  );
  return response.data;
};
