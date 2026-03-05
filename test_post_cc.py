import traceback
from app import create_app
from flask import url_for

app = create_app()

with app.app_context():
    with app.test_client() as client:
        try:
            # Login primeiro (se necessário)
            # Fazer o POST
            response = client.post(
                '/projects/1/financial/cost-centers',
                data={
                    'action': 'create',
                    'name': 'Test CC POST',
                    'description': 'Test Description',
                    'budget_allocation': '1000.00'
                },
                follow_redirects=False
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Location: {response.headers.get('Location', 'N/A')}")
            print(f"Data: {response.data[:500]}")
            
        except Exception as e:
            print("❌ Erro durante POST:")
            traceback.print_exc()
