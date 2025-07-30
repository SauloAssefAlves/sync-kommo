#!/usr/bin/env python3
"""
Script simples para verificar status 142 e 143 no pipeline TESTE 3
"""

import requests
import os

def get_pipelines(subdomain, access_token):
    """Busca pipelines de uma conta"""
    url = f"https://{subdomain}.kommo.com/api/v4/leads/pipelines"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao buscar pipelines: {response.status_code}")
        return None

def check_teste3_status():
    # Tokens obtidos do banco ou configuração
    # Você precisa substituir por seus tokens reais
    master_token = "YOUR_MASTER_TOKEN"  # Token da conta evoresultdev
    slave_token = "YOUR_SLAVE_TOKEN"    # Token da conta testedev
    
    print('🔍 VERIFICANDO PIPELINE TESTE 3 - STATUS 142 e 143')
    print('=' * 60)
    
    # MASTER
    print('\n🏢 MASTER (evoresultdev):')
    master_pipelines = get_pipelines("evoresultdev", master_token)
    
    if master_pipelines:
        for p in master_pipelines['_embedded']['pipelines']:
            if p['name'] == 'TESTE 3':
                print(f'Pipeline: {p["name"]} (ID: {p["id"]})')
                print('Status:')
                for status in p['_embedded']['statuses']:
                    if status['id'] in [142, 143]:
                        print(f'  ⚠️  ID {status["id"]} = "{status["name"]}"')
                    else:
                        print(f'  - {status["name"]} (ID: {status["id"]})')
                break
    
    # SLAVE
    print('\n🏢 SLAVE (testedev):')
    slave_pipelines = get_pipelines("testedev", slave_token)
    
    if slave_pipelines:
        for p in slave_pipelines['_embedded']['pipelines']:
            if p['name'] == 'TESTE 3':
                print(f'Pipeline: {p["name"]} (ID: {p["id"]})')
                print('Status:')
                for status in p['_embedded']['statuses']:
                    if status['id'] in [142, 143]:
                        print(f'  ⚠️  ID {status["id"]} = "{status["name"]}"')
                    else:
                        print(f'  - {status["name"]} (ID: {status["id"]})')
                break

if __name__ == "__main__":
    print("⚠️  ATENÇÃO: Este script precisa dos tokens de acesso reais.")
    print("Edite o arquivo e adicione os tokens antes de executar.")
    # check_teste3_status()  # Descomente após adicionar os tokens
