import { useEffect } from "react";
import { useCalibrationStore } from "@/stores";
import { getCalibrationData, getAccuracyMetrics } from "@/lib/api";
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Line, ReferenceLine,
} from "recharts";
import { Target, CheckCircle, AlertTriangle, Loader2 } from "lucide-react";

const Calibration = () => {
  const { calibrationData, accuracyMetrics, loading, setCalibrationData, setAccuracyMetrics, setLoading } = useCalibrationStore();

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const [calRes, accRes] = await Promise.all([getCalibrationData(), getAccuracyMetrics()]);
        if (calRes.success) {
          setCalibrationData({
            calibration_points: calRes.calibration_points,
            perfect_line: calRes.perfect_line,
            total_markets_analyzed: calRes.total_markets_analyzed,
          });
        }
        if (accRes.success) setAccuracyMetrics(accRes.metrics);
      } catch { /* ignore */ }
      setLoading(false);
    };
    fetch();
  }, []);

  const chartData = calibrationData?.calibration_points?.map((p) => ({
    predicted: p.predicted,
    actual: p.actual,
    count: p.count,
    bin: p.bin,
  })) || [];

  const perfectLine = calibrationData?.perfect_line || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-10 h-10 text-[#00d4ff] animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#dee2f5] flex items-center gap-2">
          <Target className="w-6 h-6 text-[#00d4ff]" />
          Probability Calibration
        </h1>
        <p className="text-sm text-[#8b92a8] mt-1">
          How accurate are EdgeIQ's probability estimates? Perfect calibration means when we predict 70%, the outcome happens ~70% of the time.
        </p>
      </div>

      {/* Metrics */}
      {accuracyMetrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
            <p className="text-xs text-[#8b92a8] uppercase mb-1">Predictions</p>
            <p className="text-xl font-bold font-mono-num text-[#dee2f5]">{accuracyMetrics.total_predictions}</p>
          </div>
          <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
            <p className="text-xs text-[#8b92a8] uppercase mb-1">Accuracy</p>
            <p className="text-xl font-bold font-mono-num text-[#00ff88]">{accuracyMetrics.accuracy}%</p>
          </div>
          <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
            <p className="text-xs text-[#8b92a8] uppercase mb-1">Brier Score</p>
            <p className="text-xl font-bold font-mono-num text-[#00d4ff]">{accuracyMetrics.brier_score}</p>
          </div>
          <div className="bg-[#131a2b] rounded-lg p-4 border border-[#1a2030]">
            <p className="text-xs text-[#8b92a8] uppercase mb-1">Calibration Error</p>
            <p className="text-xl font-bold font-mono-num text-[#ffa502]">{accuracyMetrics.calibration_error}%</p>
          </div>
        </div>
      )}

      {/* Calibration Chart */}
      <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
        <h3 className="text-sm font-semibold text-[#dee2f5] mb-4">
          Predicted Probability vs. Actual Outcome Frequency
        </h3>
        <div className="h-[400px]">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a2030" />
                <XAxis
                  type="number"
                  dataKey="predicted"
                  name="Predicted"
                  domain={[0, 100]}
                  stroke="#5a6070"
                  fontSize={11}
                  label={{ value: "Predicted Probability (%)", position: "bottom", fill: "#8b92a8", fontSize: 12 }}
                />
                <YAxis
                  type="number"
                  dataKey="actual"
                  name="Actual"
                  domain={[0, 100]}
                  stroke="#5a6070"
                  fontSize={11}
                  label={{ value: "Actual Frequency (%)", angle: -90, position: "insideLeft", fill: "#8b92a8", fontSize: 12 }}
                />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  contentStyle={{ backgroundColor: "#131a2b", border: "1px solid #1a2030", borderRadius: 8, fontSize: 12 }}
                  formatter={(value: number, name: string) => [`${value.toFixed(1)}%`, name]}
                  labelFormatter={(_, p: any) => `Bin: ${p?.payload?.bin || ""} (${p?.payload?.count || 0} markets)`}
                />
                <ReferenceLine x={0} y={0} stroke="#1a2030" />
                <Line data={perfectLine} dataKey="actual" stroke="#5a6070" strokeDasharray="5 5" dot={false} type="monotone" />
                <Scatter name="Calibration" data={chartData} fill="#00d4ff" />
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-[#5a6070]">
              <AlertTriangle className="w-8 h-8 mb-2" />
              <p>Not enough resolved markets for calibration</p>
              <p className="text-xs mt-1">Run more backtests to generate data</p>
            </div>
          )}
        </div>
      </div>

      {/* Interpretation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-5">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="w-4 h-4 text-[#00ff88]" />
            <h4 className="text-sm font-semibold text-[#dee2f5]">Well-Calibrated Regions</h4>
          </div>
          <p className="text-sm text-[#8b92a8]">
            Probabilities between 40-60% tend to align closest with actual outcomes. This is the "efficient" range where market prices and AI estimates converge.
          </p>
        </div>
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-[#ffa502]" />
            <h4 className="text-sm font-semibold text-[#dee2f5]">Under-Confident Regions</h4>
          </div>
          <p className="text-sm text-[#8b92a8]">
            Extreme probabilities (below 20% or above 80%) show the most deviation. EdgeIQ is conservative in high-confidence predictions — this is safer but leaves edge on the table.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Calibration;
