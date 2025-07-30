#!/usr/bin/env python3
"""
Teste direto para verificar a estrutura dos dados retornados pela API do Kommo
"""

import requests
import json

def test_kommo_api_structure():
    """Testa diretamente a API do Kommo para ver a estrutura dos dados"""
    
    # Dados da conta mestre (substitua pelos dados reais)
    print(f"🔍 Testando API da conta mestre: {SUBDOMAIN}")
    
    # Headers para API
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    base_url = f"https://{SUBDOMAIN}.kommo.com/api/v4"
    
    # 1. Testar endpoint de custom fields com diferentes parâmetros
    print("\n📋 Testando endpoint de custom fields...")
    for entity_type in ['leads', 'contacts', 'companies']:
        print(f"\n--- {entity_type.upper()} ---")
        
        # Testar sem parâmetros
        url = f"{base_url}/{entity_type}/custom_fields"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            fields = data.get('_embedded', {}).get('custom_fields', [])
            print(f"✅ {len(fields)} campos obtidos")
            
            # Verificar se algum campo tem required_statuses
            for field in fields[:3]:  # Apenas os primeiros 3 para não flood
                print(f"  Campo: {field.get('name', 'N/A')}")
                print(f"    ID: {field.get('id')}")
                print(f"    Type: {field.get('type')}")
                print(f"    is_required: {field.get('is_required', False)}")
                print(f"    required_statuses: {field.get('required_statuses', 'N/A')}")
                print(f"    Chaves disponíveis: {list(field.keys())}")
                print()
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
        
        # 2. Testar endpoint de pipelines
        print("\n📊 Testando endpoint de pipelines...")
        url = f"{base_url}/leads/pipelines"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            pipelines = data.get('_embedded', {}).get('pipelines', [])
            print(f"✅ {len(pipelines)} pipelines obtidos")
            
            for pipeline in pipelines[:2]:  # Apenas os primeiros 2
                print(f"  Pipeline: {pipeline.get('name', 'N/A')} (ID: {pipeline.get('id')})")
                
                # Testar estágios do pipeline
                pipeline_id = pipeline.get('id')
                stages_url = f"{base_url}/leads/pipelines/{pipeline_id}/statuses"
                stages_response = requests.get(stages_url, headers=headers)
                
                if stages_response.status_code == 200:
                    stages_data = stages_response.json()
                    stages = stages_data.get('_embedded', {}).get('statuses', [])
                    print(f"    ✅ {len(stages)} estágios obtidos")
                    
                    for stage in stages[:2]:  # Apenas os primeiros 2
                        print(f"      Estágio: {stage.get('name', 'N/A')} (ID: {stage.get('id')})")
                        print(f"        required_fields: {stage.get('required_fields', 'N/A')}")
                        print(f"        Chaves disponíveis: {list(stage.keys())}")
                else:
                    print(f"    ❌ Erro nos estágios {stages_response.status_code}: {stages_response.text}")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")

if __name__ == "__main__":
    test_kommo_api_structure()
