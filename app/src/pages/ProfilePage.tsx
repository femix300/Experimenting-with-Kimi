import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores";
import { logoutFirebase } from "@/lib/firebase";
import { firebaseLogout } from "@/lib/api";
import {
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Save,
  LogOut,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

const ProfilePage = () => {
  const navigate = useNavigate();
  const { user, logout, setUser } = useAuthStore();
  const [displayName, setDisplayName] = useState(user?.displayName || "");
  const [email, setEmail] = useState(user?.email || "");
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (user?.displayName) setDisplayName(user.displayName);
    if (user?.email) setEmail(user.email);
  }, [user]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const { updateUserProfile } = await import("@/lib/firebase");
      await updateUserProfile(displayName);
      setUser({ ...user, displayName, username: displayName } as any);
      setSuccess("Profile updated successfully");
    } catch (err: any) {
      setError(err?.message || "Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const { updateUserPassword } = await import("@/lib/firebase");
      await updateUserPassword(newPassword);
      setNewPassword("");
      setSuccess("Password updated successfully");
    } catch (err: any) {
      setError(err?.message || "Failed to update password");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logoutFirebase();
      await firebaseLogout();
    } catch { /* ignore */ }
    logout();
    navigate("/auth");
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <button
          onClick={() => navigate("/home")}
          className="flex items-center gap-2 text-sm text-[#8b92a8] hover:text-[#dee2f5] transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>

        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6 space-y-6">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-[#00d4ff]/10 border border-[#00d4ff]/30 flex items-center justify-center mx-auto mb-3">
              <User className="w-8 h-8 text-[#00d4ff]" />
            </div>
            <h2 className="text-lg font-bold text-[#dee2f5]">{user?.displayName || "Trader"}</h2>
            <p className="text-sm text-[#8b92a8]">{user?.email || user?.username || ""}</p>
          </div>

          {error && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#ff4757]/10 border border-[#ff4757]/30">
              <AlertTriangle className="w-4 h-4 text-[#ff4757] flex-shrink-0" />
              <span className="text-xs text-[#ff4757]">{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#00ff88]/10 border border-[#00ff88]/30">
              <CheckCircle2 className="w-4 h-4 text-[#00ff88] flex-shrink-0" />
              <span className="text-xs text-[#00ff88]">{success}</span>
            </div>
          )}

          {/* Profile Info */}
          <form onSubmit={handleUpdateProfile} className="space-y-4">
            <h3 className="text-sm font-semibold text-[#dee2f5] border-b border-[#1a2030] pb-2">Profile Information</h3>
            <div>
              <label className="text-xs text-[#8b92a8] mb-1.5 block">Display Name / Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5a6070]" />
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#dee2f5] focus:outline-none focus:border-[#00d4ff]/50"
                />
              </div>
            </div>

            <div>
              <label className="text-xs text-[#8b92a8] mb-1.5 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5a6070]" />
                <input
                  type="email"
                  value={email}
                  disabled
                  className="w-full pl-10 pr-4 py-2.5 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#5a6070] cursor-not-allowed"
                />
              </div>
              <p className="text-[10px] text-[#5a6070] mt-1">Email cannot be changed</p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-[#00d4ff] text-[#0a0e17] rounded-lg text-sm font-bold hover:brightness-110 transition-all disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {loading ? "Saving..." : "Update Profile"}
            </button>
          </form>

          {/* Password Change */}
          <form onSubmit={handleUpdatePassword} className="space-y-4">
            <h3 className="text-sm font-semibold text-[#dee2f5] border-b border-[#1a2030] pb-2">Change Password</h3>
            <div>
              <label className="text-xs text-[#8b92a8] mb-1.5 block">New Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5a6070]" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-2.5 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#dee2f5] placeholder:text-[#5a6070] focus:outline-none focus:border-[#00d4ff]/50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#5a6070] hover:text-[#8b92a8]"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !newPassword}
              className="flex items-center gap-2 px-4 py-2 bg-[#131a2b] border border-[#1a2030] text-[#dee2f5] rounded-lg text-sm font-medium hover:border-[#00d4ff]/30 transition-all disabled:opacity-50"
            >
              <Lock className="w-4 h-4" />
              {loading ? "Updating..." : "Update Password"}
            </button>
          </form>

          {/* Logout */}
          <div className="pt-4 border-t border-[#1a2030]">
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-[#ff4757]/10 border border-[#ff4757]/30 text-[#ff4757] rounded-lg text-sm font-medium hover:bg-[#ff4757]/20 transition-all"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;