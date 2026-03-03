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
            project_id=project_id,
            name=request.form.get('name', '').strip(),
            description=request.form.get('description') or None,
            budget_allocation=request.form.get('budget_allocation') or None,
        )
        if cc:
            flash('Centro de custo criado com sucesso.', 'success')
        else:
            flash(error, 'error')
        return redirect(url_for('financial.cost_centers', project_id=project_id))

    cc_list = CostCenterService.get_project_cost_centers(project_id)
    return render_template(
        'projects/financial/cost_centers.html',
        project=project,
        cost_centers=cc_list,
    )


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
