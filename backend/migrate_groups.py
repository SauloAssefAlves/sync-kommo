#!/usr/bin/env python3
"""
Script de migração para o sistema de grupos
Migra dados existentes para a nova estrutura de grupos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup
from datetime import datetime

def migrate_to_groups():
    """Migra contas existentes para o sistema de grupos"""
    
    print("🔄 Iniciando migração para sistema de grupos...")
    
    try:
        # 1. Verificar se já existem grupos
        existing_groups = SyncGroup.query.count()
        if existing_groups > 0:
            print(f"⚠️  Já existem {existing_groups} grupos no sistema.")
            response = input("Deseja continuar? (s/N): ")
            if response.lower() != 's':
                print("Migração cancelada.")
                return False
        
        # 2. Buscar conta mestre existente
        master_account = KommoAccount.query.filter_by(is_master=True).first()
        if not master_account:
            print("❌ Nenhuma conta mestre encontrada. Criando grupo padrão sem conta mestre...")
            
            # Criar grupo padrão sem conta mestre
            default_group = SyncGroup(
                name="Grupo Padrão",
                description="Grupo criado durante migração automática",
                master_account_id=None,
                created_at=datetime.utcnow()
            )
            db.session.add(default_group)
            db.session.commit()
            
            print(f"✅ Grupo padrão criado com ID: {default_group.id}")
            return True
        
        # 3. Criar grupo principal baseado na conta mestre
        print(f"📋 Encontrada conta mestre: {master_account.subdomain}")
        
        main_group = SyncGroup(
            name=f"Grupo Principal - {master_account.subdomain}",
            description=f"Grupo principal migrado automaticamente para a conta mestre {master_account.subdomain}",
            master_account_id=master_account.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(main_group)
        db.session.commit()
        
        print(f"✅ Grupo principal criado com ID: {main_group.id}")
        
        # 4. Atualizar conta mestre
        master_account.sync_group_id = main_group.id
        master_account.account_role = 'master'
        
        # 5. Buscar e atualizar contas escravas
        slave_accounts = KommoAccount.query.filter_by(is_master=False).all()
        print(f"📋 Encontradas {len(slave_accounts)} contas escravas para migrar...")
        
        for slave_account in slave_accounts:
            slave_account.sync_group_id = main_group.id
            slave_account.account_role = 'slave'
            print(f"   ✅ Migrada conta escrava: {slave_account.subdomain}")
        
        # 6. Migrar logs de sincronização
        from src.models.kommo_account import SyncLog
        sync_logs = SyncLog.query.filter_by(sync_group_id=None).all()
        print(f"📋 Encontrados {len(sync_logs)} logs de sincronização para migrar...")
        
        for sync_log in sync_logs:
            sync_log.sync_group_id = main_group.id
        
        # 7. Migrar mapeamentos se existirem
        from src.models.kommo_account import PipelineMapping, StageMapping, CustomFieldMapping
        
        # Pipelines
        pipeline_mappings = PipelineMapping.query.filter_by(sync_group_id=None).all()
        for mapping in pipeline_mappings:
            mapping.sync_group_id = main_group.id
        print(f"   ✅ Migrados {len(pipeline_mappings)} mapeamentos de pipeline")
        
        # Stages
        stage_mappings = StageMapping.query.filter_by(sync_group_id=None).all()
        for mapping in stage_mappings:
            mapping.sync_group_id = main_group.id
        print(f"   ✅ Migrados {len(stage_mappings)} mapeamentos de estágio")
        
        # Custom Fields
        field_mappings = CustomFieldMapping.query.filter_by(sync_group_id=None).all()
        for mapping in field_mappings:
            mapping.sync_group_id = main_group.id
        print(f"   ✅ Migrados {len(field_mappings)} mapeamentos de campo personalizado")
        
        # 8. Salvar todas as mudanças
        db.session.commit()
        
        print(f"\n✅ Migração concluída com sucesso!")
        print(f"   - Grupo criado: {main_group.name} (ID: {main_group.id})")
        print(f"   - Conta mestre: {master_account.subdomain}")
        print(f"   - Contas escravas migradas: {len(slave_accounts)}")
        print(f"   - Logs migrados: {len(sync_logs)}")
        print(f"   - Mapeamentos migrados: {len(pipeline_mappings) + len(stage_mappings) + len(field_mappings)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        db.session.rollback()
        return False

def validate_migration():
    """Valida se a migração foi bem-sucedida"""
    
    print("\n🔍 Validando migração...")
    
    try:
        # Verificar grupos
        groups = SyncGroup.query.all()
        print(f"✅ Grupos encontrados: {len(groups)}")
        
        for group in groups:
            print(f"   - {group.name} (ID: {group.id})")
            print(f"     Conta mestre: {group.master_account.subdomain if group.master_account else 'Nenhuma'}")
            
            # Contar contas escravas
            slave_count = KommoAccount.query.filter_by(sync_group_id=group.id, account_role='slave').count()
            print(f"     Contas escravas: {slave_count}")
            
            # Contar logs
            from src.models.kommo_account import SyncLog
            log_count = SyncLog.query.filter_by(sync_group_id=group.id).count()
            print(f"     Logs associados: {log_count}")
        
        # Verificar contas sem grupo
        orphan_accounts = KommoAccount.query.filter_by(sync_group_id=None).count()
        if orphan_accounts > 0:
            print(f"⚠️  Contas órfãs (sem grupo): {orphan_accounts}")
        else:
            print("✅ Todas as contas estão associadas a grupos")
        
        # Verificar logs sem grupo
        from src.models.kommo_account import SyncLog
        orphan_logs = SyncLog.query.filter_by(sync_group_id=None).count()
        if orphan_logs > 0:
            print(f"⚠️  Logs órfãos (sem grupo): {orphan_logs}")
        else:
            print("✅ Todos os logs estão associados a grupos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante validação: {e}")
        return False

def create_sample_groups():
    """Cria grupos de exemplo para demonstração"""
    
    print("\n🎯 Criando grupos de exemplo...")
    
    try:
        # Exemplo 1: Grupo E-commerce
        ecommerce_group = SyncGroup(
            name="E-commerce Principal",
            description="Grupo para sincronização de contas de e-commerce",
            master_account_id=None,  # Será definido depois
            created_at=datetime.utcnow()
        )
        
        # Exemplo 2: Grupo Imobiliário  
        real_estate_group = SyncGroup(
            name="Imobiliário",
            description="Grupo para sincronização de contas imobiliárias",
            master_account_id=None,
            created_at=datetime.utcnow()
        )
        
        # Exemplo 3: Grupo Consultoria
        consulting_group = SyncGroup(
            name="Consultoria",
            description="Grupo para sincronização de contas de consultoria",
            master_account_id=None,
            created_at=datetime.utcnow()
        )
        
        db.session.add_all([ecommerce_group, real_estate_group, consulting_group])
        db.session.commit()
        
        print(f"✅ Grupos de exemplo criados:")
        print(f"   - {ecommerce_group.name} (ID: {ecommerce_group.id})")
        print(f"   - {real_estate_group.name} (ID: {real_estate_group.id})")
        print(f"   - {consulting_group.name} (ID: {consulting_group.id})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar grupos de exemplo: {e}")
        db.session.rollback()
        return False

def main():
    """Função principal do script de migração"""
    
    print("🚀 Script de Migração para Sistema de Grupos")
    print("=" * 50)
    
    with app.app_context():
        # Menu de opções
        print("\nOpções disponíveis:")
        print("1. Migrar dados existentes para grupos")
        print("2. Validar migração")
        print("3. Criar grupos de exemplo")
        print("4. Executar tudo")
        print("0. Sair")
        
        choice = input("\nEscolha uma opção (0-4): ")
        
        if choice == "1":
            migrate_to_groups()
        elif choice == "2":
            validate_migration()
        elif choice == "3":
            create_sample_groups()
        elif choice == "4":
            print("Executando migração completa...\n")
            if migrate_to_groups():
                validate_migration()
                create_sample_groups()
        elif choice == "0":
            print("Saindo...")
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    main()
