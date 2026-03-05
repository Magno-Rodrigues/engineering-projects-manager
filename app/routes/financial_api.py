"""Financial REST API blueprint."""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.models.financial_report import REPORT_TYPES
from app.services.project_service import ProjectService
from app.services.financial_service import (
    FinancialTransactionService,
    FinancialBudgetService,
)
from app.services.cash_flow_service import CashFlowService
from app.services.evm_analysis_service import EVMAnalysisService
from app.services.reporting_service import ReportingService

financial_api_bp = Blueprint('financial_api', __name__, url_prefix='/api/projects')


def _get_project_or_error(project_id):
    """Return (project, None) or (None, error_response_tuple)."""
    project = ProjectService.get_project(project_id)
    if not project:
        return None, (jsonify({'error': 'Project not found'}), 404)
    if not (current_user.role == 'admin' or project.owner_id == current_user.id):
        return None, (jsonify({'error': 'Forbidden'}), 403)
    return project, None


@financial_api_bp.route('/<int:project_id>/financial/summary', methods=['GET'])
@login_required
def get_summary(project_id):
    """Return financial summary for a project."""
    project, err = _get_project_or_error(project_id)
    if err:
        return err
    summary = FinancialTransactionService.get_project_summary(project_id)
    evm = EVMAnalysisService.get_evm_summary(project_id)
    return jsonify({'summary': summary, 'evm': evm})


@financial_api_bp.route('/<int:project_id>/financial/budget', methods=['GET'])
@login_required
def get_budget(project_id):
    """Return active budget for a project."""
    project, err = _get_project_or_error(project_id)
    if err:
        return err
    budget = FinancialBudgetService.get_active_budget(project_id)
    if not budget:
        return jsonify({'budget': None})
    items = budget.items.all()
    return jsonify({
        'budget': {
            'id': budget.id,
            'status': budget.status,
            'total_planned_budget': float(budget.total_planned_budget),
            'currency': budget.currency,
            'baseline_date': str(budget.baseline_date),
            'items': [
                {
                    'id': i.id,
                    'description': i.description,
                    'planned_amount': float(i.planned_amount),
                    'category': i.category,
                }
                for i in items
            ],
        }
    })


@financial_api_bp.route('/<int:project_id>/financial/transactions', methods=['GET'])
@login_required
def get_transactions(project_id):
    """Return transactions for a project."""
    project, err = _get_project_or_error(project_id)
    if err:
        return err
    txns = FinancialTransactionService.get_project_transactions(project_id)
    return jsonify({
        'transactions': [
            {
                'id': t.id,
                'type': t.type,
                'description': t.description,
                'amount': float(t.amount),
                'category': t.category,
                'transaction_date': str(t.transaction_date),
                'payment_status': t.payment_status,
                'payment_method': t.payment_method,
                'invoice_number': t.invoice_number,
            }
            for t in txns
        ]
    })


@financial_api_bp.route('/<int:project_id>/financial/transactions', methods=['POST'])
@login_required
def create_transaction(project_id):
    """Create a new transaction for a project."""
    project, err = _get_project_or_error(project_id)
    if err:
        return err
    data = request.get_json() or {}
    required = ('type', 'description', 'amount', 'category', 'transaction_date')
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required.'}), 400
    txn, error = FinancialTransactionService.create_transaction(
        project_id=project_id,
        type=data['type'],
        description=data['description'],
        amount=data['amount'],
        category=data['category'],
        transaction_date=data['transaction_date'],
        created_by=current_user.id,
        cost_center_id=data.get('cost_center_id'),
        payment_status=data.get('payment_status', 'pending'),
        payment_method=data.get('payment_method'),
        supplier_id=data.get('supplier_id'),
        invoice_number=data.get('invoice_number'),
        notes=data.get('notes'),
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': txn.id, 'message': 'Transaction created.'}), 201


@financial_api_bp.route('/<int:project_id>/financial/transactions/<int:txn_id>', methods=['PUT'])
@login_required
def update_transaction(project_id, txn_id):
    """Update an existing transaction."""
    project, err = _get_project_or_error(project_id)
    if err:
        return err
    data = request.get_json() or {}
    txn, error = FinancialTransactionService.update_transaction(txn_id, **data)
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': txn.id, 'message': 'Transaction updated.'})


@financial_api_bp.route('/<int:project_id>/financial/transactions/<int:txn_id>', methods=['DELETE'])
@login_required
def delete_transaction_api(project_id, txn_id):
    """Delete a transaction."""
    project, err = _get_project_or_error(project_id)
    if err:
        return err
    success, error = FinancialTransactionService.delete_transaction(txn_id)
    if not success:
        return jsonify({'error': error}), 404
    return jsonify({'message': 'Transaction deleted.'})


@financial_api_bp.route('/<int:project_id>/financial/cash-flow', methods=['GET'])
@login_required
def get_cash_flow(project_id):
    """Return monthly cash flow data for a project."""
    project, err = _get_project_or_error(project_id)
    if err:
        return err
    data = CashFlowService.get_monthly_cash_flow(project_id)
    return jsonify({'cash_flow': data})


@financial_api_bp.route('/<int:project_id>/financial/evm', methods=['GET'])
@login_required
def get_evm(project_id):
    """Return EVM summary data for a project."""
    project, err = _get_project_or_error(project_id)
    if err:
        return err
    summary = EVMAnalysisService.get_evm_summary(project_id)
    scurve = EVMAnalysisService.get_scurve_data(project_id)
    trend = EVMAnalysisService.get_performance_trend(project_id)
    return jsonify({'evm_summary': summary, 'scurve': scurve, 'performance_trend': trend})


@financial_api_bp.route('/<int:project_id>/financial/reports', methods=['GET'])
@login_required
def get_reports(project_id):
    """Return list of reports for a project."""
    project, err = _get_project_or_error(project_id)
    if err:
        return err
    reports = ReportingService.get_project_reports(project_id)
    return jsonify({
        'reports': [
            {
                'id': r.id,
                'report_type': r.report_type,
                'format': r.format,
                'status': r.status,
                'generated_at': r.generated_at.isoformat() if r.generated_at else None,
                'file_path': r.file_path,
            }
            for r in reports
        ]
    })


@financial_api_bp.route('/<int:project_id>/financial/reports', methods=['POST'])
@login_required
def create_report(project_id):
    """Generate a new financial report."""
    project, err = _get_project_or_error(project_id)
    if err:
        return err
    data = request.get_json() or {}
    report_type = data.get('report_type', 'executive')
    if report_type not in REPORT_TYPES:
        return jsonify({'error': f'Invalid report_type. Must be one of: {", ".join(REPORT_TYPES)}.'}), 400
    report, error = ReportingService.generate_excel_report(
        project_id=project_id,
        report_type=report_type,
        generated_by=current_user.id,
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({
        'id': report.id,
        'report_type': report.report_type,
        'format': report.format,
        'status': report.status,
        'message': 'Report generated.',
    }), 201
