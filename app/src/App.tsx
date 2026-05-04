import MarketDeepDive from "./pages/MarketDeepDive";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Suspense, lazy, useEffect } from "react";
import { useAuthStore } from "./stores";
import { initAuthListener } from "./lib/firebase";
import DashboardLayout from "./components/DashboardLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import LoadingScreen from "./components/LoadingScreen";

const HomePage = lazy(() => import("./pages/HomePage"));
const AuthPage = lazy(() => import("./pages/AuthPage"));
const ProfilePage = lazy(() => import("./pages/ProfilePage"));
const SignalFeed = lazy(() => import("./pages/SignalFeed"));
const MarketsExplorer = lazy(() => import("./pages/MarketsExplorer"));
const Backtester = lazy(() => import("./pages/Backtester"));
const Portfolio = lazy(() => import("./pages/Portfolio"));
const Calibration = lazy(() => import("./pages/Calibration"));
const Settings = lazy(() => import("./pages/Settings"));
const Onboarding = lazy(() => import("./pages/Onboarding"));

function App() {
  const { setAuthenticated, setUser, setToken, setAuthLoading, authLoading, isAuthenticated } = useAuthStore();

  useEffect(() => {
    setAuthLoading(true);
    const unsubscribe = initAuthListener((firebaseUser) => {
      if (firebaseUser) {
        setAuthenticated(true);
        setUser({
          id: firebaseUser.uid,
          username: firebaseUser.displayName || firebaseUser.email?.split("@")[0] || "trader",
          email: firebaseUser.email || "",
          displayName: firebaseUser.displayName || "",
        });
      } else {
        setAuthenticated(false);
        setUser(null);
        setToken(null);
      }
      setAuthLoading(false);
    });
    return () => unsubscribe();
  }, [setAuthenticated, setUser, setToken, setAuthLoading]);

  if (authLoading && !window.location.pathname.startsWith("/market/")) return <LoadingScreen message="Initializing EdgeIQ..." />;

  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingScreen message="Loading..." />}>
        <Routes>
          {/* Public routes */}
          <Route path="/auth" element={isAuthenticated ? <Navigate to="/markets" replace /> : <AuthPage />} />
          <Route path="/onboarding" element={<Onboarding />} />

          {/* Protected routes — with sidebar */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/home" element={<HomePage />} />
              <Route path="/markets" element={<MarketsExplorer />} />
              <Route path="/signals" element={<SignalFeed />} />
              <Route path="/market/:id" element={<MarketDeepDive />} />
              <Route path="/backtest" element={<Backtester />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/calibration" element={<Calibration />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>
          </Route>

          {/* Public landing page — same content, no sidebar */}
          <Route path="/" element={<HomePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
