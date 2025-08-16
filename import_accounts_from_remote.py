#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para importar contas (master e slave) do servidor remoto para o banco de dados local

Este script:
1. Busca as informações das contas do endpoint remoto
2. Verifica se já existem no banco local
3. Cria/atualiza as contas no banco local
4. Associa as contas aos grupos de sincronização corretos
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup

# URL do servidor remoto
REMOTE_API_URL = "http://89.116.186.230:5000"

def get_remote_accounts():
    """Busca as contas do servidor remoto"""
    try:
        print("🔗 Conectando ao servidor remoto...")
        response = requests.get(f"{REMOTE_API_URL}/api/sync/accounts", 
                              headers={"Accept": "application/json"},
                              timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'accounts' in data:
                print(f"✅ {data['total']} contas encontradas no servidor remoto")
                return data['accounts']
            else:
                print(f"❌ Resposta inválida do servidor: {data}")
                return None
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        return None

def get_remote_groups():
    """Busca os grupos de sincronização do servidor remoto"""
    try:
        print("🔗 Buscando grupos de sincronização...")
        response = requests.get(f"{REMOTE_API_URL}/api/groups", 
                              headers={"Accept": "application/json"},
                              timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'groups' in data:
                print(f"✅ {len(data['groups'])} grupos encontrados")
                return data['groups']
            elif isinstance(data, list):
                print(f"✅ {len(data)} grupos encontrados")
                return data
            else:
                print(f"⚠️ Formato de resposta inesperado para grupos: {type(data)}")
                return []
        else:
            print(f"⚠️ Erro ao buscar grupos HTTP {response.status_code}: {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro ao buscar grupos: {e}")
        return []

def create_or_update_sync_group(group_data):
    """Cria ou atualiza um grupo de sincronização no banco local"""
    try:
        group_id = group_data.get('id')
        group_name = group_data.get('name', f'Grupo {group_id}')
        
        # Verificar se o grupo já existe
        existing_group = SyncGroup.query.filter_by(id=group_id).first()
        
        if existing_group:
            print(f"🔄 Atualizando grupo existente: '{group_name}' (ID: {group_id})")
            existing_group.name = group_name
            existing_group.description = group_data.get('description', '')
            existing_group.updated_at = datetime.utcnow()
            return existing_group
        else:
            print(f"➕ Criando novo grupo: '{group_name}' (ID: {group_id})")
            new_group = SyncGroup(
                id=group_id,
                name=group_name,
                description=group_data.get('description', ''),
                master_account_id=1,  # Será atualizado depois
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(new_group)
            return new_group
            
    except Exception as e:
        print(f"❌ Erro ao criar/atualizar grupo {group_data}: {e}")
        return None

def create_or_update_account(account_data):
    """Cria ou atualiza uma conta no banco de dados local"""
    try:
        subdomain = account_data['subdomain']
        account_role = account_data.get('account_role', 'slave')
        is_master = account_data.get('is_master', False)
        sync_group_id = account_data.get('sync_group_id')
        
        print(f"🔄 Processando conta: {subdomain} ({account_role})")
        
        # Verificar se a conta já existe
        existing_account = KommoAccount.query.filter_by(subdomain=subdomain).first()
        
        if existing_account:
            print(f"✏️ Atualizando conta existente: {subdomain}")
            existing_account.account_role = account_role
            existing_account.is_master = is_master
            existing_account.sync_group_id = sync_group_id
            existing_account.updated_at = datetime.utcnow()
            return existing_account, False  # False = não é nova
        else:
            print(f"➕ Criando nova conta: {subdomain}")
            
            # Para contas novas, precisamos de tokens válidos
            # Como não temos os tokens reais, vamos usar placeholders
            default_token = "placeholder_token_" + subdomain
            default_expires = datetime.utcnow() + timedelta(hours=1)
            
            new_account = KommoAccount(
                subdomain=subdomain,
                access_token=default_token,
                refresh_token=default_token,
                token_expires_at=default_expires,
                sync_group_id=sync_group_id,
                account_role=account_role,
                is_master=is_master,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(new_account)
            return new_account, True  # True = é nova
            
    except Exception as e:
        print(f"❌ Erro ao criar/atualizar conta {account_data}: {e}")
        return None, False

def update_group_master_references():
    """Atualiza as referências de conta mestre nos grupos"""
    try:
        print("🔗 Atualizando referências de contas mestre nos grupos...")
        
        groups = SyncGroup.query.all()
        for group in groups:
            # Encontrar a conta mestre deste grupo
            master_account = KommoAccount.query.filter_by(
                sync_group_id=group.id,
                account_role='master'
            ).first()
            
            if master_account:
                group.master_account_id = master_account.id
                print(f"✅ Grupo '{group.name}' -> Conta mestre: {master_account.subdomain}")
            else:
                # Se não encontrou conta mestre específica, usar a primeira master disponível
                fallback_master = KommoAccount.query.filter_by(account_role='master').first()
                if fallback_master:
                    group.master_account_id = fallback_master.id
                    print(f"⚠️ Grupo '{group.name}' -> Usando conta mestre padrão: {fallback_master.subdomain}")
                else:
                    print(f"❌ Nenhuma conta mestre encontrada para o grupo '{group.name}'")
                    
    except Exception as e:
        print(f"❌ Erro ao atualizar referências de grupos: {e}")

def main():
    """Função principal"""
    print("🚀 Iniciando importação de contas do servidor remoto...")
    print("=" * 60)
    
    # Inicializar contexto da aplicação
    from src.main import app
    
    with app.app_context():
        try:
            # 1. Buscar grupos do servidor remoto
            remote_groups = get_remote_groups()
            groups_created = 0
            
            if remote_groups:
                print(f"\n📁 Processando {len(remote_groups)} grupos...")
                for group_data in remote_groups:
                    group = create_or_update_sync_group(group_data)
                    if group:
                        groups_created += 1
                        
                print(f"✅ {groups_created} grupos processados")
            
            # 2. Buscar contas do servidor remoto
            remote_accounts = get_remote_accounts()
            if not remote_accounts:
                print("❌ Não foi possível obter as contas do servidor remoto")
                return
            
            print(f"\n👥 Processando {len(remote_accounts)} contas...")
            
            accounts_created = 0
            accounts_updated = 0
            master_accounts = 0
            slave_accounts = 0
            
            # 3. Processar cada conta
            for account_data in remote_accounts:
                account, is_new = create_or_update_account(account_data)
                
                if account:
                    if is_new:
                        accounts_created += 1
                    else:
                        accounts_updated += 1
                    
                    if account.account_role == 'master':
                        master_accounts += 1
                    else:
                        slave_accounts += 1
            
            # 4. Atualizar referências de grupos
            update_group_master_references()
            
            # 5. Salvar todas as mudanças
            print("\n💾 Salvando alterações no banco de dados...")
            db.session.commit()
            
            # 6. Relatório final
            print("\n" + "=" * 60)
            print("📊 RELATÓRIO DE IMPORTAÇÃO:")
            print(f"   📁 Grupos processados: {groups_created}")
            print(f"   ➕ Contas criadas: {accounts_created}")
            print(f"   ✏️ Contas atualizadas: {accounts_updated}")
            print(f"   👑 Contas master: {master_accounts}")
            print(f"   🔗 Contas slave: {slave_accounts}")
            print("✅ Importação concluída com sucesso!")
            
            # 7. Listar contas importadas
            print("\n📋 CONTAS IMPORTADAS:")
            all_accounts = KommoAccount.query.all()
            for account in all_accounts:
                group_name = account.sync_group.name if account.sync_group else "Sem grupo"
                role_icon = "👑" if account.account_role == 'master' else "🔗"
                print(f"   {role_icon} {account.subdomain} ({account.account_role}) - Grupo: {group_name}")
                
        except Exception as e:
            print(f"❌ Erro durante a importação: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    main()
