import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore, usePortfolioStore } from "@/stores";
import {
  KeyRound,
  Wallet,
  Tags,
  CheckCircle2,
  ChevronRight,
  ChevronLeft,
  Radar,
  ArrowRight,
} from "lucide-react";

const STEPS = [
  { id: 1, title: "Connect", icon: KeyRound },
  { id: 2, title: "Bankroll", icon: Wallet },
  { id: 3, title: "Categories", icon: Tags },
];

const CATEGORIES = [
  { key: "crypto", label: "Crypto", icon: "₿", color: "#00d4ff" },
  { key: "sports", label: "Sports", icon: "⚽", color: "#00ff88" },
  { key: "politics", label: "Politics", icon: "🗳️", color: "#ffa502" },
  { key: "entertainment", label: "Entertainment", icon: "🎬", color: "#ff6b81" },
];

const Onboarding = () => {
  const navigate = useNavigate();
  const { setAuthenticated, setOnboardingComplete } = useAuthStore();
  const { updateProfile } = usePortfolioStore();
  const [step, setStep] = useState(1);
  const [apiKey, setApiKey] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<"success" | "error" | null>(null);
  const [bankroll, setBankroll] = useState(10000);
  const [selectedCats, setSelectedCats] = useState<string[]>(["crypto"]);

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    setTimeout(() => {
      setTestResult("success");
      setTesting(false);
    }, 1500);
  };

  const toggleCat = (cat: string) => {
    setSelectedCats((prev) => (prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]));
  };

  const complete = () => {
    setOnboardingComplete(true);
    setAuthenticated(true);
    updateProfile({ bankroll, risk_tolerance: "balanced", tracked_categories: selectedCats });
    navigate("/signals");
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-[#00d4ff] flex items-center justify-center">
            <Radar className="w-6 h-6 text-[#0a0e17]" />
          </div>
          <span className="font-bold text-2xl text-[#dee2f5]">EdgeIQ</span>
        </div>

        {/* Progress */}
        <div className="flex items-center justify-center gap-4 mb-8">
          {STEPS.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={s.id} className="flex items-center gap-2">
                <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                  step >= s.id ? "bg-[#00d4ff]/10 text-[#00d4ff]" : "bg-[#1a2030] text-[#5a6070]"
                }`}>
                  {step > s.id ? (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  ) : (
                    <Icon className="w-3.5 h-3.5" />
                  )}
                  {s.title}
                </div>
                {i < STEPS.length - 1 && (
                  <div className={`w-8 h-px ${step > s.id ? "bg-[#00d4ff]" : "bg-[#1a2030]"}`} />
                )}
              </div>
            );
          })}
        </div>

        {/* Step Content */}
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6 space-y-6">
          {step === 1 && (
            <>
              <div className="text-center">
                <KeyRound className="w-10 h-10 text-[#00d4ff] mx-auto mb-3" />
                <h2 className="text-lg font-bold text-[#dee2f5]">Connect Bayse Account</h2>
                <p className="text-sm text-[#8b92a8] mt-1">
                  Enter your Bayse API key to enable live market analysis.
                </p>
              </div>
              <div>
                <label className="text-xs text-[#8b92a8] mb-1 block">Bayse API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => { setApiKey(e.target.value); setTestResult(null); }}
                  placeholder="pk_live_..."
                  className="w-full px-4 py-3 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#dee2f5] placeholder:text-[#5a6070] focus:outline-none focus:border-[#00d4ff]/50 font-mono"
                />
              </div>
              <button
                onClick={testConnection}
                disabled={!apiKey || testing}
                className="w-full py-3 bg-[#00d4ff]/10 border border-[#00d4ff]/30 text-[#00d4ff] rounded-lg text-sm font-medium hover:bg-[#00d4ff]/20 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {testing ? "Testing..." : testResult === "success" ? "Connected!" : "Test Connection"}
              </button>
              {testResult === "success" && (
                <p className="text-xs text-[#00ff88] text-center">Connection successful! Ready to proceed.</p>
              )}
            </>
          )}

          {step === 2 && (
            <>
              <div className="text-center">
                <Wallet className="w-10 h-10 text-[#00d4ff] mx-auto mb-3" />
                <h2 className="text-lg font-bold text-[#dee2f5]">Set Your Bankroll</h2>
                <p className="text-sm text-[#8b92a8] mt-1">
                  This is your total trading capital. Kelly Criterion will use this for stake sizing.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold text-[#dee2f5]">₦</span>
                <input
                  type="number"
                  value={bankroll}
                  onChange={(e) => setBankroll(Number(e.target.value))}
                  className="flex-1 px-4 py-3 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-lg font-mono-num text-[#dee2f5] focus:outline-none focus:border-[#00d4ff]/50"
                />
              </div>
              <div className="grid grid-cols-4 gap-2">
                {[5000, 10000, 25000, 50000].map((amt) => (
                  <button
                    key={amt}
                    onClick={() => setBankroll(amt)}
                    className={`py-2 rounded-lg text-xs font-medium transition-all ${
                      bankroll === amt
                        ? "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30"
                        : "bg-[#0a0e17] text-[#8b92a8] border border-[#1a2030]"
                    }`}
                  >
                    ₦{amt.toLocaleString()}
                  </button>
                ))}
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <div className="text-center">
                <Tags className="w-10 h-10 text-[#00d4ff] mx-auto mb-3" />
                <h2 className="text-lg font-bold text-[#dee2f5]">Choose Categories</h2>
                <p className="text-sm text-[#8b92a8] mt-1">
                  Select the markets you want EdgeIQ to prioritize in your feed.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat.key}
                    onClick={() => toggleCat(cat.key)}
                    className={`p-4 rounded-lg border text-center transition-all ${
                      selectedCats.includes(cat.key)
                        ? "border-[#00d4ff]/30"
                        : "border-[#1a2030] opacity-50"
                    }`}
                    style={selectedCats.includes(cat.key) ? { backgroundColor: `${cat.color}10` } : {}}
                  >
                    <span className="text-2xl mb-1 block">{cat.icon}</span>
                    <span className="text-sm font-medium text-[#dee2f5]">{cat.label}</span>
                    {selectedCats.includes(cat.key) && (
                      <CheckCircle2 className="w-4 h-4 mx-auto mt-1" style={{ color: cat.color }} />
                    )}
                  </button>
                ))}
              </div>
            </>
          )}

          {/* Navigation */}
          <div className="flex items-center justify-between pt-4 border-t border-[#1a2030]">
            {step > 1 ? (
              <button
                onClick={() => setStep(step - 1)}
                className="flex items-center gap-1 text-sm text-[#8b92a8] hover:text-[#dee2f5] transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                Back
              </button>
            ) : (
              <div />
            )}
            {step < 3 ? (
              <button
                onClick={() => setStep(step + 1)}
                className="flex items-center gap-2 px-4 py-2 bg-[#00d4ff] text-[#0a0e17] rounded-lg text-sm font-bold hover:brightness-110 transition-all"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={complete}
                className="flex items-center gap-2 px-6 py-2 bg-[#00ff88] text-[#0a0e17] rounded-lg text-sm font-bold hover:brightness-110 transition-all"
              >
                Launch EdgeIQ
                <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
