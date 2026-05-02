import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores";
import { Radar, Zap, BrainCircuit, Shield, ChevronRight, LogIn, ArrowRight } from "lucide-react";

const LandingPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="min-h-screen bg-[#0a0e17] text-[#dee2f5]">
      <div className="max-w-6xl mx-auto px-4 py-16 md:py-24">
        <nav className="flex items-center justify-between mb-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#00d4ff] flex items-center justify-center">
              <Radar className="w-5 h-5 text-[#0a0e17]" />
            </div>
            <span className="font-bold text-xl">EdgeIQ</span>
          </div>
          {isAuthenticated ? (
            <button onClick={() => navigate("/markets")} className="px-4 py-2 bg-[#00d4ff] text-[#0a0e17] rounded-lg text-sm font-bold hover:brightness-110 transition-all">
              Dashboard
            </button>
          ) : (
            <button onClick={() => navigate("/auth")} className="px-4 py-2 bg-[#00d4ff] text-[#0a0e17] rounded-lg text-sm font-bold hover:brightness-110 transition-all flex items-center gap-2">
              <LogIn className="w-4 h-4" /> Sign In
            </button>
          )}
        </nav>

        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6">
            AI Quant Intelligence for{" "}
            <span className="text-[#00d4ff]">Prediction Markets</span>
          </h1>
          <p className="text-lg text-[#8b92a8] mb-8 leading-relaxed">
            EdgeIQ detects gaps between market-implied probabilities and AI-estimated true probabilities.
            Surface actionable trade signals with Expected Value calculations and Kelly Criterion stake sizing.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {isAuthenticated ? (
              <button onClick={() => navigate("/markets")} className="px-8 py-4 bg-[#00d4ff] text-[#0a0e17] rounded-xl font-bold text-base hover:brightness-110 transition-all flex items-center gap-2">
                Launch Platform <ChevronRight className="w-5 h-5" />
              </button>
            ) : (
              <button onClick={() => navigate("/auth")} className="px-8 py-4 bg-[#00d4ff] text-[#0a0e17] rounded-xl font-bold text-base hover:brightness-110 transition-all flex items-center gap-2">
                Get Started <ArrowRight className="w-5 h-5" />
              </button>
            )}
            <button onClick={() => isAuthenticated ? navigate("/signals") : navigate("/auth")} className="px-8 py-4 bg-[#131a2b] border border-[#1a2030] text-[#dee2f5] rounded-xl font-medium text-base hover:border-[#00d4ff]/30 transition-all">
              {isAuthenticated ? "View Signals" : "Learn More"}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-16 border-t border-[#1a2030]">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
            <div className="w-10 h-10 rounded-lg bg-[#00d4ff]/10 flex items-center justify-center mb-4"><Zap className="w-5 h-5 text-[#00d4ff]" /></div>
            <h3 className="font-bold text-[#dee2f5] mb-2">4-Agent Pipeline</h3>
            <p className="text-sm text-[#8b92a8]">Market scanning, quant analysis, AI probability estimation, and signal generation — all in 8-12 seconds.</p>
          </div>
          <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
            <div className="w-10 h-10 rounded-lg bg-[#00ff88]/10 flex items-center justify-center mb-4"><BrainCircuit className="w-5 h-5 text-[#00ff88]" /></div>
            <h3 className="font-bold text-[#dee2f5] mb-2">Gemini-Powered AI</h3>
            <p className="text-sm text-[#8b92a8]">Google Gemini 1.5 Flash with Search Grounding researches events, news, and historical precedent for accurate probability estimates.</p>
          </div>
          <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
            <div className="w-10 h-10 rounded-lg bg-[#ffa502]/10 flex items-center justify-center mb-4"><Shield className="w-5 h-5 text-[#ffa502]" /></div>
            <h3 className="font-bold text-[#dee2f5] mb-2">Kelly Criterion Sizing</h3>
            <p className="text-sm text-[#8b92a8]">Optimal stake sizing with conservative, balanced, and aggressive risk profiles. Never over-stake again.</p>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8 border-t border-[#1a2030] text-center">
        <p className="text-xs text-[#5a6070]">Built for Build With AI OAU 2026 Hackathon · Quantitative Finance Track · GDG × Bayse Markets</p>
      </div>
    </div>
  );
};

export default LandingPage;
