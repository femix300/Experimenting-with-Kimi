import { useEffect, useState, memo, useCallback } from "react";
import { usePortfolioStore } from "@/stores";
import { getProfile, getTrades, getAnalytics, getQPI, closeTrade } from "@/lib/api";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";
import {
  Wallet,
  Target,
  Loader2,
  Award,
  Activity,
  BarChart3,
  CheckCircle2,
  XCircle,
} from "lucide-react";

const COLORS = ["#00ff88", "#ff4757"];

const StatCard = memo(({ label, value, color = "text-[#dee2f5]" }: { label: string; value: string; color?: string }) => (
  <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
    <p className="text-xs text-[#8b92a8] uppercase mb-1">{label}</p>
    <p className={`text-xl font-bold font-mono-num ${color}`}>{value}</p>
  </div>
));
StatCard.displayName = "StatCard";

const Portfolio = () => {
  const { profile, openTrades, closedTrades, analytics, setProfile, setTrades, setAnalytics } = usePortfolioStore();
  const [loading, setLoading] = useState(true);
  const [qpi, setQpi] = useState<{ score: number; trend: string; components: Record<string, number> } | null>(null);
  const [resolvingTrade, setResolvingTrade] = useState<{ id: string; outcome: "YES" | "NO" } | null>(null);
  const [resolveToast, setResolveToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const [profileRes, tradesRes, analyticsRes] = await Promise.all([
          getProfile(),
          getTrades(),
          getAnalytics(),
        ]);
        if (profileRes.success) setProfile(profileRes.profile);
        if (tradesRes.success) setTrades(tradesRes.trades);
        if (analyticsRes.success) setAnalytics(analyticsRes.analytics);
      } catch { /* ignore */ }
      getQPI().then(res => { if (res?.success) setQpi(res.qpi); }).catch(() => {});
      setLoading(false);
    };
    fetch();
  }, []);

  const handleResolve = useCallback(async (tradeId: string, outcome: "YES" | "NO") => {
    setResolvingTrade({ id: tradeId, outcome });
    try {
      const exitPrice = outcome === "YES" ? 1.0 : 0.0;
      const res = await closeTrade(tradeId, exitPrice);
      if (res.success) {
        setResolveToast({ message: `Trade resolved as ${outcome === "YES" ? "WIN 🎉" : "LOSS"}`, type: outcome === "YES" ? "success" : "error" });
        // Refresh portfolio data
        const [profileRes, tradesRes, analyticsRes] = await Promise.all([getProfile(), getTrades(), getAnalytics()]);
        if (profileRes.success) setProfile(profileRes.profile);
        if (tradesRes.success) setTrades(tradesRes.trades);
        if (analyticsRes.success) setAnalytics(analyticsRes.analytics);
        getQPI().then(r => { if (r?.success) setQpi(r.qpi); }).catch(() => {});
      } else {
        setResolveToast({ message: "Failed to resolve trade", type: "error" });
      }
    } catch {
      setResolveToast({ message: "Failed to resolve trade", type: "error" });
    } finally {
      setResolvingTrade(null);
      setTimeout(() => setResolveToast(null), 4000);
    }
  }, [setProfile, setTrades, setAnalytics]);

  const pnlData = closedTrades.map((_t, i) => ({
    trade: i + 1,
    cumulative: Number(closedTrades.slice(0, i + 1).reduce((sum, tr) => sum + (tr.pnl || 0), 0).toFixed(2)),
  }));

  const winLossData = [
    { name: "Wins", value: analytics?.winning_trades || 0 },
    { name: "Losses", value: (analytics?.losing_trades || 0) },
  ];

  const qpiScore = qpi?.score ?? Math.min(100, Math.round(
    ((analytics?.win_rate || 0) * 0.4 +
    (Math.max(0, analytics?.sharpe_ratio || 0) * 20) * 0.3 +
    (closedTrades.filter((t) => t.kelly_compliant).length / Math.max(1, closedTrades.length) * 100) * 0.3)
  ));

  const bankrollFormatted = `₦${(profile?.bankroll || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const totalPnl = analytics?.total_pnl || 0;
  const totalPnlFormatted = `${totalPnl >= 0 ? "+" : ""}₦${Math.abs(totalPnl).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const winRateFormatted = `${Number(analytics?.win_rate || 0).toFixed(1)}%`;
  const sharpeFormatted = analytics?.sharpe_ratio ? Number(analytics.sharpe_ratio).toFixed(2) : "N/A";

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-10 h-10 text-[#00d4ff] animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Resolve Toast */}
      {resolveToast && (
        <div className={`fixed bottom-6 right-6 z-[9999] flex items-center gap-3 px-5 py-4 rounded-xl shadow-2xl border ${resolveToast.type === "success" ? "bg-[#0a2e1a] border-[#00ff88]/30 text-[#00ff88]" : "bg-[#2e0a0a] border-[#ff4757]/30 text-[#ff4757]"}`}>
          {resolveToast.type === "success" ? <CheckCircle2 className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
          <span className="text-sm text-[#dee2f5]">{resolveToast.message}</span>
        </div>
      )}
      <div>
        <h1 className="text-2xl font-bold text-[#dee2f5] flex items-center gap-2">
          <Wallet className="w-6 h-6 text-[#00d4ff]" />
          Portfolio Analytics
        </h1>
        <p className="text-sm text-[#8b92a8] mt-1">Track performance, PnL, and decision quality</p>
      </div>

      {/* Hero Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Bankroll" value={bankrollFormatted} />
        <StatCard
          label="Total PnL"
          value={totalPnlFormatted}
          color={totalPnl >= 0 ? "text-[#00ff88]" : "text-[#ff4757]"}
        />
        <StatCard label="Win Rate" value={winRateFormatted} color="text-[#00d4ff]" />
        <StatCard label="Sharpe Ratio" value={sharpeFormatted} color="text-[#ffa502]" />
      </div>

      {/* QPI Score */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-[#dee2f5] flex items-center gap-2">
            <Award className="w-4 h-4 text-[#00d4ff]" />
            Quant Performance Index (QPI)
          </h3>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#00ff88]" />
            <span className="text-xs text-[#8b92a8]">Trending Up</span>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="relative w-24 h-24">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
              <path className="text-[#1a2030]" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
              <path className="text-[#00d4ff]" strokeDasharray={`${qpiScore}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-lg font-bold text-[#dee2f5]">{qpiScore}</span>
            </div>
          </div>
          <div className="flex-1 space-y-2">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#8b92a8]">Win Rate</span>
                <span className="text-[#00d4ff]">{qpi?.components?.win_rate ?? Math.round(analytics?.win_rate || 0)}%</span>
              </div>
              <div className="h-1.5 bg-[#1a2030] rounded-full overflow-hidden">
                <div className="h-full bg-[#00d4ff] rounded-full" style={{ width: `${Math.min(100, qpi?.components?.win_rate || (analytics?.win_rate || 0))}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#8b92a8]">EV Accuracy</span>
                <span className="text-[#00ff88]">{qpi?.components?.ev_accuracy ?? 50}%</span>
              </div>
              <div className="h-1.5 bg-[#1a2030] rounded-full overflow-hidden">
                <div className="h-full bg-[#00ff88] rounded-full" style={{ width: `${Math.min(100, qpi?.components?.ev_accuracy || 50)}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#8b92a8]">Kelly Compliance</span>
                <span className="text-[#ffa502]">{qpi?.components?.kelly_compliance ?? Math.round(closedTrades.filter((t) => t.kelly_compliant).length / Math.max(1, closedTrades.length) * 100)}%</span>
              </div>
              <div className="h-1.5 bg-[#1a2030] rounded-full overflow-hidden">
                <div className="h-full bg-[#ffa502] rounded-full" style={{ width: `${Math.min(100, qpi?.components?.kelly_compliance || (closedTrades.filter((t) => t.kelly_compliant).length / Math.max(1, closedTrades.length) * 100))}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PnL Curve */}
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
          <h3 className="text-sm font-semibold text-[#dee2f5] mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-[#00d4ff]" />
            Running PnL
          </h3>
          <div className="h-[250px]">
            {pnlData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={pnlData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" />
                  <XAxis dataKey="trade" stroke="#5a6070" fontSize={11} />
                  <YAxis stroke="#5a6070" fontSize={11} tickFormatter={(v) => `₦${Number(v).toFixed(0)}`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#131a2b", border: "1px solid #1a2030", borderRadius: 8 }}
                    formatter={(value: number) => [`₦${Number(value).toFixed(2)}`, "Cumulative PnL"]}
                  />
                  <Line type="monotone" dataKey="cumulative" stroke="#00d4ff" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-[#5a6070]">No closed trades yet</div>
            )}
          </div>
        </div>

        {/* Win Rate Donut */}
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
          <h3 className="text-sm font-semibold text-[#dee2f5] mb-4">Win Rate Distribution</h3>
          <div className="h-[250px]">
            {winLossData.some((d) => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={winLossData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={4} dataKey="value">
                    {winLossData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: "#131a2b", border: "1px solid #1a2030", borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-[#5a6070]">No trades yet</div>
            )}
          </div>
          <div className="flex justify-center gap-4 mt-2">
            {winLossData.map((d, i) => (
              <div key={d.name} className="flex items-center gap-1 text-xs">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i] }} />
                <span className="text-[#8b92a8]">{d.name}: {d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Open Positions */}
      {openTrades.length > 0 && (
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] overflow-hidden">
          <div className="p-4 border-b border-[#1a2030]">
            <h3 className="text-sm font-semibold text-[#dee2f5]">Open Positions ({openTrades.length})</h3>
          </div>
          <div className="divide-y divide-[#1a2030]">
            {openTrades.map((trade) => (
              <div key={trade.id} className="p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[#dee2f5] truncate">{trade.market_title}</p>
                  <p className="text-xs text-[#8b92a8] mt-0.5">
                    {trade.direction} · ₦{Number(trade.stake_amount).toLocaleString("en-US", { minimumFractionDigits: 2 })} · Entry: ₦{Number(trade.entry_price).toFixed(2)}
                  </p>
                  <p className={`text-xs mt-0.5 ${trade.kelly_compliant ? "text-[#00ff88]" : "text-[#ff4757]"}`}>
                    Kelly {trade.kelly_compliant ? "Compliant ✓" : "Non-Compliant"}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <p className="text-xs text-[#8b92a8] mr-1">Outcome:</p>
                  <button
                    onClick={() => handleResolve(trade.id, "YES")}
                    disabled={resolvingTrade?.id === trade.id}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/30 rounded-lg text-xs font-bold hover:bg-[#00ff88]/20 transition-all disabled:opacity-50"
                  >
                    {resolvingTrade?.id === trade.id && resolvingTrade?.outcome === "YES" ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
                    YES
                  </button>
                  <button
                    onClick={() => handleResolve(trade.id, "NO")}
                    disabled={resolvingTrade?.id === trade.id}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-[#ff4757]/10 text-[#ff4757] border border-[#ff4757]/30 rounded-lg text-xs font-bold hover:bg-[#ff4757]/20 transition-all disabled:opacity-50"
                  >
                    {resolvingTrade?.id === trade.id && resolvingTrade?.outcome === "NO" ? <Loader2 className="w-3 h-3 animate-spin" /> : <XCircle className="w-3 h-3" />}
                    NO
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Performance Review */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
        <h3 className="text-sm font-semibold text-[#dee2f5] mb-4 flex items-center gap-2">
          <Target className="w-4 h-4 text-[#00d4ff]" />
          AI Performance Review
        </h3>
        <div className="bg-[#0a0e17] rounded-lg p-4">
          <p className="text-sm text-[#8b92a8] leading-relaxed">
            Your last {analytics?.total_trades || 0} trades show a {Number(analytics?.win_rate || 0).toFixed(0)}% win rate
            with {analytics?.total_pnl && analytics.total_pnl > 0 ? "positive" : analytics?.total_pnl && analytics.total_pnl < 0 ? "negative" : "no closed"} total PnL.
            {closedTrades.filter((t) => !t.kelly_compliant).length > 0
              ? ` You over-staked ${closedTrades.filter((t) => !t.kelly_compliant).length} times — Kelly discipline is your biggest improvement area.`
              : closedTrades.length > 0 ? " Excellent Kelly compliance. Keep it up." : " Open trades pending resolution."}
          </p>
        </div>
      </div>
    </div>
  );
};

export default Portfolio;