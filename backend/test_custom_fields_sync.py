#!/usr/bin/env python3
"""
Script para testar sincronização de campos personalizados e reproduzir o erro de mapping
"""

import requests
import json
import time

def test_custom_fields_sync():
    """Testa sincronização de campos personalizados"""
    
    API_BASE = "http://localhost:5000/api/sync"
    
    print("🧪 Testando sincronização de campos personalizados...")
    
    # Payload para sincronização
    payload = {
        "sync_type": "custom_fields",
        "batch_config": {
            "batch_size": 10,
            "batch_delay": 1,
            "max_concurrent": 3
        }
    }
    
    try:
        print(f"📡 Fazendo chamada para: {API_BASE}/groups/1/trigger")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{API_BASE}/groups/1/trigger",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Sincronização iniciada com sucesso!")
            print(f"📄 Resposta: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # Aguardar um pouco e verificar status
            print("\n⏳ Aguardando conclusão...")
            time.sleep(15)
            
            # Verificar status
            status_response = requests.get(f"{API_BASE}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"📊 Status final: {json.dumps(status_data, indent=2, ensure_ascii=False)}")
            
        else:
            print(f"❌ Erro na sincronização: {response.status_code}")
            print(f"📄 Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro ao executar sincronização: {e}")

if __name__ == "__main__":
    test_custom_fields_sync()
