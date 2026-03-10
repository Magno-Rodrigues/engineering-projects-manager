"""Flask CLI commands for development and seeding."""
import click
from datetime import date
from flask import Blueprint
from app import db

cli_bp = Blueprint('cli', __name__, cli_group=None)


@cli_bp.cli.command('seed-pep-sample')
@click.argument('project_id', type=int, required=False)
def seed_pep_sample(project_id=None):
    """Populate a project with sample PEP data (phases, stages, activities, risks, baseline).

    If PROJECT_ID is not provided a new sample project is created.

    Usage:
        flask seed-pep-sample
        flask seed-pep-sample 4
    """
    from app.models.user import User
    from app.models.project import Project
    from app.models.pep import (
        PEPPhase, PEPStage, PEPActivity,
        PEPRisk, PEPBaseline, PEPChangeLog,
        PEPResourceAllocation,
    )

    # ------------------------------------------------------------------ #
    # Resolve user
    # ------------------------------------------------------------------ #
    user = User.query.filter_by(role='admin').first() or User.query.first()
    if user is None:
        click.echo('❌  Nenhum usuário encontrado. Crie um usuário antes de rodar este comando.')
        return

    # ------------------------------------------------------------------ #
    # Resolve / create project
    # ------------------------------------------------------------------ #
    if project_id:
        project = Project.query.get(project_id)
        if project is None:
            click.echo(f'❌  Projeto {project_id} não encontrado.')
            return
        click.echo(f'📁  Usando projeto existente: {project.name} (id={project.id})')
    else:
        project = Project(
            name='Renovação Campus — Prédio C',
            description='Projeto de renovação completa do Prédio C do campus universitário.',
            status='in_progress',
            start_date=date(2026, 3, 15),
            end_date=date(2026, 6, 15),
            owner_id=user.id,
            category='Construção',
            priority='high',
        )
        db.session.add(project)
        db.session.flush()
        click.echo(f'📁  Projeto criado: {project.name} (id={project.id})')

    project_id = project.id

    # ------------------------------------------------------------------ #
    # Helper — avoid duplicates
    # ------------------------------------------------------------------ #
    if PEPPhase.query.filter_by(project_id=project_id).count() > 0:
        click.echo('⚠️   EAP já possui dados. Pulando criação de fases/atividades.')
    else:
        _create_eap(db, project_id, user.id)

    if PEPRisk.query.filter_by(project_id=project_id).count() > 0:
        click.echo('⚠️   Riscos já existem. Pulando criação de riscos.')
    else:
        _create_risks(db, project_id, user.id)

    if PEPBaseline.query.filter_by(project_id=project_id).count() > 0:
        click.echo('⚠️   Baseline já existe. Pulando criação de baseline.')
    else:
        _create_baseline(db, project_id, user.id)

    db.session.commit()
    click.echo(f'✅  Dados de exemplo criados com sucesso para o projeto {project_id}!')
    click.echo(f'    Acesse: /projects/{project_id}/pep/')


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #

def _create_eap(db, project_id, user_id):
    """Create the sample EAP structure (3 phases × 3 stages × 2-3 activities)."""
    from app.models.pep import PEPPhase, PEPStage, PEPActivity, PEPResourceAllocation

    structure = [
        {
            'name': 'Fase 1: Projeto',
            'start': date(2026, 3, 15),
            'end': date(2026, 4, 15),
            'status': 'in_progress',
            'sequence': 1,
            'stages': [
                {
                    'name': 'Levantamento de Requisitos',
                    'start': date(2026, 3, 15),
                    'end': date(2026, 3, 25),
                    'status': 'completed',
                    'sequence': 1,
                    'activities': [
                        {
                            'name': 'Entrevistas com stakeholders',
                            'description': 'Reuniões com responsáveis de cada área do prédio.',
                            'duration_hours': 40,
                            'start_date': date(2026, 3, 15),
                            'end_date': date(2026, 3, 20),
                            'status': 'completed',
                            'progress': 100,
                        },
                        {
                            'name': 'Documentação dos requisitos',
                            'description': 'Consolidar requisitos funcionais e técnicos.',
                            'duration_hours': 24,
                            'start_date': date(2026, 3, 20),
                            'end_date': date(2026, 3, 25),
                            'status': 'completed',
                            'progress': 100,
                        },
                    ],
                },
                {
                    'name': 'Projeto Conceitual',
                    'start': date(2026, 3, 25),
                    'end': date(2026, 4, 5),
                    'status': 'in_progress',
                    'sequence': 2,
                    'activities': [
                        {
                            'name': 'Esboço arquitetônico inicial',
                            'description': 'Rascunho do layout e definição de áreas.',
                            'duration_hours': 60,
                            'start_date': date(2026, 3, 25),
                            'end_date': date(2026, 4, 1),
                            'status': 'in_progress',
                            'progress': 60,
                        },
                        {
                            'name': 'Validação com engenharia',
                            'description': 'Revisão técnica do esboço com equipe de engenharia.',
                            'duration_hours': 16,
                            'start_date': date(2026, 4, 1),
                            'end_date': date(2026, 4, 5),
                            'status': 'pending',
                            'progress': 0,
                        },
                    ],
                },
                {
                    'name': 'Projeto Final',
                    'start': date(2026, 4, 5),
                    'end': date(2026, 4, 15),
                    'status': 'pending',
                    'sequence': 3,
                    'activities': [
                        {
                            'name': 'Detalhamento técnico',
                            'description': 'Especificações completas de materiais e execução.',
                            'duration_hours': 80,
                            'start_date': date(2026, 4, 5),
                            'end_date': date(2026, 4, 12),
                            'status': 'pending',
                            'progress': 10,
                        },
                        {
                            'name': 'Aprovação e assinaturas',
                            'description': 'Aprovação final pelos gestores responsáveis.',
                            'duration_hours': 8,
                            'start_date': date(2026, 4, 12),
                            'end_date': date(2026, 4, 15),
                            'status': 'pending',
                            'progress': 0,
                        },
                    ],
                },
            ],
        },
        {
            'name': 'Fase 2: Planejamento',
            'start': date(2026, 4, 15),
            'end': date(2026, 5, 15),
            'status': 'pending',
            'sequence': 2,
            'stages': [
                {
                    'name': 'Planejamento de Recursos',
                    'start': date(2026, 4, 15),
                    'end': date(2026, 4, 30),
                    'status': 'pending',
                    'sequence': 1,
                    'activities': [
                        {
                            'name': 'Definição da equipe',
                            'description': 'Identificação e alocação de profissionais necessários.',
                            'duration_hours': 24,
                            'start_date': date(2026, 4, 15),
                            'end_date': date(2026, 4, 22),
                            'status': 'pending',
                            'progress': 0,
                        },
                        {
                            'name': 'Cronograma detalhado',
                            'description': 'Elaboração do cronograma mestre de execução.',
                            'duration_hours': 32,
                            'start_date': date(2026, 4, 22),
                            'end_date': date(2026, 4, 30),
                            'status': 'pending',
                            'progress': 0,
                        },
                    ],
                },
                {
                    'name': 'Estimativa de Custos',
                    'start': date(2026, 4, 25),
                    'end': date(2026, 5, 5),
                    'status': 'pending',
                    'sequence': 2,
                    'activities': [
                        {
                            'name': 'Orçamento de materiais',
                            'description': 'Levantamento e cotação de todos os materiais.',
                            'duration_hours': 48,
                            'start_date': date(2026, 4, 25),
                            'end_date': date(2026, 5, 2),
                            'status': 'pending',
                            'progress': 20,
                        },
                        {
                            'name': 'Estimativa de mão de obra',
                            'description': 'Cálculo de horas e custos de mão de obra.',
                            'duration_hours': 24,
                            'start_date': date(2026, 5, 2),
                            'end_date': date(2026, 5, 5),
                            'status': 'pending',
                            'progress': 0,
                        },
                    ],
                },
                {
                    'name': 'Análise de Riscos',
                    'start': date(2026, 5, 5),
                    'end': date(2026, 5, 15),
                    'status': 'pending',
                    'sequence': 3,
                    'activities': [
                        {
                            'name': 'Identificação de riscos',
                            'description': 'Workshop de identificação de riscos com a equipe.',
                            'duration_hours': 16,
                            'start_date': date(2026, 5, 5),
                            'end_date': date(2026, 5, 10),
                            'status': 'pending',
                            'progress': 0,
                        },
                        {
                            'name': 'Plano de mitigação',
                            'description': 'Desenvolvimento de planos para os riscos críticos.',
                            'duration_hours': 24,
                            'start_date': date(2026, 5, 10),
                            'end_date': date(2026, 5, 15),
                            'status': 'pending',
                            'progress': 0,
                        },
                    ],
                },
            ],
        },
        {
            'name': 'Fase 3: Execução',
            'start': date(2026, 5, 15),
            'end': date(2026, 6, 15),
            'status': 'pending',
            'sequence': 3,
            'stages': [
                {
                    'name': 'Aquisição e Compras',
                    'start': date(2026, 5, 15),
                    'end': date(2026, 5, 30),
                    'status': 'pending',
                    'sequence': 1,
                    'activities': [
                        {
                            'name': 'Processo licitatório',
                            'description': 'Abertura e condução do processo de licitação.',
                            'duration_hours': 40,
                            'start_date': date(2026, 5, 15),
                            'end_date': date(2026, 5, 25),
                            'status': 'pending',
                            'progress': 0,
                        },
                        {
                            'name': 'Emissão de pedidos',
                            'description': 'Emissão de ordens de compra e contratos.',
                            'duration_hours': 16,
                            'start_date': date(2026, 5, 25),
                            'end_date': date(2026, 5, 30),
                            'status': 'pending',
                            'progress': 0,
                        },
                    ],
                },
                {
                    'name': 'Obras e Construção',
                    'start': date(2026, 5, 30),
                    'end': date(2026, 6, 10),
                    'status': 'pending',
                    'sequence': 2,
                    'activities': [
                        {
                            'name': 'Demolição e preparação',
                            'description': 'Demolição das áreas e preparação do canteiro.',
                            'duration_hours': 80,
                            'start_date': date(2026, 5, 30),
                            'end_date': date(2026, 6, 5),
                            'status': 'pending',
                            'progress': 0,
                        },
                        {
                            'name': 'Execução das obras',
                            'description': 'Construção conforme projeto aprovado.',
                            'duration_hours': 160,
                            'start_date': date(2026, 6, 5),
                            'end_date': date(2026, 6, 10),
                            'status': 'pending',
                            'progress': 0,
                        },
                    ],
                },
                {
                    'name': 'Testes e Controle de Qualidade',
                    'start': date(2026, 6, 10),
                    'end': date(2026, 6, 15),
                    'status': 'pending',
                    'sequence': 3,
                    'activities': [
                        {
                            'name': 'Inspeção final',
                            'description': 'Vistoria completa das obras executadas.',
                            'duration_hours': 16,
                            'start_date': date(2026, 6, 10),
                            'end_date': date(2026, 6, 13),
                            'status': 'pending',
                            'progress': 0,
                        },
                        {
                            'name': 'Entrega e aceite',
                            'description': 'Entrega formal ao cliente com termo de aceite.',
                            'duration_hours': 8,
                            'start_date': date(2026, 6, 13),
                            'end_date': date(2026, 6, 15),
                            'status': 'pending',
                            'progress': 0,
                        },
                    ],
                },
            ],
        },
    ]

    for phase_data in structure:
        phase = PEPPhase(
            project_id=project_id,
            name=phase_data['name'],
            start_date=phase_data['start'],
            end_date=phase_data['end'],
            status=phase_data['status'],
            sequence=phase_data['sequence'],
        )
        db.session.add(phase)
        db.session.flush()

        for stage_data in phase_data['stages']:
            stage = PEPStage(
                phase_id=phase.id,
                name=stage_data['name'],
                start_date=stage_data['start'],
                end_date=stage_data['end'],
                status=stage_data['status'],
                sequence=stage_data['sequence'],
            )
            db.session.add(stage)
            db.session.flush()

            for act_data in stage_data['activities']:
                activity = PEPActivity(
                    stage_id=stage.id,
                    name=act_data['name'],
                    description=act_data['description'],
                    duration_hours=act_data['duration_hours'],
                    start_date=act_data['start_date'],
                    end_date=act_data['end_date'],
                    status=act_data['status'],
                    progress=act_data['progress'],
                    responsible_user_id=user_id,
                )
                db.session.add(activity)
                db.session.flush()

                # Add resource allocation for each activity
                alloc = PEPResourceAllocation(
                    activity_id=activity.id,
                    user_id=user_id,
                    allocated_hours=act_data['duration_hours'],
                )
                db.session.add(alloc)

    click.echo('   ✅ EAP (fases, etapas e atividades) criado.')


def _create_risks(db, project_id, user_id):
    """Create 5 sample risks with varying levels."""
    from app.models.pep import PEPRisk

    risks = [
        {
            'description': 'Atraso na entrega de materiais pelo fornecedor principal',
            'probability': 4,
            'impact': 5,
            'status': 'identified',
            'mitigation_plan': 'Manter fornecedores alternativos cadastrados e solicitar entrega com antecedência de 2 semanas.',
        },
        {
            'description': 'Condições climáticas adversas durante a fase de obras externas',
            'probability': 3,
            'impact': 3,
            'status': 'identified',
            'mitigation_plan': 'Planejar buffer de 10% no cronograma e acompanhar previsão do tempo.',
        },
        {
            'description': 'Aumento de custos de mão de obra acima do orçado',
            'probability': 2,
            'impact': 4,
            'status': 'identified',
            'mitigation_plan': 'Contratos com cláusulas de reajuste fixo e reserva de contingência de 8%.',
        },
        {
            'description': 'Descoberta de problemas estruturais não previstos no projeto',
            'probability': 2,
            'impact': 5,
            'status': 'identified',
            'mitigation_plan': 'Realizar inspeção estrutural detalhada antes do início das obras.',
        },
        {
            'description': 'Rotatividade na equipe de projeto durante fase crítica',
            'probability': 1,
            'impact': 3,
            'status': 'identified',
            'mitigation_plan': 'Documentar conhecimento e manter backup para funções-chave.',
        },
    ]

    for risk_data in risks:
        risk = PEPRisk(
            project_id=project_id,
            description=risk_data['description'],
            probability=risk_data['probability'],
            impact=risk_data['impact'],
            status=risk_data['status'],
            mitigation_plan=risk_data['mitigation_plan'],
            owner_id=user_id,
        )
        db.session.add(risk)

    click.echo('   ✅ Riscos criados (5 riscos com níveis variados).')


def _create_baseline(db, project_id, user_id):
    """Create initial project baseline."""
    from app.models.pep import PEPBaseline

    baseline = PEPBaseline(
        project_id=project_id,
        name='Baseline Inicial v1.0',
        baseline_date=date(2026, 3, 10),
        status='active',
        created_by=user_id,
    )
    db.session.add(baseline)
    click.echo('   ✅ Baseline inicial criada.')
