import traceback
from app import create_app, db
from app.models.project import Project
from app.services.financial_service import CostCenterService

app = create_app()

with app.app_context():
    try:
        # Teste 1: Verificar se projeto existe
        project = db.session.get(Project, 1)
        print(f"✅ Projeto encontrado: {project}")
        
        # Teste 2: Tentar criar cost center
        print("\nTentando criar cost center...")
        cc, error = CostCenterService.create_cost_center(
            project_id=1,
            name="Test CC",
            description="Test Description",
            budget_allocation=1000.00
        )
        
        if cc:
            print(f"✅ Cost center criado: {cc}")
        else:
            print(f"❌ Erro ao criar: {error}")
            
    except Exception as e:
        print("❌ Erro durante execução:")
        traceback.print_exc()
