#!/usr/bin/env python3
"""
Script para verificar contas no banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup

def check_accounts():
    """Verificar todas as contas no banco"""
    with app.app_context():
        # Buscar todas as contas
        accounts = KommoAccount.query.all()
        
        print(f"🔍 Total de contas encontradas: {len(accounts)}")
        print("=" * 50)
        
        for account in accounts:
            print(f"ID: {account.id}")
            print(f"Subdomínio: {account.subdomain}")
            print(f"Role: {account.account_role}")
            print(f"Grupo ID: {account.sync_group_id}")
            print(f"Criado em: {account.created_at}")
            print("-" * 30)
        
        # Verificar duplicatas
        subdomains = [acc.subdomain for acc in accounts]
        duplicates = set([x for x in subdomains if subdomains.count(x) > 1])
        
        if duplicates:
            print(f"⚠️  DUPLICATAS ENCONTRADAS:")
            for dup in duplicates:
                dup_accounts = [acc for acc in accounts if acc.subdomain == dup]
                print(f"  Subdomínio '{dup}' aparece {len(dup_accounts)} vezes:")
                for acc in dup_accounts:
                    print(f"    - ID {acc.id}, Role: {acc.account_role}, Grupo: {acc.sync_group_id}")
        else:
            print("✅ Nenhuma duplicata encontrada")
        
        # Verificar grupos
        groups = SyncGroup.query.all()
        print(f"\n📦 Total de grupos: {len(groups)}")
        for group in groups:
            print(f"Grupo: {group.name} (ID: {group.id})")
            print(f"  Master: {group.master_account.subdomain if group.master_account else 'Nenhuma'}")
            slave_count = KommoAccount.query.filter_by(sync_group_id=group.id, account_role='slave').count()
            print(f"  Escravas: {slave_count}")

if __name__ == "__main__":
    check_accounts()
