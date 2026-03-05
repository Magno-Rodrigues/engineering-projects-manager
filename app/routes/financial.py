"""Financial module routes."""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.services.project_service import ProjectService
from app.services.financial_service import (
    CostCenterService,
    FinancialBudgetService,
    FinancialTransactionService,
    FinancialEVMService,
    SupplierService,
)
from app.models.financial_budget import BUDGET_CATEGORIES, BUDGET_STATUSES
from app.models.financial_transaction import TRANSACTION_TYPES, TRANSACTION_CATEGORIES, PAYMENT_STATUSES, PAYMENT_METHODS
from app.services.cash_flow_service import CashFlowService
from app.services.evm_analysis_service import EVMAnalysisService
from app.services.reporting_service import ReportingService
from app.models.financial_scenario import FinancialScenario
from app.models.financial_report import REPORT_TYPES, REPORT_FORMATS
from app import db

financial_bp = Blueprint('financial', __name__, url_prefix='/projects')


def _parse_date(date_str):
    """Parse a date string (YYYY-MM-DD) into a date object or return None."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _get_project_or_abort(project_id: int):
    """Return project if current user is admin or owner, else flash error and return None."""
    project = ProjectService.get_project(project_id)
    if not project:
        flash('Projeto não encontrado.', 'error')
        return None
    if not (current_user.role == 'admin' or project.owner_id == current_user.id):
        flash('Acesso negado.', 'error')
        return None
    return project


# ---------------------------------------------------------------------------
# Financial Dashboard
# ---------------------------------------------------------------------------

@financial_bp.route('/<int:project_id>/financial')
@login_required
def dashboard(project_id: int):
    """Show the financial dashboard for a project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    summary = FinancialTransactionService.get_project_summary(project_id)
    active_budget = FinancialBudgetService.get_active_budget(project_id)
    latest_evm = FinancialEVMService.get_project_evm_reports(project_id)
    latest_evm = latest_evm[0] if latest_evm else None
    monthly_cash_flow = FinancialTransactionService.get_monthly_cash_flow(project_id)
    recent_transactions = FinancialTransactionService.get_project_transactions(project_id)[:5]

    return render_template(
        'projects/financial/dashboard.html',
        project=project,
        summary=summary,
        active_budget=active_budget,
        latest_evm=latest_evm,
        monthly_cash_flow=monthly_cash_flow,
        recent_transactions=recent_transactions,
    )


# ---------------------------------------------------------------------------
# Budget routes
# ---------------------------------------------------------------------------

@financial_bp.route('/<int:project_id>/financial/budgets', methods=['GET', 'POST'])
@login_required
def budgets(project_id: int):
    """List or create budgets for a project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    if request.method == 'POST':
        budget, error = FinancialBudgetService.create_budget(
            project_id=project_id,
            total_planned_budget=request.form.get('total_planned_budget'),
            baseline_date=request.form.get('baseline_date'),
            created_by=current_user.id,
            currency=request.form.get('currency', 'BRL'),
            notes=request.form.get('notes') or None,
        )
        if budget:
            flash('Orçamento criado com sucesso.', 'success')
        else:
            flash(error, 'error')
        return redirect(url_for('financial.budgets', project_id=project_id))

    budget_list = FinancialBudgetService.get_project_budgets(project_id)
    return render_template(
        'projects/financial/budgets.html',
        project=project,
        budgets=budget_list,
    )


@financial_bp.route('/<int:project_id>/financial/budgets/<int:budget_id>', methods=['GET', 'POST'])
@login_required
def budget_detail(project_id: int, budget_id: int):
    """Show budget details and manage budget items."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    budget = FinancialBudgetService.get_budget(budget_id)
    if not budget or budget.project_id != project_id:
        flash('Orçamento não encontrado.', 'error')
        return redirect(url_for('financial.budgets', project_id=project_id))

    if request.method == 'POST':
        item, error = FinancialBudgetService.add_budget_item(
            budget_id=budget_id,
            description=request.form.get('description', '').strip(),
            planned_amount=request.form.get('planned_amount'),
            category=request.form.get('category', 'other'),
            cost_center_id=request.form.get('cost_center_id') or None,
            planned_date_start=_parse_date(request.form.get('planned_date_start')),
            planned_date_end=_parse_date(request.form.get('planned_date_end')),
        )
        if item:
            flash('Item adicionado ao orçamento.', 'success')
        else:
            flash(error, 'error')
        return redirect(url_for('financial.budget_detail', project_id=project_id, budget_id=budget_id))

    cost_centers = CostCenterService.get_project_cost_centers(project_id)
    items = budget.items.all()
    total_items = sum(float(i.planned_amount) for i in items)
    return render_template(
        'projects/financial/budget_detail.html',
        project=project,
        budget=budget,
        items=items,
        total_items=total_items,
        categories=BUDGET_CATEGORIES,
        cost_centers=cost_centers,
    )


@financial_bp.route('/<int:project_id>/financial/budgets/<int:budget_id>/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_budget_item(project_id: int, budget_id: int, item_id: int):
    """Delete a budget item."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    success, error = FinancialBudgetService.delete_budget_item(item_id)
    if success:
        flash('Item removido do orçamento.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('financial.budget_detail', project_id=project_id, budget_id=budget_id))


@financial_bp.route('/<int:project_id>/financial/budgets/<int:budget_id>/lock', methods=['POST'])
@login_required
def lock_baseline(project_id: int, budget_id: int):
    """Lock (freeze) a budget baseline."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    success, error = FinancialBudgetService.lock_baseline(budget_id)
    if success:
        flash('Baseline travado com sucesso. Nenhuma alteração será permitida.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('financial.budget_detail', project_id=project_id, budget_id=budget_id))


@financial_bp.route('/<int:project_id>/financial/budgets/<int:budget_id>/revision', methods=['POST'])
@login_required
def create_budget_revision(project_id: int, budget_id: int):
    """Create a new revision from a locked budget baseline."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    notes = request.form.get('notes') or None
    new_budget, error = FinancialBudgetService.create_revision(budget_id, created_by=current_user.id, notes=notes)
    if new_budget:
        flash('Nova revisão de baseline criada com sucesso.', 'success')
        return redirect(url_for('financial.budget_detail', project_id=project_id, budget_id=new_budget.id))
    flash(error, 'error')
    return redirect(url_for('financial.budget_detail', project_id=project_id, budget_id=budget_id))


# ---------------------------------------------------------------------------
# Cost Center routes
# ---------------------------------------------------------------------------

@financial_bp.route('/<int:project_id>/financial/cost-centers', methods=['GET', 'POST'])
@login_required
def cost_centers(project_id: int):
    """List or create cost centers for a project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    if request.method == 'POST':
        cc, error = CostCenterService.create_cost_center(
            name=request.form.get('name', '').strip(),
            description=request.form.get('description') or None,
            budget_allocation=request.form.get('budget_allocation') or None,
            status=request.form.get('status', 'active'),
        )
        if cc:
            CostCenterService.associate_with_project(cc.id, project_id)
            flash('Centro de custo criado com sucesso.', 'success')
        else:
            flash(error, 'error')
        return redirect(url_for('financial.cost_centers', project_id=project_id))

    cc_list = CostCenterService.get_project_cost_centers(project_id)
    all_cost_centers = CostCenterService.get_all_cost_centers()
    return render_template(
        'projects/financial/cost_centers.html',
        project=project,
        cost_centers=cc_list,
        all_cost_centers=all_cost_centers,
    )


@financial_bp.route('/<int:project_id>/financial/cost-centers/<int:cc_id>/edit', methods=['POST'])
@login_required
def edit_cost_center(project_id: int, cc_id: int):
    """Edit a cost center."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    cc, error = CostCenterService.update_cost_center(
        cost_center_id=cc_id,
        name=request.form.get('name', '').strip() or None,
        description=request.form.get('description') or None,
        budget_allocation=request.form.get('budget_allocation') or None,
        status=request.form.get('status') or None,
    )
    if cc:
        flash('Centro de custo atualizado.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('financial.cost_centers', project_id=project_id))


@financial_bp.route('/<int:project_id>/financial/cost-centers/<int:cc_id>/associate', methods=['POST'])
@login_required
def associate_cost_center(project_id: int, cc_id: int):
    """Associate an existing cost center with the project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    success, error = CostCenterService.associate_with_project(cc_id, project_id)
    if success:
        flash('Centro de custo associado ao projeto.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('financial.cost_centers', project_id=project_id))


@financial_bp.route('/<int:project_id>/financial/cost-centers/<int:cc_id>/dissociate', methods=['POST'])
@login_required
def dissociate_cost_center(project_id: int, cc_id: int):
    """Remove the association between a cost center and the project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    success, error = CostCenterService.dissociate_from_project(cc_id, project_id)
    if success:
        flash('Centro de custo desassociado do projeto.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('financial.cost_centers', project_id=project_id))


@financial_bp.route('/<int:project_id>/financial/cost-centers/<int:cc_id>/toggle-status', methods=['POST'])
@login_required
def toggle_cost_center_status(project_id: int, cc_id: int):
    """Toggle a cost center's status between active and blocked."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    cc = CostCenterService.get_cost_center(cc_id)
    if not cc:
        flash('Centro de custo não encontrado.', 'error')
        return redirect(url_for('financial.cost_centers', project_id=project_id))

    new_status = 'blocked' if cc.status == 'active' else 'active'
    updated_cc, error = CostCenterService.update_cost_center(cost_center_id=cc_id, status=new_status)
    if updated_cc:
        label = 'bloqueado' if new_status == 'blocked' else 'ativado'
        flash(f'Centro de custo {label}.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('financial.cost_centers', project_id=project_id))


@financial_bp.route('/<int:project_id>/financial/cost-centers/<int:cc_id>/delete', methods=['POST'])
@login_required
def delete_cost_center(project_id: int, cc_id: int):
    """Delete a cost center."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    success, error = CostCenterService.delete_cost_center(cc_id)
    if success:
        flash('Centro de custo removido.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('financial.cost_centers', project_id=project_id))


# ---------------------------------------------------------------------------
# Transaction routes
# ---------------------------------------------------------------------------

@financial_bp.route('/<int:project_id>/financial/transactions', methods=['GET', 'POST'])
@login_required
def transactions(project_id: int):
    """List or create transactions for a project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    if request.method == 'POST':
        txn, error = FinancialTransactionService.create_transaction(
            project_id=project_id,
            type=request.form.get('type', 'expense'),
            description=request.form.get('description', '').strip(),
            amount=request.form.get('amount'),
            category=request.form.get('category', 'other'),
            transaction_date=request.form.get('transaction_date'),
            created_by=current_user.id,
            cost_center_id=request.form.get('cost_center_id') or None,
            payment_status=request.form.get('payment_status', 'pending'),
            payment_method=request.form.get('payment_method') or None,
            supplier_id=request.form.get('supplier_id') or None,
            invoice_number=request.form.get('invoice_number') or None,
            reference_document=request.form.get('reference_document') or None,
            notes=request.form.get('notes') or None,
        )
        if txn:
            flash('Transação registrada com sucesso.', 'success')
        else:
            flash(error, 'error')
        return redirect(url_for('financial.transactions', project_id=project_id))

    txn_list = FinancialTransactionService.get_project_transactions(project_id)
    summary = FinancialTransactionService.get_project_summary(project_id)
    cost_centers = CostCenterService.get_project_cost_centers(project_id)
    suppliers = SupplierService.get_all_suppliers()
    return render_template(
        'projects/financial/transactions.html',
        project=project,
        transactions=txn_list,
        summary=summary,
        cost_centers=cost_centers,
        suppliers=suppliers,
        transaction_types=TRANSACTION_TYPES,
        categories=TRANSACTION_CATEGORIES,
        payment_statuses=PAYMENT_STATUSES,
        payment_methods=PAYMENT_METHODS,
    )


@financial_bp.route('/<int:project_id>/financial/transactions/<int:txn_id>/delete', methods=['POST'])
@login_required
def delete_transaction(project_id: int, txn_id: int):
    """Delete a transaction."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    success, error = FinancialTransactionService.delete_transaction(txn_id)
    if success:
        flash('Transação removida.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('financial.transactions', project_id=project_id))


# ---------------------------------------------------------------------------
# EVM routes
# ---------------------------------------------------------------------------

@financial_bp.route('/<int:project_id>/financial/evm', methods=['GET', 'POST'])
@login_required
def evm(project_id: int):
    """List or create EVM reports for a project."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    if request.method == 'POST':
        report, error = FinancialEVMService.create_evm_report(
            project_id=project_id,
            report_date=request.form.get('report_date'),
            bac=request.form.get('bac'),
            ac=request.form.get('ac'),
            ev=request.form.get('ev'),
            pv=request.form.get('pv'),
            eac=request.form.get('eac') or None,
            etc=request.form.get('etc') or None,
            notes=request.form.get('notes') or None,
        )
        if report:
            flash('Relatório EVM registrado com sucesso.', 'success')
        else:
            flash(error, 'error')
        return redirect(url_for('financial.evm', project_id=project_id))

    reports = FinancialEVMService.get_project_evm_reports(project_id)
    return render_template(
        'projects/financial/evm.html',
        project=project,
        reports=reports,
    )


@financial_bp.route('/<int:project_id>/financial/evm/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_evm_report(project_id: int, report_id: int):
    """Delete an EVM report."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))

    success, error = FinancialEVMService.delete_evm_report(report_id)
    if success:
        flash('Relatório EVM removido.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('financial.evm', project_id=project_id))


# ---------------------------------------------------------------------------
# Suppliers routes
# ---------------------------------------------------------------------------

@financial_bp.route('/suppliers', methods=['GET', 'POST'])
@login_required
def suppliers():
    """List or create suppliers."""
    if request.method == 'POST':
        supplier, error = SupplierService.create_supplier(
            name=request.form.get('name', '').strip(),
            cnpj=request.form.get('cnpj') or None,
            contact_person=request.form.get('contact_person') or None,
            email=request.form.get('email') or None,
            phone=request.form.get('phone') or None,
            address=request.form.get('address') or None,
            city=request.form.get('city') or None,
            state=request.form.get('state') or None,
        )
        if supplier:
            flash('Fornecedor criado com sucesso.', 'success')
        else:
            flash(error, 'error')
        return redirect(url_for('financial.suppliers'))

    supplier_list = SupplierService.get_all_suppliers()
    return render_template(
        'projects/financial/suppliers.html',
        suppliers=supplier_list,
    )


@financial_bp.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete_supplier(supplier_id: int):
    """Delete a supplier."""
    success, error = SupplierService.delete_supplier(supplier_id)
    if success:
        flash('Fornecedor removido.', 'success')
    else:
        flash(error, 'error')
    return redirect(url_for('financial.suppliers'))


@financial_bp.route('/<int:project_id>/financial/cash-flow')
@login_required
def cash_flow(project_id: int):
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))
    monthly_cash_flow = CashFlowService.get_monthly_cash_flow(project_id)
    seasonal = CashFlowService.get_seasonal_analysis(project_id)
    scenarios = FinancialScenario.query.filter_by(project_id=project_id).order_by(FinancialScenario.created_at.desc()).all()
    return render_template(
        'projects/financial/cash_flow.html',
        project=project,
        monthly_cash_flow=monthly_cash_flow,
        seasonal=seasonal,
        scenarios=scenarios,
    )


@financial_bp.route('/<int:project_id>/financial/comparison')
@login_required
def comparison(project_id: int):
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))
    active_budget = FinancialBudgetService.get_active_budget(project_id)
    transactions = FinancialTransactionService.get_project_transactions(project_id)
    actual_by_category = {}
    for cat in TRANSACTION_CATEGORIES:
        actual_by_category[cat] = sum(
            float(t.amount) for t in transactions
            if t.category == cat and t.type in ('expense', 'payment') and t.payment_status != 'cancelled'
        )
    planned_by_category = {}
    for cat in TRANSACTION_CATEGORIES:
        planned_by_category[cat] = 0.0
    if active_budget:
        for item in active_budget.items.all():
            if item.category in planned_by_category:
                planned_by_category[item.category] += float(item.planned_amount)
    categories_data = []
    for cat in TRANSACTION_CATEGORIES:
        planned = planned_by_category.get(cat, 0.0)
        actual = actual_by_category.get(cat, 0.0)
        variance = actual - planned
        pct = (variance / planned * 100) if planned > 0 else 0.0
        categories_data.append({
            'category': cat,
            'planned': planned,
            'actual': actual,
            'variance': variance,
            'variance_pct': pct,
        })
    return render_template(
        'projects/financial/comparison.html',
        project=project,
        categories_data=categories_data,
        active_budget=active_budget,
    )


@financial_bp.route('/<int:project_id>/financial/schedule-comparison')
@login_required
def schedule_comparison(project_id: int):
    """Show planned vs actual schedule progress for project tasks."""
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))
    tasks_data = EVMAnalysisService.get_schedule_comparison(project_id)
    return render_template(
        'projects/financial/schedule_comparison.html',
        project=project,
        tasks_data=tasks_data,
    )


@financial_bp.route('/<int:project_id>/financial/evm-dashboard')
@login_required
def evm_dashboard(project_id: int):
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))
    scurve = EVMAnalysisService.get_scurve_data(project_id)
    evm_summary = EVMAnalysisService.get_evm_summary(project_id)
    trend = EVMAnalysisService.get_performance_trend(project_id)
    variance = EVMAnalysisService.get_variance_analysis(project_id)
    return render_template(
        'projects/financial/evm_dashboard.html',
        project=project,
        scurve=scurve,
        evm_summary=evm_summary,
        trend=trend,
        variance=variance,
    )


@financial_bp.route('/<int:project_id>/financial/reports', methods=['GET', 'POST'])
@login_required
def reports(project_id: int):
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))
    if request.method == 'POST':
        report_type = request.form.get('report_type', 'executive')
        report, error = ReportingService.generate_excel_report(
            project_id=project_id,
            report_type=report_type,
            generated_by=current_user.id,
        )
        if report:
            flash('Relatório gerado com sucesso.', 'success')
        else:
            flash(error, 'error')
        return redirect(url_for('financial.reports', project_id=project_id))
    report_list = ReportingService.get_project_reports(project_id)
    return render_template(
        'projects/financial/reports.html',
        project=project,
        reports=report_list,
        report_types=REPORT_TYPES,
        report_formats=REPORT_FORMATS,
    )


@financial_bp.route('/<int:project_id>/financial/scenarios', methods=['POST'])
@login_required
def create_scenario(project_id: int):
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))
    from app.models.financial_scenario import SCENARIO_TYPES
    name = request.form.get('name', '').strip()
    if not name:
        flash('Nome do cenário é obrigatório.', 'error')
        return redirect(url_for('financial.cash_flow', project_id=project_id))
    scenario_type = request.form.get('scenario_type', 'realistic')
    if scenario_type not in SCENARIO_TYPES:
        scenario_type = 'realistic'
    try:
        budget_variance = float(request.form.get('budget_variance', 0))
        schedule_variance = float(request.form.get('schedule_variance', 0))
    except (ValueError, TypeError):
        budget_variance, schedule_variance = 0.0, 0.0
    scenario = FinancialScenario(
        project_id=project_id,
        name=name,
        description=request.form.get('description') or None,
        scenario_type=scenario_type,
        budget_variance=budget_variance,
        schedule_variance=schedule_variance,
        created_by=current_user.id,
    )
    db.session.add(scenario)
    db.session.commit()
    flash('Cenário criado com sucesso.', 'success')
    return redirect(url_for('financial.cash_flow', project_id=project_id))


@financial_bp.route('/<int:project_id>/financial/scenarios/<int:scenario_id>/delete', methods=['POST'])
@login_required
def delete_scenario(project_id: int, scenario_id: int):
    project = _get_project_or_abort(project_id)
    if project is None:
        return redirect(url_for('projects.index'))
    scenario = db.session.get(FinancialScenario, scenario_id)
    if scenario and scenario.project_id == project_id:
        db.session.delete(scenario)
        db.session.commit()
        flash('Cenário removido.', 'success')
    else:
        flash('Cenário não encontrado.', 'error')
    return redirect(url_for('financial.cash_flow', project_id=project_id))
