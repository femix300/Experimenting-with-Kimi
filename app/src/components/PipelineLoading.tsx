import { useEffect, useState } from "react";
import { ScanLine, BarChart3, BrainCircuit, Zap, Activity } from "lucide-react";

const AGENTS = [
  { id: 1, name: "Market Scanner", icon: ScanLine, color: "#00d4ff" },
  { id: 2, name: "Quant Analyzer", icon: BarChart3, color: "#00ff88" },
  { id: 3, name: "AI Probability", icon: BrainCircuit, color: "#ffa502" },
  { id: 4, name: "Signal Generator", icon: Zap, color: "#ff6b81" },
];

interface Props {
  progress?: { step: string; agent: number; total: number; message: string } | null;
}

const PipelineLoading = ({ progress }: Props) => {
  const [completedAgents, setCompletedAgents] = useState<number[]>([]);
  const [activeAgent, setActiveAgent] = useState(0);
  const [statusMessage, setStatusMessage] = useState("Initializing market scanner...");

  useEffect(() => {
    if (!progress) return;

    const newCompleted: number[] = [];
    for (let i = 1; i < progress.agent; i++) {
      newCompleted.push(i);
    }
    setCompletedAgents(newCompleted);
    setActiveAgent(progress.agent);
    setStatusMessage(progress.message);
  }, [progress]);

  const progressPct = progress ? (progress.agent / progress.total) * 100 : 0;

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center w-full max-w-lg px-4">
        <div className="relative w-20 h-20 mx-auto mb-6">
          <div className="absolute inset-0 rounded-full bg-[#00d4ff]/20 animate-ping" style={{ animationDuration: "2s" }} />
          <div className="absolute inset-2 rounded-full bg-[#00d4ff]/10 animate-ping" style={{ animationDuration: "2s", animationDelay: "0.3s" }} />
          <div className="relative w-full h-full rounded-full bg-[#131a2b] border border-[#00d4ff]/30 flex items-center justify-center">
            <Activity className="w-8 h-8 text-[#00d4ff] animate-pulse" />
          </div>
        </div>

        <h2 className="text-lg font-bold text-[#dee2f5] mb-2">Running 4-Agent Pipeline</h2>
        <p className="text-sm text-[#8b92a8] mb-6">Analyzing market data with AI-powered quant intelligence</p>

        <div className="h-1.5 bg-[#1a2030] rounded-full overflow-hidden mb-8">
          <div
            className="h-full bg-[#00d4ff] rounded-full transition-all duration-700 ease-out"
            style={{ width: `${Math.min(progressPct, 100)}%` }}
          />
        </div>

        <div className="space-y-3">
          {AGENTS.map((agent) => {
            const Icon = agent.icon;
            const isCompleted = completedAgents.includes(agent.id);
            const isActive = activeAgent === agent.id;
            const isPending = !isCompleted && !isActive;
            return (
              <div
                key={agent.id}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-all duration-500 ${
                  isCompleted ? "bg-[#00ff88]/5 border-[#00ff88]/20"
                  : isActive ? "bg-[#00d4ff]/5 border-[#00d4ff]/30"
                  : "bg-[#131a2b] border-[#1a2030]"
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
                  isCompleted ? "bg-[#00ff88]/20" : isActive ? "bg-[#00d4ff]/20 animate-pulse" : "bg-[#1a2030]"
                }`}>
                  <Icon className={`w-4 h-4 transition-colors ${
                    isCompleted ? "text-[#00ff88]" : isActive ? "text-[#00d4ff]" : "text-[#5a6070]"
                  }`} />
                </div>
                <div className="flex-1 text-left">
                  <p className={`text-sm font-medium transition-colors ${
                    isCompleted ? "text-[#00ff88]" : isActive ? "text-[#dee2f5]" : "text-[#5a6070]"
                  }`}>Agent 0{agent.id}: {agent.name}</p>
                  {isActive && <p className="text-[10px] text-[#8b92a8] mt-0.5 font-mono">{statusMessage}</p>}
                </div>
                {isCompleted && (
                  <div className="w-5 h-5 rounded-full bg-[#00ff88]/20 flex items-center justify-center">
                    <svg className="w-3 h-3 text-[#00ff88]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                )}
                {isActive && <div className="w-5 h-5 rounded-full border-2 border-[#00d4ff]/30 border-t-[#00d4ff] animate-spin" />}
                {isPending && <div className="w-5 h-5 rounded-full border border-[#1a2030]" />}
              </div>
            );
          })}
        </div>

        <div className="mt-6 bg-[#131a2b] rounded-lg border border-[#1a2030] p-3 font-mono text-left">
          <p className="text-[10px] text-[#5a6070]">{statusMessage}</p>
          <p className="text-[10px] text-[#00d4ff] mt-1">{`> agent ${activeAgent || 0}/${AGENTS.length} · ${Math.round(progressPct)}%`}</p>
        </div>
      </div>
    </div>
  );
};

export default PipelineLoading;
