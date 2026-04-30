import { create } from 'zustand';
import type { Market, Signal, Trade, UserProfile, BacktestResult, CalibrationData, AccuracyMetrics, SignalStats, QuantMetrics, AIAnalysis } from '@/types';

interface MarketState {
  markets: Market[];
  filteredMarkets: Market[];
  selectedMarket: Market | null;
  quantMetrics: QuantMetrics | null;
  aiAnalysis: AIAnalysis | null;
  priceHistory: Array<{ price: number; timestamp: string; volume?: number }>;
  orderBook: { bids: Array<{ price: number; quantity: number }>; asks: Array<{ price: number; quantity: number }> } | null;
  loading: boolean;
  error: string | null;
  viewMode: 'grid' | 'list';
  filters: {
    categories: string[];
    status: string;
    sortBy: string;
    timeRange: string;
    search: string;
    minLiquidity: boolean;
  };
  setMarkets: (markets: Market[]) => void;
  setFilteredMarkets: (markets: Market[]) => void;
  setSelectedMarket: (market: Market | null) => void;
  setQuantMetrics: (metrics: QuantMetrics | null) => void;
  setAiAnalysis: (analysis: AIAnalysis | null) => void;
  setPriceHistory: (history: Array<{ price: number; timestamp: string; volume?: number }>) => void;
  setOrderBook: (ob: { bids: Array<{ price: number; quantity: number }>; asks: Array<{ price: number; quantity: number }> } | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setViewMode: (mode: 'grid' | 'list') => void;
  setFilters: (filters: Partial<MarketState['filters']>) => void;
  applyFilters: () => void;
}

export const useMarketStore = create<MarketState>((set, get) => ({
  markets: [],
  filteredMarkets: [],
  selectedMarket: null,
  quantMetrics: null,
  aiAnalysis: null,
  priceHistory: [],
  orderBook: null,
  loading: false,
  error: null,
  viewMode: 'grid',
  filters: {
    categories: [],
    status: 'open',
    sortBy: 'volume',
    timeRange: 'all',
    search: '',
    minLiquidity: false,
  },
  setMarkets: (markets) => {
    set({ markets });
    get().applyFilters();
  },
  setFilteredMarkets: (filteredMarkets) => set({ filteredMarkets }),
  setSelectedMarket: (market) => set({ selectedMarket: market }),
  setQuantMetrics: (metrics) => set({ quantMetrics: metrics }),
  setAiAnalysis: (analysis) => set({ aiAnalysis: analysis }),
  setPriceHistory: (history) => set({ priceHistory: history }),
  setOrderBook: (ob) => set({ orderBook: ob }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setFilters: (newFilters) => {
    set((state) => ({ filters: { ...state.filters, ...newFilters } }));
    get().applyFilters();
  },
  applyFilters: () => {
    const { markets, filters } = get();
    let result = [...markets];

    if (filters.categories.length > 0) {
      result = result.filter((m) => filters.categories.includes(m.category));
    }

    if (filters.search) {
      const q = filters.search.toLowerCase();
      result = result.filter((m) => m.title.toLowerCase().includes(q));
    }

    if (filters.minLiquidity) {
      result = result.filter((m) => m.liquidity > 5000);
    }

    switch (filters.sortBy) {
      case 'volume':
        result.sort((a, b) => b.total_volume - a.total_volume);
        break;
      case 'edge':
        result.sort((a, b) => (b.edge_score || 0) - (a.edge_score || 0));
        break;
      case 'time_asc':
        result.sort((a, b) => (a.time_remaining_hours || 9999) - (b.time_remaining_hours || 9999));
        break;
      case 'time_desc':
        result.sort((a, b) => (b.time_remaining_hours || 0) - (a.time_remaining_hours || 0));
        break;
      case 'change':
        result.sort((a, b) => Math.abs(b.volume_24h || 0) - Math.abs(a.volume_24h || 0));
        break;
    }

    set({ filteredMarkets: result });
  },
}));

interface SignalState {
  signals: Signal[];
  activeSignals: Signal[];
  selectedSignal: Signal | null;
  stats: SignalStats | null;
  loading: boolean;
  error: string | null;
  minEdgeFilter: number;
  categoryFilter: string | null;
  setSignals: (signals: Signal[]) => void;
  setActiveSignals: (signals: Signal[]) => void;
  setSelectedSignal: (signal: Signal | null) => void;
  setStats: (stats: SignalStats | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setMinEdgeFilter: (minEdge: number) => void;
  setCategoryFilter: (category: string | null) => void;
}

export const useSignalStore = create<SignalState>((set) => ({
  signals: [],
  activeSignals: [],
  selectedSignal: null,
  stats: null,
  loading: false,
  error: null,
  minEdgeFilter: 0,
  categoryFilter: null,
  setSignals: (signals) => set({ signals }),
  setActiveSignals: (activeSignals) => set({ activeSignals }),
  setSelectedSignal: (selectedSignal) => set({ selectedSignal }),
  setStats: (stats) => set({ stats }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setMinEdgeFilter: (minEdgeFilter) => set({ minEdgeFilter }),
  setCategoryFilter: (categoryFilter) => set({ categoryFilter }),
}));

interface PortfolioState {
  profile: UserProfile | null;
  trades: Trade[];
  openTrades: Trade[];
  closedTrades: Trade[];
  analytics: Record<string, number | null> | null;
  loading: boolean;
  setProfile: (profile: UserProfile | null) => void;
  setTrades: (trades: Trade[]) => void;
  setAnalytics: (analytics: Record<string, number | null> | null) => void;
  setLoading: (loading: boolean) => void;
  updateProfile: (updates: Partial<UserProfile>) => void;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  profile: null,
  trades: [],
  openTrades: [],
  closedTrades: [],
  analytics: null,
  loading: false,
  setProfile: (profile) => set({ profile }),
  setTrades: (trades) => {
    const openTrades = trades.filter((t) => t.status === 'open');
    const closedTrades = trades.filter((t) => t.status === 'won' || t.status === 'lost');
    set({ trades, openTrades, closedTrades });
  },
  setAnalytics: (analytics) => set({ analytics }),
  setLoading: (loading) => set({ loading }),
  updateProfile: (updates) =>
    set((state) => ({
      profile: state.profile ? { ...state.profile, ...updates } : null,
    })),
}));

interface BacktestState {
  strategies: Array<{ id: string; name: string; description: string; params: Record<string, number> }>;
  results: BacktestResult | null;
  history: Array<{ strategy_config: Record<string, unknown>; initial_bankroll: number; results: BacktestResult; created_at: string }>;
  loading: boolean;
  selectedStrategy: string | null;
  setStrategies: (strategies: BacktestState['strategies']) => void;
  setResults: (results: BacktestResult | null) => void;
  setHistory: (history: BacktestState['history']) => void;
  setLoading: (loading: boolean) => void;
  setSelectedStrategy: (selectedStrategy: string | null) => void;
}

export const useBacktestStore = create<BacktestState>((set) => ({
  strategies: [],
  results: null,
  history: [],
  loading: false,
  selectedStrategy: null,
  setStrategies: (strategies) => set({ strategies }),
  setResults: (results) => set({ results }),
  setHistory: (history) => set({ history }),
  setLoading: (loading) => set({ loading }),
  setSelectedStrategy: (selectedStrategy) => set({ selectedStrategy }),
}));

interface CalibrationState {
  calibrationData: CalibrationData | null;
  accuracyMetrics: AccuracyMetrics | null;
  loading: boolean;
  setCalibrationData: (data: CalibrationData | null) => void;
  setAccuracyMetrics: (metrics: AccuracyMetrics | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useCalibrationStore = create<CalibrationState>((set) => ({
  calibrationData: null,
  accuracyMetrics: null,
  loading: false,
  setCalibrationData: (calibrationData) => set({ calibrationData }),
  setAccuracyMetrics: (accuracyMetrics) => set({ accuracyMetrics }),
  setLoading: (loading) => set({ loading }),
}));

interface AuthState {
  isAuthenticated: boolean;
  user: { id: string; username: string; email?: string } | null;
  token: string | null;
  onboardingComplete: boolean;
  setAuthenticated: (auth: boolean) => void;
  setUser: (user: AuthState['user']) => void;
  setToken: (token: string | null) => void;
  setOnboardingComplete: (complete: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  token: localStorage.getItem('edgeiq_token'),
  onboardingComplete: localStorage.getItem('edgeiq_onboarding') === 'complete',
  setAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (token) localStorage.setItem('edgeiq_token', token);
    else localStorage.removeItem('edgeiq_token');
    set({ token });
  },
  setOnboardingComplete: (onboardingComplete) => {
    if (onboardingComplete) localStorage.setItem('edgeiq_onboarding', 'complete');
    else localStorage.removeItem('edgeiq_onboarding');
    set({ onboardingComplete });
  },
  logout: () => {
    localStorage.removeItem('edgeiq_token');
    localStorage.removeItem('edgeiq_onboarding');
    set({ isAuthenticated: false, user: null, token: null });
  },
}));
