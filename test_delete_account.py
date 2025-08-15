#!/usr/bin/env python3
"""
🗑️ TESTE: Exclusão de Conta Slave

Este script testa a funcionalidade de exclusão de contas slaves individuais.

ENDPOINTS TESTADOS:
- GET /api/sync/accounts - Listar contas
- DELETE /api/sync/accounts/{id} - Excluir conta específica
- DELETE /api/sync/accounts/clear - Limpar todas as contas
"""

import requests
import json

def test_delete_account_endpoints():
    """Testa os endpoints de exclusão de contas"""
    
    base_url = "http://localhost:5000/api/sync"
    
    print("🗑️ TESTE: Endpoints de Exclusão de Contas")
    print("=" * 50)
    
    # 1. Listar contas existentes
    print("\n📋 1. Listando contas existentes...")
    try:
        response = requests.get(f"{base_url}/accounts")
        if response.status_code == 200:
            accounts = response.json()
            print(f"   ✅ {accounts['total']} contas encontradas")
            
            if accounts['accounts']:
                print("   📊 Contas disponíveis:")
                for acc in accounts['accounts']:
                    role_emoji = "👑" if acc['is_master'] or acc['account_role'] == 'master' else "👤"
                    print(f"      {role_emoji} ID: {acc['id']} - {acc['subdomain']} ({acc['account_role']})")
            else:
                print("   ℹ️ Nenhuma conta cadastrada")
                return
        else:
            print(f"   ❌ Erro ao listar contas: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Erro na conexão: {e}")
        return
    
    # 2. Encontrar uma conta slave para testar exclusão
    slave_accounts = [acc for acc in accounts['accounts'] if not acc['is_master'] and acc['account_role'] != 'master']
    
    if not slave_accounts:
        print("\n   ⚠️ Nenhuma conta slave encontrada para testar exclusão")
        print("   💡 Apenas contas slave podem ser excluídas individualmente")
        return
    
    test_account = slave_accounts[0]
    account_id = test_account['id']
    subdomain = test_account['subdomain']
    
    print(f"\n🎯 2. Testando exclusão da conta slave: {subdomain} (ID: {account_id})")
    
    # 3. Tentar excluir uma conta master (deve falhar)
    master_accounts = [acc for acc in accounts['accounts'] if acc['is_master'] or acc['account_role'] == 'master']
    if master_accounts:
        master_id = master_accounts[0]['id']
        master_subdomain = master_accounts[0]['subdomain']
        
        print(f"\n🚫 3. Testando exclusão de conta master (deve falhar): {master_subdomain} (ID: {master_id})")
        try:
            response = requests.delete(f"{base_url}/accounts/{master_id}")
            if response.status_code == 400:
                result = response.json()
                print(f"   ✅ Proteção funcionando: {result['error']}")
            else:
                print(f"   ❌ Erro inesperado: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erro na requisição: {e}")
    
    # 4. Excluir conta slave
    print(f"\n🗑️ 4. Excluindo conta slave: {subdomain}")
    try:
        response = requests.delete(f"{base_url}/accounts/{account_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Conta excluída: {result['message']}")
            print(f"   📊 Detalhes: {result['account']}")
        else:
            result = response.json()
            print(f"   ❌ Erro ao excluir: {result.get('error', 'Erro desconhecido')}")
    except Exception as e:
        print(f"   ❌ Erro na requisição: {e}")
    
    # 5. Verificar se conta foi realmente removida
    print(f"\n✅ 5. Verificando se conta foi removida...")
    try:
        response = requests.get(f"{base_url}/accounts")
        if response.status_code == 200:
            new_accounts = response.json()
            remaining_ids = [acc['id'] for acc in new_accounts['accounts']]
            
            if account_id not in remaining_ids:
                print(f"   ✅ Conta {subdomain} (ID: {account_id}) foi removida com sucesso")
                print(f"   📊 Contas restantes: {new_accounts['total']}")
            else:
                print(f"   ❌ Conta {subdomain} ainda existe no banco!")
        else:
            print(f"   ❌ Erro ao verificar contas: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro na verificação: {e}")
    
    # 6. Testar exclusão de conta inexistente
    print(f"\n🔍 6. Testando exclusão de conta inexistente (ID: 99999)...")
    try:
        response = requests.delete(f"{base_url}/accounts/99999")
        if response.status_code == 404:
            result = response.json()
            print(f"   ✅ Tratamento correto: {result['error']}")
        else:
            print(f"   ❌ Resposta inesperada: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erro na requisição: {e}")
    
    print(f"\n" + "=" * 50)
    print("📊 RESUMO DOS ENDPOINTS DE EXCLUSÃO:")
    print("✅ GET /api/sync/accounts - Lista todas as contas")
    print("✅ DELETE /api/sync/accounts/{id} - Exclui conta específica (apenas slaves)")
    print("🚫 Contas master são protegidas contra exclusão individual")
    print("ℹ️ Use DELETE /api/sync/accounts/clear para remover todas as contas")
    print("=" * 50)

def show_available_endpoints():
    """Mostra os endpoints disponíveis para gerenciamento de contas"""
    
    print("\n🔧 ENDPOINTS DISPONÍVEIS PARA CONTAS:")
    print("=" * 40)
    print("📋 GET /api/sync/accounts")
    print("   └─ Lista todas as contas cadastradas")
    print()
    print("➕ POST /api/sync/accounts") 
    print("   └─ Adiciona nova conta")
    print()
    print("🗑️ DELETE /api/sync/accounts/{id}")
    print("   └─ Remove conta específica (apenas slaves)")
    print()
    print("💥 DELETE /api/sync/accounts/clear")
    print("   └─ Remove TODAS as contas")
    print()
    print("🔍 GET /api/sync/accounts/{id}/test")
    print("   └─ Testa conexão com conta específica")
    print("=" * 40)

if __name__ == '__main__':
    show_available_endpoints()
    
    print("\n🚀 Deseja testar os endpoints? (servidor deve estar rodando)")
    choice = input("Digite 'sim' para testar ou qualquer tecla para sair: ")
    
    if choice.lower() in ['sim', 's', 'yes', 'y']:
        test_delete_account_endpoints()
    else:
        print("👋 Teste cancelado")
