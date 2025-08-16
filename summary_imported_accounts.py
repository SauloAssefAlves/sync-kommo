#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resumo das contas importadas do servidor remoto

Este script exibe um resumo organizado das contas que foram importadas
"""

import sys
import os

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup

def main():
    """Função principal"""
    print("📊 RESUMO DAS CONTAS IMPORTADAS")
    print("=" * 50)
    
    # Inicializar contexto da aplicação
    from src.main import app
    
    with app.app_context():
        try:
            # Dados originais do servidor remoto
            print("🔗 DADOS ORIGINAIS DO SERVIDOR REMOTO:")
            print("""
            {
              "accounts": [
                {
                  "account_role": "master",
                  "created_at": "2025-08-15T20:21:54.239273",
                  "group": null,
                  "id": 1,
                  "is_master": false,
                  "subdomain": "evoresultdev",
                  "sync_group_id": null,
                  "updated_at": "2025-08-15T21:21:50.906478"
                },
                {
                  "account_role": "slave",
                  "created_at": "2025-08-15T20:22:12.819313",
                  "group": {
                    "id": 3,
                    "name": "Teste"
                  },
                  "id": 2,
                  "is_master": false,
                  "subdomain": "testedev",
                  "sync_group_id": 3,
                  "updated_at": "2025-08-15T20:22:12.819316"
                },
                {
                  "account_role": "master",
                  "created_at": "2025-08-15T21:21:50.911645",
                  "group": null,
                  "id": 3,
                  "is_master": true,
                  "subdomain": "test",
                  "sync_group_id": null,
                  "updated_at": "2025-08-15T21:21:50.911649"
                }
              ],
              "success": true,
              "total": 3
            }
            """)
            
            print("\n📁 GRUPOS DE SINCRONIZAÇÃO NO BANCO LOCAL:")
            groups = SyncGroup.query.all()
            for group in groups:
                print(f"   • ID: {group.id} | Nome: '{group.name}' | Descrição: '{group.description}'")
                print(f"     Master: {group.master_account.subdomain if group.master_account else 'Não definida'}")
                print(f"     Slaves: {len(group.slave_accounts)} conta(s)")
            
            print("\n👥 CONTAS NO BANCO LOCAL:")
            accounts = KommoAccount.query.all()
            for account in accounts:
                group_info = f"Grupo: {account.sync_group.name}" if account.sync_group else "Sem grupo"
                role_icon = "👑" if account.account_role == 'master' else "🔗"
                print(f"   {role_icon} {account.subdomain} ({account.account_role}) | {group_info}")
            
            print("\n✅ RESULTADO:")
            print(f"   • {len(groups)} grupo(s) de sincronização importado(s)")
            print(f"   • {len(accounts)} conta(s) importada(s)")
            print(f"   • {KommoAccount.query.filter_by(account_role='master').count()} conta(s) master")
            print(f"   • {KommoAccount.query.filter_by(account_role='slave').count()} conta(s) slave")
            
            print("\n🎯 ESTRUTURA DE SINCRONIZAÇÃO:")
            print("   Grupo 'Teste':")
            print("   ├── 👑 Master: evoresultdev")
            print("   └── 🔗 Slave: testedev")
            print("")
            print("   Contas master independentes:")
            print("   ├── 👑 evoresultdev (também está no grupo)")
            print("   └── 👑 test (sem grupo)")
            
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
