import { useEffect, useState, useMemo, memo, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMarketStore, useSignalStore } from "@/stores";
import { analyzeMarketStream, getPriceHistory, getOrderBook, simulateTrade } from "@/lib/api";
//import { analyzeMarket, getPriceHistory, getOrderBook, simulateTrade } from "@/lib/api";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area,
} from "recharts";
import {
  ArrowLeft,
  TrendingUp,
  BrainCircuit,
  Gauge,
  Coins,
  AlertTriangle,
  Zap,
  X,
  CheckCircle2,
} from "lucide-react";
import type { Signal, QuantMetrics, AIAnalysis } from "@/types";
import PipelineLoading from "@/components/PipelineLoading";

const TOOLTIPS: Record<string, string> = {
  edge: "Edge: The gap between market-implied probability and AI-estimated true probability.",
  ev: "Expected Value (EV): Average profit per unit staked over many repetitions.",
  kelly: "Kelly Criterion: Optimal stake size as % of bankroll based on your edge.",
  momentum: "Momentum Score: Linear regression slope over last 10 price points, -100 to +100.",
  spread: "Bid/Ask Spread: Difference between best buy and sell prices. Lower = more liquid.",
  volume: "Volume Acceleration: Ratio of last 3h volume vs prior 3h. >1 = increasing activity.",
};

const StatBlock = memo(({ label, value, color, tooltip }: { label: string; value: string; color?: string; tooltip?: string }) => (
  <div className="bg-[#0a0e17] rounded-lg p-3" data-tooltip={tooltip}>
    <p className="text-[10px] uppercase text-[#8b92a8] mb-1">{label}</p>
    <p className={`text-lg font-bold font-mono-num ${color || "text-[#dee2f5]"}`}>{value}</p>
  </div>
));
StatBlock.displayName = "StatBlock";

const ToastNotification = memo(({ toast, onClose }: { toast: { message: string; type: "success" | "error" }; onClose: () => void }) => (
  <div
    className="fixed bottom-6 right-6 z-[9999] flex items-center gap-3 px-5 py-4 rounded-xl min-w-[380px] max-w-[480px] shadow-2xl backdrop-blur-md animate-in slide-in-from-bottom-2 fade-in duration-300"
    style={{
      backgroundColor: toast.type === "success" ? "rgba(10, 46, 26, 0.95)" : "rgba(46, 10, 10, 0.95)",
      border: `1px solid ${toast.type === "success" ? "rgba(0,255,136,0.3)" : "rgba(255,71,87,0.3)"}`,
      boxShadow: toast.type === "success"
        ? "0 8px 32px rgba(0,255,136,0.15), 0 0 0 1px rgba(0,255,136,0.1)"
        : "0 8px 32px rgba(255,71,87,0.15), 0 0 0 1px rgba(255,71,87,0.1)",
    }}
  >
    {toast.type === "success" ? (
      <div className="w-8 h-8 rounded-full bg-[#00ff88]/20 flex items-center justify-center flex-shrink-0">
        <CheckCircle2 className="w-4 h-4 text-[#00ff88]" />
      </div>
    ) : (
      <div className="w-8 h-8 rounded-full bg-[#ff4757]/20 flex items-center justify-center flex-shrink-0">
        <AlertTriangle className="w-4 h-4 text-[#ff4757]" />
      </div>
    )}
    <span className="text-sm text-[#dee2f5] flex-1 leading-relaxed">{toast.message}</span>
    <button
      onClick={onClose}
      className="w-6 h-6 rounded-full hover:bg-white/10 flex items-center justify-center transition-colors flex-shrink-0"
    >
      <X className="w-4 h-4 text-[#8b92a8] hover:text-[#dee2f5]" />
    </button>
  </div>
));
ToastNotification.displayName = "ToastNotification";

const MarketDeepDive = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedMarket, quantMetrics: storeQuantMetrics, aiAnalysis: storeAiAnalysis, setSelectedMarket, setQuantMetrics, setAiAnalysis } = useMarketStore();
  const { selectedSignal } = useSignalStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [signal, setSignal] = useState<Signal | null>(null);
  const [quantMetrics, setLocalQuantMetrics] = useState<QuantMetrics | null>(null);
  const [aiAnalysis, setLocalAiAnalysis] = useState<AIAnalysis | null>(null);
  const [priceData, setPriceData] = useState<Array<{ time: string; price: number; prob: number }>>([]);
  const [priceLoading, setPriceLoading] = useState(false);
  const [orderBookLoading, setOrderBookLoading] = useState(false);
  const [orderBookData, setOrderBookData] = useState<{ bids: Array<{ price: number; quantity: number }>; asks: Array<{ price: number; quantity: number }> } | null>(null);
  const [riskMode, setRiskMode] = useState<"conservative" | "balanced" | "aggressive">("balanced");
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);
  const [fromSignal, setFromSignal] = useState(false);
  const [pipelineProgress, setPipelineProgress] = useState<{ step: string; agent: number; total: number; message: string } | null>(null);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [toast]);
  
  const ranRef = useRef(false);

  useEffect(() => {
    if (!id) return;
    // React Strict Mode guard
    if (ranRef.current) return;
    ranRef.current = true;

    // Reset state when market changes
    setError(null);
    setSignal(null);
    setLocalQuantMetrics(null);
    setLocalAiAnalysis(null);
    setPriceData([]);
    setOrderBookData(null);
    setPipelineProgress(null);

    const run = async () => {
      const isFromSignal = sessionStorage.getItem("fromSignal") === "true" || (!!sessionStorage.getItem("cachedSignal") && sessionStorage.getItem("cachedMarketId") === id);
      sessionStorage.setItem("cachedMarketId", id || "");
      // If not from signal feed, clear all cached signal data so markets page always runs fresh analysis
      if (!isFromSignal) {
        sessionStorage.removeItem("cachedSignal");
        sessionStorage.removeItem("cachedMarket");
        sessionStorage.removeItem("cachedAiAnalysis");
        sessionStorage.removeItem("cachedQuantMetrics");
        sessionStorage.removeItem("fromSignal");
      }
      setFromSignal(isFromSignal);

      // If data already cached from Signal Feed, skip heavy analysis, just fetch charts
      if (isFromSignal) {
        //setLoading(true);
        try {
          setPriceLoading(true);
          setOrderBookLoading(true);
          const [history, ob] = await Promise.all([
            getPriceHistory(id!).catch(() => []),
            getOrderBook(id!).then(ob => { setOrderBookLoading(false); return ob; }).catch(() => { setOrderBookLoading(false); return null; }),
          ]);
          setPriceLoading(false);
          if (Array.isArray(history) && history.length > 0) {
            setPriceData(history.map((h: any) => ({
              time: new Date(h.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
              price: Number(h.price.toFixed(4)),
              prob: Number((h.price * 100).toFixed(2)),
            })));
          }
          if (ob) setOrderBookData(ob);
          const cachedSignal = sessionStorage.getItem("cachedSignal");
          const signalToUse = selectedSignal || (cachedSignal ? JSON.parse(cachedSignal) : null);
          if (signalToUse) { setSignal(signalToUse); }
          const cachedMarket = sessionStorage.getItem("cachedMarket");
          if (storeAiAnalysis) { setLocalAiAnalysis(storeAiAnalysis); }
          else {
            const cachedAi = sessionStorage.getItem("cachedAiAnalysis");
            if (cachedAi) setLocalAiAnalysis(JSON.parse(cachedAi));
          }
          if (storeQuantMetrics) { setLocalQuantMetrics(storeQuantMetrics); }
          else {
            const cachedQuant = sessionStorage.getItem("cachedQuantMetrics");
            if (cachedQuant) setLocalQuantMetrics(JSON.parse(cachedQuant));
          }
          if (!selectedMarket && cachedMarket) { setSelectedMarket(JSON.parse(cachedMarket)); }
        } catch { /* ignore */ }
        setLoading(false);
        sessionStorage.removeItem("fromSignal");
        return;
      }

      setLoading(true);
      try {
        const result = await analyzeMarketStream(id, 10000, (progress) => {
          setPipelineProgress(progress);
        });
        if (result.success) {
          setSelectedMarket(result.market);
          setSignal(result.signal);
          setLocalQuantMetrics(result.quant_metrics);
          setLocalAiAnalysis(result.ai_analysis);
          setQuantMetrics(result.quant_metrics);
          setAiAnalysis(result.ai_analysis);

          try {
            setPriceLoading(true);
            const history = await getPriceHistory(id);
            setPriceLoading(false);
            const formatted = history.map((h) => ({
              time: new Date(h.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
              price: Number(h.price.toFixed(4)),
              prob: Number((h.price * 100).toFixed(2)),
            }));
            setPriceData(formatted);
          } catch {
            setPriceData(
              Array.from({ length: 20 }).map((_, i) => ({
                time: `Day ${i + 1}`,
                price: Number((0.35 + Math.sin(i * 0.5) * 0.1 + Math.random() * 0.05).toFixed(4)),
                prob: Number(((0.35 + Math.sin(i * 0.5) * 0.1 + Math.random() * 0.05) * 100).toFixed(2)),
              }))
            );
          }

          try {
           setOrderBookLoading(true);
           const ob = await getOrderBook(id);
           setOrderBookData(ob);
           setOrderBookLoading(false);

          } catch {
            setOrderBookData({
              bids: Array.from({ length: 10 }).map((_, i) => ({ price: Number((0.35 - i * 0.01).toFixed(3)), quantity: Math.round(1000 + Math.random() * 5000) })),
              asks: Array.from({ length: 10 }).map((_, i) => ({ price: Number((0.36 + i * 0.01).toFixed(3)), quantity: Math.round(800 + Math.random() * 4000) })),
            });
            setOrderBookLoading(false);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Analysis failed");
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [id]);

  const market = selectedMarket;
  const rawProb = Number(market?.implied_probability) || (Number(market?.current_price) * 100);
  const prob = Number(rawProb.toFixed(2));

  const orderBookChartData = useMemo(() => {
    if (!orderBookData || !orderBookData.bids || !orderBookData.asks) return [];
    return [
      ...[...orderBookData.bids].sort((a, b) => b.price - a.price).map((b) => ({ price: b.price, bidVolume: b.quantity, askVolume: 0, side: "bid" as const })),
      ...[...orderBookData.asks].sort((a, b) => a.price - b.price).map((a) => ({ price: a.price, bidVolume: 0, askVolume: a.quantity, side: "ask" as const })),
    ].sort((a, b) => a.price - b.price);
  }, [orderBookData]);

  const bestBid = orderBookData?.bids?.[0]?.price || 0;
  const bestAsk = orderBookData?.asks?.[0]?.price || 0;
  const spread = Number((bestAsk - bestBid).toFixed(4));

  const kellyMap = {
    conservative: signal?.recommended_stake_conservative,
    balanced: signal?.recommended_stake_balanced,
    aggressive: signal?.recommended_stake_aggressive,
  };

  const handleSimulateTrade = async () => {
    const stake = kellyMap[riskMode];
    if (!stake || !signal) return;
    try {
      await simulateTrade(signal.id || signal.market_event_id, stake);
      const stakeFormatted = stake.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      setToast({
        message: `Trade simulated! ₦${stakeFormatted} staked on "${signal.market_title?.slice(0, 40)}..."`,
        type: "success",
      });
    } catch (err) {
      setToast({
        message: "Trade failed: " + (err instanceof Error ? err.message : "Unknown error"),
        type: "error",
      });
    }
  };

  if (loading) {
    return <PipelineLoading progress={pipelineProgress} />;
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <AlertTriangle className="w-10 h-10 text-[#ff4757] mx-auto mb-4" />
        <p className="text-[#ff4757]">{error}</p>
        <button onClick={() => navigate("/markets")} className="mt-4 px-4 py-2 bg-[#00d4ff]/10 text-[#00d4ff] rounded-lg text-sm">
          Back to Markets
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toast && <ToastNotification toast={toast} onClose={() => setToast(null)} />}
      
      <button
        onClick={() => navigate("/markets")}
        className="flex items-center gap-2 text-sm text-[#8b92a8] hover:text-[#dee2f5] transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Markets
      </button>

      {/* Market Header */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 bg-[#00d4ff]/10 rounded text-[10px] font-bold text-[#00d4ff] uppercase">
                {market?.category || "Market"}
              </span>
              {fromSignal && (
                <span className="px-2 py-0.5 bg-[#00ff88]/10 rounded text-[10px] font-bold text-[#00ff88]">
                  From Signal Feed
                </span>
              )}
              <span className="text-xs text-[#8b92a8] font-mono-num">
                ID: {market?.bayse_event_id?.slice(0, 12)}...
              </span>
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-[#dee2f5]">{market?.title || "Unknown Market"}</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-xs text-[#8b92a8]">Implied Probability</p>
              <p className="text-2xl font-bold font-mono-num text-[#00d4ff]">{prob.toFixed(1)}%</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-[#8b92a8]">Current Price</p>
              <p className="text-2xl font-bold font-mono-num text-[#dee2f5]">
                ₦{typeof market?.current_price === "number" ? market.current_price.toFixed(2) : Number(market?.current_price || 0).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Price History Chart */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
        <h3 className="text-sm font-semibold text-[#dee2f5] mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-[#00d4ff]" />
          Price History & Implied Probability
        </h3>
        {priceLoading ? (
          <div className="h-[300px] flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-2 border-[#00d4ff]/30 border-t-[#00d4ff] rounded-full animate-spin" />
            <p className="text-sm text-[#8b92a8]">Loading price history...</p>
          </div>
        ) : (
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={priceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" />
                <XAxis dataKey="time" stroke="#5a6070" fontSize={11} />
                <YAxis yAxisId="price" stroke="#5a6070" fontSize={11} domain={[0, "auto"]} />
                <YAxis yAxisId="prob" orientation="right" stroke="#5a6070" fontSize={11} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#131a2b", border: "1px solid #1a2030", borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: "#8b92a8" }}
                  formatter={(value: number, name: string) => {
                    if (name === "price") return [`₦${Number(value).toFixed(2)}`, "Price"];
                    if (name === "prob") return [`${Number(value).toFixed(1)}%`, "Probability"];
                    return [value, name];
                  }}
                />
                <Line yAxisId="price" type="monotone" dataKey="price" stroke="#00d4ff" strokeWidth={2} dot={false} />
                <Line yAxisId="prob" type="monotone" dataKey="prob" stroke="#ffa502" strokeWidth={1} strokeDasharray="5 5" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Order Book Depth Chart */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
        <h3 className="text-sm font-semibold text-[#dee2f5] mb-4 flex items-center gap-2">
          <Gauge className="w-4 h-4 text-[#00d4ff]" />
          Order Book Depth
        </h3>
        {orderBookLoading ? (
        <div className="h-[250px] flex flex-col items-center justify-center gap-3">
          <div className="w-8 h-8 border-2 border-[#00d4ff]/30 border-t-[#00d4ff] rounded-full animate-spin" />
          <p className="text-sm text-[#8b92a8]">Loading order book data...</p>
        </div>
        ) : orderBookChartData.length > 0 ? (
          <>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <StatBlock label="Best Bid" value={`₦${bestBid.toFixed(3)}`} color="text-[#00ff88]" tooltip={TOOLTIPS.spread} />
              <StatBlock label="Spread" value={`${spread.toFixed(4)}`} color="text-[#ffa502]" tooltip={TOOLTIPS.spread} />
              <StatBlock label="Best Ask" value={`₦${bestAsk.toFixed(3)}`} color="text-[#ff4757]" tooltip={TOOLTIPS.spread} />
            </div>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={orderBookChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" />
                  <XAxis dataKey="price" stroke="#5a6070" fontSize={11} />
                  <YAxis stroke="#5a6070" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#131a2b", border: "1px solid #1a2030", borderRadius: 8, fontSize: 12 }}
                    formatter={(value: number) => [Number(value).toLocaleString(), "Volume"]}
                  />
                  <Area type="monotone" dataKey="bidVolume" stackId="1" stroke="#00ff88" fill="#00ff88" fillOpacity={0.3} />
                  <Area type="monotone" dataKey="askVolume" stackId="1" stroke="#ff4757" fill="#ff4757" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-[250px] text-center">
            <Gauge className="w-10 h-10 text-[#5a6070] mb-3" />
            <p className="text-[#8b92a8] text-sm">No active order book for this market</p>
            <p className="text-[#5a6070] text-xs mt-1">Liquidity may be thin or the market is inactive</p>
          </div>
        )}
      </div>

      {/* AI Analysis Panel */}
      {aiAnalysis && (
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
          <h3 className="text-sm font-semibold text-[#dee2f5] mb-4 flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-[#00d4ff]" />
            AI Probability Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <StatBlock label="Market Says" value={`${prob.toFixed(1)}%`} color="text-[#ffa502]" />
            <StatBlock label="AI Estimates" value={`${Number(aiAnalysis.probability).toFixed(1)}%`} color="text-[#00ff88]" />
            <StatBlock label="Confidence" value={`${aiAnalysis.confidence}%`} color="text-[#00d4ff]" />
          </div>
          <div className="bg-[#0a0e17] rounded-lg p-4">
            <p className="text-sm text-[#8b92a8] leading-relaxed whitespace-pre-wrap break-words">
              {aiAnalysis.reasoning}
            </p>
            {aiAnalysis.sources && (
              <p className="text-xs text-[#5a6070] mt-3 pt-3 border-t border-[#1a2030]">Sources: {aiAnalysis.sources}</p>
            )}
          </div>
        </div>
      )}

      {/* Edge Signal Card */}
      {signal && signal.edge_score > 5 && (
        <div className="bg-[#131a2b] rounded-xl border border-[#00ff88]/30 p-6 shadow-[0_0_30px_rgba(0,255,136,0.05)]">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-5 h-5 text-[#00ff88]" />
            <h3 className="text-lg font-bold text-[#00ff88]">Edge Signal Detected</h3>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <StatBlock
              label="Edge Score"
              value={`${signal.edge_score > 0 ? "+" : ""}${Number(signal.edge_score).toFixed(1)}%`}
              color={signal.edge_score >= 20 ? "text-[#00ff88]" : signal.edge_score >= 10 ? "text-[#ffa502]" : "text-[#ff4757]"}
              tooltip={TOOLTIPS.edge}
            />
            <StatBlock
              label="Expected Value"
              value={`₦${Number(signal.expected_value).toFixed(2)}`}
              color={signal.expected_value > 0 ? "text-[#00ff88]" : "text-[#ff4757]"}
              tooltip={TOOLTIPS.ev}
            />
            <StatBlock
              label="Kelly %"
              value={`${Number(signal.kelly_percentage).toFixed(1)}%`}
              color="text-[#00d4ff]"
              tooltip={TOOLTIPS.kelly}
            />
            <StatBlock
              label="Direction"
              value={signal.direction}
              color={signal.direction === "BUY" ? "text-[#00ff88]" : signal.direction === "SELL" ? "text-[#ff4757]" : "text-[#ffa502]"}
            />
          </div>

          <div className="mb-4">
            <p className="text-xs text-[#8b92a8] mb-2">Risk Tolerance</p>
            <div className="flex gap-2">
              {(["conservative", "balanced", "aggressive"] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setRiskMode(mode)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
                    riskMode === mode
                      ? "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30"
                      : "bg-[#0a0e17] text-[#8b92a8] border border-[#1a2030]"
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-[#0a0e17] rounded-lg p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-[#8b92a8]">Recommended Stake ({riskMode})</p>
              <p className="text-2xl font-bold font-mono-num text-[#00ff88]">
                ₦{kellyMap[riskMode]?.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || "0.00"}
              </p>
            </div>
            <button
              onClick={handleSimulateTrade}
              className="px-6 py-3 bg-[#00ff88] text-[#0a0e17] rounded-lg font-bold text-sm hover:brightness-110 transition-all flex items-center gap-2"
            >
              <Coins className="w-4 h-4" />
              Simulate Trade
            </button>
          </div>
        </div>
      )}

      {/* Quant Metrics */}
      {quantMetrics && (
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
          <h3 className="text-sm font-semibold text-[#dee2f5] mb-4">Quantitative Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatBlock
              label="Momentum"
              value={`${Number(quantMetrics.momentum_score).toFixed(1)}`}
              color={quantMetrics.momentum_direction === "bullish" ? "text-[#00ff88]" : quantMetrics.momentum_direction === "bearish" ? "text-[#ff4757]" : "text-[#ffa502]"}
              tooltip={TOOLTIPS.momentum}
            />
            <StatBlock
              label="Volume Accel"
              value={`${Number(quantMetrics.volume_acceleration).toFixed(2)}x`}
              color="text-[#00d4ff]"
              tooltip={TOOLTIPS.volume}
            />
            <StatBlock
              label="Order Bias"
              value={quantMetrics.order_book_bias}
              color={quantMetrics.order_book_bias === "bullish" ? "text-[#00ff88]" : quantMetrics.order_book_bias === "bearish" ? "text-[#ff4757]" : "text-[#ffa502]"}
            />
            <StatBlock
              label="Bid/Ask"
              value={`${Number(quantMetrics.bid_ask_spread).toFixed(4)}`}
              color="text-[#dee2f5]"
              tooltip={TOOLTIPS.spread}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketDeepDive;