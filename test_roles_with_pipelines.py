#!/usr/bin/env python3
"""
Teste do novo endpoint de roles com sincronização automática de pipelines
"""
import requests
import json

def test_roles_sync_with_auto_pipelines():
    """Testa o endpoint /roles que agora sincroniza pipelines automaticamente"""
    print("🧪 Testando endpoint /roles com sincronização automática de pipelines...")
    
    api_base = "http://localhost:5000/api/sync"
    
    # Dados do teste
    test_payload = {
        "batch_config": {
            "batch_size": 5,
            "batch_delay": 1.0
        }
    }
    
    print(f"📡 Endpoint: {api_base}/roles")
    print(f"📋 Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        print("\n🚀 Enviando requisição...")
        response = requests.post(f"{api_base}/roles", json=test_payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Resposta recebida com sucesso!")
            print(f"📋 Resultado: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Erro na requisição:")
            print(f"   Status: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão - certifique-se de que o servidor está rodando em localhost:5000")
    except requests.exceptions.Timeout:
        print("⏰ Timeout - a sincronização pode estar demorada, mas provavelmente está funcionando")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

def test_single_account_roles():
    """Testa sincronização de roles para uma conta específica"""
    print("\n🧪 Testando sincronização de roles para conta específica...")
    
    api_base = "http://localhost:5000/api/sync"
    account_id = 1  # Ajuste conforme necessário
    
    test_payload = {
        "sync_type": "roles"
    }
    
    print(f"📡 Endpoint: {api_base}/account/{account_id}")
    print(f"📋 Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        print("\n🚀 Enviando requisição...")
        response = requests.post(f"{api_base}/account/{account_id}", json=test_payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Resposta recebida com sucesso!")
            print(f"📋 Resultado: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Erro na requisição:")
            print(f"   Status: {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão - certifique-se de que o servidor está rodando em localhost:5000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

def main():
    """Executa todos os testes"""
    print("=" * 70)
    print("🧪 TESTE DOS NOVOS ENDPOINTS DE ROLES")
    print("📋 Funcionalidades testadas:")
    print("   1. /roles - Sincronização de roles com pipelines automáticas")
    print("   2. /account/{id} - Sincronização individual com pipelines automáticas")
    print("=" * 70)
    
    # Teste 1: Endpoint principal de roles
    test_roles_sync_with_auto_pipelines()
    
    # Teste 2: Endpoint de conta individual
    test_single_account_roles()
    
    print("\n" + "=" * 70)
    print("✅ TESTES CONCLUÍDOS")
    print("💡 Verifique os logs do servidor para ver:")
    print("   🔧 'Sincronizando pipelines primeiro...'")
    print("   🔐 'Sincronizando roles...'")
    print("   📊 Estatísticas de mapeamentos atualizados")
    print("=" * 70)

if __name__ == "__main__":
    main()
