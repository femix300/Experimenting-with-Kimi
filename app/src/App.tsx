import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
// import { useAuthStore } from "./stores";
import DashboardLayout from "./components/DashboardLayout";
import SignalFeed from "./pages/SignalFeed";
import MarketsExplorer from "./pages/MarketsExplorer";
import MarketDeepDive from "./pages/MarketDeepDive";
import Backtester from "./pages/Backtester";
import Portfolio from "./pages/Portfolio";
import Calibration from "./pages/Calibration";
import Settings from "./pages/Settings";
import Onboarding from "./pages/Onboarding";
import LandingPage from "./pages/LandingPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route element={<DashboardLayout />}>
          <Route path="/signals" element={<SignalFeed />} />
          <Route path="/markets" element={<MarketsExplorer />} />
          <Route path="/market/:id" element={<MarketDeepDive />} />
          <Route path="/backtest" element={<Backtester />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/calibration" element={<Calibration />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/signals" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
