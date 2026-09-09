import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  fetchNotifications, fetchUnreadCount, markNotificationRead,
  markAllNotificationsRead, deleteNotification
} from '../../services/api';
import type { Notification } from '../../services/api';
import { Bell, BellRing, CheckCheck, Trash2, X, Info, Zap } from 'lucide-react';

const TYPE_ICONS: Record<string, React.ReactNode> = {
  crawl_complete: <Zap className="w-3.5 h-3.5 text-emerald-400" />,
  default: <Info className="w-3.5 h-3.5 text-blue-400" />,
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(mins / 60);
  const days = Math.floor(hours / 24);
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (mins > 0) return `${mins}m ago`;
  return 'just now';
}

export const NotificationBell: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const loadCount = useCallback(async () => {
    try {
      setUnreadCount(await fetchUnreadCount());
    } catch { /* silent */ }
  }, []);

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchNotifications();
      setNotifications(data);
      setUnreadCount(data.filter(n => !n.read_at).length);
    } catch { /* silent */ } finally {
      setLoading(false);
    }
  }, []);

  // Poll unread count every 30s
  useEffect(() => {
    loadCount();
    const interval = setInterval(loadCount, 30000);
    return () => clearInterval(interval);
  }, [loadCount]);

  // Load when opened
  useEffect(() => {
    if (open) loadNotifications();
  }, [open, loadNotifications]);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleMarkRead = async (id: number) => {
    try {
      await markNotificationRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read_at: new Date().toISOString() } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch { /* silent */ }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read_at: n.read_at || new Date().toISOString() })));
      setUnreadCount(0);
    } catch { /* silent */ }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteNotification(id);
      setNotifications(prev => {
        const removed = prev.find(n => n.id === id);
        if (removed && !removed.read_at) setUnreadCount(c => Math.max(0, c - 1));
        return prev.filter(n => n.id !== id);
      });
    } catch { /* silent */ }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={() => setOpen(!open)}
        className={`relative p-2 rounded-xl transition-all ${
          open ? 'bg-slate-700' : 'hover:bg-slate-800/80'
        } text-slate-400 hover:text-white`}
        title="Notifications"
      >
        {unreadCount > 0
          ? <BellRing className="w-5 h-5 text-amber-400 animate-[wiggle_1s_ease-in-out_infinite]" />
          : <Bell className="w-5 h-5" />
        }
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center shadow-sm animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-96 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl z-[60] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-amber-400" />
              <span className="text-sm font-bold text-white">Notifications</span>
              {unreadCount > 0 && (
                <span className="px-1.5 py-0.5 bg-rose-500/20 text-rose-400 text-xs font-bold rounded-full border border-rose-500/30">
                  {unreadCount} new
                </span>
              )}
            </div>
            <div className="flex items-center gap-1">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  title="Mark all as read"
                  className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-emerald-400 transition-colors"
                >
                  <CheckCheck className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => setOpen(false)}
                className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/60">
            {loading ? (
              <div className="flex items-center justify-center h-24">
                <div className="w-6 h-6 border-3 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center px-4">
                <Bell className="w-8 h-8 text-slate-700 mb-2" />
                <p className="text-sm text-slate-500">All caught up!</p>
                <p className="text-xs text-slate-600 mt-1">Notifications will appear here after crawls complete.</p>
              </div>
            ) : (
              notifications.map(notif => {
                const isUnread = !notif.read_at;
                const icon = TYPE_ICONS[notif.type] || TYPE_ICONS.default;
                return (
                  <div
                    key={notif.id}
                    onClick={() => isUnread && handleMarkRead(notif.id)}
                    className={`group flex items-start gap-3 px-4 py-3.5 transition-colors cursor-pointer ${
                      isUnread ? 'bg-slate-800/40 hover:bg-slate-800/60' : 'hover:bg-slate-800/20'
                    }`}
                  >
                    {/* Icon */}
                    <div className={`mt-0.5 p-1.5 rounded-lg shrink-0 ${
                      isUnread ? 'bg-amber-500/10' : 'bg-slate-800'
                    }`}>
                      {icon}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs leading-relaxed ${isUnread ? 'text-white' : 'text-slate-400'}`}>
                        {notif.message}
                      </p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-[10px] text-slate-500">{timeAgo(notif.created_at)}</span>
                        {isUnread && (
                          <span className="w-1.5 h-1.5 bg-amber-400 rounded-full" />
                        )}
                      </div>
                    </div>

                    {/* Delete */}
                    <button
                      onClick={e => { e.stopPropagation(); handleDelete(notif.id); }}
                      className="shrink-0 p-1 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-rose-500/10 text-slate-500 hover:text-rose-400 transition-all"
                      title="Dismiss"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-2.5 border-t border-slate-800 bg-slate-900/60">
              <p className="text-xs text-slate-500 text-center">
                {notifications.length} notification{notifications.length !== 1 ? 's' : ''} •{' '}
                <button
                  onClick={handleMarkAllRead}
                  className="text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  Mark all read
                </button>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
