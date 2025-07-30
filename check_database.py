#!/usr/bin/env python3
"""Script para verificar o estado do banco de dados"""

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup

def check_database():
    with app.app_context():
        print('=== CONTAS ===')
        accounts = KommoAccount.query.all()
        
        if not accounts:
            print('Nenhuma conta encontrada')
        else:
            for account in accounts:
                group_name = 'Sem grupo'
                if account.sync_group_id:
                    group = SyncGroup.query.get(account.sync_group_id)
                    if group:
                        group_name = group.name
                
                print(f'ID: {account.id}')
                print(f'  Subdomain: {account.subdomain}')
                print(f'  is_master: {account.is_master}')
                print(f'  account_role: {account.account_role}')
                print(f'  sync_group_id: {account.sync_group_id}')
                print(f'  Grupo: {group_name}')
                print()
        
        print('=== GRUPOS ===')
        groups = SyncGroup.query.all()
        
        if not groups:
            print('Nenhum grupo encontrado')
        else:
            for group in groups:
                master_name = 'Sem mestre'
                if group.master_account_id:
                    master = KommoAccount.query.get(group.master_account_id)
                    if master:
                        master_name = master.subdomain
                
                print(f'ID: {group.id}')
                print(f'  Name: {group.name}')
                print(f'  master_account_id: {group.master_account_id}')
                print(f'  Conta mestre: {master_name}')
                print(f'  is_active: {group.is_active}')
                print(f'  Description: {group.description}')
                print()
        
        print('=== ASSOCIAÇÕES ===')
        print('Contas em grupos:')
        for group in groups:
            accounts_in_group = KommoAccount.query.filter_by(sync_group_id=group.id).all()
            print(f'Grupo "{group.name}" (ID: {group.id}):')
            if accounts_in_group:
                for acc in accounts_in_group:
                    print(f'  - {acc.subdomain} ({acc.account_role})')
            else:
                print('  - Nenhuma conta associada')
            print()

if __name__ == '__main__':
    check_database()
