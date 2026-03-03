"""Cash flow analysis service."""
from typing import Any, Dict, List
from app.services.financial_service import FinancialTransactionService


class CashFlowService:
    """Service class for cash flow analysis."""

    @staticmethod
    def get_monthly_cash_flow(project_id: int) -> List[Dict[str, Any]]:
        """Return monthly inflows/outflows/net/accumulated for a project."""
        return FinancialTransactionService.get_monthly_cash_flow(project_id)

    @staticmethod
    def get_seasonal_analysis(project_id: int) -> List[Dict[str, Any]]:
        """Return average cash flows by month number (1-12) to identify seasonal patterns."""
        monthly = FinancialTransactionService.get_monthly_cash_flow(project_id)
        buckets: Dict[int, Dict[str, Any]] = {}
        for row in monthly:
            month_num = int(row['month'].split('-')[1])
            if month_num not in buckets:
                buckets[month_num] = {'month_number': month_num, 'total_inflows': 0.0,
                                      'total_outflows': 0.0, 'count': 0}
            buckets[month_num]['total_inflows'] += row['inflows']
            buckets[month_num]['total_outflows'] += row['outflows']
            buckets[month_num]['count'] += 1

        result = []
        for m in range(1, 13):
            if m in buckets:
                b = buckets[m]
                count = b['count']
                result.append({
                    'month_number': m,
                    'avg_inflows': b['total_inflows'] / count,
                    'avg_outflows': b['total_outflows'] / count,
                    'avg_net': (b['total_inflows'] - b['total_outflows']) / count,
                })
            else:
                result.append({'month_number': m, 'avg_inflows': 0.0,
                               'avg_outflows': 0.0, 'avg_net': 0.0})
        return result

    @staticmethod
    def get_cash_flow_projection(project_id: int, months_ahead: int = 3) -> List[Dict[str, Any]]:
        """Project future months based on average monthly net cash flow."""
        monthly = FinancialTransactionService.get_monthly_cash_flow(project_id)
        if not monthly:
            return []
        avg_net = sum(r['net_cash_flow'] for r in monthly) / len(monthly)
        avg_inflows = sum(r['inflows'] for r in monthly) / len(monthly)
        avg_outflows = sum(r['outflows'] for r in monthly) / len(monthly)
        last_accumulated = monthly[-1]['accumulated_cash_flow'] if monthly else 0.0

        projections = []
        last_month_str = monthly[-1]['month']
        year, month = int(last_month_str.split('-')[0]), int(last_month_str.split('-')[1])
        accumulated = last_accumulated
        for _ in range(months_ahead):
            month += 1
            if month > 12:
                month = 1
                year += 1
            accumulated += avg_net
            projections.append({
                'month': f'{year:04d}-{month:02d}',
                'inflows': avg_inflows,
                'outflows': avg_outflows,
                'net_cash_flow': avg_net,
                'accumulated_cash_flow': accumulated,
                'projected': True,
            })
        return projections

    @staticmethod
    def simulate_scenario(project_id: int, budget_variance_pct: float,
                          schedule_variance_pct: float) -> List[Dict[str, Any]]:
        """Return adjusted cash flows based on variance percentages."""
        monthly = FinancialTransactionService.get_monthly_cash_flow(project_id)
        budget_factor = 1 + float(budget_variance_pct) / 100
        schedule_factor = 1 + float(schedule_variance_pct) / 100
        result = []
        accumulated = 0.0
        for row in monthly:
            adj_outflows = row['outflows'] * budget_factor
            adj_inflows = row['inflows'] * schedule_factor
            net = adj_inflows - adj_outflows
            accumulated += net
            result.append({
                'month': row['month'],
                'inflows': adj_inflows,
                'outflows': adj_outflows,
                'net_cash_flow': net,
                'accumulated_cash_flow': accumulated,
            })
        return result
