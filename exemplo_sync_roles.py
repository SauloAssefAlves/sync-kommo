"""
Exemplo de uso do endpoint de sincronização de roles

POST /sync/roles

Este endpoint sincroniza somente as roles (funções/permissões) entre as contas Kommo.
"""

import requests
import json

def test_sync_roles():
    """Exemplo de uso do endpoint /sync/roles"""
    
    url = "http://localhost:5000/sync/roles"
    
    # Exemplo 1: Sincronizar todas as contas (usar master padrão e todos os slaves)
    payload1 = {
        "batch_config": {
            "batch_size": 5,        # Processar 5 roles por vez
            "batch_delay": 1.0      # Aguardar 1 segundo entre lotes
        }
    }
    
    # Exemplo 2: Sincronizar contas específicas
    payload2 = {
        "master_account_id": 1,     # ID da conta master
        "slave_account_ids": [2, 3, 4],  # IDs das contas slave
        "batch_config": {
            "batch_size": 3,
            "batch_delay": 2.0
        }
    }
    
    # Exemplo 3: Sincronização mais rápida (lotes maiores, menos delay)
    payload3 = {
        "batch_config": {
            "batch_size": 10,       # Lotes maiores
            "batch_delay": 0.5      # Menos delay
        }
    }
    
    print("🔐 Exemplo de sincronização de roles:")
    print("POST", url)
    print("Payload:", json.dumps(payload1, indent=2))
    
    # Em um código real, você faria:
    # response = requests.post(url, json=payload1)
    # print("Response:", response.json())

def check_sync_status():
    """Verificar status da sincronização em andamento"""
    
    url = "http://localhost:5000/sync/status"
    
    print("📊 Verificar status da sincronização:")
    print("GET", url)
    
    # Em um código real:
    # response = requests.get(url)
    # status = response.json()
    # print("Status:", status)

def stop_sync():
    """Parar sincronização em andamento"""
    
    url = "http://localhost:5000/sync/stop"
    
    print("🛑 Parar sincronização:")
    print("POST", url)
    
    # Em um código real:
    # response = requests.post(url)
    # print("Response:", response.json())

if __name__ == "__main__":
    test_sync_roles()
    print("\n" + "="*50 + "\n")
    check_sync_status()
    print("\n" + "="*50 + "\n")
    stop_sync()
