import React, { useEffect, useState } from 'react';
import type { Page, PageDetail } from '../../services/api';
import { fetchProjectPages, getPageDetails } from '../../services/api';
import { 
  Search, 
  Clock, 
  FileText, 
  Link as LinkIcon, 
  Image as ImageIcon, 
  X, 
  ChevronLeft, 
  ChevronRight,
  Loader2,
  Filter
} from 'lucide-react';

interface PageListProps {
  projectId: number;
}

export const PageList: React.FC<PageListProps> = ({ projectId }) => {
  const [pages, setPages] = useState<Page[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  // Selected page detail modal
  const [selectedPageId, setSelectedPageId] = useState<number | null>(null);
  const [pageDetail, setPageDetail] = useState<PageDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const loadPages = async () => {
    setLoading(true);
    try {
      const res = await fetchProjectPages(projectId, {
        query: searchQuery.trim() || undefined,
        status_code: statusFilter,
        page,
        page_size: pageSize,
      });
      setPages(res.pages);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to load project pages:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPages();
  }, [projectId, page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadPages();
  };

  const handleOpenDetail = async (pageId: number) => {
    setSelectedPageId(pageId);
    setLoadingDetail(true);
    try {
      const detail = await getPageDetails(pageId);
      setPageDetail(detail);
    } catch (err) {
      console.error('Failed to load page detail:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const getStatusBadge = (code: number) => {
    if (code >= 200 && code < 300) {
      return <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-mono font-bold">{code} OK</span>;
    }
    if (code >= 300 && code < 400) {
      return <span className="px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-mono font-bold">{code} Redirect</span>;
    }
    if (code >= 400 && code < 500) {
      return <span className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-mono font-bold">{code} Client Error</span>;
    }
    if (code >= 500) {
      return <span className="px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20 text-xs font-mono font-bold">{code} Server Error</span>;
    }
    return <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 border border-slate-700 text-xs font-mono font-bold">0 Failed</span>;
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      {/* Search & Filter Control Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 rounded-2xl p-4">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search crawled URL or title..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </form>

        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5 text-slate-400">
            <Filter className="w-3.5 h-3.5" />
            <span>HTTP Status:</span>
          </div>
          <select
            value={statusFilter || ''}
            onChange={(e) => {
              const val = e.target.value ? Number(e.target.value) : undefined;
              setStatusFilter(val);
              setPage(1);
            }}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Status Codes</option>
            <option value="200">200 OK</option>
            <option value="301">301 Moved Permanently</option>
            <option value="404">404 Not Found</option>
            <option value="500">500 Server Error</option>
          </select>
        </div>
      </div>

      {/* Pages Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold">
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Crawled URL & Page Title</th>
                <th className="py-3.5 px-4">Word Count</th>
                <th className="py-3.5 px-4">Response Time</th>
                <th className="py-3.5 px-4">Depth</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <div className="inline-flex items-center space-x-2">
                      <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                      <span>Loading crawled pages...</span>
                    </div>
                  </td>
                </tr>
              ) : pages.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No crawled pages match the current filter.
                  </td>
                </tr>
              ) : (
                pages.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {getStatusBadge(p.status_code)}
                    </td>
                    <td className="py-3.5 px-4 max-w-md">
                      <div className="font-semibold text-slate-100 truncate" title={p.title || 'Untitled Page'}>
                        {p.title || <span className="text-slate-500 italic">No Title Tag</span>}
                      </div>
                      <a
                        href={p.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[11px] font-mono text-slate-400 hover:text-blue-400 truncate block mt-0.5"
                      >
                        {p.url}
                      </a>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap font-mono text-slate-300">
                      {p.word_count.toLocaleString()} words
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap font-mono text-slate-300">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>{p.response_time_ms} ms</span>
                      </span>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap font-mono text-slate-400">
                      Level {p.depth}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap text-right">
                      <button
                        onClick={() => handleOpenDetail(p.id)}
                        className="px-3 py-1.5 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 font-semibold border border-blue-500/20 transition-all"
                      >
                        Inspect Tags
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} pages
            </span>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                disabled={page === 1}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-mono text-slate-200">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
                disabled={page === totalPages}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Page Detail Inspection Modal */}
      {selectedPageId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in">
          <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-500/10 rounded-xl text-blue-400">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Page SEO Inspection</h3>
                  <p className="text-xs text-slate-400 truncate max-w-lg">{pageDetail?.url}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setSelectedPageId(null);
                  setPageDetail(null);
                }}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
              {loadingDetail ? (
                <div className="py-12 flex justify-center text-slate-400 space-x-2">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
                  <span>Loading metadata...</span>
                </div>
              ) : pageDetail ? (
                <>
                  {/* Summary Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">Title Tag</span>
                      <p className="text-sm font-semibold text-slate-100">{pageDetail.title || 'None'}</p>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">Canonical URL</span>
                      <p className="text-sm font-mono text-slate-300 truncate">{pageDetail.canonical_url || 'None'}</p>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-semibold">Meta Description</span>
                    <p className="text-xs text-slate-300">{pageDetail.meta_description || 'No description meta tag found.'}</p>
                  </div>

                  {/* Extracted Links */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-sm text-white flex items-center space-x-2">
                      <LinkIcon className="w-4 h-4 text-blue-400" />
                      <span>Extracted Links ({pageDetail.links.length})</span>
                    </h4>
                    <div className="max-h-40 overflow-y-auto rounded-xl bg-slate-950 border border-slate-800 p-3 space-y-2">
                      {pageDetail.links.length === 0 ? (
                        <p className="text-slate-500 italic">No links extracted.</p>
                      ) : (
                        pageDetail.links.map((l) => (
                          <div key={l.id} className="flex items-center justify-between text-[11px]">
                            <div className="truncate max-w-md font-mono text-slate-300">
                              {l.target_url}
                            </div>
                            <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                              l.link_type === 'internal' ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'
                            }`}>
                              {l.link_type}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Extracted Images */}
                  <div className="space-y-3">
                    <h4 className="font-bold text-sm text-white flex items-center space-x-2">
                      <ImageIcon className="w-4 h-4 text-indigo-400" />
                      <span>Extracted Images ({pageDetail.images.length})</span>
                    </h4>
                    <div className="max-h-40 overflow-y-auto rounded-xl bg-slate-950 border border-slate-800 p-3 space-y-2">
                      {pageDetail.images.length === 0 ? (
                        <p className="text-slate-500 italic">No images found on page.</p>
                      ) : (
                        pageDetail.images.map((img) => (
                          <div key={img.id} className="flex items-center justify-between text-[11px]">
                            <div className="truncate max-w-md font-mono text-slate-300">
                              {img.url}
                            </div>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              img.has_alt ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                            }`}>
                              {img.has_alt ? `ALT: "${img.alt_text}"` : 'Missing ALT Tag'}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
