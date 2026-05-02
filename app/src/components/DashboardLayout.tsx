import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { logoutFirebase } from "@/lib/firebase";
import { useState } from "react";
import { useAuthStore } from "@/stores";
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
  Home,
  User,
  LogOut,
} from "lucide-react";

const navItems = [
  { name: "Home", route: "/home", icon: Home },
  { name: "Markets", route: "/markets", icon: Grid3X3 },
  { name: "Signals", route: "/signals", icon: Zap },
  { name: "Portfolio", route: "/portfolio", icon: Wallet },
  { name: "Backtest", route: "/backtest", icon: FlaskConical },
  { name: "Calibration", route: "/calibration", icon: Target },
  { name: "Settings", route: "/settings", icon: Settings },
];

const DashboardLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const handleLogout = async () => {
    try { await logoutFirebase(); } catch {}
    localStorage.removeItem("edgeiq_firebase_token");
    logout();
    navigate("/auth");
  };

  return (
    <div className="flex min-h-screen bg-[#0a0e17]">
      <aside className="hidden md:flex flex-col w-64 bg-[#0f1420] border-r border-[#1a2030] fixed h-screen z-40">
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#00d4ff] flex items-center justify-center">
            <Radar className="w-5 h-5 text-[#0a0e17]" />
          </div>
          <span className="font-bold text-lg text-[#dee2f5] tracking-tight">EdgeIQ</span>
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
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-[#1a2030] transition-all"
          >
            <div className="w-8 h-8 rounded-full bg-[#00d4ff]/10 border border-[#00d4ff]/30 flex items-center justify-center">
              <User className="w-4 h-4 text-[#00d4ff]" />
            </div>
            <div className="flex-1 text-left min-w-0">
              <p className="text-sm text-[#dee2f5] truncate">{user?.displayName || user?.username || "Trader"}</p>
              <p className="text-xs text-[#5a6070] truncate">{user?.email || ""}</p>
            </div>
          </button>

          {profileOpen && (
            <div className="mt-2 space-y-1">
              <button
                onClick={() => { navigate("/profile"); setProfileOpen(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#8b92a8] hover:text-[#dee2f5] hover:bg-[#1a2030] transition-all"
              >
                <User className="w-4 h-4" />
                Profile
              </button>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#ff4757] hover:bg-[#ff4757]/10 transition-all"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            </div>
          )}

          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#1a2030]/50 mt-3">
            <div className="w-2 h-2 rounded-full bg-[#00ff88] animate-pulse-dot" />
            <span className="text-xs text-[#8b92a8]">Live Data</span>
          </div>
        </div>
      </aside>

      <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-[#0f1420] border-b border-[#1a2030] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-[#00d4ff] flex items-center justify-center">
            <Radar className="w-4 h-4 text-[#0a0e17]" />
          </div>
          <span className="font-bold text-[#dee2f5]">EdgeIQ</span>
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <button onClick={() => navigate("/profile")} className="w-7 h-7 rounded-full bg-[#00d4ff]/10 border border-[#00d4ff]/30 flex items-center justify-center">
              <User className="w-3.5 h-3.5 text-[#00d4ff]" />
            </button>
          )}
          <button onClick={() => setMobileOpen(!mobileOpen)} className="text-[#dee2f5]">
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-[#0a0e17]/95 pt-16">
          <nav className="p-4 space-y-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.route;
              const Icon = item.icon;
              return (
                <button
                  key={item.route}
                  onClick={() => { navigate(item.route); setMobileOpen(false); }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium ${isActive ? "bg-[#00d4ff]/10 text-[#00d4ff]" : "text-[#8b92a8]"}`}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </button>
              );
            })}
            <div className="border-t border-[#1a2030] pt-2 mt-2">
              <button onClick={() => { navigate("/profile"); setMobileOpen(false); }} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-[#8b92a8]">
                <User className="w-5 h-5" />
                Profile
              </button>
              <button onClick={() => { handleLogout(); setMobileOpen(false); }} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-[#ff4757]">
                <LogOut className="w-5 h-5" />
                Sign Out
              </button>
            </div>
          </nav>
        </div>
      )}

      <main className="flex-1 md:ml-64 pt-14 md:pt-0 min-h-screen">
        <div className="p-4 md:p-8 max-w-[1440px] mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
