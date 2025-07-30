#!/usr/bin/env python3
"""
Script para limpar todas as contas do banco de dados
"""

import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup, PipelineMapping
# Configurações de segurança
SECRET_KEY = "asdf#FGSgvasgf$5$WGT"

def create_app():
    """Criar app Flask para acesso ao banco"""
    app = Flask(__name__)
    
    # Usar caminho absoluto para o banco de dados
    db_path = os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def clear_database():
    """Limpar todas as tabelas do banco de dados"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🗑️  Iniciando limpeza do banco de dados...")
            
            # Contar registros antes da exclusão
            sync_groups_count = SyncGroup.query.count()
            accounts_count = KommoAccount.query.count()
            pipeline_mappings_count = PipelineMapping.query.count()
            
            print(f"📊 Registros encontrados:")
            print(f"   - Grupos de Sincronização: {sync_groups_count}")
            print(f"   - Contas Kommo: {accounts_count}")
            print(f"   - Mapeamentos de Pipeline: {pipeline_mappings_count}")
            
            if accounts_count == 0 and sync_groups_count == 0 and pipeline_mappings_count == 0:
                print("✅ Banco de dados já está vazio!")
                return
            
            # Confirmar a exclusão
            confirm = input("\n⚠️  Tem certeza que deseja apagar TODOS os dados? (sim/não): ").lower().strip()
            
            if confirm not in ['sim', 's', 'yes', 'y']:
                print("❌ Operação cancelada pelo usuário.")
                return
            
            print("\n🔄 Apagando dados...")
            
            # Apagar na ordem correta (devido às foreign keys)
            # 1. Pipeline Mappings (não tem dependências)
            deleted_mappings = PipelineMapping.query.delete()
            print(f"   ✅ {deleted_mappings} mapeamentos de pipeline apagados")
            
            # 2. Contas Kommo (referenciadas por sync_groups)
            deleted_accounts = KommoAccount.query.delete()
            print(f"   ✅ {deleted_accounts} contas Kommo apagadas")
            
            # 3. Grupos de Sincronização
            deleted_groups = SyncGroup.query.delete()
            print(f"   ✅ {deleted_groups} grupos de sincronização apagados")
            
            # Commit das mudanças
            db.session.commit()
            
            print("\n🎉 Banco de dados limpo com sucesso!")
            print("   - Todas as contas foram removidas")
            print("   - Todos os grupos foram removidos")
            print("   - Todos os mapeamentos foram removidos")
            
        except Exception as e:
            print(f"\n❌ Erro ao limpar banco de dados: {str(e)}")
            db.session.rollback()
            return False
            
    return True

def show_current_data():
    """Mostrar dados atuais do banco"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("📋 Dados atuais no banco:")
            print("=" * 50)
            
            # Grupos de sincronização
            groups = SyncGroup.query.all()
            print(f"\n🔗 Grupos de Sincronização ({len(groups)}):")
            for group in groups:
                print(f"   - ID: {group.id}, Nome: {group.name}")
                if group.description:
                    print(f"     Descrição: {group.description}")
                if group.master_account:
                    print(f"     Conta Master: {group.master_account.subdomain}")
                slave_count = len(group.slave_accounts)
                print(f"     Contas Escravas: {slave_count}")
                print()
            
            # Contas Kommo
            accounts = KommoAccount.query.all()
            print(f"\n💼 Contas Kommo ({len(accounts)}):")
            for account in accounts:
                role = "🔴 Master" if account.is_master else "🔵 Escrava"
                group_name = account.sync_group.name if account.sync_group else "Sem grupo"
                print(f"   - ID: {account.id}, Subdomínio: {account.subdomain}")
                print(f"     Tipo: {role}, Grupo: {group_name}")
                print()
            
            # Pipeline Mappings
            mappings = PipelineMapping.query.all()
            print(f"\n⚙️  Mapeamentos de Pipeline ({len(mappings)}):")
            for mapping in mappings:
                print(f"   - ID: {mapping.id}")
                print()
                
        except Exception as e:
            print(f"❌ Erro ao buscar dados: {str(e)}")

if __name__ == "__main__":
    print("🔧 Utilitário de Limpeza do Banco de Dados")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        show_current_data()
    else:
        print("Opções:")
        print("1. Limpar banco de dados")
        print("2. Mostrar dados atuais")
        print("3. Sair")
        
        choice = input("\nEscolha uma opção (1-3): ").strip()
        
        if choice == "1":
            clear_database()
        elif choice == "2":
            show_current_data()
        elif choice == "3":
            print("👋 Saindo...")
        else:
            print("❌ Opção inválida!")
