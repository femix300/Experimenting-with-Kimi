import { useEffect, useState } from "react";
import { useBacktestStore } from "@/stores";
import { getBacktestStrategies, runBacktest } from "@/lib/api";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  FlaskConical,
  Play,
  Loader2,
  Trophy,
  TrendingDown,
  TrendingUp,
  Activity,
  Target,
  CheckCircle,
  XCircle,
} from "lucide-react";

const Backtester = () => {
  const { strategies, results, loading, selectedStrategy, setStrategies, setResults, setLoading, setSelectedStrategy } = useBacktestStore();
  const [config, setConfig] = useState({ min_edge: 15, min_momentum: 10, categories: [] as string[] });
  const [initialBankroll, setInitialBankroll] = useState(10000);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await getBacktestStrategies();
        if (res.success) setStrategies(res.strategies);
      } catch { /* ignore */ }
    };
    fetch();
  }, []);

  const handleRun = async () => {
    setLoading(true);
    try {
      const res = await runBacktest(config, initialBankroll);
      if (res.success) setResults(res.result);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Backtest failed");
    } finally {
      setLoading(false);
    }
  };

  const equityCurve = results?.trade_log?.map((t, i) => ({
    trade: i + 1,
    pnl: t.pnl,
    cumulative: results.trade_log.slice(0, i + 1).reduce((sum, tr) => sum + tr.pnl, 0),
  })) || [];

  const _winLossData = results ? [results.winning_trades, results.losing_trades] : [0, 0];
  void _winLossData;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#dee2f5] flex items-center gap-2">
          <FlaskConical className="w-6 h-6 text-[#00d4ff]" />
          Strategy Backtester
        </h1>
        <p className="text-sm text-[#8b92a8] mt-1">Test your quant strategy against historical Bayse data</p>
      </div>

      {/* Strategy Config */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6 space-y-4">
        <h3 className="text-sm font-semibold text-[#dee2f5]">Strategy Configuration</h3>

        {/* Presets */}
        <div className="flex flex-wrap gap-2">
          {strategies.map((s) => (
            <button
              key={s.id}
              onClick={() => {
                setSelectedStrategy(s.id);
                setConfig({
                  min_edge: s.params.min_edge || 15,
                  min_momentum: s.params.min_momentum || 10,
                  categories: config.categories,
                });
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedStrategy === s.id
                  ? "bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30"
                  : "bg-[#0a0e17] text-[#8b92a8] border border-[#1a2030]"
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-xs text-[#8b92a8] mb-1 block">Min Edge Threshold (%)</label>
            <input
              type="range"
              min="5"
              max="30"
              value={config.min_edge}
              onChange={(e) => setConfig({ ...config, min_edge: Number(e.target.value) })}
              className="w-full accent-[#00d4ff]"
            />
            <p className="text-xs text-[#00d4ff] font-mono-num mt-1">{config.min_edge}%</p>
          </div>
          <div>
            <label className="text-xs text-[#8b92a8] mb-1 block">Min Momentum</label>
            <input
              type="range"
              min="0"
              max="50"
              value={config.min_momentum}
              onChange={(e) => setConfig({ ...config, min_momentum: Number(e.target.value) })}
              className="w-full accent-[#00d4ff]"
            />
            <p className="text-xs text-[#00d4ff] font-mono-num mt-1">{config.min_momentum}</p>
          </div>
          <div>
            <label className="text-xs text-[#8b92a8] mb-1 block">Initial Bankroll (₦)</label>
            <input
              type="number"
              value={initialBankroll}
              onChange={(e) => setInitialBankroll(Number(e.target.value))}
              className="w-full px-3 py-2 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#dee2f5] focus:outline-none focus:border-[#00d4ff]/50"
            />
          </div>
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 bg-[#00d4ff] text-[#0a0e17] rounded-lg font-bold text-sm hover:brightness-110 transition-all disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {loading ? "Running Simulation..." : "Run Backtest"}
        </button>
      </div>

      {/* Results */}
      {results && (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
              <div className="flex items-center gap-2 mb-2">
                <Trophy className="w-4 h-4 text-[#00d4ff]" />
                <span className="text-xs text-[#8b92a8]">Win Rate</span>
              </div>
              <p className="text-2xl font-bold font-mono-num text-[#00ff88]">{(results.win_rate * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-[#00d4ff]" />
                <span className="text-xs text-[#8b92a8]">Total Return</span>
              </div>
              <p className="text-2xl font-bold font-mono-num text-[#00ff88]">+{(results.total_return * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
              <div className="flex items-center gap-2 mb-2">
                <TrendingDown className="w-4 h-4 text-[#ff4757]" />
                <span className="text-xs text-[#8b92a8]">Max Drawdown</span>
              </div>
              <p className="text-2xl font-bold font-mono-num text-[#ff4757]">{(results.max_drawdown * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-[#00d4ff]" />
                <span className="text-xs text-[#8b92a8]">Sharpe Ratio</span>
              </div>
              <p className="text-2xl font-bold font-mono-num text-[#00d4ff]">{results.sharpe_ratio.toFixed(2)}</p>
            </div>
          </div>

          {/* Equity Curve */}
          <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
            <h3 className="text-sm font-semibold text-[#dee2f5] mb-4">Equity Curve</h3>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={equityCurve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" />
                  <XAxis dataKey="trade" stroke="#5a6070" fontSize={11} />
                  <YAxis stroke="#5a6070" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: "#131a2b", border: "1px solid #1a2030", borderRadius: 8 }} />
                  <Line type="monotone" dataKey="cumulative" stroke="#00d4ff" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trade Log */}
          <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] overflow-hidden">
            <div className="p-4 border-b border-[#1a2030]">
              <h3 className="text-sm font-semibold text-[#dee2f5]">Trade Log</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#1a2030] text-xs text-[#8b92a8] uppercase">
                    <th className="py-3 px-4 text-left">Market</th>
                    <th className="py-3 px-4 text-left">Action</th>
                    <th className="py-3 px-4 text-left">Edge</th>
                    <th className="py-3 px-4 text-left">Outcome</th>
                    <th className="py-3 px-4 text-left">PnL</th>
                  </tr>
                </thead>
                <tbody>
                  {results.trade_log?.slice(0, 20).map((trade, i) => (
                    <tr key={i} className="border-b border-[#1a2030]/50 hover:bg-[#1a2030]/30">
                      <td className="py-3 px-4 text-sm text-[#dee2f5]">{trade.market_title}</td>
                      <td className="py-3 px-4">
                        <span className={`text-xs font-bold ${trade.action === "BUY" ? "text-[#00ff88]" : "text-[#ff4757]"}`}>
                          {trade.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm font-mono-num text-[#00d4ff]">{trade.edge.toFixed(1)}%</td>
                      <td className="py-3 px-4">
                        {trade.is_win ? (
                          <CheckCircle className="w-4 h-4 text-[#00ff88]" />
                        ) : (
                          <XCircle className="w-4 h-4 text-[#ff4757]" />
                        )}
                      </td>
                      <td className={`py-3 px-4 text-sm font-mono-num ${trade.pnl > 0 ? "text-[#00ff88]" : "text-[#ff4757]"}`}>
                        {trade.pnl > 0 ? "+" : ""}₦{trade.pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Gemini Review Placeholder */}
          <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
            <h3 className="text-sm font-semibold text-[#dee2f5] mb-4 flex items-center gap-2">
              <Target className="w-4 h-4 text-[#00d4ff]" />
              AI Strategy Review
            </h3>
            <div className="bg-[#0a0e17] rounded-lg p-4 space-y-3">
              <p className="text-sm text-[#8b92a8]">
                <strong className="text-[#dee2f5]">Strengths:</strong> Strategy shows positive expected value with {(results.win_rate * 100).toFixed(0)}% win rate.
                Kelly-compliant sizing protects bankroll during drawdowns.
              </p>
              <p className="text-sm text-[#8b92a8]">
                <strong className="text-[#dee2f5]">Weaknesses:</strong> Max drawdown of {(results.max_drawdown * 100).toFixed(1)}% suggests position sizing could be more conservative in volatile periods.
              </p>
              <p className="text-sm text-[#00d4ff]">
                <strong>Improvement:</strong> Add a volatility filter — skip trades when volume acceleration exceeds 3x to avoid crowded exits.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Backtester;
