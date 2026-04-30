/**
 * EdgeIQ Type Definitions
 * Shared types for the frontend application
 */

export interface Market {
  id: string;
  bayse_event_id: string;
  bayse_market_id: string;
  title: string;
  description?: string;
  category: 'crypto' | 'sports' | 'politics' | 'entertainment' | 'other';
  current_price: number;
  implied_probability: number;
  volume_24h: number;
  total_volume: number;
  liquidity: number;
  status: string;
  opens_at?: string;
  closes_at?: string;
  resolved_at?: string;
  signal_potential_score: number;
  last_scanned_at?: string;
  edge_score?: number;
  time_remaining_hours?: number;
}

export interface QuantMetrics {
  market_id: string;
  market_title: string;
  momentum_score: number;
  momentum_direction: 'bullish' | 'bearish' | 'neutral';
  price_change_1h: number;
  price_change_6h: number;
  price_change_24h: number;
  volume_acceleration: number;
  volume_trend: 'increasing' | 'decreasing' | 'stable';
  bid_ask_spread: number;
  order_book_bias: 'bullish' | 'bearish' | 'neutral';
  bid_depth: number;
  ask_depth: number;
  calculated_at: string;
}

export interface AIAnalysis {
  market_id: string;
  market_title: string;
  probability: number;
  confidence: number;
  reasoning: string;
  sources: string;
  model_used: string;
  search_grounding_used: boolean;
  analyzed_at: string;
}

export interface Signal {
  id: string;
  market_id: string;
  market_title: string;
  market_event_id: string;
  category?: string;
  direction: 'BUY' | 'SELL' | 'WAIT';
  edge_score: number;
  expected_value: number;
  market_probability: number;
  ai_probability: number;
  model_used: string;
  confidence: number;
  confidence_level: 'high' | 'medium' | 'low';
  kelly_percentage: number;
  recommended_stake_conservative: number;
  recommended_stake_balanced: number;
  recommended_stake_aggressive: number;
  reasoning: string;
  news_context: string;
  is_active: boolean;
  signal_strength: 'strong' | 'moderate' | 'weak';
  created_at: string;
  expires_at?: string;
  quant_snapshot?: {
    momentum_score: number;
    momentum_direction: string;
    volume_acceleration: number;
    order_book_bias: string;
  };
}

export interface OrderBook {
  bids: Array<{ price: number; quantity: number }>;
  asks: Array<{ price: number; quantity: number }>;
}

export interface PricePoint {
  price: number;
  timestamp: string;
  volume?: number;
}

export interface Trade {
  id: string;
  user_id: string;
  signal_id: string;
  market_id: string;
  market_title: string;
  direction: string;
  stake_amount: number;
  entry_price: number;
  exit_price?: number;
  pnl?: number;
  roi?: number;
  recommended_stake: number;
  kelly_compliant: boolean;
  status: 'open' | 'won' | 'lost';
  opened_at: string;
  closed_at?: string;
}

export interface UserProfile {
  user_id: string;
  username: string;
  bankroll: number;
  risk_tolerance: 'conservative' | 'balanced' | 'aggressive';
  total_trades: number;
  winning_trades: number;
  total_pnl: number;
  created_at: string;
  updated_at: string;
  win_rate?: number;
  kelly_multiplier?: Record<string, number>;
  watchlist?: string[];
  tracked_categories?: string[];
}

export interface BacktestResult {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  trade_log: Array<{
    market_title: string;
    action: string;
    edge: number;
    is_win: boolean;
    pnl: number;
    timestamp: string;
  }>;
}

export interface BacktestStrategy {
  id: string;
  name: string;
  description: string;
  params: Record<string, number>;
}

export interface CalibrationPoint {
  bin: string;
  predicted: number;
  actual: number;
  count: number;
}

export interface CalibrationData {
  calibration_points: CalibrationPoint[];
  perfect_line: Array<{ predicted: number; actual: number }>;
  total_markets_analyzed: number;
}

export interface AccuracyMetrics {
  total_predictions: number;
  accuracy: number;
  brier_score: number;
  log_loss: number;
  calibration_error: number;
  perfect_accuracy: number;
  perfect_brier: number;
  perfect_log_loss: number;
  perfect_calibration_error: number;
}

export interface SignalStats {
  total_active: number;
  by_direction: Record<string, number>;
  by_strength: Record<string, number>;
  edge_stats: { avg_edge: number; max_edge: number; min_edge: number };
  confidence_stats: { avg_confidence: number; max_confidence: number; min_confidence: number };
}

export interface QPI {
  score: number;
  win_rate_weight: number;
  ev_accuracy_weight: number;
  kelly_compliance_weight: number;
  trend: 'up' | 'down' | 'stable';
  version: number;
  calculated_at: string;
}

export type Category = 'crypto' | 'sports' | 'politics' | 'entertainment' | 'other';

export const CATEGORY_COLORS: Record<Category, string> = {
  crypto: '#00d4ff',
  sports: '#00ff88',
  politics: '#ffa502',
  entertainment: '#ff6b81',
  other: '#a4b0be',
};

export const CATEGORY_LABELS: Record<Category, string> = {
  crypto: 'Crypto',
  sports: 'Sports',
  politics: 'Politics',
  entertainment: 'Entertainment',
  other: 'Other',
};
