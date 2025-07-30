#!/usr/bin/env python3
"""
Script para limpar estágios duplicados em pipelines
Remove estágios com padrões como 'Closed - won', 'Closed - lost', 'INCOMING LEADS'
que foram criados incorretamente antes da correção do bug.
"""

import requests
import time
import json

def clean_duplicate_stages():
    """
    Remove estágios duplicados dos pipelines
    """
    
    # Lista de contas slaves
    slaves = [
        {
            'name': 'testedev',
            'access_token': 'def502007f5983844e7e0c75b6db5e3b7b0dfd57dcfa8c43a0e11ee84f68cc06b3ea6e5ad7ba4f8dc5bd30030c36dd8e71a0f8cd18c4c9de8c05c31e6d1e80bbeb9b1b1e0ef06f2a5ed5f18c5b6b2f8bbdf23e09936ea36b3fd9c48fefd0b38b0a61b2ca0e60b7b33e9e9cd8d4ee9d7d75f8a64b47e8b48df94da8fa18a3e3b3f0a87b8556e39d40bfdc2cfd1e9db87b55fb5ad3b86da0c1346c1ec7eef4d37bf9d3e28f9f6a2e61da7b5fb8a0e42a6e3b3fb7e5d3c4f7a8b1e2d3f4a5b6c7d8e9f0b0c7d8e9a1f2b3c4d5e6f7a8b9c0d1e2f3b4c5d6e7f8a9b0c1d2e3f4b5c6d7e8f9a0b1'
        }
    ]
    
    for slave in slaves:
        print(f"\n🔍 Verificando conta: {slave['name']}")
        
        # Buscar pipelines
        headers = {
            'Authorization': f'Bearer {slave["access_token"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f'https://{slave["name"]}.kommo.com/api/v4/leads/pipelines',
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Erro ao buscar pipelines: {response.status_code}")
            continue
        
        pipelines = response.json().get('_embedded', {}).get('pipelines', [])
        print(f"📋 Encontrados {len(pipelines)} pipelines")
        
        for pipeline in pipelines:
            pipeline_id = pipeline['id']
            pipeline_name = pipeline['name']
            
            print(f"\n🔄 Verificando pipeline: {pipeline_name} (ID: {pipeline_id})")
            
            stages = pipeline.get('_embedded', {}).get('statuses', [])
            
            # Identificar estágios problemáticos
            duplicates_to_remove = []
            
            for stage in stages:
                stage_name = stage['name'].strip()
                stage_id = stage['id']
                
                # Padrões de estágios duplicados/problemáticos
                problematic_patterns = [
                    'Closed - won',
                    'Closed - lost', 
                    'INCOMING LEADS',
                    'CLOSED - WON',
                    'CLOSED - LOST'
                ]
                
                if any(pattern in stage_name for pattern in problematic_patterns):
                    # Verificar se não é um dos IDs padrão do sistema
                    if stage_id not in [1, 142, 143]:
                        duplicates_to_remove.append({
                            'id': stage_id,
                            'name': stage_name
                        })
                        print(f"  🗑️ Marcando para remoção: '{stage_name}' (ID: {stage_id})")
            
            # Remover os duplicados
            if duplicates_to_remove:
                print(f"  🧹 Removendo {len(duplicates_to_remove)} estágios duplicados...")
                
                for duplicate in duplicates_to_remove:
                    try:
                        delete_response = requests.delete(
                            f'https://{slave["name"]}.kommo.com/api/v4/leads/pipelines/{pipeline_id}/statuses/{duplicate["id"]}',
                            headers=headers
                        )
                        
                        if delete_response.status_code in [200, 204]:
                            print(f"    ✅ Removido: '{duplicate['name']}'")
                        else:
                            print(f"    ❌ Erro ao remover '{duplicate['name']}': {delete_response.status_code}")
                            print(f"       Resposta: {delete_response.text}")
                        
                        # Delay para evitar rate limit
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"    ❌ Erro ao remover '{duplicate['name']}': {e}")
            else:
                print(f"  ✅ Nenhum duplicado encontrado no pipeline '{pipeline_name}'")

if __name__ == '__main__':
    print("🧹 Iniciando limpeza de estágios duplicados...")
    clean_duplicate_stages()
    print("\n✅ Limpeza concluída!")
