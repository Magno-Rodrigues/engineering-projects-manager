"""Unit tests for app/utils/pep_charts.py."""
import json
import time
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------

def _make_phase(name='Phase 1', start='2025-01-01', end='2025-03-31',
                status='in_progress', stages=None):
    """Return a minimal mock PEPPhase object."""
    phase = MagicMock()
    phase.name = name
    phase.start_date = _date(start) if start else None
    phase.end_date = _date(end) if end else None
    phase.status = status
    mock_stages = stages or []
    phase.stages.all.return_value = mock_stages
    return phase


def _make_stage(name='Stage 1', start='2025-01-01', end='2025-02-28',
                status='pending', activities=None):
    """Return a minimal mock PEPStage object."""
    stage = MagicMock()
    stage.name = name
    stage.start_date = _date(start) if start else None
    stage.end_date = _date(end) if end else None
    stage.status = status
    mock_acts = activities or []
    stage.activities.all.return_value = mock_acts
    return stage


def _make_activity(progress=50, status='in_progress'):
    """Return a minimal mock PEPActivity object."""
    act = MagicMock()
    act.progress = progress
    act.status = status
    return act


def _make_risk(probability=3, impact=4, description='Risco de teste'):
    """Return a minimal mock PEPRisk object."""
    risk = MagicMock()
    risk.probability = probability
    risk.impact = impact
    risk.description = description
    return risk


def _date(s):
    from datetime import date
    return date.fromisoformat(s)


# ---------------------------------------------------------------------------
# Tests: build_gantt_chart
# ---------------------------------------------------------------------------

class TestBuildGanttChart:
    """Tests for pep_charts.build_gantt_chart()."""

    def test_returns_none_when_no_phases(self):
        from app.utils.pep_charts import build_gantt_chart
        result = build_gantt_chart([])
        assert result is None

    def test_returns_json_string_with_phases(self):
        from app.utils.pep_charts import build_gantt_chart
        phase = _make_phase()
        result = build_gantt_chart([phase])
        assert result is not None
        parsed = json.loads(result)
        assert 'data' in parsed
        assert 'layout' in parsed

    def test_includes_today_marker_shape(self):
        from app.utils.pep_charts import build_gantt_chart
        phase = _make_phase()
        result = build_gantt_chart([phase])
        parsed = json.loads(result)
        shapes = parsed['layout'].get('shapes', [])
        assert len(shapes) == 1
        assert shapes[0]['type'] == 'line'

    def test_stages_included_in_chart(self):
        from app.utils.pep_charts import build_gantt_chart
        stage = _make_stage()
        phase = _make_phase(stages=[stage])
        result = build_gantt_chart([phase])
        parsed = json.loads(result)
        # Each unique status produces one trace; we should have at least 1
        assert len(parsed['data']) >= 1

    def test_phase_without_dates_uses_today(self):
        from app.utils.pep_charts import build_gantt_chart
        phase = _make_phase(start=None, end=None)
        result = build_gantt_chart([phase])
        assert result is not None

    def test_end_before_start_clamped(self):
        from app.utils.pep_charts import build_gantt_chart
        phase = _make_phase(start='2025-06-01', end='2025-01-01')  # end < start
        result = build_gantt_chart([phase])
        assert result is not None  # should not raise

    def test_cache_returns_same_result(self):
        from app.utils.pep_charts import build_gantt_chart, _cache_get
        phase = _make_phase()
        result1 = build_gantt_chart([phase], project_id=9999)
        cached = _cache_get('pep_chart_9999_gantt')
        assert cached == result1

    def test_no_cache_when_project_id_is_none(self):
        from app.utils.pep_charts import build_gantt_chart, _cache_get, _CACHE
        phase = _make_phase()
        before = dict(_CACHE)
        build_gantt_chart([phase], project_id=None)
        after = dict(_CACHE)
        # No new keys should have been added for project_id=None
        new_keys = set(after) - set(before)
        assert not any('None' in k for k in new_keys)

    def test_status_colours_in_traces(self):
        from app.utils.pep_charts import build_gantt_chart
        phase = _make_phase(status='completed')
        result = build_gantt_chart([phase])
        parsed = json.loads(result)
        # Should have 'Concluído' in legend names
        names = [t['name'] for t in parsed['data']]
        assert 'Concluído' in names


# ---------------------------------------------------------------------------
# Tests: build_scurve_chart
# ---------------------------------------------------------------------------

class TestBuildScurveChart:
    """Tests for pep_charts.build_scurve_chart()."""

    def test_returns_none_for_empty_data(self):
        from app.utils.pep_charts import build_scurve_chart
        assert build_scurve_chart({}) is None
        assert build_scurve_chart({'labels': []}) is None
        assert build_scurve_chart(None) is None

    def test_returns_json_with_valid_data(self):
        from app.utils.pep_charts import build_scurve_chart
        data = {
            'labels': ['Jan', 'Feb', 'Mar'],
            'planned': [10.0, 50.0, 100.0],
            'actual': [8.0, 40.0, 90.0],
        }
        result = build_scurve_chart(data)
        assert result is not None
        parsed = json.loads(result)
        assert 'data' in parsed
        assert len(parsed['data']) == 2  # planned + actual

    def test_trace_names_in_portuguese(self):
        from app.utils.pep_charts import build_scurve_chart
        data = {
            'labels': ['Jan'],
            'planned': [10.0],
            'actual': [8.0],
        }
        result = build_scurve_chart(data)
        parsed = json.loads(result)
        names = {t['name'] for t in parsed['data']}
        assert 'Planejado (%)' in names
        assert 'Realizado (%)' in names

    def test_y_axis_range_0_to_100(self):
        from app.utils.pep_charts import build_scurve_chart
        data = {'labels': ['Jan'], 'planned': [50.0], 'actual': [40.0]}
        parsed = json.loads(build_scurve_chart(data))
        assert parsed['layout']['yaxis']['range'] == [0, 100]

    def test_cache_works(self):
        from app.utils.pep_charts import build_scurve_chart, _cache_get
        data = {'labels': ['Jan'], 'planned': [50.0], 'actual': [40.0]}
        result = build_scurve_chart(data, project_id=8888)
        assert _cache_get('pep_chart_8888_scurve') == result


# ---------------------------------------------------------------------------
# Tests: build_risk_matrix_chart
# ---------------------------------------------------------------------------

class TestBuildRiskMatrixChart:
    """Tests for pep_charts.build_risk_matrix_chart()."""

    def test_returns_json_with_no_risks(self):
        from app.utils.pep_charts import build_risk_matrix_chart
        # Should still return the empty heatmap, not None
        result = build_risk_matrix_chart([])
        assert result is not None
        parsed = json.loads(result)
        assert 'data' in parsed

    def test_heatmap_has_correct_axes(self):
        from app.utils.pep_charts import build_risk_matrix_chart
        parsed = json.loads(build_risk_matrix_chart([]))
        layout = parsed['layout']
        assert 'xaxis' in layout
        assert 'yaxis' in layout

    def test_risk_counted_in_matrix(self):
        from app.utils.pep_charts import build_risk_matrix_chart
        risk = _make_risk(probability=5, impact=5, description='Crítico')
        result = build_risk_matrix_chart([risk])
        parsed = json.loads(result)
        heatmap = parsed['data'][0]
        # probability=5 → row 0, impact=5 → col 4
        # text_matrix[0][4] should be '1'
        text = heatmap['text'][0][4]
        assert text == '1'

    def test_invalid_probability_ignored(self):
        from app.utils.pep_charts import build_risk_matrix_chart
        risk = _make_risk(probability=0, impact=3)  # 0 is out of 1-5 range
        result = build_risk_matrix_chart([risk])
        parsed = json.loads(result)
        heatmap = parsed['data'][0]
        # All text entries should be empty (no counts)
        all_texts = [cell for row in heatmap['text'] for cell in row]
        assert all(t == '' for t in all_texts)

    def test_cache_works(self):
        from app.utils.pep_charts import build_risk_matrix_chart, _cache_get
        result = build_risk_matrix_chart([], project_id=7777)
        assert _cache_get('pep_chart_7777_risk_matrix') == result


# ---------------------------------------------------------------------------
# Tests: cache helpers
# ---------------------------------------------------------------------------

class TestCacheHelpers:
    """Tests for _cache_get, _cache_set, cache_invalidate_project."""

    def test_set_and_get(self):
        from app.utils.pep_charts import _cache_get, _cache_set
        _cache_set('test_key_1', 'hello')
        assert _cache_get('test_key_1') == 'hello'

    def test_expired_entry_returns_none(self):
        from app.utils.pep_charts import _cache_get, _cache_set, CACHE_TTL
        import app.utils.pep_charts as _module
        _cache_set('test_key_expired', 'value')
        # Manually back-date the entry
        with _module._CACHE_LOCK:
            ts, val = _module._CACHE['test_key_expired']
            _module._CACHE['test_key_expired'] = (ts - CACHE_TTL - 1, val)
        assert _cache_get('test_key_expired') is None

    def test_invalidate_project_removes_all_keys(self):
        from app.utils.pep_charts import _cache_get, _cache_set, cache_invalidate_project
        _cache_set('pep_chart_42_gantt', 'g')
        _cache_set('pep_chart_42_scurve', 's')
        _cache_set('pep_chart_42_risk_matrix', 'r')
        _cache_set('pep_chart_99_gantt', 'other')  # different project
        cache_invalidate_project(42)
        assert _cache_get('pep_chart_42_gantt') is None
        assert _cache_get('pep_chart_42_scurve') is None
        assert _cache_get('pep_chart_42_risk_matrix') is None
        # Other project not affected
        assert _cache_get('pep_chart_99_gantt') == 'other'

    def test_cache_miss_returns_none(self):
        from app.utils.pep_charts import _cache_get
        assert _cache_get('nonexistent_key_xyz') is None
