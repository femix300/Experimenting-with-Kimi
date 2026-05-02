import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores";
import {
  ChevronRight,
  Radar,
  Zap,
  BrainCircuit,
  Shield,
  BarChart3,
  Target,
  Activity,
  Globe,
  Cpu,
  Lock,
  ArrowRight,
  LineChart,
  Wallet,
  LogIn,
} from "lucide-react";

const HomePage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="min-h-screen bg-[#0a0e17] text-[#dee2f5]">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-16">
        {/* Top Nav */}
        <nav className="flex items-center justify-between mb-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#00d4ff] flex items-center justify-center">
              <Radar className="w-5 h-5 text-[#0a0e17]" />
            </div>
            <span className="font-bold text-xl text-[#dee2f5]">EdgeIQ</span>
          </div>
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <button
                onClick={() => navigate("/markets")}
                className="px-4 py-2 text-sm bg-[#00d4ff] text-[#0a0e17] rounded-lg font-medium hover:brightness-110 transition-all"
              >
                Dashboard
              </button>
            ) : (
              <button
                onClick={() => navigate("/auth")}
                className="px-4 py-2 text-sm bg-[#00d4ff] text-[#0a0e17] rounded-lg font-medium hover:brightness-110 transition-all flex items-center gap-2"
              >
                <LogIn className="w-4 h-4" />
                Sign In
              </button>
            )}
          </div>
        </nav>

        {/* Hero Content */}
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#00d4ff]/10 border border-[#00d4ff]/20 text-sm text-[#00d4ff] mb-8">
            <Activity className="w-4 h-4" />
            <span>AI-Powered Quant Intelligence Platform</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6">
            Find Your Edge in{" "}
            <span className="text-[#00d4ff]">Prediction Markets</span>
          </h1>
          <p className="text-lg text-[#8b92a8] mb-8 leading-relaxed max-w-2xl mx-auto">
            EdgeIQ combines quantitative finance, machine learning, and real-time market data 
            to identify mispriced probabilities across Bayse prediction markets. 
            Our 4-agent AI pipeline scans, analyzes, estimates, and generates signals 
            in under 12 seconds.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {isAuthenticated ? (
              <button
                onClick={() => navigate("/markets")}
                className="px-8 py-4 bg-[#00d4ff] text-[#0a0e17] rounded-xl font-bold text-base hover:brightness-110 transition-all flex items-center gap-2"
              >
                Explore Markets
                <ChevronRight className="w-5 h-5" />
              </button>
            ) : (
              <button
                onClick={() => navigate("/auth")}
                className="px-8 py-4 bg-[#00d4ff] text-[#0a0e17] rounded-xl font-bold text-base hover:brightness-110 transition-all flex items-center gap-2"
              >
                Get Started
                <ArrowRight className="w-5 h-5" />
              </button>
            )}
            <button
              onClick={() => isAuthenticated ? navigate("/signals") : navigate("/auth")}
              className="px-8 py-4 bg-[#131a2b] border border-[#1a2030] text-[#dee2f5] rounded-xl font-medium text-base hover:border-[#00d4ff]/30 transition-all"
            >
              {isAuthenticated ? "View Signals" : "Learn More"}
            </button>
          </div>
        </div>
      </div>

      {/* Stats Banner */}
      <div className="border-y border-[#1a2030] bg-[#0f1420]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div>
              <p className="text-3xl font-bold text-[#00d4ff] font-mono-num">Live</p>
              <p className="text-sm text-[#8b92a8] mt-1">Prediction Markets</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-[#00ff88] font-mono-num">4</p>
              <p className="text-sm text-[#8b92a8] mt-1">AI Agents</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-[#ffa502] font-mono-num">&lt;12s</p>
              <p className="text-sm text-[#8b92a8] mt-1">Analysis Pipeline</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-[#ff6b81] font-mono-num">Real-time</p>
              <p className="text-sm text-[#8b92a8] mt-1">Price Data</p>
            </div>
          </div>
        </div>
      </div>

      {/* What is Quant Finance */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl font-bold text-[#dee2f5] mb-4">
              What is <span className="text-[#00d4ff]">Quantitative Finance?</span>
            </h2>
            <p className="text-[#8b92a8] leading-relaxed mb-4">
              Quantitative finance applies mathematical models, statistical analysis, and computational 
              algorithms to financial markets. In prediction markets, the core principle is simple: 
              find situations where the market-implied probability differs from your estimate of the 
              true probability.
            </p>
            <p className="text-[#8b92a8] leading-relaxed mb-4">
              EdgeIQ automates this process. We scan Bayse markets for events with pricing inefficiencies, 
              run quantitative metrics on order books and price history, use Google's Gemini AI with 
              Search Grounding to research real-world context, and generate actionable trade signals 
              with Kelly Criterion stake sizing.
            </p>
            <div className="flex items-center gap-2 text-sm text-[#00d4ff]">
              <LineChart className="w-4 h-4" />
              <span>Expected Value · Sharpe Ratio · Kelly Criterion</span>
            </div>
          </div>
          <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6">
            <h3 className="text-sm font-semibold text-[#dee2f5] mb-4">The Edge Equation</h3>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-lg bg-[#00d4ff]/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-[#00d4ff]">1</span>
                </div>
                <div>
                  <p className="text-sm text-[#dee2f5] font-medium">Market Scanner</p>
                  <p className="text-xs text-[#8b92a8]">Discover active prediction markets with volume & liquidity</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-lg bg-[#00ff88]/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-[#00ff88]">2</span>
                </div>
                <div>
                  <p className="text-sm text-[#dee2f5] font-medium">Quant Analyzer</p>
                  <p className="text-xs text-[#8b92a8]">Calculate momentum, volume acceleration, and order book bias</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-lg bg-[#ffa502]/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-[#ffa502]">3</span>
                </div>
                <div>
                  <p className="text-sm text-[#dee2f5] font-medium">AI Probability</p>
                  <p className="text-xs text-[#8b92a8]">Gemini researches events and estimates true probabilities</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-lg bg-[#ff6b81]/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-[#ff6b81]">4</span>
                </div>
                <div>
                  <p className="text-sm text-[#dee2f5] font-medium">Signal Generator</p>
                  <p className="text-xs text-[#8b92a8]">Compute edge, expected value, and optimal stake size</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 border-t border-[#1a2030]">
        <h2 className="text-2xl font-bold text-[#dee2f5] text-center mb-12">
          Built for <span className="text-[#00d4ff]">Serious Traders</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <FeatureCard
            icon={<Zap className="w-5 h-5 text-[#00d4ff]" />}
            title="4-Agent Pipeline"
            description="Market scanning, quant analysis, AI probability estimation, and signal generation — all automated in 8-12 seconds."
            color="#00d4ff"
          />
          <FeatureCard
            icon={<BrainCircuit className="w-5 h-5 text-[#00ff88]" />}
            title="Gemini-Powered AI"
            description="Google Gemini 1.5 Flash with Search Grounding researches events, news, and historical precedent for accurate probability estimates."
            color="#00ff88"
          />
          <FeatureCard
            icon={<Shield className="w-5 h-5 text-[#ffa502]" />}
            title="Kelly Criterion Sizing"
            description="Optimal stake sizing with conservative, balanced, and aggressive risk profiles. Never over-stake again."
            color="#ffa502"
          />
          <FeatureCard
            icon={<BarChart3 className="w-5 h-5 text-[#00d4ff]" />}
            title="Real-time Charts"
            description="Price history with implied probability overlays, order book depth visualization, and momentum indicators."
            color="#00d4ff"
          />
          <FeatureCard
            icon={<Target className="w-5 h-5 text-[#00ff88]" />}
            title="Calibration Dashboard"
            description="Track how well the AI's probability estimates match actual outcomes. Improve with Brier scores and accuracy metrics."
            color="#00ff88"
          />
          <FeatureCard
            icon={<Wallet className="w-5 h-5 text-[#ffa502]" />}
            title="Portfolio Analytics"
            description="Track open positions, PnL, win rates, Sharpe ratio, and Quant Performance Index (QPI) scores."
            color="#ffa502"
          />
          <FeatureCard
            icon={<Cpu className="w-5 h-5 text-[#ff6b81]" />}
            title="Backtest Engine"
            description="Run historical simulations with different strategies and bankroll sizes to validate your edge."
            color="#ff6b81"
          />
          <FeatureCard
            icon={<Globe className="w-5 h-5 text-[#00d4ff]" />}
            title="Live Markets"
            description="Crypto, sports, politics, entertainment, and more — all synced live from Bayse prediction markets."
            color="#00d4ff"
          />
          <FeatureCard
            icon={<Lock className="w-5 h-5 text-[#00ff88]" />}
            title="Firebase Auth"
            description="Secure authentication with Firebase. Your data stays protected and your sessions are encrypted."
            color="#00ff88"
          />
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 border-t border-[#1a2030]">
        <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-8 md:p-12 text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-[#dee2f5] mb-4">
            Ready to Find Your <span className="text-[#00d4ff]">Edge?</span>
          </h2>
          <p className="text-[#8b92a8] mb-8 max-w-xl mx-auto">
            Start exploring markets, analyze signals, and build a data-driven trading strategy 
            with EdgeIQ's AI-powered quant tools.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {isAuthenticated ? (
              <button
                onClick={() => navigate("/markets")}
                className="px-8 py-4 bg-[#00d4ff] text-[#0a0e17] rounded-xl font-bold text-base hover:brightness-110 transition-all flex items-center gap-2"
              >
                Launch Markets Explorer
                <ArrowRight className="w-5 h-5" />
              </button>
            ) : (
              <button
                onClick={() => navigate("/auth")}
                className="px-8 py-4 bg-[#00d4ff] text-[#0a0e17] rounded-xl font-bold text-base hover:brightness-110 transition-all flex items-center gap-2"
              >
                Get Started Free
                <ArrowRight className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 border-t border-[#1a2030] text-center">
        <p className="text-xs text-[#5a6070]">
          EdgeIQ — AI Quant Intelligence for Prediction Markets · Built with React, Django & Gemini
        </p>
      </div>
    </div>
  );
};

const FeatureCard = ({
  icon,
  title,
  description,
  color,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: string;
}) => (
  <div className="bg-[#131a2b] rounded-xl border border-[#1a2030] p-6 hover:border-[#00d4ff]/20 transition-all group">
    <div
      className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
      style={{ backgroundColor: `${color}15` }}
    >
      {icon}
    </div>
    <h3 className="font-bold text-[#dee2f5] mb-2">{title}</h3>
    <p className="text-sm text-[#8b92a8] leading-relaxed">{description}</p>
  </div>
);

export default HomePage;
