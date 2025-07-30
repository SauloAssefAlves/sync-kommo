#!/usr/bin/env python3
"""
Teste específico para verificar se os required_statuses estão sendo sincronizados corretamente
"""

import requests
import json

# Configuração da API
API_BASE = "http://localhost:5000/api/sync"

def test_required_statuses():
    """Testa se os required_statuses estão sendo extraídos e mapeados corretamente"""
    
    print("🔍 Testando extração de required_statuses...")
    
    # Fazer uma sincronização para ver os logs
    print("\n📊 Executando sincronização para verificar required_statuses...")
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{API_BASE}/trigger", json={}, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Sincronização executada com sucesso!")
            print(f"Resultados: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Erro na sincronização: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro ao executar sincronização: {e}")
    
    print(f"\n✅ Teste concluído! Verifique os logs acima para ver se os required_statuses estão sendo processados.")

if __name__ == "__main__":
    test_required_statuses()
