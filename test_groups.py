#!/usr/bin/env python3
"""
Script para testar o sistema de grupos de sincronização
"""

import requests
import json
import time

# Configuração do servidor
BASE_URL = "http://localhost:5000"

def test_groups():
    """Testa a criação e gerenciamento de grupos"""
    
    print("🧪 Testando sistema de grupos...")
    
    # 1. Criar um grupo
    print("\n1. Criando grupo de teste...")
    group_data = {
        "name": "Grupo Principal",
        "description": "Grupo principal para testes",
        "master_account_id": 1  # Assumindo que existe uma conta com ID 1
    }
    
    response = requests.post(f"{BASE_URL}/api/groups", json=group_data)
    if response.status_code == 201:
        group = response.json()
        group_id = group['group']['id']
        print(f"✅ Grupo criado com sucesso! ID: {group_id}")
    else:
        print(f"❌ Erro ao criar grupo: {response.text}")
        return False
    
    # 2. Listar grupos
    print("\n2. Listando grupos...")
    response = requests.get(f"{BASE_URL}/api/groups")
    if response.status_code == 200:
        groups = response.json()
        print(f"✅ Grupos encontrados: {len(groups['groups'])}")
        for group in groups['groups']:
            print(f"   - {group['name']} (ID: {group['id']})")
    else:
        print(f"❌ Erro ao listar grupos: {response.text}")
    
    # 3. Obter detalhes do grupo
    print(f"\n3. Obtendo detalhes do grupo {group_id}...")
    response = requests.get(f"{BASE_URL}/api/groups/{group_id}")
    if response.status_code == 200:
        group = response.json()
        print(f"✅ Detalhes do grupo obtidos:")
        print(f"   - Nome: {group['group']['name']}")
        print(f"   - Descrição: {group['group']['description']}")
        print(f"   - Contas escravas: {len(group['group']['slave_accounts'])}")
    else:
        print(f"❌ Erro ao obter detalhes do grupo: {response.text}")
    
    # 4. Adicionar conta escrava (assumindo que existe uma conta com ID 2)
    print(f"\n4. Adicionando conta escrava ao grupo {group_id}...")
    slave_data = {"account_id": 2}
    response = requests.post(f"{BASE_URL}/api/groups/{group_id}/slaves", json=slave_data)
    if response.status_code == 200:
        print("✅ Conta escrava adicionada com sucesso!")
    else:
        print(f"❌ Erro ao adicionar conta escrava: {response.text}")
    
    # 5. Testar sincronização do grupo
    print(f"\n5. Testando sincronização do grupo {group_id}...")
    sync_data = {"sync_type": "full"}
    response = requests.post(f"{BASE_URL}/api/groups/{group_id}/sync", json=sync_data)
    if response.status_code == 200:
        sync_result = response.json()
        print(f"✅ Sincronização do grupo iniciada!")
        print(f"   - Status: {sync_result.get('message', 'N/A')}")
    else:
        print(f"❌ Erro ao sincronizar grupo: {response.text}")
    
    return group_id

def test_legacy_compatibility():
    """Testa compatibilidade com o sistema antigo"""
    
    print("\n🔄 Testando compatibilidade com sistema antigo...")
    
    # 1. Testar endpoint de contas escravas (modo antigo)
    print("\n1. Listando contas escravas (modo antigo)...")
    response = requests.get(f"{BASE_URL}/api/sync/accounts/slaves")
    if response.status_code == 200:
        accounts = response.json()
        print(f"✅ Contas escravas encontradas: {len(accounts['accounts'])}")
        for account in accounts['accounts']:
            print(f"   - {account['subdomain']} (Status: {account['status']})")
    else:
        print(f"❌ Erro ao listar contas escravas: {response.text}")
    
    # 2. Testar endpoint de conta mestre (modo antigo)
    print("\n2. Obtendo conta mestre (modo antigo)...")
    response = requests.get(f"{BASE_URL}/api/sync/accounts/master")
    if response.status_code == 200:
        master = response.json()
        print(f"✅ Conta mestre encontrada:")
        print(f"   - Subdomínio: {master['account']['subdomain']}")
        print(f"   - Status: {master['account']['status']}")
    else:
        print(f"❌ Erro ao obter conta mestre: {response.text}")

def test_group_filtering():
    """Testa filtragem por grupo"""
    
    print("\n🔍 Testando filtragem por grupo...")
    
    # Assumindo que existe um grupo com ID 1
    group_id = 1
    
    # 1. Listar contas escravas do grupo específico
    print(f"\n1. Listando contas escravas do grupo {group_id}...")
    response = requests.get(f"{BASE_URL}/api/sync/accounts/slaves?group_id={group_id}")
    if response.status_code == 200:
        accounts = response.json()
        print(f"✅ Contas escravas do grupo {group_id}: {len(accounts['accounts'])}")
        for account in accounts['accounts']:
            group_info = account.get('group', {})
            print(f"   - {account['subdomain']} (Grupo: {group_info.get('name', 'N/A')})")
    else:
        print(f"❌ Erro ao listar contas do grupo: {response.text}")
    
    # 2. Obter conta mestre do grupo específico
    print(f"\n2. Obtendo conta mestre do grupo {group_id}...")
    response = requests.get(f"{BASE_URL}/api/sync/accounts/master?group_id={group_id}")
    if response.status_code == 200:
        master = response.json()
        group_info = master['account'].get('group', {})
        print(f"✅ Conta mestre do grupo {group_id}:")
        print(f"   - Subdomínio: {master['account']['subdomain']}")
        print(f"   - Grupo: {group_info.get('name', 'N/A')}")
    else:
        print(f"❌ Erro ao obter conta mestre do grupo: {response.text}")

def test_endpoints():
    """Testa todos os endpoints do sistema"""
    
    print("🚀 Iniciando testes completos do sistema de grupos...\n")
    
    try:
        # Testar criação e gerenciamento de grupos
        group_id = test_groups()
        
        # Testar compatibilidade com sistema antigo
        test_legacy_compatibility()
        
        # Testar filtragem por grupo
        if group_id:
            test_group_filtering()
        
        print("\n✅ Todos os testes concluídos!")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")

if __name__ == "__main__":
    test_endpoints()
