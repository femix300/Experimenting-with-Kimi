import { useState } from "react";
import { usePortfolioStore, useAuthStore } from "@/stores";
import { updateProfile as apiUpdateProfile } from "@/lib/api";
import {
  Settings as SettingsIcon,
  Wallet,
  Shield,
  Eye,
  Tag,
  Save,
  Info,
} from "lucide-react";

const TOOLTIPS: Record<string, string> = {
  bankroll: "Your total trading capital. Kelly Criterion stake recommendations are calculated as a percentage of this amount.",
  conservative: "Quarter Kelly: Stakes 25% of the full Kelly recommendation. Safest option with lower variance.",
  balanced: "Half Kelly: Stakes 50% of the full Kelly recommendation. Balanced risk and return.",
  aggressive: "Full Kelly: Stakes 100% of the Kelly recommendation. Highest expected growth but higher variance.",
  watchlist: "Pin up to 5 markets for priority alerts. These markets get highlighted in the Markets Explorer.",
  categories: "Select which market categories EdgeIQ should prioritize in your Signal Feed.",
};

const RISK_MODES = [
  { key: "conservative" as const, label: "Conservative", icon: Shield, desc: "1/4 Kelly · Lower risk" },
  { key: "balanced" as const, label: "Balanced", icon: Eye, desc: "1/2 Kelly · Optimal risk/return" },
  { key: "aggressive" as const, label: "Aggressive", icon: Wallet, desc: "Full Kelly · Max growth" },
];

const CATEGORIES = [
  { key: "crypto", label: "Crypto", icon: "₿" },
  { key: "sports", label: "Sports", icon: "⚽" },
  { key: "politics", label: "Politics", icon: "🗳️" },
  { key: "entertainment", label: "Entertainment", icon: "🎬" },
];

const Settings = () => {
  const { profile, updateProfile } = usePortfolioStore();
  const { logout } = useAuthStore();
  const [bankroll, setBankroll] = useState(profile?.bankroll || 10000);
  const [risk, setRisk] = useState<"conservative" | "balanced" | "aggressive">(profile?.risk_tolerance || "balanced");
  const [tracked, setTracked] = useState<string[]>(profile?.tracked_categories || ["crypto", "sports"]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiUpdateProfile({ bankroll, risk_tolerance: risk, tracked_categories: tracked });
      updateProfile({ bankroll, risk_tolerance: risk, tracked_categories: tracked });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch { /* ignore */ }
    setSaving(false);
  };

  const toggleCategory = (cat: string) => {
    setTracked((prev) => (prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#dee2f5] flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-[#00d4ff]" />
          Settings
        </h1>
        <p className="text-sm text-[#8b92a8] mt-1">Configure your EdgeIQ preferences</p>
      </div>

      {/* Bankroll */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
        <div className="flex items-center gap-2 mb-4">
          <Wallet className="w-4 h-4 text-[#00d4ff]" />
          <h3 className="text-sm font-semibold text-[#dee2f5]">Bankroll</h3>
          <Info className="w-3 h-3 text-[#5a6070] cursor-help" data-tooltip={TOOLTIPS.bankroll} />
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
        <div className="flex gap-2 mt-3">
          {[5000, 10000, 25000, 50000].map((amt) => (
            <button
              key={amt}
              onClick={() => setBankroll(amt)}
              className="px-3 py-1.5 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-xs text-[#8b92a8] hover:border-[#00d4ff]/30 hover:text-[#dee2f5] transition-all"
            >
              ₦{amt.toLocaleString()}
            </button>
          ))}
        </div>
      </div>

      {/* Risk Tolerance */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
        <h3 className="text-sm font-semibold text-[#dee2f5] mb-4">Risk Tolerance</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {RISK_MODES.map((mode) => {
            const Icon = mode.icon;
            return (
              <button
                key={mode.key}
                onClick={() => setRisk(mode.key)}
                className={`p-4 rounded-lg border text-left transition-all ${
                  risk === mode.key
                    ? "bg-[#00d4ff]/10 border-[#00d4ff]/30"
                    : "bg-[#0a0e17] border-[#1a2030] hover:border-[#2a3040]"
                }`}
                data-tooltip={TOOLTIPS[mode.key]}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Icon className={`w-4 h-4 ${risk === mode.key ? "text-[#00d4ff]" : "text-[#8b92a8]"}`} />
                  <span className={`text-sm font-medium ${risk === mode.key ? "text-[#00d4ff]" : "text-[#dee2f5]"}`}>
                    {mode.label}
                  </span>
                </div>
                <p className="text-xs text-[#8b92a8]">{mode.desc}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tracked Categories */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
        <div className="flex items-center gap-2 mb-4">
          <Tag className="w-4 h-4 text-[#00d4ff]" />
          <h3 className="text-sm font-semibold text-[#dee2f5]">Tracked Categories</h3>
          <Info className="w-3 h-3 text-[#5a6070] cursor-help" data-tooltip={TOOLTIPS.categories} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.key}
              onClick={() => toggleCategory(cat.key)}
              className={`p-3 rounded-lg border text-center transition-all ${
                tracked.includes(cat.key)
                  ? "bg-[#00d4ff]/10 border-[#00d4ff]/30 text-[#00d4ff]"
                  : "bg-[#0a0e17] border-[#1a2030] text-[#8b92a8] hover:border-[#2a3040]"
              }`}
            >
              <span className="text-lg mb-1 block">{cat.icon}</span>
              <span className="text-xs font-medium">{cat.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Save */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-6 py-3 bg-[#00d4ff] text-[#0a0e17] rounded-lg font-bold text-sm hover:brightness-110 transition-all disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          {saving ? "Saving..." : "Save Changes"}
        </button>
        {saved && (
          <span className="text-sm text-[#00ff88]">Settings saved successfully!</span>
        )}
      </div>

      {/* Sign Out */}
      <div className="pt-6 border-t border-[#1a2030]">
        <button
          onClick={logout}
          className="text-sm text-[#ff4757] hover:underline"
        >
          Sign Out
        </button>
      </div>
    </div>
  );
};

export default Settings;
