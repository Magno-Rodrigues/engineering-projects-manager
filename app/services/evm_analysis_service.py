"""EVM analysis service."""
from typing import Any, Dict, List, Optional
from app.services.financial_service import FinancialEVMService


class EVMAnalysisService:
    """Service class for EVM analysis and charting data."""

    @staticmethod
    def get_scurve_data(project_id: int) -> List[Dict[str, Any]]:
        """Return PV, EV, AC series sorted by date for S-curve chart."""
        reports = FinancialEVMService.get_project_evm_reports(project_id)
        reports = sorted(reports, key=lambda r: r.report_date)
        return [
            {
                'date': r.report_date.strftime('%Y-%m-%d'),
                'pv': float(r.pv),
                'ev': float(r.ev),
                'ac': float(r.ac),
            }
            for r in reports
        ]

    @staticmethod
    def get_performance_trend(project_id: int) -> List[Dict[str, Any]]:
        """Return CPI and SPI trend across time."""
        reports = FinancialEVMService.get_project_evm_reports(project_id)
        reports = sorted(reports, key=lambda r: r.report_date)
        return [
            {
                'date': r.report_date.strftime('%Y-%m-%d'),
                'cpi': r.cpi,
                'spi': r.spi,
            }
            for r in reports
        ]

    @staticmethod
    def get_evm_summary(project_id: int) -> Optional[Dict[str, Any]]:
        """Return latest EVM values plus calculated indices and projections."""
        reports = FinancialEVMService.get_project_evm_reports(project_id)
        if not reports:
            return None
        latest = sorted(reports, key=lambda r: r.report_date)[-1]
        return {
            'report_date': latest.report_date.strftime('%Y-%m-%d'),
            'bac': float(latest.bac),
            'ac': float(latest.ac),
            'ev': float(latest.ev),
            'pv': float(latest.pv),
            'cpi': latest.cpi,
            'spi': latest.spi,
            'cost_variance': float(latest.cost_variance),
            'schedule_variance': float(latest.schedule_variance),
            'eac': latest.calculated_eac,
            'etc': latest.calculated_etc,
        }

    @staticmethod
    def get_variance_analysis(project_id: int) -> List[Dict[str, Any]]:
        """Return cost variance and schedule variance analysis across time."""
        reports = FinancialEVMService.get_project_evm_reports(project_id)
        reports = sorted(reports, key=lambda r: r.report_date)
        return [
            {
                'date': r.report_date.strftime('%Y-%m-%d'),
                'cost_variance': float(r.cost_variance),
                'schedule_variance': float(r.schedule_variance),
                'cpi': r.cpi,
                'spi': r.spi,
            }
            for r in reports
        ]
