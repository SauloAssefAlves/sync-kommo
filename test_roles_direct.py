#!/usr/bin/env python3
"""
🔧 TESTE DIRETO DO SYNC DE ROLES

Vamos testar apenas a lógica básica sem os filtros problemáticos
"""

import requests
import json

def test_roles_sync_direct():
    """Teste direto do sync de roles"""
    
    print("🔧 TESTE DIRETO DO SYNC DE ROLES")
    print("=" * 50)
    
    base_url = "http://89.116.186.230:5000/api/sync"
    
    # Primeiro: verificar contas disponíveis
    print("📋 1. Verificando contas disponíveis...")
    response = requests.get(f"{base_url}/accounts")
    if response.status_code == 200:
        accounts = response.json()
        print(f"   Total de contas: {accounts['total']}")
        
        master_accounts = [acc for acc in accounts['accounts'] if acc['account_role'] == 'master']
        slave_accounts = [acc for acc in accounts['accounts'] if acc['account_role'] == 'slave']
        
        print(f"   Contas master: {len(master_accounts)}")
        print(f"   Contas slave: {len(slave_accounts)}")
        
        if master_accounts and slave_accounts:
            master_id = master_accounts[0]['id']
            slave_id = slave_accounts[0]['id']
            
            print(f"\n🎯 2. Testando sync roles específico:")
            print(f"   Master: {master_accounts[0]['subdomain']} (ID: {master_id})")
            print(f"   Slave: {slave_accounts[0]['subdomain']} (ID: {slave_id})")
            
            # Teste com parâmetros específicos
            payload = {
                "master_account_id": master_id,
                "slave_account_ids": [slave_id]
            }
            
            print(f"\n📡 3. Enviando requisição...")
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f"{base_url}/roles",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            print(f"\n📥 4. Resposta:")
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Sucesso: {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                try:
                    error = response.json()
                    print(f"   ❌ Erro: {json.dumps(error, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   ❌ Erro (raw): {response.text}")
        else:
            print("   ❌ Não há contas master e slave suficientes para teste")
    else:
        print(f"   ❌ Erro ao obter contas: {response.status_code} - {response.text}")

if __name__ == '__main__':
    test_roles_sync_direct()
