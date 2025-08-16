"""
🔑 VERIFICAÇÃO E ATUALIZAÇÃO DE TOKENS
Verifica se os tokens das contas estão válidos e atualiza se necessário
"""

import os
import sys
import sqlite3
from datetime import datetime, timezone
import requests

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def check_and_refresh_tokens():
    """Verifica e atualiza tokens das contas"""
    print("🔑 VERIFICAÇÃO E ATUALIZAÇÃO DE TOKENS")
    print("=" * 50)
    
    # Verificar banco
    db_path = os.path.join('src', 'database', 'app.db')
    if not os.path.exists(db_path):
        print(f"❌ Banco não encontrado: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar contas com tokens
    cursor.execute('''
        SELECT id, subdomain, access_token, refresh_token, token_expires_at, 
               client_id, client_secret, account_role
        FROM kommo_accounts 
        ORDER BY account_role DESC, id
    ''')
    
    accounts = cursor.fetchall()
    print(f"📊 Verificando {len(accounts)} contas:")
    
    for account in accounts:
        account_id, subdomain, access_token, refresh_token, expires_at, client_id, client_secret, role = account
        
        print(f"\n🔍 Conta: {subdomain} ({role})")
        print(f"   ID: {account_id}")
        print(f"   Token atual: {access_token[:20] if access_token else 'None'}...")
        print(f"   Expira em: {expires_at}")
        print(f"   Refresh token: {refresh_token[:20] if refresh_token else 'None'}...")
        
        if not access_token:
            print("   ❌ Sem access token")
            continue
        
        # Testar token atual
        test_url = f"https://{subdomain}.kommo.com/api/v4/account"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            print("   🧪 Testando token atual...")
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("   ✅ Token válido!")
                continue
            elif response.status_code == 401:
                print("   ❌ Token expirado - tentando renovar...")
                
                # Tentar renovar com refresh token
                if refresh_token and client_id and client_secret:
                    refresh_url = f"https://{subdomain}.kommo.com/oauth2/access_token"
                    refresh_data = {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "redirect_uri": "https://httpbin.org/get"  # URI padrão
                    }
                    
                    print("   🔄 Renovando token...")
                    refresh_response = requests.post(refresh_url, data=refresh_data, timeout=10)
                    
                    if refresh_response.status_code == 200:
                        token_data = refresh_response.json()
                        new_access_token = token_data.get('access_token')
                        new_refresh_token = token_data.get('refresh_token')
                        expires_in = token_data.get('expires_in', 86400)  # 24h padrão
                        
                        # Calcular nova data de expiração
                        new_expires_at = datetime.now(timezone.utc).timestamp() + expires_in
                        
                        # Atualizar no banco
                        cursor.execute('''
                            UPDATE kommo_accounts 
                            SET access_token = ?, refresh_token = ?, token_expires_at = ?
                            WHERE id = ?
                        ''', (new_access_token, new_refresh_token, new_expires_at, account_id))
                        
                        conn.commit()
                        
                        print(f"   ✅ Token renovado com sucesso!")
                        print(f"   📅 Novo token expira em: {datetime.fromtimestamp(new_expires_at)}")
                    else:
                        print(f"   ❌ Falha ao renovar token: {refresh_response.status_code}")
                        print(f"   📄 Resposta: {refresh_response.text}")
                else:
                    print("   ❌ Sem dados para renovação (refresh_token, client_id ou client_secret)")
            else:
                print(f"   ⚠️ Resposta inesperada: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro ao testar token: {e}")
    
    conn.close()
    print(f"\n✅ Verificação concluída!")

if __name__ == "__main__":
    check_and_refresh_tokens()
