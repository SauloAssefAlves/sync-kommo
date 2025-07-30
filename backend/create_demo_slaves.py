#!/usr/bin/env python3
"""
Script para criar contas escravas de demonstração
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup
from datetime import datetime, timedelta
import random

def create_demo_slave_accounts():
    """Criar contas escravas de demonstração"""
    with app.app_context():
        # Buscar o primeiro grupo
        group = SyncGroup.query.first()
        if not group:
            print("❌ Nenhum grupo encontrado")
            return
        
        print(f"📦 Adicionando contas escravas ao grupo: {group.name}")
        
        # Lista de subdomínios para demonstração
        demo_subdomains = [
            "empresa-sp", "empresa-rj", "empresa-mg", "empresa-pr", 
            "filial-norte", "filial-sul", "escritorio-centro", "sucursal-oeste",
            "regional-nordeste", "matriz-sudeste", "unidade-campinas", "polo-santos"
        ]
        
        created_count = 0
        for i, subdomain in enumerate(demo_subdomains[:8]):  # Criar 8 contas para testar "ver mais"
            # Verificar se já existe
            existing = KommoAccount.query.filter_by(subdomain=subdomain).first()
            if existing:
                print(f"⚠️  Conta {subdomain} já existe, pulando...")
                continue
            
            # Criar nova conta escrava
            slave_account = KommoAccount(
                subdomain=subdomain,
                access_token=f"demo_access_token_{i}",
                refresh_token=f"demo_refresh_token_{i}",
                token_expires_at=datetime.utcnow() + timedelta(hours=1),
                sync_group_id=group.id,
                account_role='slave'
            )
            
            db.session.add(slave_account)
            created_count += 1
            print(f"✅ Criada conta escrava: {subdomain}")
        
        if created_count > 0:
            db.session.commit()
            print(f"\n💾 {created_count} contas escravas criadas com sucesso!")
        else:
            print("\n📋 Nenhuma conta nova foi criada")
        
        # Mostrar estado final
        total_slaves = KommoAccount.query.filter_by(sync_group_id=group.id, account_role='slave').count()
        print(f"📊 Total de contas escravas no grupo: {total_slaves}")

if __name__ == "__main__":
    create_demo_slave_accounts()
