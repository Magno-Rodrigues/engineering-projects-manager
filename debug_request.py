import traceback
from app import create_app
from flask import url_for

app = create_app()
app.config['PROPAGATE_EXCEPTIONS'] = True

with app.app_context():
    with app.test_client() as client:
        # Simular login (ou usar sessão)
        try:
            # Teste o POST com mais informações
            response = client.post(
                '/projects/1/financial/cost-centers',
                data={
                    'action': 'create',
                    'name': 'Test CC',
                    'description': 'Test',
                    'budget_allocation': '1000.00'
                },
                follow_redirects=False
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code != 302:
                print(f"Response: {response.data.decode()[:1000]}")
                
        except Exception as e:
            print("❌ ERRO CAPTURADO:")
            traceback.print_exc()
