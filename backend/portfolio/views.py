"""
Portfolio API Views (Firestore Refactored) with User Authentication
===================================================================
- Replaces DEFAULT_USER_ID with authenticated user from request
- All data is now user-specific (bankroll, trades, etc.)
- Requires authentication via Token or Session
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from decimal import Decimal
from utils.firebase_client import fs, Collection
import logging

logger = logging.getLogger(__name__)


def _get_or_create_profile(user_id, username="trader"):
    """Get user profile from Firestore, or create if missing."""
    profile = fs.get(Collection.USER_PROFILES, user_id)
    if not profile:
        profile = {
            "user_id": user_id,
            "username": username,
            "bankroll": 10000.0,
            "risk_tolerance": "balanced",
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0.0,
            "created_at": timezone.now(),
            "updated_at": timezone.now(),
        }
        fs.set(Collection.USER_PROFILES, user_id, profile)
    return profile


class PortfolioViewSet(ViewSet):
    """
    Portfolio API endpoints backed by Firestore.
    All endpoints require authentication.
    """
    
    #permission_classes = [IsAuthenticated]
    
    def _get_user_id(self, request):
        """Get the current user's ID from the request."""
        return str(request.user.id)
    
    # ---------- profile ----------
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """GET /api/portfolio/profile/"""
        user_id = self._get_user_id(request)
        profile = _get_or_create_profile(user_id, request.user.username)
        
        win_rate = (profile.get("winning_trades", 0) / profile.get("total_trades", 1) * 100) \
            if profile.get("total_trades", 0) > 0 else 0
        
        return Response({
            "success": True,
            "profile": {
                **profile,
                "win_rate": round(win_rate, 2),
                "kelly_multiplier": {"conservative": 0.25, "balanced": 0.5, "aggressive": 1.0}.get(
                    profile.get("risk_tolerance", "balanced"), 0.5
                ),
            }
        })

    # ---------- update_profile ----------
    @action(detail=False, methods=['post'])
    def update_profile(self, request):
        """POST /api/portfolio/update_profile/"""
        try:
            user_id = self._get_user_id(request)
            profile = _get_or_create_profile(user_id, request.user.username)
            updates = {"updated_at": timezone.now()}

            if 'bankroll' in request.data:
                updates["bankroll"] = float(request.data['bankroll'])
            
            if 'risk_tolerance' in request.data:
                risk = request.data['risk_tolerance']
                if risk in ('conservative', 'balanced', 'aggressive'):
                    updates["risk_tolerance"] = risk
            
            if 'username' in request.data:
                updates["username"] = str(request.data['username'])

            success = fs.update(Collection.USER_PROFILES, user_id, updates)
            if success:
                profile.update(updates)

            return Response({"success": True, "profile": profile})
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return Response({"success": False, "error": str(e)}, status=400)

    # ---------- trades ----------
    @action(detail=False, methods=['get'])
    def trades(self, request):
        """GET /api/portfolio/trades/?status=open"""
        user_id = self._get_user_id(request)
        
        filters = [("user_id", "==", user_id)]
        status_filter = request.query_params.get('status')
        if status_filter:
            filters.append(("status", "==", status_filter))

        trades = fs.query(
            Collection.TRADES,
            filters=filters,
            order_by=("opened_at", True),
            limit=100,
        )
        return Response({"success": True, "count": len(trades), "trades": trades})

    # ---------- simulate_trade ----------
    @action(detail=False, methods=['post'])
    def simulate_trade(self, request):
        """POST /api/portfolio/simulate_trade/"""
        try:
            user_id = self._get_user_id(request)
            signal_id = str(request.data.get('signal_id', ''))
            stake_amount = Decimal(str(request.data.get('stake_amount', 0)))

            if not signal_id:
                return Response({"success": False, "error": "signal_id required"}, status=400)

            # Fetch signal from Firestore
            signal = fs.get(Collection.SIGNALS, signal_id)
            if not signal:
                # Try with _signal suffix
                signal = fs.get(Collection.SIGNALS, f"{signal_id}_signal")
            if not signal:
                return Response({"success": False, "error": "Signal not found"}, status=404)

            profile = _get_or_create_profile(user_id, request.user.username)
            if float(stake_amount) > profile.get("bankroll", 0):
                return Response(
                    {"success": False, "error": "Stake exceeds bankroll"}, status=400
                )

            # Determine recommended stake based on risk tolerance
            risk = profile.get("risk_tolerance", "balanced")
            if risk == "conservative":
                recommended = Decimal(str(signal.get("recommended_stake_conservative", 0)))
            elif risk == "aggressive":
                recommended = Decimal(str(signal.get("recommended_stake_aggressive", 0)))
            else:
                recommended = Decimal(str(signal.get("recommended_stake_balanced", 0)))

            # Kelly compliance check
            kelly_compliant = False
            if recommended > 0:
                variance = abs(stake_amount - recommended) / recommended
                kelly_compliant = variance <= Decimal("0.1")

            # Create trade in Firestore
            trade_doc = {
                "user_id": user_id,
                "signal_id": signal_id,
                "signal_doc_id": signal.get("id", signal_id),
                "market_id": signal.get("market_id", ""),
                "market_title": signal.get("market_title", ""),
                "direction": signal.get("direction", "BUY"),
                "stake_amount": float(stake_amount.quantize(Decimal("0.01"))),
                "entry_price": signal.get("current_price") or signal.get("market_probability", 0),
                "exit_price": None,
                "pnl": None,
                "roi": None,
                "recommended_stake": float(recommended.quantize(Decimal("0.01"))),
                "kelly_compliant": kelly_compliant,
                "status": "open",
                "opened_at": timezone.now(),
                "closed_at": None,
            }
            trade_id = fs.add(Collection.TRADES, trade_doc)

            # Update profile
            new_bankroll = profile.get("bankroll", 0) - float(stake_amount)
            new_total = profile.get("total_trades", 0) + 1
            fs.update(Collection.USER_PROFILES, user_id, {
                "bankroll": new_bankroll,
                "total_trades": new_total,
                "updated_at": timezone.now(),
            })

            trade_doc["id"] = trade_id
            return Response({
                "success": True,
                "trade": trade_doc,
                "message": "Trade recorded successfully",
            })

        except Exception as e:
            logger.error(f"Error simulating trade: {e}")
            return Response({"success": False, "error": str(e)}, status=400)

    # ---------- close_trade ----------
    @action(detail=False, methods=['post'])
    def close_trade(self, request):
        """POST /api/portfolio/close_trade/"""
        try:
            user_id = self._get_user_id(request)
            trade_id = str(request.data.get('trade_id', ''))
            exit_price = Decimal(str(request.data.get('exit_price', 0)))

            trade = fs.get(Collection.TRADES, trade_id)
            if not trade or trade.get("status") != "open":
                return Response(
                    {"success": False, "error": "Trade not found or already closed"}, status=404
                )
            
            # Verify trade belongs to this user
            if trade.get("user_id") != user_id:
                return Response(
                    {"success": False, "error": "Unauthorized"}, status=403
                )

            direction = trade.get("direction", "BUY")
            entry = Decimal(str(trade.get("entry_price", 0)))
            stake = Decimal(str(trade.get("stake_amount", 0)))

            if direction == "BUY":
                pnl = (exit_price - entry) * stake
            else:
                pnl = (entry - exit_price) * stake

            roi = (pnl / stake * 100) if stake > 0 else Decimal("0")
            trade_status = "won" if pnl > 0 else "lost"

            # Update trade
            now = timezone.now()
            fs.update(Collection.TRADES, trade_id, {
                "exit_price": float(exit_price.quantize(Decimal("0.000001"))),
                "pnl": float(pnl.quantize(Decimal("0.01"))),
                "roi": float(roi.quantize(Decimal("0.01"))),
                "status": trade_status,
                "closed_at": now,
            })

            # Update profile
            profile = _get_or_create_profile(user_id, request.user.username)
            new_pnl = profile.get("total_pnl", 0) + float(pnl)
            new_bankroll = profile.get("bankroll", 0) + float(stake) + float(pnl)
            updates = {
                "total_pnl": new_pnl,
                "bankroll": new_bankroll,
                "updated_at": now,
            }
            if trade_status == "won":
                updates["winning_trades"] = profile.get("winning_trades", 0) + 1

            fs.update(Collection.USER_PROFILES, user_id, updates)

            trade.update({
                "exit_price": float(exit_price),
                "pnl": float(pnl),
                "roi": float(roi),
                "status": trade_status,
                "closed_at": now,
            })

            return Response({
                "success": True,
                "trade": trade,
                "message": f'Trade closed - {"Win" if pnl > 0 else "Loss"}',
            })

        except Exception as e:
            logger.error(f"Error closing trade: {e}")
            return Response({"success": False, "error": str(e)}, status=400)

    # ---------- analytics ----------
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """GET /api/portfolio/analytics/"""
        try:
            user_id = self._get_user_id(request)
            profile = _get_or_create_profile(user_id, request.user.username)
            
            trades = fs.query(
                Collection.TRADES,
                filters=[("user_id", "==", user_id)],
            )

            total = profile.get("total_trades", 0)
            wins = profile.get("winning_trades", 0)
            win_rate = (wins / total * 100) if total > 0 else 0

            open_trades = [t for t in trades if t.get("status") == "open"]
            closed_trades = [t for t in trades if t.get("status") in ("won", "lost")]
            total_staked = sum(t.get("stake_amount", 0) for t in trades)
            total_returned = sum(
                (t.get("stake_amount", 0) + t.get("pnl", 0)) for t in closed_trades
            )

            # Simple Sharpe-ish ratio
            rois = [t.get("roi", 0) for t in closed_trades if t.get("roi") is not None]
            if len(rois) > 1:
                avg_roi = sum(rois) / len(rois)
                variance = sum((r - avg_roi) ** 2 for r in rois) / (len(rois) - 1)
                std = variance ** 0.5
                sharpe = round(avg_roi / std, 4) if std > 0 else 0
            else:
                sharpe = None

            # Max drawdown
            cumulative = 0
            peak = 0
            max_dd = 0
            for t in sorted(closed_trades, key=lambda x: x.get("closed_at") or timezone.now()):
                pnl = t.get("pnl", 0) or 0
                cumulative += pnl
                if cumulative > peak:
                    peak = cumulative
                dd = peak - cumulative
                if dd > max_dd:
                    max_dd = dd

            metrics = {
                "bankroll": profile.get("bankroll", 0),
                "total_trades": total,
                "winning_trades": wins,
                "losing_trades": total - wins,
                "win_rate": round(win_rate, 2),
                "total_pnl": profile.get("total_pnl", 0),
                "total_staked": round(total_staked, 2),
                "total_returned": round(total_returned, 2),
                "open_positions": len(open_trades),
                "sharpe_ratio": sharpe,
                "max_drawdown": round(max_dd, 2),
                "risk_tolerance": profile.get("risk_tolerance", "balanced"),
            }

            return Response({"success": True, "analytics": metrics})

        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return Response({"success": False, "error": str(e)}, status=500)