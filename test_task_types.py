#!/usr/bin/env python3
"""
Teste da sincronização de task types
"""

import sys
import os
sys.path.append('/home/user/sync-kommo')

from src.services.kommo_api import KommoAPIService
from src.models.kommo_account import KommoAccount
from src.app import app

def test_task_types():
    """Testa a obtenção de task types das contas master e slave"""
    with app.app_context():
        # Buscar contas do banco
        master_account = KommoAccount.query.filter_by(subdomain='vox2youmatriz').first()
        slave_account = KommoAccount.query.filter_by(subdomain='testedev').first()
        
        if not master_account:
            print("❌ Conta master 'vox2youmatriz' não encontrada!")
            return
            
        if not slave_account:
            print("❌ Conta slave 'testedev' não encontrada!")
            return
        
        print(f"✅ Master: {master_account.subdomain}")
        print(f"✅ Slave: {slave_account.subdomain}")
        
        # Criar APIs
        master_api = KommoAPIService(master_account.subdomain, master_account.api_token)
        slave_api = KommoAPIService(slave_account.subdomain, slave_account.api_token)
        
        try:
            # Testar task types da master
            print("\n🔍 Obtendo task types da MASTER...")
            master_task_types = master_api.get_task_types()
            print(f"📊 Master tem {len(master_task_types)} task types:")
            for key, task_type in master_task_types.items():
                print(f"   - {task_type['option']} (ID: {task_type['id']}, cor: {task_type['color']})")
            
        except Exception as e:
            print(f"❌ Erro ao obter task types da master: {e}")
            
        try:
            # Testar task types da slave
            print("\n🔍 Obtendo task types da SLAVE...")
            slave_task_types = slave_api.get_task_types()
            print(f"📊 Slave tem {len(slave_task_types)} task types:")
            for key, task_type in slave_task_types.items():
                print(f"   - {task_type['option']} (ID: {task_type['id']}, cor: {task_type['color']})")
                
        except Exception as e:
            print(f"❌ Erro ao obter task types da slave: {e}")

if __name__ == '__main__':
    test_task_types()
