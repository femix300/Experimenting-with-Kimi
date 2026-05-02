import { useEffect, useState } from "react";
import { useBacktestStore } from "@/stores";
import { getBacktestStrategies, runBacktest, getBacktestResults } from "@/lib/api";
import {
  FlaskConical,
  Loader2,
  Play,
} from "lucide-react";

const Backtester = () => {
  const { strategies, results, history, setStrategies, setResults, setHistory, setLoading } = useBacktestStore();
  const [loading, setLocalLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [bankroll, setBankroll] = useState(10000);

  useEffect(() => {
    const fetch = async () => {
      setLocalLoading(true);
      setLoading(true);
      try {
        const [stratRes, histRes] = await Promise.all([
          getBacktestStrategies(),
          getBacktestResults(),
        ]);
        if (stratRes.success) setStrategies(stratRes.strategies);
        if (histRes.success) setHistory(histRes.results);
      } catch { /* ignore */ }
      setLocalLoading(false);
      setLoading(false);
    };
    fetch();
  }, []);

  const handleRun = async () => {
    if (!selectedStrategy) return;
    const strategy = strategies.find((s) => s.id === selectedStrategy);
    if (!strategy) return;

    setRunning(true);
    try {
      const res = await runBacktest(strategy.params, bankroll);
      if (res.success) {
        setResults(res.result);
        const hist = await getBacktestResults();
        if (hist.success) setHistory(hist.results);
      }
    } catch { /* ignore */ }
    setRunning(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-10 h-10 text-[#00d4ff] animate-spin" />
      </div>
    );
  }

  const formatPercent = (v: number) => `${Number(v).toFixed(1)}%`;
  const formatMoney = (v: number) => `₦${Number(v).toLocaleString("en-US", { minimumFractionDigits: 2 })}`;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#dee2f5] flex items-center gap-2">
          <FlaskConical className="w-6 h-6 text-[#00d4ff]" />
          Backtester
        </h1>
        <p className="text-sm text-[#8b92a8] mt-1">Simulate strategies on historical market data</p>
      </div>

      {/* Strategy Selector */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
        <h3 className="text-sm font-semibold text-[#dee2f5] mb-4">Select Strategy</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          {strategies.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedStrategy(s.id)}
              className={`p-4 rounded-lg border text-left transition-all ${
                selectedStrategy === s.id
                  ? "bg-[#00d4ff]/10 border-[#00d4ff]/30"
                  : "bg-[#0a0e17] border-[#1a2030] hover:border-[#2a3040]"
              }`}
            >
              <p className={`text-sm font-medium ${selectedStrategy === s.id ? "text-[#00d4ff]" : "text-[#dee2f5]"}`}>
                {s.name}
              </p>
              <p className="text-xs text-[#8b92a8] mt-1">{s.description}</p>
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3 mb-4">
          <span className="text-sm text-[#8b92a8]">Bankroll:</span>
          <input
            type="number"
            value={bankroll}
            onChange={(e) => setBankroll(Number(e.target.value))}
            className="px-3 py-2 bg-[#0a0e17] border border-[#1a2030] rounded-lg text-sm text-[#dee2f5] font-mono-num focus:outline-none focus:border-[#00d4ff]/50 w-40"
          />
        </div>

        <button
          onClick={handleRun}
          disabled={running || !selectedStrategy}
          className="flex items-center gap-2 px-6 py-3 bg-[#00d4ff] text-[#0a0e17] rounded-lg font-bold text-sm hover:brightness-110 transition-all disabled:opacity-50"
        >
          {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {running ? "Running..." : "Run Backtest"}
        </button>
      </div>

      {/* Results */}
      {results && (
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
          <h3 className="text-sm font-semibold text-[#dee2f5] mb-4">Backtest Results</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <div className="bg-[#0a0e17] rounded-lg p-3">
              <p className="text-[10px] uppercase text-[#8b92a8]">Total Trades</p>
              <p className="text-lg font-bold font-mono-num text-[#dee2f5]">{results.total_trades}</p>
            </div>
            <div className="bg-[#0a0e17] rounded-lg p-3">
              <p className="text-[10px] uppercase text-[#8b92a8]">Win Rate</p>
              <p className="text-lg font-bold font-mono-num text-[#00ff88]">{formatPercent(results.win_rate)}</p>
            </div>
            <div className="bg-[#0a0e17] rounded-lg p-3">
              <p className="text-[10px] uppercase text-[#8b92a8]">Total Return</p>
              <p className={`text-lg font-bold font-mono-num ${results.total_return >= 0 ? "text-[#00ff88]" : "text-[#ff4757]"}`}>
                {results.total_return >= 0 ? "+" : ""}{formatPercent(results.total_return)}
              </p>
            </div>
            <div className="bg-[#0a0e17] rounded-lg p-3">
              <p className="text-[10px] uppercase text-[#8b92a8]">Max Drawdown</p>
              <p className="text-lg font-bold font-mono-num text-[#ff4757]">{formatPercent(results.max_drawdown)}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-[#0a0e17] rounded-lg p-3">
              <p className="text-[10px] uppercase text-[#8b92a8]">Sharpe Ratio</p>
              <p className="text-lg font-bold font-mono-num text-[#ffa502]">{Number(results.sharpe_ratio).toFixed(2)}</p>
            </div>
            <div className="bg-[#0a0e17] rounded-lg p-3">
              <p className="text-[10px] uppercase text-[#8b92a8]">Wins / Losses</p>
              <p className="text-lg font-bold font-mono-num text-[#dee2f5]">
                {results.winning_trades} / {results.losing_trades}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] overflow-hidden">
          <div className="p-4 border-b border-[#1a2030]">
            <h3 className="text-sm font-semibold text-[#dee2f5]">Backtest History</h3>
          </div>
          <div className="divide-y divide-[#1a2030]">
            {history.slice(0, 5).map((h, i) => (
              <div key={i} className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#dee2f5]">
                    Bankroll: {formatMoney(h.initial_bankroll)}
                  </p>
                  <p className="text-xs text-[#8b92a8]">
                    {new Date(h.created_at).toLocaleDateString()} · {h.results.total_trades} trades
                  </p>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-bold font-mono-num ${h.results.total_return >= 0 ? "text-[#00ff88]" : "text-[#ff4757]"}`}>
                    {h.results.total_return >= 0 ? "+" : ""}{formatPercent(h.results.total_return)}
                  </p>
                  <p className="text-xs text-[#8b92a8]">Sharpe: {Number(h.results.sharpe_ratio).toFixed(2)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Backtester;