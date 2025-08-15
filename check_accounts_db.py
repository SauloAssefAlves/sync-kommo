#!/usr/bin/env python3
"""
Verificar contas no banco de dados
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.models.kommo_account import KommoAccount
from src.main import app as flask_app

def check_accounts():
    with flask_app.app_context():
        print("🔍 CONTAS NO BANCO:")
        print("=" * 40)
        
        accounts = KommoAccount.query.all()
        
        if not accounts:
            print("❌ Nenhuma conta encontrada no banco!")
            return
            
        for acc in accounts:
            print(f"ID: {acc.id}")
            print(f"Subdomain: {acc.subdomain}")
            print(f"Is Master: {acc.is_master}")
            print(f"Account Role: {acc.account_role}")
            print(f"Sync Group ID: {acc.sync_group_id}")
            print("-" * 40)

if __name__ == '__main__':
    check_accounts()
