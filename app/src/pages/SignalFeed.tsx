import { useEffect, useState, useCallback, memo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useSignalStore, useMarketStore } from "@/stores";
import { getActiveSignals, getSignalStats, clearAllSignalsDb } from "@/lib/api";
import {
  Zap,
  TrendingUp,
  TrendingDown,
  Minus,
  Filter,
  ChevronRight,
  Loader2,
  Bell,
  X,
  Trash2,
  Tag,
  Search,
} from "lucide-react";
import type { Signal } from "@/types";
import { CATEGORY_COLORS, CATEGORY_LABELS } from "@/types";

const TOASTS: Record<string, string> = {
  edge: "Edge: The gap between market-implied probability and AI-estimated true probability. A 25% edge means the market is undervaluing this outcome by 25 percentage points.",
  ev: "Expected Value (EV): The average profit per unit staked if you repeated this trade many times. Positive EV = statistically profitable.",
  kelly: "Kelly Criterion: A mathematical formula for optimal stake sizing. It tells you what percentage of your bankroll to bet based on your edge.",
  momentum: "Momentum Score: Measures price trend direction and strength using linear regression. +100 = strongly bullish, -100 = strongly bearish.",
  confidence: "Confidence: How certain the AI is about its probability estimate. Higher confidence = more reliable signal.",
};

const SignalCard = memo(({ signal, onClick }: { signal: Signal; onClick: () => void }) => {
  const edge = signal.edge_score;
  const edgeColor = edge >= 20 ? "text-[#00ff88]" : edge >= 10 ? "text-[#ffa502]" : "text-[#ff4757]";
  const label = signal.direction === "BUY" ? "BUY" : signal.direction === "SELL" ? "AVOID" : "WAIT";
  const labelColor = signal.direction === "BUY" ? "text-[#00ff88]" : signal.direction === "SELL" ? "text-[#ff4757]" : "text-[#ffa502]";
  const category = (signal.category || "other") as keyof typeof CATEGORY_COLORS;
  const catColor = CATEGORY_COLORS[category] || CATEGORY_COLORS.other;
  const catLabel = CATEGORY_LABELS[category] || "Other";

  return (
    <div
      onClick={onClick}
      className="group relative bg-[#131a2b] border border-[#1a2030] rounded-xl p-5 hover:border-[#00d4ff]/30 hover:shadow-[0_0_20px_rgba(0,212,255,0.08)] transition-all cursor-pointer"
    >
      {/* Category Badge */}
      <div className="absolute top-3 left-3">
        <span
          className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
          style={{ backgroundColor: `${catColor}15`, color: catColor }}
        >
          {catLabel}
        </span>
      </div>

      <div className="flex items-start justify-between mb-4 pt-6">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-[#dee2f5] text-sm leading-snug line-clamp-2 mb-1">
            {signal.market_title}
          </h3>
          <div className="flex items-center gap-2 text-xs text-[#8b92a8]">
            <span className="font-mono-num">ID: {signal.market_event_id?.slice(0, 8)}</span>
          </div>
        </div>
        <div className="flex items-center gap-2 ml-3">
          <div className={`w-2 h-2 rounded-full animate-pulse-dot ${edge >= 20 ? "bg-[#00ff88]" : "bg-[#ffa502]"}`} />
          <span className={`text-xs font-bold uppercase ${labelColor}`}>{label}</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-[#0a0e17] rounded-lg p-3" data-tooltip={TOASTS.edge}>
          <p className="text-[10px] uppercase text-[#8b92a8] mb-1">Edge</p>
          <p className={`text-lg font-bold font-mono-num ${edgeColor}`}>
            {edge > 0 ? "+" : ""}{edge.toFixed(1)}%
          </p>
        </div>
        <div className="bg-[#0a0e17] rounded-lg p-3" data-tooltip={TOASTS.ev}>
          <p className="text-[10px] uppercase text-[#8b92a8] mb-1">EV</p>
          <p className={`text-lg font-bold font-mono-num ${signal.expected_value > 0 ? "text-[#00ff88]" : "text-[#ff4757]"}`}>
            {signal.expected_value > 0 ? "+" : ""}₦{Number(signal.expected_value).toFixed(2)}
          </p>
        </div>
        <div className="bg-[#0a0e17] rounded-lg p-3" data-tooltip={TOASTS.kelly}>
          <p className="text-[10px] uppercase text-[#8b92a8] mb-1">Kelly</p>
          <p className="text-lg font-bold font-mono-num text-[#00d4ff]">
            {Number(signal.kelly_percentage).toFixed(1)}%
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <span className="text-[#8b92a8]">
            Market: <span className="text-[#dee2f5] font-mono-num">{Number(signal.market_probability).toFixed(1)}%</span>
          </span>
          <span className="text-[#8b92a8]">
            AI: <span className="text-[#00d4ff] font-mono-num">{Number(signal.ai_probability).toFixed(1)}%</span>
          </span>
        </div>
        <div className="flex items-center gap-1 text-[#00d4ff]">
          <span className="text-xs">Deep Dive</span>
          <ChevronRight className="w-3 h-3" />
        </div>
      </div>

      {signal.quant_snapshot && (
        <div className="mt-3 pt-3 border-t border-[#1a2030] flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1" data-tooltip={TOASTS.momentum}>
            {signal.quant_snapshot.momentum_direction === "bullish" ? (
              <TrendingUp className="w-3 h-3 text-[#00ff88]" />
            ) : signal.quant_snapshot.momentum_direction === "bearish" ? (
              <TrendingDown className="w-3 h-3 text-[#ff4757]" />
            ) : (
              <Minus className="w-3 h-3 text-[#8b92a8]" />
            )}
            <span className="text-[#8b92a8]">Mo: {Number(signal.quant_snapshot.momentum_score).toFixed(1)}</span>
          </div>
          <div className="flex items-center gap-1" data-tooltip={TOASTS.confidence}>
            <span className="text-[#8b92a8]">Conf: {signal.confidence}%</span>
          </div>
        </div>
      )}

      {/* Full AI Reasoning */}
      {signal.reasoning && (
        <div className="mt-3 pt-3 border-t border-[#1a2030]">
          <p className="text-xs text-[#8b92a8] mb-1 flex items-center gap-1">
            <Tag className="w-3 h-3" /> AI Reasoning
          </p>
          <p className="text-xs text-[#5a6070] leading-relaxed line-clamp-3">{signal.reasoning}</p>
        </div>
      )}
    </div>
  );
});
SignalCard.displayName = "SignalCard";

const SignalFeed = () => {
  const navigate = useNavigate();
  const { activeSignals, loading, error, minEdgeFilter, categoryFilter, setActiveSignals, setLoading, setError, setMinEdgeFilter, setCategoryFilter, clearAllSignals, cleared, setSelectedSignal } = useSignalStore();
  const clearedRef = useRef(cleared);
  useEffect(() => { clearedRef.current = cleared; }, [cleared]);
  const { setSelectedMarket, setQuantMetrics, setAiAnalysis } = useMarketStore();
  const [stats, setStats] = useState<{ total_active: number; by_direction: Record<string, number>; by_strength: Record<string, number>; edge_stats?: { avg_edge: number; max_edge: number; min_edge: number }; confidence_stats?: { avg_confidence: number; max_confidence: number; min_confidence: number } } | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "success" | "info" } | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [searchQuery, setSearchQuery] = useState("");

  const fetchSignals = useCallback(async () => {
    if (clearedRef.current) return;
    useSignalStore.setState({ cleared: false });
    setLoading(true);
    setError(null);
    try {
      const [signalsRes, statsRes] = await Promise.all([
        getActiveSignals(50, minEdgeFilter),
        getSignalStats(),
      ]);
      if (signalsRes.success) {
        let signals = signalsRes.signals;
        if (categoryFilter) {
          signals = signals.filter((s) => (s.category || "other").toLowerCase() === categoryFilter.toLowerCase());
        }
        setActiveSignals(signals);
        const highEdge = signals.find((s) => s.edge_score > 20);
        if (highEdge) {
          setToast({ message: `High-edge signal: ${highEdge.market_title.slice(0, 30)}... (+${Number(highEdge.edge_score).toFixed(0)}%)`, type: "success" });
          setTimeout(() => setToast(null), 5000);
        }
      }
      if (statsRes.success) setStats(statsRes.stats);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch signals");
    } finally {
      setLoading(false);
    }
  }, [minEdgeFilter, categoryFilter, setActiveSignals, setLoading, setError]);

  useEffect(() => {
    if (cleared) return;
    fetchSignals();
    const interval = setInterval(fetchSignals, 60000);
    return () => clearInterval(interval);
  }, [fetchSignals]);

  const handleSignalClick = (signal: Signal) => {
    const marketId = signal.market_event_id || signal.market_id;
    
    // Pre-populate basic market data from the signal
    setSelectedMarket({
      title: signal.market_title,
      bayse_event_id: marketId,
      current_price: signal.market_probability / 100,
      implied_probability: signal.market_probability,
      category: signal.category || "other",
    } as any);
    
    setQuantMetrics({
      momentum_score: signal.quant_snapshot?.momentum_score || 0,
      momentum_direction: signal.quant_snapshot?.momentum_direction || "neutral",
      volume_acceleration: signal.quant_snapshot?.volume_acceleration || 1,
      order_book_bias: signal.quant_snapshot?.order_book_bias || "neutral",
      bid_ask_spread: 0,
    } as any);
    
    setAiAnalysis({
      market_id: marketId,
      market_title: signal.market_title,
      probability: signal.ai_probability,
      confidence: signal.confidence,
      reasoning: signal.reasoning || "",
      sources: "",
      model_used: signal.model_used || "gemini-1.5-flash",
      search_grounding_used: true,
      analyzed_at: signal.created_at,
    } as any);
    
    setSelectedSignal(signal);
    sessionStorage.setItem("cachedSignal", JSON.stringify(signal));
    sessionStorage.setItem("cachedMarket", JSON.stringify({ title: signal.market_title, bayse_event_id: marketId, current_price: signal.market_probability / 100, implied_probability: signal.market_probability, category: signal.category || "other" }));
    sessionStorage.setItem("cachedAiAnalysis", JSON.stringify({
      market_id: marketId,
      market_title: signal.market_title,
      probability: signal.ai_probability,
      confidence: signal.confidence,
      reasoning: signal.reasoning || "",
      sources: "",
      model_used: signal.model_used || "gemini-1.5-flash",
      search_grounding_used: true,
      analyzed_at: signal.created_at,
    }));
    sessionStorage.setItem("cachedQuantMetrics", JSON.stringify({
      momentum_score: signal.quant_snapshot?.momentum_score || 0,
      momentum_direction: signal.quant_snapshot?.momentum_direction || "neutral",
      volume_acceleration: signal.quant_snapshot?.volume_acceleration || 1,
      order_book_bias: signal.quant_snapshot?.order_book_bias || "neutral",
      bid_ask_spread: 0,
    }));
    sessionStorage.setItem("cachedMarketId", marketId);
    sessionStorage.setItem("fromSignal", "true");
    navigate(`/market/${marketId}`);
  };

  const handleClearAll = () => {
    clearAllSignalsDb().then(() => clearAllSignals());
    setStats(null);
    setToast(null);
    setToast({ message: "All signals cleared", type: "info" });
    setTimeout(() => setToast(null), 3000);
  };

  const categories = ["crypto", "sports", "politics", "entertainment", "other"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#dee2f5] flex items-center gap-2">
            <Zap className="w-6 h-6 text-[#00d4ff]" />
            Signal Feed
          </h1>
          <p className="text-sm text-[#8b92a8] mt-1">
            Live edge opportunities from Bayse markets · Updated {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {activeSignals.length > 0 && (
            <button
              onClick={handleClearAll}
              className="flex items-center gap-2 px-4 py-2 bg-[#ff4757]/10 text-[#ff4757] rounded-lg text-sm font-medium hover:bg-[#ff4757]/20 transition-all border border-[#ff4757]/30"
            >
              <Trash2 className="w-4 h-4" />
              Clear All
            </button>
          )}
          <button
            onClick={fetchSignals}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-[#00d4ff]/10 text-[#00d4ff] rounded-lg text-sm font-medium hover:bg-[#00d4ff]/20 transition-all disabled:opacity-50"
          >
            <Loader2 className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div className={`flex items-center gap-3 px-4 py-3 rounded-lg ${toast.type === "success" ? "bg-[#00ff88]/10 border border-[#00ff88]/30" : "bg-[#00d4ff]/10 border border-[#00d4ff]/30"}`}>
          <Bell className={`w-4 h-4 ${toast.type === "success" ? "text-[#00ff88]" : "text-[#00d4ff]"}`} />
          <span className="text-sm text-[#dee2f5]">{toast.message}</span>
          <button onClick={() => setToast(null)} className="ml-auto">
            <X className="w-4 h-4 text-[#8b92a8]" />
          </button>
        </div>
      )}

      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
            <p className="text-xs text-[#8b92a8] uppercase">Active Signals</p>
            <p className="text-2xl font-bold text-[#dee2f5] font-mono-num">{stats.total_active}</p>
          </div>
          <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
            <p className="text-xs text-[#8b92a8] uppercase">BUY Signals</p>
            <p className="text-2xl font-bold text-[#00ff88] font-mono-num">{stats.by_direction?.BUY || 0}</p>
          </div>
          <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
            <p className="text-xs text-[#8b92a8] uppercase">Strong Edge</p>
            <p className="text-2xl font-bold text-[#00d4ff] font-mono-num">{stats.by_strength?.strong || 0}</p>
          </div>
          <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
            <p className="text-xs text-[#8b92a8] uppercase">Avg Edge</p>
            <p className="text-2xl font-bold text-[#ffa502] font-mono-num">
              {Number(stats.edge_stats?.avg_edge || 0).toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-[#131a2b] rounded-xl p-4 border border-[#1a2030]">
        <div className="flex items-center gap-2 text-[#8b92a8]">
          <Filter className="w-4 h-4" />
          <span className="text-sm">Filters</span>
        </div>
        <div className="relative min-w-[200px] flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8b92a8]" />
          <input
            type="text"
            placeholder="Search signals..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#dee2f5] placeholder:text-[#5a6070] focus:outline-none focus:border-[#00d4ff]/50"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(categoryFilter === cat ? null : cat)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium capitalize transition-all ${
                categoryFilter === cat
                  ? "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30"
                  : "bg-[#0a0e17] text-[#8b92a8] border border-[#1a2030] hover:border-[#2a3040]"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <span className="text-xs text-[#8b92a8]">Min Edge</span>
          <input
            type="range"
            min="0"
            max="30"
            step="5"
            value={minEdgeFilter}
            onChange={(e) => setMinEdgeFilter(Number(e.target.value))}
            className="w-24 accent-[#00d4ff]"
          />
          <span className="text-xs font-mono-num text-[#00d4ff] w-8">{minEdgeFilter}%</span>
        </div>
      </div>

      {/* Signals Grid */}
      {loading && activeSignals.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-[#131a2b] rounded-xl p-5 border border-[#1a2030] animate-pulse">
              <div className="h-4 bg-[#1a2030] rounded w-3/4 mb-4" />
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="h-12 bg-[#1a2030] rounded" />
                <div className="h-12 bg-[#1a2030] rounded" />
                <div className="h-12 bg-[#1a2030] rounded" />
              </div>
              <div className="h-3 bg-[#1a2030] rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : error && activeSignals.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-[#ff4757] mb-2">{error}</p>
          <p className="text-sm text-[#8b92a8]">Retrying in 30 seconds...</p>
          <button
            onClick={fetchSignals}
            className="mt-4 px-4 py-2 bg-[#00d4ff]/10 text-[#00d4ff] rounded-lg text-sm"
          >
            Retry Now
          </button>
        </div>
      ) : activeSignals.length === 0 ? (
        <div className="text-center py-16 bg-[#131a2b] rounded-xl border border-[#1a2030]">
          <Zap className="w-12 h-12 text-[#1a2030] mx-auto mb-4" />
          <p className="text-[#8b92a8] text-lg">Scanning Bayse markets for edge opportunities...</p>
          <p className="text-sm text-[#5a6070] mt-2">No signals match your current filters</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {activeSignals
            .filter((s) => !searchQuery || s.market_title.toLowerCase().includes(searchQuery.toLowerCase()))
            .sort((a, b) => b.edge_score - a.edge_score)
            .map((signal) => (
              <SignalCard
                key={signal.id}
                signal={signal}
                onClick={() => handleSignalClick(signal)}
              />
            ))}
        </div>
      )}
    </div>
  );
};

export default SignalFeed;