import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import {
  Radar,
  Grid3X3,
  FlaskConical,
  Wallet,
  Target,
  Settings,
  Menu,
  X,
  Zap,
} from "lucide-react";

const navItems = [
  { name: "Signal Feed", route: "/signals", icon: Zap },
  { name: "Markets", route: "/markets", icon: Grid3X3 },
  { name: "Portfolio", route: "/portfolio", icon: Wallet },
  { name: "Backtest", route: "/backtest", icon: FlaskConical },
  { name: "Calibration", route: "/calibration", icon: Target },
  { name: "Settings", route: "/settings", icon: Settings },
];

const DashboardLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#0a0e17]">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-[#0f1420] border-r border-[#1a2030] fixed h-screen z-40">
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#00d4ff] flex items-center justify-center">
            <Radar className="w-5 h-5 text-[#0a0e17]" />
          </div>
          <span className="font-bold text-lg text-[#dee2f5] tracking-tight">
            EdgeIQ
          </span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.route || location.pathname.startsWith(`${item.route}/`);
            const Icon = item.icon;
            return (
              <button
                key={item.route}
                onClick={() => navigate(item.route)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? "bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/20"
                    : "text-[#8b92a8] hover:text-[#dee2f5] hover:bg-[#1a2030]"
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </button>
            );
          })}
        </nav>

        <div className="p-4 border-t border-[#1a2030]">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#1a2030]/50">
            <div className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse-dot" />
            <span className="text-xs text-[#8b92a8]">Live Data</span>
          </div>
        </div>
      </aside>

      {/* Mobile Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-[#0f1420] border-b border-[#1a2030] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-[#00d4ff] flex items-center justify-center">
            <Radar className="w-4 h-4 text-[#0a0e17]" />
          </div>
          <span className="font-bold text-[#dee2f5]">EdgeIQ</span>
        </div>
        <button onClick={() => setMobileOpen(!mobileOpen)} className="text-[#dee2f5]">
          {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Nav Overlay */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-[#0a0e17]/95 pt-16">
          <nav className="p-4 space-y-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.route;
              const Icon = item.icon;
              return (
                <button
                  key={item.route}
                  onClick={() => {
                    navigate(item.route);
                    setMobileOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium ${
                    isActive
                      ? "bg-[#00d4ff]/10 text-[#00d4ff]"
                      : "text-[#8b92a8]"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </button>
              );
            })}
          </nav>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 md:ml-64 pt-14 md:pt-0 min-h-screen">
        <div className="p-4 md:p-8 max-w-[1440px] mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
