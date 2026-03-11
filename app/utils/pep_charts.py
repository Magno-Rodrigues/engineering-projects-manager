"""PEP dashboard chart generation utilities.

This module provides functions to build Plotly interactive chart figures
for the PEP (Project Execution Plan) dashboard:

- :func:`build_gantt_chart`      – Gantt chart (fases/etapas com status)
- :func:`build_scurve_chart`     – Curva S (progresso acumulado planejado vs realizado)
- :func:`build_risk_matrix_chart` – Matriz de Riscos (heatmap probabilidade × impacto)

Results are cached in memory with a configurable TTL (default 5 minutes) to
avoid re-computing heavy figures on every page load.
"""

from __future__ import annotations

import logging
import time
import threading
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simple in-memory TTL cache (avoids adding Flask-Caching dependency)
# ---------------------------------------------------------------------------

_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, tuple[float, Any]] = {}
CACHE_TTL = 300  # seconds (5 minutes)


def _cache_get(key: str) -> Any | None:
    """Return cached value for *key* if still valid, otherwise ``None``."""
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts > CACHE_TTL:
            del _CACHE[key]
            return None
        return value


def _cache_set(key: str, value: Any) -> None:
    """Store *value* in cache under *key*."""
    with _CACHE_LOCK:
        _CACHE[key] = (time.monotonic(), value)


def cache_invalidate_project(project_id: int) -> None:
    """Remove all cached chart entries for *project_id*.

    Call this whenever PEP data for the project changes so the next
    dashboard load regenerates fresh figures.
    """
    prefix = f"pep_chart_{project_id}_"
    with _CACHE_LOCK:
        stale = [k for k in _CACHE if k.startswith(prefix)]
        for k in stale:
            del _CACHE[k]


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

_COLOR_MAP: dict[str, str] = {
    'pending': '#94a3b8',
    'in_progress': '#3b82f6',
    'completed': '#10b981',
}

_LABEL_MAP: dict[str, str] = {
    'pending': 'Pendente',
    'in_progress': 'Em Andamento',
    'completed': 'Concluído',
}


def _phase_progress(phase) -> int:
    """Return average completion percentage (0-100) for a phase."""
    total = 0
    total_progress = 0
    for stage in phase.stages.all():
        for act in stage.activities.all():
            total += 1
            total_progress += act.progress or 0
    return int(total_progress / total) if total else 0


def _stage_progress(stage) -> int:
    """Return average completion percentage (0-100) for a stage."""
    activities = stage.activities.all()
    if not activities:
        return 0
    return int(sum(a.progress or 0 for a in activities) / len(activities))


# ---------------------------------------------------------------------------
# Gantt chart
# ---------------------------------------------------------------------------

def build_gantt_chart(phases, project_id: int | None = None) -> str | None:
    """Build an interactive Plotly Gantt chart for *phases* and return JSON.

    Renders fases (phases) and their etapas (stages) as horizontal bars,
    colour-coded by status. Includes today marker, tooltips with progress,
    and is exportable as PNG/SVG.

    Args:
        phases:     Iterable of :class:`~app.models.pep.PEPPhase` ORM objects.
        project_id: Optional project ID used as cache key.

    Returns:
        JSON string suitable for ``Plotly.newPlot()``, or ``None`` if Plotly
        is not installed or there are no tasks to render.
    """
    cache_key = f"pep_chart_{project_id}_gantt" if project_id is not None else None
    if cache_key:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    try:
        import plotly.graph_objects as go
    except ImportError:
        logger.warning("plotly is not installed – Gantt chart unavailable")
        return None

    try:
        today_str = date.today().isoformat()
        tasks: list[dict] = []

        for phase in phases:
            p_start = phase.start_date.isoformat() if phase.start_date else today_str
            p_end = phase.end_date.isoformat() if phase.end_date else today_str
            if p_end < p_start:
                p_end = p_start
            p_status = getattr(phase, 'status', None) or 'pending'
            tasks.append({
                'name': phase.name,
                'start': p_start,
                'end': p_end,
                'progress': _phase_progress(phase),
                'type': 'phase',
                'status': p_status,
            })
            for stage in phase.stages.all():
                s_start = stage.start_date.isoformat() if stage.start_date else p_start
                s_end = stage.end_date.isoformat() if stage.end_date else p_end
                if s_end < s_start:
                    s_end = s_start
                s_status = getattr(stage, 'status', None) or 'pending'
                tasks.append({
                    'name': f'\u00a0\u00a0{stage.name}',
                    'start': s_start,
                    'end': s_end,
                    'progress': _stage_progress(stage),
                    'type': 'stage',
                    'status': s_status,
                })

        if not tasks:
            logger.debug("build_gantt_chart: no phases found – returning None")
            return None
    except Exception:
        logger.exception("build_gantt_chart: unexpected error while building task list")
        return None

    try:
        fig = go.Figure()
        status_shown: set[str] = set()

        for task in tasks:
            status = task['status'] if task['status'] in _COLOR_MAP else 'pending'
            color = _COLOR_MAP[status]
            show_legend = status not in status_shown
            status_shown.add(status)

            opacity = 1.0 if task['type'] == 'phase' else 0.75
            fig.add_trace(go.Bar(
                name=_LABEL_MAP.get(status, status),
                legendgroup=status,
                showlegend=show_legend,
                y=[task['name']],
                x=[task['end']],
                base=[task['start']],
                orientation='h',
                marker_color=color,
                marker_opacity=opacity,
                marker_line_width=0,
                customdata=[[task['start'], task['end'], task['progress'], task['type']]],
                hovertemplate=(
                    '<b>%{y}</b><br>'
                    'Início: %{customdata[0]}<br>'
                    'Fim: %{customdata[1]}<br>'
                    'Progresso: %{customdata[2]}%'
                    '<extra></extra>'
                ),
            ))

        # Today marker as a vertical line shape
        shapes = [dict(
            type='line',
            x0=today_str,
            x1=today_str,
            y0=-0.5,
            y1=len(tasks) - 0.5,
            line=dict(color='#f59e0b', width=2, dash='dot'),
        )]

        height = max(450, len(tasks) * 50 + 180)
        fig.update_layout(
            barmode='overlay',
            height=height,
            margin=dict(l=180, r=10, t=40, b=10),
            xaxis_type='date',
            xaxis=dict(
                showgrid=True,
                gridcolor='#f1f5f9',
                tickformat='%d/%m',
                tickangle=-45,
                tickfont=dict(size=12),
            ),
            yaxis=dict(
                autorange='reversed',
                tickfont=dict(size=12),
                showgrid=False,
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=11),
            ),
            shapes=shapes,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Inter, sans-serif', size=12),
            hovermode='closest',
        )

        result = fig.to_json()
        if cache_key:
            _cache_set(cache_key, result)
        return result
    except Exception:
        logger.exception("build_gantt_chart: unexpected error while building figure")
        return None


# ---------------------------------------------------------------------------
# S-Curve chart
# ---------------------------------------------------------------------------

def build_scurve_chart(scurve_data: dict, project_id: int | None = None) -> str | None:
    """Build an interactive Plotly S-Curve (Curva S) figure and return JSON.

    Shows cumulative planned vs. actual progress over time.

    Args:
        scurve_data: Dict with keys ``labels``, ``planned``, ``actual``
                     as returned by the route helper ``_get_scurve_data()``.
        project_id:  Optional project ID used as cache key.

    Returns:
        JSON string for Plotly, or ``None`` when data is absent or Plotly
        is not available.
    """
    cache_key = f"pep_chart_{project_id}_scurve" if project_id is not None else None
    if cache_key:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    try:
        import plotly.graph_objects as go
    except ImportError:
        logger.warning("plotly is not installed – S-Curve chart unavailable")
        return None

    if not scurve_data or not scurve_data.get('labels'):
        logger.debug("build_scurve_chart: no data labels – returning None")
        return None

    try:
        labels = scurve_data['labels']
        planned = scurve_data.get('planned', [])
        actual = scurve_data.get('actual', [])

        fig = go.Figure()

        # Planned line
        fig.add_trace(go.Scatter(
            x=labels,
            y=planned,
            mode='lines+markers',
            name='Planejado (%)',
            line=dict(color='#1A3A52', width=2.5),
            marker=dict(size=6, color='#1A3A52'),
            fill='tozeroy',
            fillcolor='rgba(26,58,82,0.06)',
            hovertemplate='Planejado: %{y:.1f}%<extra></extra>',
        ))

        # Actual line
        fig.add_trace(go.Scatter(
            x=labels,
            y=actual,
            mode='lines+markers',
            name='Realizado (%)',
            line=dict(color='#C9A961', width=2.5),
            marker=dict(size=6, color='#C9A961'),
            fill='tozeroy',
            fillcolor='rgba(201,169,97,0.06)',
            hovertemplate='Realizado: %{y:.1f}%<extra></extra>',
        ))

        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(
                range=[0, 100],
                ticksuffix='%',
                tickfont=dict(size=11),
                showgrid=True,
                gridcolor='#f1f5f9',
            ),
            xaxis=dict(
                tickfont=dict(size=11),
                showgrid=False,
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=11),
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Inter, sans-serif', size=12),
            hovermode='x unified',
        )

        result = fig.to_json()
        if cache_key:
            _cache_set(cache_key, result)
        return result
    except Exception:
        logger.exception("build_scurve_chart: unexpected error while building figure")
        return None


# ---------------------------------------------------------------------------
# Risk Matrix chart
# ---------------------------------------------------------------------------

def build_risk_matrix_chart(risks, project_id: int | None = None) -> str | None:
    """Build an interactive Plotly heatmap for the risk matrix and return JSON.

    Renders a 5×5 probability × impact matrix with risk count overlays and
    colour-coded cells (green → yellow → red).

    Args:
        risks:      Iterable of :class:`~app.models.pep.PEPRisk` ORM objects.
        project_id: Optional project ID used as cache key.

    Returns:
        JSON string for Plotly, or ``None`` when Plotly is not available.
    """
    cache_key = f"pep_chart_{project_id}_risk_matrix" if project_id is not None else None
    if cache_key:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    try:
        import plotly.graph_objects as go
    except ImportError:
        logger.warning("plotly is not installed – Risk Matrix chart unavailable")
        return None

    try:
        # 5×5 matrix: rows = probability 5→1 (top→bottom), cols = impact 1→5
        z_count = [[0] * 5 for _ in range(5)]
        hover_details: list[list[list[str]]] = [[[] for _ in range(5)] for _ in range(5)]

        for risk in risks:
            p = int(getattr(risk, 'probability', 0) or 0)
            i = int(getattr(risk, 'impact', 0) or 0)
            if 1 <= p <= 5 and 1 <= i <= 5:
                row = 5 - p   # probability 5 → row 0
                col = i - 1   # impact 1 → col 0
                z_count[row][col] += 1
                name = (
                    getattr(risk, 'description', None)
                    or getattr(risk, 'name', None)
                    or ''
                )
                if name:
                    hover_details[row][col].append(str(name)[:50])

        # Background values (p × i) used for colour scale
        z_risk = [[(5 - row) * (col + 1) for col in range(5)] for row in range(5)]

        x_labels = ['1 - MB', '2 - B', '3 - M', '4 - A', '5 - MA']
        y_labels = ['5 - Crítico', '4 - Alto', '3 - Médio', '2 - Baixo', '1 - Mínimo']

        text_matrix = []
        hover_matrix = []
        for row in range(5):
            text_row = []
            hover_row = []
            p_val = 5 - row
            for col in range(5):
                i_val = col + 1
                count = z_count[row][col]
                text_row.append(str(count) if count > 0 else '')
                names_str = (
                    '<br>' + '<br>'.join(hover_details[row][col])
                    if hover_details[row][col] else ''
                )
                hover_row.append(
                    f'Probabilidade: {p_val}<br>Impacto: {i_val}'
                    f'<br>Nível: {p_val * i_val}'
                    f'<br>Riscos: {count}{names_str}'
                )
            text_matrix.append(text_row)
            hover_matrix.append(hover_row)

        colorscale = [
            [0.00, '#bbf7d0'],
            [0.20, '#bbf7d0'],
            [0.40, '#fef08a'],
            [0.60, '#fed7aa'],
            [0.80, '#fca5a5'],
            [1.00, '#dc2626'],
        ]

        fig = go.Figure(data=go.Heatmap(
            z=z_risk,
            x=x_labels,
            y=y_labels,
            text=text_matrix,
            texttemplate='%{text}',
            textfont=dict(size=16, color='#1e293b', family='Inter, sans-serif'),
            colorscale=colorscale,
            showscale=False,
            zmin=1,
            zmax=25,
            hovertext=hover_matrix,
            hoverinfo='text',
        ))

        fig.update_layout(
            height=320,
            margin=dict(l=0, r=0, t=10, b=10),
            xaxis=dict(
                title='Impacto →',
                side='bottom',
                tickfont=dict(size=11),
                showgrid=False,
            ),
            yaxis=dict(
                title='← Probabilidade',
                tickfont=dict(size=11),
                showgrid=False,
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family='Inter, sans-serif', size=12),
        )

        result = fig.to_json()
        if cache_key:
            _cache_set(cache_key, result)
        return result
    except Exception:
        logger.exception("build_risk_matrix_chart: unexpected error while building figure")
        return None
