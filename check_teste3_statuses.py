#!/usr/bin/env python3
"""
Script para verificar os status 142 e 143 no pipeline TESTE 3
nas contas master e slave
"""

import sys
import os
sys.path.append('src')

# Configurar variáveis de ambiente se necessário
if not os.getenv('FLASK_APP'):
    os.environ['FLASK_APP'] = 'main.py'

from main import app
from models.kommo_account import KommoAccount
from services.kommo_api import KommoSyncService

def check_teste3_statuses():
    print('🔍 VERIFICANDO PIPELINE TESTE 3 - STATUS 142 e 143')
    print('=' * 60)
    
    with app.app_context():
        # Obter contas
        master_account = KommoAccount.query.filter_by(is_master=True).first()
        slave_account = KommoAccount.query.filter_by(is_master=False).first()
        
        if not master_account:
            print("❌ Conta master não encontrada")
            return
        if not slave_account:
            print("❌ Conta slave não encontrada")
            return
        
        # Verificar MASTER
        print(f'\n🏢 MASTER ({master_account.subdomain}):')
        sync_service = KommoSyncService(master_account)
        pipelines = sync_service.get_pipelines()
        
        for p in pipelines['_embedded']['pipelines']:
            if p['name'] == 'TESTE 3':
                print(f'Pipeline: {p["name"]} (ID: {p["id"]})')
                print('Status:')
                for status in p['_embedded']['statuses']:
                    if status['id'] in [142, 143]:
                        print(f'  ⚠️  ID {status["id"]} = "{status["name"]}"')
                    else:
                        print(f'  - {status["name"]} (ID: {status["id"]})')
                break
        
        # Verificar SLAVE
        print(f'\n🏢 SLAVE ({slave_account.subdomain}):')
        sync_service = KommoSyncService(slave_account)
        pipelines = sync_service.get_pipelines()
        
        for p in pipelines['_embedded']['pipelines']:
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
    check_teste3_statuses()
