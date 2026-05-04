import { useEffect, useState, useCallback, memo } from "react";
import { useNavigate } from "react-router-dom";
import { useMarketStore, useSignalStore } from "@/stores";
import { getMarkets, scanMarkets } from "@/lib/api";
import { Loader2,
  Search,
  Grid3X3,
  List,
  SlidersHorizontal,
  ChevronRight,
  ArrowUpDown,
  Clock,
  Volume2,
  TrendingUp,
  X,
  Droplets,
} from "lucide-react";
import type { Market } from "@/types";

const CATEGORY_CONFIG = [
  { key: "crypto", label: "Crypto", color: "#00d4ff" },
  { key: "sports", label: "Sports", color: "#00ff88" },
  { key: "politics", label: "Politics", color: "#ffa502" },
  { key: "entertainment", label: "Entertainment", color: "#ff6b81" },
  { key: "other", label: "Other", color: "#a4b0be" },
];

const formatTimeRemaining = (hours?: number, status?: string) => {
  if (!hours || hours <= 0) {
    if (status === "open") return "Active";
    if (status === "resolved") return "Resolved";
    return "Closed";
  }
  const days = Math.floor(hours / 24);
  const hrs = Math.floor(hours % 24);
  if (days > 0) return `${days}d ${hrs}h`;
  return `${hrs}h`;
};

const formatVolume = (vol: number) => {
  if (vol >= 1e6) return `₦${(vol / 1e6).toFixed(1)}M`;
  if (vol >= 1e3) return `₦${(vol / 1e3).toFixed(1)}K`;
  return `₦${Math.round(vol).toLocaleString()}`;
};

const formatPrice = (price: number) => {
  return `₦${Number(price).toFixed(2)}`;
};

const formatProb = (prob: number) => {
  return `${Number(prob).toFixed(1)}%`;
};

const getLiquidityLabel = (liq: number) => {
  if (liq > 50000) return { label: "Deep", color: "text-[#00ff88]" };
  if (liq > 10000) return { label: "Moderate", color: "text-[#ffa502]" };
  return { label: "Thin", color: "text-[#ff4757]" };
};

const MarketCard = memo(({ market, onClick, hasEdge }: { market: Market; onClick: () => void; hasEdge?: boolean }) => {
  const cat = CATEGORY_CONFIG.find((c) => c.key === market.category) || CATEGORY_CONFIG[4];
  const liq = getLiquidityLabel(market.liquidity);
  const prob = market.implied_probability || (market.current_price || 0) * 100;

  return (
    <div
      onClick={onClick}
      className="group bg-[#131a2b] border border-[#1a2030] rounded-xl p-5 hover:border-[#00d4ff]/30 hover:shadow-[0_0_20px_rgba(0,212,255,0.08)] transition-all cursor-pointer relative overflow-hidden"
    >
      {hasEdge && (
        <div className="absolute top-3 right-3 px-2 py-0.5 bg-[#00ff88]/10 border border-[#00ff88]/30 rounded text-xs font-bold text-[#00ff88]">
          +{Number(market.edge_score).toFixed(0)}% Edge
        </div>
      )}
      <div className="flex items-start justify-between mb-3">
        <span
          className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
          style={{ backgroundColor: `${cat.color}15`, color: cat.color }}
        >
          {cat.label}
        </span>
      </div>
      <h3 className="font-semibold text-[#dee2f5] text-sm leading-snug line-clamp-2 min-h-[40px] mb-3">
        {market.title}
      </h3>
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-[#0a0e17] rounded-lg p-2">
          <p className="text-[10px] text-[#8b92a8] uppercase">Price</p>
          <p className="text-sm font-bold font-mono-num text-[#dee2f5]">{formatPrice(market.current_price || 0)}</p>
        </div>
        <div className="bg-[#0a0e17] rounded-lg p-2">
          <p className="text-[10px] text-[#8b92a8] uppercase">Implied Prob</p>
          <p className="text-sm font-bold font-mono-num text-[#00d4ff]">{formatProb(prob)}</p>
        </div>
      </div>
      <div className="flex items-center justify-between text-xs text-[#8b92a8]">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Volume2 className="w-3 h-3" />
            {formatVolume(market.total_volume || 0)}
          </span>
          <span className={`flex items-center gap-1 ${liq.color}`}>
            <Droplets className="w-3 h-3" />
            {liq.label}
          </span>
        </div>
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {formatTimeRemaining(market.time_remaining_hours, market.status)}
        </span>
      </div>
    </div>
  );
});
MarketCard.displayName = "MarketCard";

const MarketRow = memo(({ market, onClick, hasEdge }: { market: Market; onClick: () => void; hasEdge?: boolean }) => {
  const cat = CATEGORY_CONFIG.find((c) => c.key === market.category) || CATEGORY_CONFIG[4];
  const prob = market.implied_probability || (market.current_price || 0) * 100;

  return (
    <tr
      onClick={onClick}
      className="border-b border-[#1a2030] hover:bg-[#1a2030]/50 cursor-pointer transition-colors"
    >
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold" style={{ backgroundColor: `${cat.color}15`, color: cat.color }}>
            {cat.label}
          </span>
          <span className="text-sm text-[#dee2f5] line-clamp-1">{market.title}</span>
          {hasEdge && (
            <span className="px-1.5 py-0.5 bg-[#00ff88]/10 rounded text-[10px] text-[#00ff88] font-bold">
              +{Number(market.edge_score).toFixed(0)}%
            </span>
          )}
        </div>
      </td>
      <td className="py-3 px-4 text-sm font-mono-num text-[#dee2f5]">{formatPrice(market.current_price || 0)}</td>
      <td className="py-3 px-4 text-sm font-mono-num text-[#00d4ff]">{formatProb(prob)}</td>
      <td className="py-3 px-4 text-sm font-mono-num text-[#8b92a8]">{formatVolume(market.total_volume || 0)}</td>
      <td className="py-3 px-4 text-sm font-mono-num text-[#8b92a8]">{formatTimeRemaining(market.time_remaining_hours, market.status)}</td>
      <td className="py-3 px-4">
        <ChevronRight className="w-4 h-4 text-[#00d4ff]" />
      </td>
    </tr>
  );
});
MarketRow.displayName = "MarketRow";

const MarketsExplorer = () => {
  const navigate = useNavigate();
  const { filteredMarkets, markets, loading, error, viewMode, filters, setMarkets, setLoading, setError, setViewMode, setFilters } = useMarketStore();
  const { activeSignals } = useSignalStore();
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [scanning, setScanning] = useState(false);

  const handleScan = async () => {
    setScanning(true);
    try {
      await scanMarkets({ max_results: 100 });
      await fetchMarkets();
    } catch { /* ignore */ }
    setScanning(false);
  };

  const fetchMarkets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getMarkets({ status: "open", page_size: 100 });
      const seen = new Set<string>();
      const enriched = (res.results || [])
        .filter((m) => {
          if (seen.has(m.bayse_event_id)) return false;
          seen.add(m.bayse_event_id);
          return true;
        })
        .map((m) => {
        const signal = activeSignals.find((s) => s.market_id === m.bayse_event_id || s.market_event_id === m.bayse_event_id);
        return {
          ...m,
          edge_score: signal?.edge_score,
          time_remaining_hours: m.closes_at
            ? Math.max(0, (new Date(m.closes_at).getTime() - Date.now()) / 3600000)
            : undefined,
        };
      });
      setMarkets(enriched);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch markets");
    } finally {
      setLoading(false);
    }
  }, [activeSignals, setMarkets, setLoading, setError]);

  useEffect(() => {
    fetchMarkets();
  }, [fetchMarkets]);

  const activeFilterCount = [
    filters.categories.length > 0,
    filters.status !== "open",
    filters.search,
    filters.minLiquidity,
  ].filter(Boolean).length;

  const clearFilters = () => {
    setFilters({ categories: [], status: "open", search: "", minLiquidity: false, sortBy: "volume" });
  };

  const paginated = filteredMarkets.slice(0, page * 20);
  const hasMore = paginated.length < filteredMarkets.length;

  const signalMarketIds = new Set(activeSignals.map((s) => s.market_id || s.market_event_id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#dee2f5] flex items-center gap-2">
            <Grid3X3 className="w-6 h-6 text-[#00d4ff]" />
            Markets Explorer
          </h1>
          <p className="text-sm text-[#8b92a8] mt-1">
            {markets.length} active Bayse markets · Browse the full landscape
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleScan}
            disabled={scanning}
            className="flex items-center gap-2 px-3 py-2 bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/30 rounded-lg text-sm font-medium hover:bg-[#00ff88]/20 transition-all disabled:opacity-50"
          >
            <Loader2 className={`w-4 h-4 ${scanning ? "animate-spin" : ""}`} />
            {scanning ? "Scanning..." : "Scan Latest"}
          </button>
          <button
            onClick={() => setViewMode(viewMode === "grid" ? "list" : "grid")}
            className="p-2 bg-[#131a2b] border border-[#1a2030] rounded-lg text-[#8b92a8] hover:text-[#dee2f5] transition-colors"
          >
            {viewMode === "grid" ? <List className="w-4 h-4" /> : <Grid3X3 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-4 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8b92a8]" />
            <input
              type="text"
              placeholder="Search markets..."
              value={filters.search}
              onChange={(e) => setFilters({ search: e.target.value })}
              className="w-full pl-9 pr-4 py-2 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#dee2f5] placeholder:text-[#5a6070] focus:outline-none focus:border-[#00d4ff]/50"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#8b92a8] hover:text-[#dee2f5] transition-colors"
          >
            <SlidersHorizontal className="w-4 h-4" />
            Filters
            {activeFilterCount > 0 && (
              <span className="px-1.5 py-0.5 bg-[#00d4ff]/20 rounded text-[10px] text-[#00d4ff] font-bold">
                {activeFilterCount}
              </span>
            )}
          </button>
          {activeFilterCount > 0 && (
            <button onClick={clearFilters} className="text-xs text-[#00d4ff] hover:underline flex items-center gap-1">
              <X className="w-3 h-3" />
              Clear all
            </button>
          )}
        </div>

        {showFilters && (
          <div className="pt-3 border-t border-[#1a2030] space-y-3">
            {/* Categories */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-[#8b92a8] mr-1">Categories:</span>
              {CATEGORY_CONFIG.map((cat) => (
                <button
                  key={cat.key}
                  onClick={() => {
                    const next = filters.categories.includes(cat.key)
                      ? filters.categories.filter((c) => c !== cat.key)
                      : [...filters.categories, cat.key];
                    setFilters({ categories: next });
                  }}
                  className={`px-3 py-1 rounded-full text-xs font-medium capitalize transition-all ${
                    filters.categories.includes(cat.key)
                      ? "text-[#0a0e17]"
                      : "bg-[#0a0e17] text-[#8b92a8] border border-[#1a2030]"
                  }`}
                  style={
                    filters.categories.includes(cat.key)
                      ? { backgroundColor: cat.color, color: "#0a0e17" }
                      : {}
                  }
                >
                  {cat.label}
                </button>
              ))}
            </div>
            {/* Status Filter */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs text-[#8b92a8] mr-1">Status:</span>
              {[
                { key: "open", label: "Active" },
                { key: "closed", label: "Closed" },
                { key: "resolved", label: "Resolved" },
                { key: "", label: "All" },
              ].map((opt) => (
                <button
                  key={opt.key}
                  onClick={() => setFilters({ status: opt.key })}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    filters.status === opt.key
                      ? "bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/30"
                      : "bg-[#0a0e17] text-[#8b92a8] border border-[#1a2030] hover:text-[#dee2f5]"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            {/* Sort & Liquidity */}
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs text-[#8b92a8]">Sort by:</span>
              {[
                { key: "volume", label: "Volume", icon: Volume2 },
                { key: "edge", label: "Edge", icon: TrendingUp },
                { key: "time_asc", label: "Closing Soon", icon: Clock },
                { key: "change", label: "24h Change", icon: ArrowUpDown },
              ].map((opt) => (
                <button
                  key={opt.key}
                  onClick={() => setFilters({ sortBy: opt.key })}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs transition-all ${
                    filters.sortBy === opt.key
                      ? "bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/30"
                      : "bg-[#0a0e17] text-[#8b92a8] border border-[#1a2030]"
                  }`}
                >
                  <opt.icon className="w-3 h-3" />
                  {opt.label}
                </button>
              ))}
              <label className="flex items-center gap-2 ml-auto cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.minLiquidity}
                  onChange={(e) => setFilters({ minLiquidity: e.target.checked })}
                  className="accent-[#00d4ff]"
                />
                <span className="text-xs text-[#8b92a8]">Hide thin markets</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      {loading && markets.length === 0 ? (
        viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="bg-[#131a2b] rounded-xl p-5 border border-[#1a2030] animate-pulse">
                <div className="h-3 bg-[#1a2030] rounded w-16 mb-3" />
                <div className="h-4 bg-[#1a2030] rounded w-3/4 mb-4" />
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="h-10 bg-[#1a2030] rounded" />
                  <div className="h-10 bg-[#1a2030] rounded" />
                </div>
                <div className="h-3 bg-[#1a2030] rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] animate-pulse">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-12 bg-[#1a2030]/50 border-b border-[#1a2030]" />
            ))}
          </div>
        )
      ) : error && markets.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-[#ff4757] mb-2">{error}</p>
          <button onClick={fetchMarkets} className="mt-4 px-4 py-2 bg-[#00d4ff]/10 text-[#00d4ff] rounded-lg text-sm">
            Retry Now
          </button>
        </div>
      ) : filteredMarkets.length === 0 ? (
        <div className="text-center py-16 bg-[#131a2b] rounded-xl border border-[#1a2030]">
          <p className="text-[#8b92a8] text-lg">No markets match your filters</p>
          <p className="text-sm text-[#5a6070] mt-2">Try adjusting your criteria</p>
          <button onClick={clearFilters} className="mt-4 px-4 py-2 bg-[#00d4ff]/10 text-[#00d4ff] rounded-lg text-sm">
            Clear All Filters
          </button>
        </div>
      ) : viewMode === "grid" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {paginated.map((market) => (
            <MarketCard
              key={market.id}
              market={market}
              hasEdge={signalMarketIds.has(market.bayse_event_id)}
              onClick={() => navigate(`/market/${market.bayse_event_id}`)}
            />
          ))}
        </div>
      ) : (
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#1a2030] text-xs text-[#8b92a8] uppercase">
                <th className="py-3 px-4 text-left">Event</th>
                <th className="py-3 px-4 text-left">Price</th>
                <th className="py-3 px-4 text-left">Prob%</th>
                <th className="py-3 px-4 text-left">Volume</th>
                <th className="py-3 px-4 text-left">Time Left</th>
                <th className="py-3 px-4"></th>
              </tr>
            </thead>
            <tbody>
              {paginated.map((market) => (
                <MarketRow
                  key={market.id}
                  market={market}
                  hasEdge={signalMarketIds.has(market.bayse_event_id)}
                  onClick={() => navigate(`/market/${market.bayse_event_id}`)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Load More */}
      {hasMore && (
        <div className="flex justify-center">
          <button
            onClick={() => setPage(page + 1)}
            className="px-6 py-2 bg-[#131a2b] border border-[#1a2030] rounded-lg text-sm text-[#8b92a8] hover:text-[#dee2f5] hover:border-[#00d4ff]/30 transition-all"
          >
            Load More ({filteredMarkets.length - paginated.length} remaining)
          </button>
        </div>
      )}
    </div>
  );
};

export default MarketsExplorer;