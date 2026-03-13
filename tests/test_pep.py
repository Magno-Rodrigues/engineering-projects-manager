"""Tests for PEP (Project Execution Plan) module."""
import pytest
from app.models.project import Project
from app.models.user import User
from app.models.pep import (
    PEPPhase, PEPStage, PEPActivity,
    PEPRisk, PEPBaseline, PEPChangeLog, PEPDecisionLog,
    PEPResourceAllocation, PEPResourceCapacity,
)


class TestPEPModels:
    """Tests for PEP model creation and relationships."""

    def _create_project_and_user(self, db, app):
        """Helper: create a user and project for PEP tests."""
        with app.app_context():
            user = User(username='pepuser', email='pep@test.com')
            user.set_password('pass')
            db.session.add(user)
            db.session.flush()

            project = Project(name='PEP Test Project', owner_id=user.id)
            db.session.add(project)
            db.session.commit()
            return user.id, project.id

    def test_create_phase(self, app, db):
        """Test creating a PEP phase linked to a project."""
        with app.app_context():
            user_id, project_id = self._create_project_and_user(db, app)
            phase = PEPPhase(project_id=project_id, name='Phase 1', sequence=1)
            db.session.add(phase)
            db.session.commit()
            found = PEPPhase.query.filter_by(project_id=project_id).first()
            assert found is not None
            assert found.name == 'Phase 1'
            db.session.delete(found)
            project = Project.query.get(project_id)
            db.session.delete(project)
            user = User.query.get(user_id)
            db.session.delete(user)
            db.session.commit()

    def test_phase_stage_activity_hierarchy(self, app, db):
        """Test the full Phase → Stage → Activity hierarchy."""
        with app.app_context():
            user_id, project_id = self._create_project_and_user(db, app)
            try:
                phase = PEPPhase(project_id=project_id, name='Design', sequence=1)
                db.session.add(phase)
                db.session.flush()

                stage = PEPStage(phase_id=phase.id, name='Conceptual', sequence=1)
                db.session.add(stage)
                db.session.flush()

                activity = PEPActivity(
                    stage_id=stage.id,
                    name='Brainstorm',
                    duration_hours=8,
                    status='pending',
                    progress=0,
                )
                db.session.add(activity)
                db.session.commit()

                loaded_phase = PEPPhase.query.get(phase.id)
                assert loaded_phase is not None
                stages = loaded_phase.stages.all()
                assert len(stages) == 1
                assert stages[0].name == 'Conceptual'
                activities = stages[0].activities.all()
                assert len(activities) == 1
                assert activities[0].name == 'Brainstorm'
            finally:
                db.session.query(PEPPhase).filter_by(project_id=project_id).delete()
                db.session.delete(Project.query.get(project_id))
                db.session.delete(User.query.get(user_id))
                db.session.commit()

    def test_risk_level_calculation(self, app, db):
        """Test risk level and color properties."""
        with app.app_context():
            user_id, project_id = self._create_project_and_user(db, app)
            try:
                low_risk = PEPRisk(project_id=project_id, description='Low', probability=1, impact=1)
                med_risk = PEPRisk(project_id=project_id, description='Med', probability=3, impact=3)
                high_risk = PEPRisk(project_id=project_id, description='High', probability=5, impact=5)

                assert low_risk.risk_level == 1
                assert low_risk.risk_color == 'green'

                assert med_risk.risk_level == 9
                assert med_risk.risk_color == 'yellow'

                assert high_risk.risk_level == 25
                assert high_risk.risk_color == 'red'

                db.session.add_all([low_risk, med_risk, high_risk])
                db.session.commit()

                risks = PEPRisk.query.filter_by(project_id=project_id).all()
                assert len(risks) == 3
            finally:
                db.session.query(PEPRisk).filter_by(project_id=project_id).delete()
                db.session.delete(Project.query.get(project_id))
                db.session.delete(User.query.get(user_id))
                db.session.commit()

    def test_baseline_locked_property(self, app, db):
        """Test that PEPBaseline.is_locked reflects status correctly."""
        import datetime
        with app.app_context():
            user_id, project_id = self._create_project_and_user(db, app)
            try:
                bl = PEPBaseline(
                    project_id=project_id,
                    name='v1',
                    baseline_date=datetime.date.today(),
                    status='active',
                    created_by=user_id,
                )
                db.session.add(bl)
                db.session.commit()

                assert bl.is_locked is False
                bl.status = 'locked'
                assert bl.is_locked is True
            finally:
                db.session.query(PEPBaseline).filter_by(project_id=project_id).delete()
                db.session.delete(Project.query.get(project_id))
                db.session.delete(User.query.get(user_id))
                db.session.commit()

    def test_change_log_creation(self, app, db):
        """Test PEPChangeLog records are created correctly."""
        with app.app_context():
            user_id, project_id = self._create_project_and_user(db, app)
            try:
                log = PEPChangeLog(
                    project_id=project_id,
                    entity_type='phase',
                    change_description='Fase criada: Design',
                    created_by=user_id,
                )
                db.session.add(log)
                db.session.commit()

                found = PEPChangeLog.query.filter_by(project_id=project_id).first()
                assert found is not None
                assert found.entity_type == 'phase'
                assert 'Design' in found.change_description
            finally:
                db.session.query(PEPChangeLog).filter_by(project_id=project_id).delete()
                db.session.delete(Project.query.get(project_id))
                db.session.delete(User.query.get(user_id))
                db.session.commit()

    def test_variation_variance_properties(self, app, db):
        """Test PEPVariation.variance and variance_pct calculations."""
        import datetime
        from app.models.pep import PEPVariation
        with app.app_context():
            user_id, project_id = self._create_project_and_user(db, app)
            try:
                bl = PEPBaseline(
                    project_id=project_id,
                    name='v1',
                    baseline_date=datetime.date.today(),
                    status='active',
                )
                db.session.add(bl)
                db.session.flush()

                variation = PEPVariation(
                    baseline_id=bl.id,
                    original_value=100,
                    current_value=120,
                    variation_type='cost',
                )
                db.session.add(variation)
                db.session.commit()

                assert float(variation.variance) == 20.0
                assert abs(variation.variance_pct - 20.0) < 0.01
            finally:
                db.session.query(PEPBaseline).filter_by(project_id=project_id).delete()
                db.session.delete(Project.query.get(project_id))
                db.session.delete(User.query.get(user_id))
                db.session.commit()


class TestPEPRoutes:
    """Tests for PEP blueprint routes."""

    def _login(self, client, app, db):
        """Helper: register + login a user, return project id."""
        with app.app_context():
            user = User.query.filter_by(username='routepepuser').first()
            if not user:
                user = User(username='routepepuser', email='routepep@test.com', role='admin')
                user.set_password('pass')
                db.session.add(user)
                db.session.flush()
                project = Project(name='Route PEP Project', owner_id=user.id)
                db.session.add(project)
                db.session.commit()
            else:
                project = Project.query.filter_by(owner_id=user.id).first()

        client.post('/login', data={'username': 'routepepuser', 'password': 'pass'}, follow_redirects=True)

        with app.app_context():
            p = Project.query.filter_by(name='Route PEP Project').first()
            return p.id if p else None

    def test_pep_dashboard_redirects_unauthenticated(self, client, app, db):
        """Unauthenticated access to PEP dashboard should redirect."""
        resp = client.get('/projects/1/pep/', follow_redirects=False)
        assert resp.status_code in (302, 301)

    def test_pep_dashboard_returns_200_for_authenticated(self, client, app, db):
        """Authenticated access to PEP dashboard should return 200."""
        project_id = self._login(client, app, db)
        if project_id is None:
            pytest.skip('Could not create project for route test')
        resp = client.get(f'/projects/{project_id}/pep/')
        assert resp.status_code == 200

    def test_pep_eap_returns_200(self, client, app, db):
        """EAP page returns 200 for authenticated user."""
        project_id = self._login(client, app, db)
        if project_id is None:
            pytest.skip('Could not create project for route test')
        resp = client.get(f'/projects/{project_id}/pep/eap')
        assert resp.status_code == 200

    def test_pep_risks_returns_200(self, client, app, db):
        """Risks page returns 200 for authenticated user."""
        project_id = self._login(client, app, db)
        if project_id is None:
            pytest.skip('Could not create project for route test')
        resp = client.get(f'/projects/{project_id}/pep/risks')
        assert resp.status_code == 200

    def test_create_phase_via_post(self, client, app, db):
        """POST to create_phase creates a new phase."""
        project_id = self._login(client, app, db)
        if project_id is None:
            pytest.skip('Could not create project for route test')
        resp = client.post(
            f'/projects/{project_id}/pep/eap/phases/new',
            data={'name': 'Test Phase', 'status': 'pending', 'sequence': '1'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        with app.app_context():
            phase = PEPPhase.query.filter_by(project_id=project_id, name='Test Phase').first()
            assert phase is not None

    def test_create_risk_via_post(self, client, app, db):
        """POST to create_risk creates a new risk entry."""
        project_id = self._login(client, app, db)
        if project_id is None:
            pytest.skip('Could not create project for route test')
        resp = client.post(
            f'/projects/{project_id}/pep/risks/new',
            data={
                'description': 'Test risk description',
                'probability': '3',
                'impact': '4',
                'status': 'identified',
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        with app.app_context():
            risk = PEPRisk.query.filter_by(project_id=project_id, description='Test risk description').first()
            assert risk is not None
            assert risk.risk_level == 12

    def test_pep_alerts_returns_200(self, client, app, db):
        """Alerts page returns 200 for authenticated user."""
        project_id = self._login(client, app, db)
        if project_id is None:
            pytest.skip('Could not create project for route test')
        resp = client.get(f'/projects/{project_id}/pep/alerts')
        assert resp.status_code == 200

    def test_pep_variance_analysis_returns_200(self, client, app, db):
        """Variance analysis page returns 200 for authenticated user."""
        project_id = self._login(client, app, db)
        if project_id is None:
            pytest.skip('Could not create project for route test')
        resp = client.get(f'/projects/{project_id}/pep/variance-analysis')
        assert resp.status_code == 200

    def test_pep_activity_sync_history_returns_json(self, client, app, db):
        """Sync history endpoint returns JSON for a valid activity."""
        from app.models.pep import PEPPhase, PEPStage, PEPActivity
        project_id = self._login(client, app, db)
        if project_id is None:
            pytest.skip('Could not create project for route test')
        with app.app_context():
            phase = PEPPhase(project_id=project_id, name='SyncPhase', sequence=1)
            db.session.add(phase)
            db.session.flush()
            stage = PEPStage(phase_id=phase.id, name='SyncStage', sequence=1)
            db.session.add(stage)
            db.session.flush()
            activity = PEPActivity(stage_id=stage.id, name='SyncActivity')
            db.session.add(activity)
            db.session.commit()
            activity_id = activity.id
        resp = client.get(f'/projects/{project_id}/pep/activity/{activity_id}/sync-history')
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
