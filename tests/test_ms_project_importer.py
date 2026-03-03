"""Tests for MSProjectImporter."""
import pytest
from app.services.importers.ms_project_importer import MSProjectImporter

_MS_NS = 'http://schemas.microsoft.com/project'

MINIMAL_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<Project xmlns="{_MS_NS}">
  <CurrencySymbol>USD</CurrencySymbol>
  <Tasks>
    <Task>
      <UID>0</UID>
      <Name>Project Summary</Name>
      <WBS>0</WBS>
      <OutlineNumber>0</OutlineNumber>
      <OutlineLevel>0</OutlineLevel>
      <Summary>1</Summary>
    </Task>
    <Task>
      <UID>1</UID>
      <Name>Phase 1</Name>
      <WBS>1</WBS>
      <OutlineNumber>1</OutlineNumber>
      <OutlineLevel>1</OutlineLevel>
      <Summary>1</Summary>
      <Start>2025-01-06T08:00:00</Start>
      <Finish>2025-01-17T17:00:00</Finish>
      <Duration>PT80H0M0S</Duration>
      <BaselineCost>10000.00</BaselineCost>
      <BaselineStart>2025-01-06T08:00:00</BaselineStart>
      <BaselineFinish>2025-01-17T17:00:00</BaselineFinish>
      <PercentComplete>0</PercentComplete>
    </Task>
    <Task>
      <UID>2</UID>
      <Name>Task 1.1</Name>
      <WBS>1.1</WBS>
      <OutlineNumber>1.1</OutlineNumber>
      <OutlineLevel>2</OutlineLevel>
      <Summary>0</Summary>
      <Start>2025-01-06T08:00:00</Start>
      <Finish>2025-01-10T17:00:00</Finish>
      <Duration>PT40H0M0S</Duration>
      <BaselineCost>5000.00</BaselineCost>
      <BaselineStart>2025-01-06T08:00:00</BaselineStart>
      <BaselineFinish>2025-01-10T17:00:00</BaselineFinish>
      <PercentComplete>50</PercentComplete>
    </Task>
  </Tasks>
  <Resources>
    <Resource>
      <UID>0</UID>
      <Name>Unassigned</Name>
    </Resource>
    <Resource>
      <UID>1</UID>
      <Name>John Doe</Name>
      <Type>1</Type>
      <Cost>1000.00</Cost>
    </Resource>
  </Resources>
</Project>
"""


class TestMSProjectImporter:
    def test_parse_returns_structure(self):
        importer = MSProjectImporter()
        data = importer.parse(MINIMAL_XML.encode(), 'test.xml')
        assert 'tasks' in data
        assert 'wbs_items' in data
        assert 'resources' in data
        assert 'budgets' in data

    def test_tasks_count(self):
        importer = MSProjectImporter()
        data = importer.parse(MINIMAL_XML.encode(), 'test.xml')
        # UID 0 is skipped; 2 tasks remain
        assert len(data['tasks']) == 2

    def test_task_fields(self):
        importer = MSProjectImporter()
        data = importer.parse(MINIMAL_XML.encode(), 'test.xml')
        task = next(t for t in data['tasks'] if t['uid'] == '2')
        assert task['name'] == 'Task 1.1'
        assert task['start'] == '2025-01-06'
        assert task['finish'] == '2025-01-10'
        assert task['estimated_effort'] == 40.0

    def test_resources_count(self):
        importer = MSProjectImporter()
        data = importer.parse(MINIMAL_XML.encode(), 'test.xml')
        # UID 0 (Unassigned) is skipped
        assert len(data['resources']) == 1
        assert data['resources'][0]['name'] == 'John Doe'

    def test_wbs_items_built(self):
        importer = MSProjectImporter()
        data = importer.parse(MINIMAL_XML.encode(), 'test.xml')
        # Only summary tasks form WBS
        assert len(data['wbs_items']) >= 1

    def test_budgets_from_baseline(self):
        importer = MSProjectImporter()
        data = importer.parse(MINIMAL_XML.encode(), 'test.xml')
        # Both tasks have baseline cost > 0
        assert len(data['budgets']) >= 1
        total = sum(float(b['planned_amount']) for b in data['budgets'])
        assert total > 0

    def test_invalid_xml(self):
        importer = MSProjectImporter()
        data = importer.parse(b'not xml at all', 'bad.xml')
        assert data['tasks'] == []
        assert len(importer.errors) > 0

    def test_validate_passes(self):
        importer = MSProjectImporter()
        data = importer.parse(MINIMAL_XML.encode(), 'test.xml')
        errors = importer.validate(data)
        assert errors == []

    def test_parse_duration_hours(self):
        assert MSProjectImporter._parse_duration_hours('PT8H0M0S') == 8.0
        assert MSProjectImporter._parse_duration_hours('PT40H0M0S') == 40.0
        assert MSProjectImporter._parse_duration_hours('') is None
        assert MSProjectImporter._parse_duration_hours('PT30M0S') == 0.5
