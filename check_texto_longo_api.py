#!/usr/bin/env python3
"""
Script para verificar campos com required_statuses diretamente da API
"""

import requests
import sys
import os
import sqlite3
import json

# Buscar tokens do banco
def get_master_account():
    """Busca conta master do banco"""
    db_path = "src/database/app.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT subdomain, refresh_token FROM kommo_accounts WHERE is_master = 1 LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {'subdomain': row['subdomain'], 'refresh_token': row['refresh_token']}
    return None

def get_access_token(subdomain, refresh_token):
    """Obtém access token usando refresh token"""
    url = f"https://{subdomain}.amocrm.ru/oauth2/access_token"
    
    data = {
        'client_id': 'your_client_id',  # Seria necessário o real
        'client_secret': 'your_client_secret',  # Seria necessário o real
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'redirect_uri': 'your_redirect_uri'
    }
    
    # Como não temos as credenciais OAuth, vamos simular
    print(f"⚠️ Simulando busca de access token para {subdomain}")
    return "fake_access_token"

def check_custom_fields_api():
    """Verifica campos customizados diretamente na API"""
    print("🔍 VERIFICANDO REQUIRED_STATUSES NA API")
    print("=" * 60)
    
    # Buscar conta master
    master = get_master_account()
    if not master:
        print("❌ Conta master não encontrada no banco")
        return
    
    print(f"✅ Conta master: {master['subdomain']}")
    
    # Como não podemos fazer a requisição real sem as credenciais OAuth,
    # vamos simular o que deveria acontecer:
    
    print(f"\n📡 SIMULANDO REQUISIÇÃO:")
    print(f"GET https://{master['subdomain']}.amocrm.ru/api/v4/leads/custom_fields?with=required_statuses,enums")
    
    print(f"\n🎯 O QUE DEVERIA RETORNAR PARA 'texto longo':")
    simulated_response = {
        "id": 123456,
        "name": "texto longo",
        "type": "textarea",
        "required_statuses": [
            {
                "pipeline_id": 11670079,
                "status_id": 89684599
            }
        ],
        "settings": {},
        "group_id": None
    }
    
    print(json.dumps(simulated_response, indent=2, ensure_ascii=False))
    
    print(f"\n💾 ONDE ISSO É PROCESSADO NO CÓDIGO:")
    print(f"1. src/services/kommo_api.py -> get_custom_fields() linha ~119")
    print(f"   - Faz GET /leads/custom_fields?with=required_statuses,enums")
    print(f"   - Retorna lista de campos com required_statuses incluído")
    
    print(f"\n2. src/services/kommo_api.py -> sync_custom_fields_to_slave() linha ~1365")
    print(f"   - Para cada campo, mapeia required_statuses usando stage_mappings")
    print(f"   - Converte master_status_id → slave_status_id")
    
    print(f"\n🔍 POSSÍVEIS PROBLEMAS:")
    print(f"1. ❓ Campo 'texto longo' realmente tem required_statuses na API?")
    print(f"2. ❓ Required_statuses está sendo perdido durante processamento?")
    print(f"3. ❓ Mapeamento falha e remove required_statuses?")
    print(f"4. ❓ Campo é atualizado sem required_statuses na slave?")

def check_actual_database_mappings():
    """Verifica mapeamentos reais no banco"""
    print(f"\n📊 VERIFICANDO MAPEAMENTOS NO BANCO:")
    
    db_path = "src/database/app.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Pipeline mapping
    cursor.execute("SELECT master_pipeline_id, slave_pipeline_id FROM pipeline_mappings WHERE master_pipeline_id = 11670079")
    pipeline_row = cursor.fetchone()
    
    if pipeline_row:
        print(f"✅ Pipeline mapeado: {pipeline_row['master_pipeline_id']} → {pipeline_row['slave_pipeline_id']}")
    else:
        print(f"❌ Pipeline 11670079 não mapeado!")
        return
    
    # Stage mapping  
    cursor.execute("SELECT master_stage_id, slave_stage_id FROM stage_mappings WHERE master_stage_id = 89684599")
    stage_row = cursor.fetchone()
    
    if stage_row:
        print(f"✅ Stage mapeado: {stage_row['master_stage_id']} → {stage_row['slave_stage_id']}")
    else:
        print(f"❌ Stage 89684599 não mapeado!")
        return
    
    conn.close()
    
    # Simular resultado final
    print(f"\n📤 REQUIRED_STATUS MAPEADO DEVERIA SER:")
    result = {
        "status_id": stage_row['slave_stage_id'],
        "pipeline_id": pipeline_row['slave_pipeline_id']
    }
    print(json.dumps(result, indent=2))

def check_logs_for_texto_longo():
    """Procura por logs relacionados ao campo texto longo"""
    print(f"\n📝 PROCURANDO LOGS DO CAMPO 'texto longo':")
    
    import glob
    
    # Procurar arquivos de log
    log_patterns = ['*.log', 'logs/*.log', 'src/logs/*.log']
    found_logs = False
    
    for pattern in log_patterns:
        files = glob.glob(pattern)
        if files:
            found_logs = True
            print(f"📁 Encontrados logs: {files}")
            
            for file in files[:3]:  # Limitar a 3 arquivos
                print(f"\n🔍 Verificando {file}:")
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    # Procurar por 'texto longo'
                    relevant_lines = [line.strip() for line in lines if 'texto longo' in line.lower()]
                    
                    if relevant_lines:
                        print(f"✅ Encontradas {len(relevant_lines)} referências:")
                        for line in relevant_lines[-5:]:  # Últimas 5
                            print(f"   {line}")
                    else:
                        print(f"   ❌ Nenhuma referência encontrada")
                        
                except Exception as e:
                    print(f"   ⚠️ Erro ao ler arquivo: {e}")
    
    if not found_logs:
        print(f"❌ Nenhum arquivo de log encontrado")
        print(f"💡 Sugestão: Executar uma sincronização para gerar logs")

if __name__ == "__main__":
    print("🔎 INVESTIGAÇÃO: Onde estão os required_statuses do 'texto longo'")
    print("=" * 70)
    
    check_custom_fields_api()
    check_actual_database_mappings()
    check_logs_for_texto_longo()
    
    print(f"\n" + "=" * 70)
    print(f"🎯 CONCLUSÃO:")
    print(f"Required_statuses NÃO estão no banco - vêm da API Kommo!")
    print(f"Para debugar: precisamos ver os logs da sincronização real.")
    print(f"=" * 70)
