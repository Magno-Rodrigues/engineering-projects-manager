"""Tests for PrimaveraImporter."""
import io
import pytest
from app.services.importers.primavera_importer import PrimaveraImporter

PRIMAVERA_XML = """<?xml version="1.0" encoding="UTF-8"?>
<APIBusinessObjects>
  <WBS ObjectId="100">
    <Code>P1</Code>
    <Name>Phase 1</Name>
    <Level>1</Level>
  </WBS>
  <WBS ObjectId="101">
    <Code>P1.1</Code>
    <Name>Subphase 1.1</Name>
    <Level>2</Level>
    <ParentObjectId>100</ParentObjectId>
  </WBS>
  <Activity ObjectId="200">
    <ActivityId>A1000</ActivityId>
    <Name>Design</Name>
    <WBSObjectId>100</WBSObjectId>
    <StartDate>2025-01-06T08:00:00</StartDate>
    <FinishDate>2025-01-10T17:00:00</FinishDate>
    <Duration>40</Duration>
    <BudgetedTotalCost>8000.00</BudgetedTotalCost>
  </Activity>
  <Activity ObjectId="201">
    <ActivityId>A1001</ActivityId>
    <Name>Development</Name>
    <WBSObjectId>101</WBSObjectId>
    <StartDate>2025-01-13T08:00:00</StartDate>
    <FinishDate>2025-01-24T17:00:00</FinishDate>
    <Duration>80</Duration>
    <BudgetedTotalCost>16000.00</BudgetedTotalCost>
  </Activity>
</APIBusinessObjects>
"""


class TestPrimaveraImporter:
    def test_parse_xml_returns_structure(self):
        importer = PrimaveraImporter()
        data = importer.parse(PRIMAVERA_XML.encode(), 'test.xml')
        assert 'tasks' in data
        assert 'wbs_items' in data
        assert 'resources' in data
        assert 'budgets' in data

    def test_xml_activities_count(self):
        importer = PrimaveraImporter()
        data = importer.parse(PRIMAVERA_XML.encode(), 'test.xml')
        assert len(data['tasks']) == 2

    def test_xml_task_fields(self):
        importer = PrimaveraImporter()
        data = importer.parse(PRIMAVERA_XML.encode(), 'test.xml')
        task = data['tasks'][0]
        assert task['name'] == 'Design'
        assert task['start'] == '2025-01-06'
        assert task['finish'] == '2025-01-10'

    def test_xml_wbs_items(self):
        importer = PrimaveraImporter()
        data = importer.parse(PRIMAVERA_XML.encode(), 'test.xml')
        assert len(data['wbs_items']) == 2
        child = next(w for w in data['wbs_items'] if w['wbs_code'] == 'P1.1')
        assert child['parent_uid'] == '100'

    def test_xml_budgets(self):
        importer = PrimaveraImporter()
        data = importer.parse(PRIMAVERA_XML.encode(), 'test.xml')
        assert len(data['budgets']) == 2
        total = sum(float(b['planned_amount']) for b in data['budgets'])
        assert total == pytest.approx(24000.0)

    def test_invalid_xml(self):
        importer = PrimaveraImporter()
        data = importer.parse(b'not xml', 'test.xml')
        assert data['tasks'] == []
        assert len(importer.errors) > 0

    def test_unsupported_format(self):
        importer = PrimaveraImporter()
        data = importer.parse(b'some data', 'test.pdf')
        assert data['tasks'] == []
        assert len(importer.errors) > 0

    def test_parse_excel(self):
        """Test Excel parsing with openpyxl."""
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['Activity ID', 'Activity Name', 'Start Date', 'Finish Date', 'Duration', 'Budgeted Total Cost', 'WBS'])
        ws.append(['A1000', 'Design', '2025-01-06', '2025-01-10', '40', '5000', '1.1'])
        ws.append(['A1001', 'Development', '2025-01-13', '2025-01-24', '80', '10000', '1.2'])
        buf = io.BytesIO()
        wb.save(buf)

        importer = PrimaveraImporter()
        data = importer.parse(buf.getvalue(), 'test.xlsx')
        assert len(data['tasks']) == 2
        assert data['tasks'][0]['name'] == 'Design'
        assert len(data['wbs_items']) == 2

    def test_parse_duration_days(self):
        assert PrimaveraImporter._parse_duration('5d') == 40.0

    def test_parse_duration_hours(self):
        assert PrimaveraImporter._parse_duration('8h') == 8.0

    def test_parse_duration_numeric(self):
        assert PrimaveraImporter._parse_duration('40') == 40.0

    def test_parse_duration_none(self):
        assert PrimaveraImporter._parse_duration('') is None
