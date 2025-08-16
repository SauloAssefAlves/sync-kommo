#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para visualizar as contas e grupos importados no banco de dados local

Este script exibe:
1. Todos os grupos de sincronização
2. Todas as contas (master e slave)
3. Relacionamentos entre grupos e contas
4. Estatísticas gerais
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup, PipelineMapping, StageMapping

def display_groups():
    """Exibe todos os grupos de sincronização"""
    print("📁 GRUPOS DE SINCRONIZAÇÃO:")
    print("-" * 50)
    
    groups = SyncGroup.query.all()
    
    if not groups:
        print("   ❌ Nenhum grupo encontrado")
        return
    
    for group in groups:
        master_account = group.master_account
        slave_count = len(group.slave_accounts)
        
        print(f"   📁 {group.name} (ID: {group.id})")
        print(f"      📝 Descrição: {group.description or 'Sem descrição'}")
        print(f"      👑 Conta Mestre: {master_account.subdomain if master_account else 'Não definida'}")
        print(f"      🔗 Contas Escravas: {slave_count}")
        print(f"      📅 Criado em: {group.created_at.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"      🔄 Atualizado em: {group.updated_at.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"      ✅ Ativo: {'Sim' if group.is_active else 'Não'}")
        
        if slave_count > 0:
            print("      🔗 Contas escravas:")
            for slave in group.slave_accounts:
                print(f"         • {slave.subdomain}")
        
        print()

def display_accounts():
    """Exibe todas as contas"""
    print("👥 CONTAS KOMMO:")
    print("-" * 50)
    
    accounts = KommoAccount.query.all()
    
    if not accounts:
        print("   ❌ Nenhuma conta encontrada")
        return
    
    master_accounts = []
    slave_accounts = []
    
    for account in accounts:
        if account.account_role == 'master':
            master_accounts.append(account)
        else:
            slave_accounts.append(account)
    
    # Exibir contas master
    print("   👑 CONTAS MASTER:")
    if master_accounts:
        for account in master_accounts:
            group_name = account.sync_group.name if account.sync_group else "Sem grupo"
            token_status = "✅ Válido" if account.token_expires_at > datetime.utcnow() else "❌ Expirado"
            
            print(f"      • {account.subdomain}")
            print(f"        🏷️ ID: {account.id}")
            print(f"        📁 Grupo: {group_name}")
            print(f"        🔑 Token: {token_status}")
            print(f"        📅 Criado: {account.created_at.strftime('%d/%m/%Y %H:%M:%S')}")
            print()
    else:
        print("      ❌ Nenhuma conta master encontrada")
    
    print()
    
    # Exibir contas slave
    print("   🔗 CONTAS SLAVE:")
    if slave_accounts:
        for account in slave_accounts:
            group_name = account.sync_group.name if account.sync_group else "Sem grupo"
            token_status = "✅ Válido" if account.token_expires_at > datetime.utcnow() else "❌ Expirado"
            
            print(f"      • {account.subdomain}")
            print(f"        🏷️ ID: {account.id}")
            print(f"        📁 Grupo: {group_name}")
            print(f"        🔑 Token: {token_status}")
            print(f"        📅 Criado: {account.created_at.strftime('%d/%m/%Y %H:%M:%S')}")
            print()
    else:
        print("      ❌ Nenhuma conta slave encontrada")

def display_mappings():
    """Exibe os mapeamentos existentes"""
    print("🗺️ MAPEAMENTOS:")
    print("-" * 50)
    
    # Mapeamentos de pipelines
    pipeline_mappings = PipelineMapping.query.all()
    print(f"   📊 Mapeamentos de Pipelines: {len(pipeline_mappings)}")
    
    if pipeline_mappings:
        for mapping in pipeline_mappings[:5]:  # Mostrar apenas os primeiros 5
            group_name = mapping.sync_group.name if mapping.sync_group else "Grupo desconhecido"
            slave_name = mapping.slave_account.subdomain if mapping.slave_account else "Conta desconhecida"
            print(f"      • Grupo: {group_name} | Master: {mapping.master_pipeline_id} → Slave: {mapping.slave_pipeline_id} ({slave_name})")
        
        if len(pipeline_mappings) > 5:
            print(f"      ... e mais {len(pipeline_mappings) - 5} mapeamentos")
    
    print()
    
    # Mapeamentos de estágios
    stage_mappings = StageMapping.query.all()
    print(f"   🎭 Mapeamentos de Estágios: {len(stage_mappings)}")
    
    if stage_mappings:
        for mapping in stage_mappings[:5]:  # Mostrar apenas os primeiros 5
            group_name = mapping.sync_group.name if mapping.sync_group else "Grupo desconhecido"
            slave_name = mapping.slave_account.subdomain if mapping.slave_account else "Conta desconhecida"
            print(f"      • Grupo: {group_name} | Master: {mapping.master_stage_id} → Slave: {mapping.slave_stage_id} ({slave_name})")
        
        if len(stage_mappings) > 5:
            print(f"      ... e mais {len(stage_mappings) - 5} mapeamentos")

def display_statistics():
    """Exibe estatísticas gerais"""
    print("📊 ESTATÍSTICAS:")
    print("-" * 50)
    
    total_groups = SyncGroup.query.count()
    total_accounts = KommoAccount.query.count()
    master_accounts = KommoAccount.query.filter_by(account_role='master').count()
    slave_accounts = KommoAccount.query.filter_by(account_role='slave').count()
    active_groups = SyncGroup.query.filter_by(is_active=True).count()
    
    total_pipeline_mappings = PipelineMapping.query.count()
    total_stage_mappings = StageMapping.query.count()
    
    print(f"   📁 Total de grupos: {total_groups}")
    print(f"   ✅ Grupos ativos: {active_groups}")
    print(f"   👥 Total de contas: {total_accounts}")
    print(f"   👑 Contas master: {master_accounts}")
    print(f"   🔗 Contas slave: {slave_accounts}")
    print(f"   📊 Mapeamentos de pipelines: {total_pipeline_mappings}")
    print(f"   🎭 Mapeamentos de estágios: {total_stage_mappings}")
    
    # Verificar tokens expirados
    expired_tokens = KommoAccount.query.filter(KommoAccount.token_expires_at < datetime.utcnow()).count()
    if expired_tokens > 0:
        print(f"   ⚠️ Tokens expirados: {expired_tokens}")

def display_account_relationships():
    """Exibe os relacionamentos entre contas e grupos"""
    print("🔗 RELACIONAMENTOS:")
    print("-" * 50)
    
    groups = SyncGroup.query.all()
    
    for group in groups:
        print(f"   📁 Grupo: {group.name}")
        
        # Conta master do grupo
        if group.master_account:
            print(f"      👑 Master: {group.master_account.subdomain}")
        else:
            print("      ❌ Nenhuma conta master definida")
        
        # Contas slave do grupo
        if group.slave_accounts:
            print(f"      🔗 Slaves ({len(group.slave_accounts)}):")
            for slave in group.slave_accounts:
                print(f"         • {slave.subdomain}")
        else:
            print("      ❌ Nenhuma conta slave")
        
        print()
    
    # Contas sem grupo
    accounts_without_group = KommoAccount.query.filter_by(sync_group_id=None).all()
    if accounts_without_group:
        print("   ❓ Contas sem grupo:")
        for account in accounts_without_group:
            role_icon = "👑" if account.account_role == 'master' else "🔗"
            print(f"      {role_icon} {account.subdomain} ({account.account_role})")

def main():
    """Função principal"""
    print("📋 VISUALIZAÇÃO DO BANCO DE DADOS LOCAL")
    print("=" * 60)
    
    # Inicializar contexto da aplicação
    from src.main import app
    
    with app.app_context():
        try:
            display_statistics()
            print("\n")
            
            display_groups()
            print("\n")
            
            display_accounts()
            print("\n")
            
            display_account_relationships()
            print("\n")
            
            display_mappings()
            
        except Exception as e:
            print(f"❌ Erro ao exibir informações: {e}")
            raise

if __name__ == "__main__":
    main()
