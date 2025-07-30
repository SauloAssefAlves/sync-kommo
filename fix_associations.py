#!/usr/bin/env python3
"""Script para associar contas existentes ao grupo"""

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup

def fix_associations():
    with app.app_context():
        # Obter o grupo
        group = SyncGroup.query.get(1)  # Grupo "Teste"
        if not group:
            print("Grupo não encontrado")
            return
        
        # Obter a conta mestre (evoresultdev)
        master_account = KommoAccount.query.filter_by(subdomain='evoresultdev').first()
        if master_account:
            master_account.sync_group_id = group.id
            print(f"Associando conta mestre {master_account.subdomain} ao grupo {group.name}")
        
        # Obter a conta escrava (testedev)
        slave_account = KommoAccount.query.filter_by(subdomain='testedev').first()
        if slave_account:
            slave_account.sync_group_id = group.id
            print(f"Associando conta escrava {slave_account.subdomain} ao grupo {group.name}")
        
        # Salvar mudanças
        db.session.commit()
        print("Associações atualizadas com sucesso!")

if __name__ == '__main__':
    fix_associations()
