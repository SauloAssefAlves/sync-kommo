#!/usr/bin/env python3
"""
Script para debuggar erro is_active
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.models.kommo_account import KommoAccount, SyncGroup
from src.database import db

print("🔍 Verificando modelos do banco...")

try:
    # Testar consulta que está causando erro
    print("1. Testando query KommoAccount.query.filter_by(account_role='master')")
    master = KommoAccount.query.filter_by(account_role='master').first()
    print(f"   ✅ Master encontrada: {master}")
    
    print("2. Testando query KommoAccount.query.filter_by(account_role='slave')")
    slaves = KommoAccount.query.filter_by(account_role='slave').all()
    print(f"   ✅ Slaves encontradas: {len(slaves)}")
    
    print("3. Testando query SyncGroup.query.filter_by(is_active=True)")
    groups = SyncGroup.query.filter_by(is_active=True).all()
    print(f"   ✅ Grupos ativos: {len(groups)}")
    
    print("4. Testando query KommoAccount.query.all()")
    all_accounts = KommoAccount.query.all()
    print(f"   ✅ Total de contas: {len(all_accounts)}")
    
    # Verificar campos das contas
    if all_accounts:
        account = all_accounts[0]
        print(f"5. Campos da primeira conta: {account.__dict__.keys()}")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
