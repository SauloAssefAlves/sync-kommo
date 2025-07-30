#!/usr/bin/env python3
"""
Script para limpar grupos duplicados e organizar dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup

def clean_duplicate_groups():
    """Limpar grupos duplicados"""
    with app.app_context():
        print("🧹 Limpando grupos duplicados...")
        
        # Buscar todos os grupos
        groups = SyncGroup.query.all()
        print(f"Total de grupos encontrados: {len(groups)}")
        
        # Agrupar por master_account_id
        master_groups = {}
        for group in groups:
            master_id = group.master_account_id
            if master_id not in master_groups:
                master_groups[master_id] = []
            master_groups[master_id].append(group)
        
        # Encontrar duplicatas
        duplicates_found = False
        for master_id, group_list in master_groups.items():
            if len(group_list) > 1:
                duplicates_found = True
                master_account = KommoAccount.query.get(master_id)
                print(f"\n⚠️  Conta master '{master_account.subdomain}' tem {len(group_list)} grupos:")
                
                # Manter o grupo com mais contas escravas ou o mais antigo
                best_group = None
                best_score = -1
                
                for group in group_list:
                    slave_count = KommoAccount.query.filter_by(sync_group_id=group.id, account_role='slave').count()
                    score = slave_count * 100 + (1 if group.created_at else 0)
                    
                    print(f"  - Grupo '{group.name}' (ID: {group.id}) - {slave_count} escravas - Score: {score}")
                    
                    if score > best_score:
                        best_score = score
                        best_group = group
                
                print(f"  ✅ Mantendo: '{best_group.name}' (ID: {best_group.id})")
                
                # Remover os outros grupos
                for group in group_list:
                    if group.id != best_group.id:
                        print(f"  🗑️  Removendo: '{group.name}' (ID: {group.id})")
                        
                        # Migrar contas escravas se houver
                        slaves = KommoAccount.query.filter_by(sync_group_id=group.id, account_role='slave').all()
                        for slave in slaves:
                            print(f"    📦 Migrando conta escrava '{slave.subdomain}' para o grupo principal")
                            slave.sync_group_id = best_group.id
                        
                        # Remover o grupo
                        db.session.delete(group)
        
        if duplicates_found:
            print("\n💾 Salvando alterações...")
            db.session.commit()
            print("✅ Limpeza concluída!")
        else:
            print("✅ Nenhuma duplicata encontrada!")
        
        # Mostrar estado final
        print("\n📊 Estado final:")
        final_groups = SyncGroup.query.all()
        for group in final_groups:
            slave_count = KommoAccount.query.filter_by(sync_group_id=group.id, account_role='slave').count()
            print(f"  - {group.name}: {group.master_account.subdomain} + {slave_count} escravas")

if __name__ == "__main__":
    clean_duplicate_groups()
