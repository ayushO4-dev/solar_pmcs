import { ReactNode, useEffect, useState } from 'react';
import { Home, Settings, Sliders, Menu, ChevronLeft } from 'lucide-react';
import { api } from '../lib/api';

// Badge label and colors per system status; full class names so Tailwind keeps them
const STATUS_BADGES: Record<string, { label: string; badge: string; dot: string; text: string }> = {
  active: { label: 'System Active', badge: 'bg-green-50 border-green-200', dot: 'bg-green-500 animate-pulse', text: 'text-green-700' },
  sleep: { label: 'Sleep Mode', badge: 'bg-blue-50 border-blue-200', dot: 'bg-blue-500', text: 'text-blue-700' },
  reboot: { label: 'Rebooting', badge: 'bg-amber-50 border-amber-200', dot: 'bg-amber-500 animate-pulse', text: 'text-amber-700' },
  shutdown: { label: 'Shut Down', badge: 'bg-red-50 border-red-200', dot: 'bg-red-500', text: 'text-red-700' },
  offline: { label: 'Offline', badge: 'bg-gray-100 border-gray-300', dot: 'bg-gray-400', text: 'text-gray-600' },
};

interface LayoutProps {
  children: ReactNode;
  currentPage: string;
  onNavigate: (page: string) => void;
}

export default function Layout({ children, currentPage, onNavigate }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [status, setStatus] = useState('offline');

  useEffect(() => {
    const fetchStatus = () =>
      api.system.status()
        .then((s) => setStatus(s.status))
        .catch(() => setStatus('offline'));

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const badge = STATUS_BADGES[status] ?? STATUS_BADGES.offline;

  const menuItems = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'control', label: 'Control', icon: Sliders },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 flex items-center px-6 z-50 shadow-sm">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="text-gray-600 hover:text-gray-900 p-1"
        >
          <Menu className="w-6 h-6" />
        </button>
        <h1 className="text-xl font-semibold text-gray-900 capitalize flex-1 ml-4">{currentPage}</h1>
        <div className={`flex items-center gap-2 px-3 py-1.5 border rounded-full ${badge.badge}`}>
          <div className={`w-2 h-2 rounded-full ${badge.dot}`}></div>
          <span className={`text-sm font-medium ${badge.text}`}>{badge.label}</span>
        </div>
      </header>

      <div className="flex pt-16 flex-1">
        <aside className={`fixed left-0 top-16 bottom-0 w-64 bg-white border-r border-gray-200 transform transition-all duration-300 z-40 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0`}>
          <nav className="px-4 py-6 space-y-2 flex flex-col h-full">
            <div className="flex-1">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onNavigate(item.id);
                      setSidebarOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all font-medium ${
                      isActive
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>

            <div className="border-t border-gray-200 pt-4">
              <button
                onClick={() => setSidebarOpen(false)}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-all font-medium md:hidden"
              >
                <ChevronLeft className="w-5 h-5" />
                <span>Collapse</span>
              </button>
              <div className="text-xs text-gray-500 text-center pt-4">
                Solar Monitoring System v1.0
              </div>
            </div>
          </nav>
        </aside>

        <main className={`flex-1 transition-all duration-300 ${sidebarOpen ? 'md:ml-64' : ''}`}>
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>

      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-30 md:hidden top-16"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
