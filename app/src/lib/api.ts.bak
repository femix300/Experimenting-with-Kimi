/**
 * EdgeIQ API Client
 * All Bayse API calls route through the Django backend
 * Base URL is configurable via environment variable
 */

import type {
  Market,
  Signal,
  Trade,
  UserProfile,
  BacktestResult,
  BacktestStrategy,
  CalibrationData,
  AccuracyMetrics,
  SignalStats,
  QuantMetrics,
  AIAnalysis,
  OrderBook,
  PricePoint,
} from '@/types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }
  return response.json();
}

// Markets
export async function scanMarkets(params?: {
  status?: string;
  min_volume?: number;
  min_liquidity?: number;
  max_results?: number;
  category?: string;
}): Promise<{ success: boolean; count: number; markets: Market[] }> {
  return fetchJSON(`${API_BASE}/markets/scan/`, {
    method: 'POST',
    body: JSON.stringify(params || {}),
  });
}

export async function getMarkets(params?: {
  status?: string;
  category?: string;
  page?: number;
  page_size?: number;
}): Promise<{ results: Market[]; count: number }> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.category) qs.set('category', params.category);
  if (params?.page) qs.set('page', String(params.page));
  if (params?.page_size) qs.set('page_size', String(params.page_size));
  return fetchJSON(`${API_BASE}/markets/?${qs.toString()}`);
}

export async function getTopMarkets(limit?: number, category?: string): Promise<{ success: boolean; count: number; markets: Market[] }> {
  const qs = new URLSearchParams();
  if (limit) qs.set('limit', String(limit));
  if (category) qs.set('category', category);
  return fetchJSON(`${API_BASE}/markets/top/?${qs.toString()}`);
}

export async function getMarketDetail(id: string): Promise<Market> {
  return fetchJSON(`${API_BASE}/markets/${id}/`);
}

export async function analyzeMarket(id: string, userBankroll?: number): Promise<{
  success: boolean;
  market: Market;
  quant_metrics: QuantMetrics;
  ai_analysis: AIAnalysis;
  signal: Signal;
}> {
  return fetchJSON(`${API_BASE}/markets/${id}/analyze/`, {
    method: 'POST',
    body: JSON.stringify({ user_bankroll: userBankroll || 10000 }),
  });
}

export async function getPriceHistory(eventId: string): Promise<PricePoint[]> {
  return fetchJSON(`${API_BASE}/markets/price-history/?event_id=${eventId}`);
}

export async function getOrderBook(eventId: string): Promise<OrderBook> {
  return fetchJSON(`${API_BASE}/markets/order-book/?event_id=${eventId}`);
}

// Signals
export async function getSignals(params?: {
  is_active?: boolean;
  direction?: string;
  min_edge?: number;
  strength?: string;
  category?: string;
}): Promise<{ success: boolean; count: number; signals: Signal[] }> {
  const qs = new URLSearchParams();
  if (params?.is_active !== undefined) qs.set('is_active', String(params.is_active));
  if (params?.direction) qs.set('direction', params.direction);
  if (params?.min_edge) qs.set('min_edge', String(params.min_edge));
  if (params?.strength) qs.set('strength', params.strength);
  if (params?.category) qs.set('category', params.category);
  return fetchJSON(`${API_BASE}/signals/?${qs.toString()}`);
}

export async function getActiveSignals(limit?: number, min_edge?: number): Promise<{ success: boolean; count: number; signals: Signal[] }> {
  const qs = new URLSearchParams();
  if (limit) qs.set('limit', String(limit));
  if (min_edge) qs.set('min_edge', String(min_edge));
  return fetchJSON(`${API_BASE}/signals/active/?${qs.toString()}`);
}

export async function getSignalStats(): Promise<{ success: boolean; stats: SignalStats }> {
  return fetchJSON(`${API_BASE}/signals/stats/`);
}

export async function getCalibrationData(): Promise<{ success: boolean; calibration_points: CalibrationData['calibration_points']; perfect_line: CalibrationData['perfect_line']; total_markets_analyzed: number }> {
  return fetchJSON(`${API_BASE}/signals/calibration-curve/`);
}

export async function getAccuracyMetrics(): Promise<{ success: boolean; metrics: AccuracyMetrics }> {
  return fetchJSON(`${API_BASE}/signals/accuracy-metrics/`);
}

// Portfolio
export async function getProfile(): Promise<{ success: boolean; profile: UserProfile }> {
  return fetchJSON(`${API_BASE}/portfolio/profile/`);
}

export async function updateProfile(data: Partial<UserProfile>): Promise<{ success: boolean; profile: UserProfile }> {
  return fetchJSON(`${API_BASE}/portfolio/update_profile/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getTrades(status?: string): Promise<{ success: boolean; count: number; trades: Trade[] }> {
  const qs = new URLSearchParams();
  if (status) qs.set('status', status);
  return fetchJSON(`${API_BASE}/portfolio/trades/?${qs.toString()}`);
}

export async function simulateTrade(signalId: string, stakeAmount: number): Promise<{ success: boolean; trade: Trade }> {
  return fetchJSON(`${API_BASE}/portfolio/simulate_trade/`, {
    method: 'POST',
    body: JSON.stringify({ signal_id: signalId, stake_amount: stakeAmount }),
  });
}

export async function closeTrade(tradeId: string, exitPrice: number): Promise<{ success: boolean; trade: Trade }> {
  return fetchJSON(`${API_BASE}/portfolio/close_trade/`, {
    method: 'POST',
    body: JSON.stringify({ trade_id: tradeId, exit_price: exitPrice }),
  });
}

export async function getAnalytics(): Promise<{ success: boolean; analytics: Record<string, number | null> }> {
  return fetchJSON(`${API_BASE}/portfolio/analytics/`);
}

// Backtesting
export async function getBacktestStrategies(): Promise<{ success: boolean; strategies: BacktestStrategy[] }> {
  return fetchJSON(`${API_BASE}/backtest/strategies/`);
}

export async function runBacktest(strategyConfig: Record<string, unknown>, initialBankroll?: number): Promise<{ success: boolean; result: BacktestResult }> {
  return fetchJSON(`${API_BASE}/backtest/run/`, {
    method: 'POST',
    body: JSON.stringify({
      strategy_config: strategyConfig,
      initial_bankroll: initialBankroll || 10000,
    }),
  });
}

export async function getBacktestResults(): Promise<{ success: boolean; results: Array<{ strategy_config: Record<string, unknown>; initial_bankroll: number; results: BacktestResult; created_at: string }> }> {
  return fetchJSON(`${API_BASE}/backtest/results/`);
}

// QPI
export async function getQPI(): Promise<{ success: boolean; qpi: { score: number; trend: string; version: number; calculated_at: string; components: Record<string, number> } }> {
  return fetchJSON(`${API_BASE}/portfolio/qpi/`);
}

// Health
export async function getHealth(): Promise<{ status: string; services: Record<string, string> }> {
  return fetchJSON(`${API_BASE.replace('/api', '')}/health/`);
}
