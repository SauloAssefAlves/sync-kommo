#!/usr/bin/env python3
"""Script para testar as funcionalidades de sincronização"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_sync_functionality():
    print("=== TESTE DE FUNCIONALIDADES DE SINCRONIZAÇÃO ===\n")
    
    # 1. Verificar grupos
    print("1. Verificando grupos disponíveis...")
    response = requests.get(f"{BASE_URL}/groups/")
    if response.status_code == 200:
        groups_response = response.json()
        print(f"   Response type: {type(groups_response)}")
        print(f"   Response content: {groups_response}")
        
        # Se a resposta for uma lista diretamente
        if isinstance(groups_response, list):
            groups = groups_response
        # Se a resposta for um dict com chave 'groups' ou similar
        elif isinstance(groups_response, dict) and 'groups' in groups_response:
            groups = groups_response['groups']
        else:
            groups = []
            
        print(f"   ✅ Encontrados {len(groups)} grupos")
        for group in groups:
            if isinstance(group, dict):
                print(f"   📁 Grupo: {group.get('name', 'N/A')} (ID: {group.get('id', 'N/A')})")
            else:
                print(f"   📁 Grupo: {group}")
    else:
        print(f"   ❌ Erro ao buscar grupos: {response.status_code}")
        return
    
    # 2. Verificar contas
    print("\n2. Verificando contas disponíveis...")
    response = requests.get(f"{BASE_URL}/sync/accounts")
    if response.status_code == 200:
        accounts_response = response.json()
        
        # Se a resposta for uma lista diretamente
        if isinstance(accounts_response, list):
            accounts = accounts_response
        # Se a resposta for um dict com chave 'accounts' ou similar
        elif isinstance(accounts_response, dict) and 'accounts' in accounts_response:
            accounts = accounts_response['accounts']
        else:
            accounts = []
            
        print(f"   ✅ Encontradas {len(accounts)} contas")
        for account in accounts:
            if isinstance(account, dict):
                subdomain = account.get('subdomain', 'N/A')
                is_master = account.get('is_master', False) or account.get('account_role') == 'master'
                role = 'Mestre' if is_master else 'Escrava'
                print(f"   👤 Conta: {subdomain} - {role}")
            else:
                print(f"   👤 Conta: {account}")
    else:
        print(f"   ❌ Erro ao buscar contas: {response.status_code}")
        return
    
    if not groups:
        print("\n❌ Nenhum grupo encontrado. Criar um grupo primeiro.")
        return
    
    # 3. Testar sincronização de grupo
    group_id = groups[0]['id'] if groups and isinstance(groups[0], dict) else 1
    group_name = groups[0]['name'] if groups and isinstance(groups[0], dict) else 'Teste'
    
    print(f"\n3. Testando sincronização do grupo '{group_name}' (ID: {group_id})...")
    
    sync_data = {
        "sync_type": "custom_fields",
        "batch_config": {
            "batch_size": 5,
            "batch_delay": 1.0,
            "max_concurrent": 2
        }
    }
    
    response = requests.post(f"{BASE_URL}/sync/groups/{group_id}/trigger", 
                           headers={'Content-Type': 'application/json'},
                           data=json.dumps(sync_data))
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Sincronização iniciada com sucesso")
        print(f"   📊 Resultado: {result.get('message', 'N/A')}")
        if 'sync_log_id' in result:
            print(f"   📝 Log ID: {result['sync_log_id']}")
    else:
        print(f"   ❌ Erro na sincronização: {response.status_code}")
        try:
            error = response.json()
            print(f"   💬 Mensagem: {error.get('error', 'Erro desconhecido')}")
        except:
            print(f"   💬 Resposta: {response.text}")
    
    # 4. Testar sincronização global
    print(f"\n4. Testando sincronização global...")
    
    global_sync_data = {
        "sync_type": "pipelines",
        "batch_config": {
            "batch_size": 3,
            "batch_delay": 0.5,
            "max_concurrent": 1
        }
    }
    
    response = requests.post(f"{BASE_URL}/sync/trigger", 
                           headers={'Content-Type': 'application/json'},
                           data=json.dumps(global_sync_data))
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Sincronização global iniciada com sucesso")
        print(f"   📊 Resultado: {result.get('message', 'N/A')}")
    else:
        print(f"   ❌ Erro na sincronização global: {response.status_code}")
        try:
            error = response.json()
            print(f"   💬 Mensagem: {error.get('error', 'Erro desconhecido')}")
        except:
            print(f"   💬 Resposta: {response.text}")
    
    # 5. Verificar status da sincronização
    print(f"\n5. Verificando status da sincronização...")
    time.sleep(2)  # Aguardar um pouco
    
    response = requests.get(f"{BASE_URL}/sync/status")
    if response.status_code == 200:
        status = response.json()
        print(f"   📊 Status: {status.get('current_status', 'N/A')}")
        print(f"   🔄 Operação: {status.get('current_operation', 'N/A')}")
        print(f"   📈 Progresso: {status.get('progress', 0)}%")
        print(f"   ⚙️ Executando: {status.get('is_running', False)}")
    else:
        print(f"   ❌ Erro ao verificar status: {response.status_code}")

if __name__ == '__main__':
    test_sync_functionality()
