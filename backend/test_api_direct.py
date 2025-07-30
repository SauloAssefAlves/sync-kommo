#!/usr/bin/env python3
"""
Teste direto para verificar a estrutura dos dados retornados pela API do Kommo
"""

import requests
import json

def test_kommo_api_structure():
    """Testa diretamente a API do Kommo para ver a estrutura dos dados"""
    
    # Dados da conta mestre (substitua pelos dados reais)
    SUBDOMAIN = "evoresultdev"
    ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImYwNGZhZjNkMGZjOGYyZTRhZmFkM2Y3ZGUwMzg5NDM0ZTg3MzQ1NGE5NjMzODBlNzZiZGFmODhlNWFjOTI5YTFmOWQwN2MzNThhYWQxNTJmIn0.eyJhdWQiOiJkZTcyMjY1NS1iYWM4LTQ3M2ItYTgzYy0yNzMwOTdmZGRhZGMiLCJqdGkiOiJmMDRmYWYzZDBmYzhmMmU0YWZhZDNmN2RlMDM4OTQzNGU4NzM0NTRhOTYzMzgwZTc2YmRhZjg4ZTVhYzkyOWExZjlkMDdjMzU4YWFkMTUyZiIsImlhdCI6MTc1MzEzNzkyMiwibmJmIjoxNzUzMTM3OTIyLCJleHAiOjE3NTMyMjQzMjIsInN1YiI6IjEwMjgxNTk5IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyMDg0NDkxLCJiYXNlX2RvbWFpbiI6ImtvbW1vLmNvbSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJwdXNoX25vdGlmaWNhdGlvbnMiLCJmaWxlcyIsImNybSIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiM2NkOWJhODctZWI3OS00NjVlLWEwNWQtNWU2MjgwYWNlZTk5IiwiYXBpX2RvbWFpbiI6ImFwaS1jLmtvbW1vLmNvbSJ9.GnJqd6t9J97DFe4gFjXeu455diizBJ14qUqjLwbUOFV86f5lLEFdXNKw6NvL8pBD5S5IopA7jw3Flvyh3ThYYgd4xHMPU7zE61LlVtj1abirAGt3TKHTka02bTidDnLcUiC-7wN1Ccil88Otyq4eW2gI4WujxOzmYIg0Fu7FZh2IMyX_BB6nY8_0SkYPYq-qlI8OUfw9kKA2GgMYG_qQ6J-boQT6v4eRUeWacwROLeQcAQHxRd4dXYnMqZSrRU-V78gIjmQ5q69tDxcILSBZvB8bbHTYITqC5W5Il75eHz7ZbPKZWr9Qc76E0p-txMWIVjOnwPGTLGZZT4HxM3XVGQ"
    
    print(f"🔍 Testando API da conta mestre: {SUBDOMAIN}")
    
    # Headers para API
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    base_url = f"https://{SUBDOMAIN}.kommo.com/api/v4"
    
    # 1. Testar endpoint de custom fields
    print("\n📋 Testando endpoint de custom fields...")
    for entity_type in ['leads']:  # Apenas leads para não flood
        print(f"\n--- {entity_type.upper()} ---")
        
        # Testar sem parâmetros
        url = f"{base_url}/{entity_type}/custom_fields"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            fields = data.get('_embedded', {}).get('custom_fields', [])
            print(f"✅ {len(fields)} campos obtidos")
            
            # Verificar se algum campo tem required_statuses
            for field in fields[:5]:  # Apenas os primeiros 5 para não flood
                print(f"  Campo: {field.get('name', 'N/A')}")
                print(f"    ID: {field.get('id')}")
                print(f"    Type: {field.get('type')}")
                print(f"    is_required: {field.get('is_required', False)}")
                print(f"    required_statuses: {field.get('required_statuses', 'N/A')}")
                print(f"    Chaves disponíveis: {list(field.keys())}")
                print()
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")

if __name__ == "__main__":
    test_kommo_api_structure()
