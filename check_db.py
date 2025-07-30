#!/usr/bin/env python3
"""
Script simples para verificar o banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup

def check_database():
    """Verifica o estado atual do banco de dados"""
    with app.app_context():
        print("🔍 Verificando banco de dados...")
        
        # Verificar contas
        accounts_count = KommoAccount.query.count()
        print(f"📊 Contas encontradas: {accounts_count}")
        
        if accounts_count > 0:
            master_accounts = KommoAccount.query.filter_by(is_master=True).count()
            slave_accounts = KommoAccount.query.filter_by(is_master=False).count()
            print(f"   - Contas mestres: {master_accounts}")
            print(f"   - Contas escravas: {slave_accounts}")
            
            # Mostrar algumas contas
            accounts = KommoAccount.query.limit(5).all()
            print("\n📋 Primeiras contas:")
            for account in accounts:
                print(f"   - {account.subdomain} (Master: {account.is_master})")
        
        # Verificar grupos
        groups_count = SyncGroup.query.count()
        print(f"\n📊 Grupos encontrados: {groups_count}")
        
        if groups_count > 0:
            groups = SyncGroup.query.all()
            print("\n📋 Grupos:")
            for group in groups:
                print(f"   - {group.name} (ID: {group.id})")

if __name__ == "__main__":
    check_database()
