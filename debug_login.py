import traceback
from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    with app.test_client() as client:
        try:
            # 1. Verificar usuário admin
            admin = User.query.filter_by(username='admin').first()
            print(f"Admin encontrado: {admin}")
            
            if admin:
                # 2. Fazer login
                response = client.post('/login', data={
                    'username': 'admin',
                    'password': 'admin123'  # Ajuste se necessário
                }, follow_redirects=True)
                
                print(f"Login status: {response.status_code}")
                
                # 3. Agora fazer POST do cost center
                response = client.post(
                    '/projects/1/financial/cost-centers',
                    data={
                        'action': 'create',
                        'name': 'CC via Login',
                        'description': 'Test',
                        'budget_allocation': '1000.00'
                    },
                    follow_redirects=False
                )
                
                print(f"POST status: {response.status_code}")
                if response.status_code == 302:
                    print(f"✅ Redirect para: {response.headers.get('Location')}")
                else:
                    print(f"Response: {response.data.decode()[:500]}")
            
        except Exception as e:
            print("❌ ERRO:")
            traceback.print_exc()
