import traceback
from app import create_app

app = create_app()

with app.app_context():
    try:
        from app.routes.financial import financial_bp
        print("✅ financial_bp importado com sucesso")
    except Exception as e:
        print("❌ Erro ao importar financial_bp:")
        traceback.print_exc()
