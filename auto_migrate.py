#!/usr/bin/env python3
"""
Script automático de migração
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup
from datetime import datetime

def auto_migrate():
    """Migração automática para grupos"""
    with app.app_context():
        print("🔄 Executando migração automática...")
        
        # Verificar conta mestre
        master_account = KommoAccount.query.filter_by(is_master=True).first()
        if not master_account:
            print("❌ Nenhuma conta mestre encontrada")
            return False
        
        print(f"📋 Conta mestre encontrada: {master_account.subdomain}")
        
        # Criar grupo principal
        main_group = SyncGroup(
            name=f"Grupo Principal - {master_account.subdomain}",
            description=f"Grupo principal migrado automaticamente",
            master_account_id=master_account.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(main_group)
        db.session.flush()  # Para obter o ID
        
        # Atualizar conta mestre
        master_account.sync_group_id = main_group.id
        master_account.account_role = 'master'
        
        # Atualizar contas escravas
        slave_accounts = KommoAccount.query.filter_by(is_master=False).all()
        for slave_account in slave_accounts:
            slave_account.sync_group_id = main_group.id
            slave_account.account_role = 'slave'
        
        db.session.commit()
        
        print(f"✅ Migração concluída!")
        print(f"   - Grupo: {main_group.name} (ID: {main_group.id})")
        print(f"   - Contas migradas: {1 + len(slave_accounts)}")
        
        return True

if __name__ == "__main__":
    auto_migrate()
