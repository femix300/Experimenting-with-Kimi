import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore, usePortfolioStore } from "@/stores";
import { registerWithEmail, loginWithEmail } from "@/lib/firebase";
import { firebaseLogin, getProfile } from "@/lib/api";
import {
  Radar,
  Mail,
  Lock,
  User,
  Eye,
  EyeOff,
  ChevronRight,
  Loader2,
  AlertTriangle,
} from "lucide-react";

const AuthPage = () => {
  const navigate = useNavigate();
  const { setAuthenticated, setUser, setToken, setOnboardingComplete } = useAuthStore();
  const { setProfile } = usePortfolioStore();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateForm = (): boolean => {
    setError(null);
    if (!email || !password) {
      setError("Email and password are required");
      return false;
    }
    if (!isLogin && !username) {
      setError("Username is required");
      return false;
    }
    if (!isLogin && password !== confirmPassword) {
      setError("Passwords do not match");
      return false;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setError(null);

    try {
      let firebaseUser;
      if (isLogin) {
        firebaseUser = await loginWithEmail(email, password);
      } else {
        firebaseUser = await registerWithEmail(email, password, username);
      }

      const token = await firebaseUser.getIdToken();
      setToken(token);

      // Exchange Firebase token for Django session
      try {
        const loginRes = await firebaseLogin(token);
        if (loginRes.success) {
          setUser({
            id: String(loginRes.user.id),
            username: loginRes.user.username || username || firebaseUser.displayName || email.split("@")[0],
            email: loginRes.user.email || email,
            displayName: loginRes.user.display_name || firebaseUser.displayName || username,
          });
        }
      } catch {
        // If backend login fails, still set frontend user from Firebase
        setUser({
          id: firebaseUser.uid,
          username: username || firebaseUser.displayName || email.split("@")[0],
          email: firebaseUser.email || email,
          displayName: firebaseUser.displayName || username,
        });
      }

      setAuthenticated(true);

      // Check if user has profile / bankroll set
      try {
        const profileRes = await getProfile();
        if (profileRes.success && profileRes.profile && profileRes.profile.bankroll > 0) {
          setProfile(profileRes.profile);
          setOnboardingComplete(true);
          navigate("/markets");
        } else {
          navigate("/onboarding");
        }
      } catch {
        navigate("/onboarding");
      }
    } catch (err: any) {
      const msg = err?.message || "Authentication failed";
      if (msg.includes("user-not-found") || msg.includes("invalid-credential")) {
        setError("Invalid email or password");
      } else if (msg.includes("email-already-in-use")) {
        setError("Email already registered. Try logging in instead.");
      } else if (msg.includes("weak-password")) {
        setError("Password is too weak. Use at least 6 characters.");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-10">
          <div className="w-10 h-10 rounded-xl bg-[#00d4ff] flex items-center justify-center">
            <Radar className="w-6 h-6 text-[#0a0e17]" />
          </div>
          <span className="font-bold text-2xl text-[#dee2f5]">EdgeIQ</span>
        </div>

        {/* Auth Card */}
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6 space-y-5">
          <div className="text-center">
            <h2 className="text-lg font-bold text-[#dee2f5]">{isLogin ? "Welcome Back" : "Create Account"}</h2>
            <p className="text-sm text-[#8b92a8] mt-1">
              {isLogin ? "Sign in to access your EdgeIQ dashboard" : "Join EdgeIQ to start finding market edges"}
            </p>
          </div>

          {/* Toggle */}
          <div className="flex bg-[#0a0e17] rounded-lg p-1">
            <button
              onClick={() => { setIsLogin(true); setError(null); }}
              className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${
                isLogin ? "bg-[#00d4ff]/20 text-[#00d4ff]" : "text-[#8b92a8] hover:text-[#dee2f5]"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setIsLogin(false); setError(null); }}
              className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${
                !isLogin ? "bg-[#00d4ff]/20 text-[#00d4ff]" : "text-[#8b92a8] hover:text-[#dee2f5]"
              }`}
            >
              Sign Up
            </button>
          </div>

          {error && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#ff4757]/10 border border-[#ff4757]/30">
              <AlertTriangle className="w-4 h-4 text-[#ff4757] flex-shrink-0" />
              <span className="text-xs text-[#ff4757]">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="text-xs text-[#8b92a8] mb-1.5 block">Username</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5a6070]" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="trader_01"
                    className="w-full pl-10 pr-4 py-2.5 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#dee2f5] placeholder:text-[#5a6070] focus:outline-none focus:border-[#00d4ff]/50"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-xs text-[#8b92a8] mb-1.5 block">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5a6070]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#dee2f5] placeholder:text-[#5a6070] focus:outline-none focus:border-[#00d4ff]/50"
                />
              </div>
            </div>

            <div>
              <label className="text-xs text-[#8b92a8] mb-1.5 block">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5a6070]" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
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

            {!isLogin && (
              <div>
                <label className="text-xs text-[#8b92a8] mb-1.5 block">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5a6070]" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-4 py-2.5 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#dee2f5] placeholder:text-[#5a6070] focus:outline-none focus:border-[#00d4ff]/50"
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-[#00d4ff] text-[#0a0e17] rounded-lg font-bold text-sm hover:brightness-110 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {isLogin ? "Signing in..." : "Creating account..."}
                </>
              ) : (
                <>
                  {isLogin ? "Sign In" : "Create Account"}
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-[#5a6070] mt-6">
          EdgeIQ — AI Quant Intelligence for Prediction Markets
        </p>
      </div>
    </div>
  );
};

export default AuthPage;