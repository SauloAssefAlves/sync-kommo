#!/usr/bin/env python3
"""
Script para cadastrar contas Master e Slave no banco local
Limpa o banco e adiciona as novas contas
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
import logging

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_and_setup_database():
    """
    Limpa completamente o banco e cadastra as novas contas
    """
    db_path = 'app.db'
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🗑️ LIMPANDO banco de dados...")
        
        # Desabilitar foreign keys temporariamente
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Deletar todos os dados das tabelas (ordem importante devido às foreign keys)
        tables_to_clear = [
            'sync_logs',
            'custom_field_mappings', 
            'stage_mappings',
            'pipeline_mappings',
            'kommo_accounts',
            'sync_groups'
        ]
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                logger.info(f"✅ Tabela '{table}' limpa")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao limpar tabela '{table}': {e}")
        
        # Reabilitar foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        
        logger.info("✅ Banco de dados limpo com sucesso!")
        
        # Agora cadastrar as novas contas
        logger.info("📝 CADASTRANDO novas contas...")
        
        # Dados da conta MASTER
        master_subdomain = "evoresultdev"
        master_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImQ4MzcxYzYzYzQ1YjBkM2I2NzE1MzY1MTc0OWQ4ZDNjYjllNDAzZTNlMGM2YmU4ZGZmMWQ1OTc5YmZkYTQwODk5ZDNkOTdmNjc3YzU2MGVjIn0.eyJhdWQiOiIxNmZjYWYxYS0yOTk3LTQ1MTUtYTM1Zi1iODU1YjQwNGUwN2MiLCJqdGkiOiJkODM3MWM2M2M0NWIwZDNiNjcxNTM2NTE3NDlkOGQzY2I5ZTQwM2UzZTBjNmJlOGRmZjFkNTk3OWJmZGE0MDg5OWQzZDk3ZjY3N2M1NjBlYyIsImlhdCI6MTc1NDU4NTQ0OSwibmJmIjoxNzU0NTg1NDQ5LCJleHAiOjE4MDY2MjQwMDAsInN1YiI6IjEwMjgxNTk5IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyMDg0NDkxLCJiYXNlX2RvbWFpbiI6ImtvbW1vLmNvbSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwidXNlcl9mbGFncyI6MSwiaGFzaF91dWlkIjoiNmZiYzkyYmMtYWEyYy00ODcwLTgzY2QtMmM2NzRhNDgzODVlIiwiYXBpX2RvbWFpbiI6ImFwaS1jLmtvbW1vLmNvbSJ9.q4muJ1DhltOp1vPX1k4jabgizHUAW79O8gHL7osw5Yp93cDcLFSC42e_zleXn0QUCv7jq9MWJKxqdRT_H05AGqLZFVNJKbb9XbziJvnJE3C2p2MiSRnxWHu7ZoSlSn7Rlm-yCH0168sTBnX5-O39lnki829kPeUrGJzk5TjduK-6Xwy0Rjs_K0kScy3r58VUCbyDRWCgP1pkvj3MdOMriYk8C38GFDqtEMMRwM_GYa3yCL5H9CgGKiCvytuJBsYHKP7RSKB-28RxIVlw4nUZuvyzEkNBsHaIWNRDpq8f8Dx5tYOJCibEhvaoCiqDaKm6162Rn_gtM85yNy26B3fnSA"
        
        # Dados que precisaremos para a conta SLAVE (vamos aguardar do usuário)
        slave_subdomain = "AGUARDANDO"  # Usuário ainda não forneceu
        slave_token = "AGUARDANDO"       # Usuário ainda não forneceu
        
        # Data de expiração (definir para 1 ano no futuro)
        expires_at = datetime.now() + timedelta(days=365)
        current_time = datetime.now()
        
        # 1. Inserir conta MASTER
        cursor.execute("""
            INSERT INTO kommo_accounts 
            (subdomain, access_token, refresh_token, token_expires_at, account_role, is_master, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            master_subdomain,
            master_token,
            "refresh_token_placeholder",  # Placeholder para refresh token
            expires_at,
            "master",
            True,
            current_time,
            current_time
        ))
        
        master_account_id = cursor.lastrowid
        logger.info(f"✅ Conta MASTER cadastrada: {master_subdomain} (ID: {master_account_id})")
        
        # 2. Criar grupo de sincronização com a conta master
        cursor.execute("""
            INSERT INTO sync_groups 
            (name, description, master_account_id, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Grupo Principal",
            "Grupo de sincronização principal - Master: evoresultdev",
            master_account_id,
            True,
            current_time,
            current_time
        ))
        
        sync_group_id = cursor.lastrowid
        logger.info(f"✅ Grupo de sincronização criado: ID {sync_group_id}")
        
        # 3. Atualizar a conta master para associar ao grupo
        cursor.execute("""
            UPDATE kommo_accounts 
            SET sync_group_id = ?, updated_at = ?
            WHERE id = ?
        """, (sync_group_id, current_time, master_account_id))
        
        # Commit das mudanças
        conn.commit()
        conn.close()
        
        logger.info("🎯 CONFIGURAÇÃO INICIAL COMPLETA!")
        logger.info("📊 RESUMO:")
        logger.info(f"   ✅ Conta Master: {master_subdomain} (ID: {master_account_id})")
        logger.info(f"   ✅ Grupo de Sync: 'Grupo Principal' (ID: {sync_group_id})")
        logger.info("   ⏳ Aguardando dados da conta SLAVE...")
        logger.info("")
        logger.info("🔔 PRÓXIMOS PASSOS:")
        logger.info("   1. Fornecer subdomain e token da conta SLAVE")
        logger.info("   2. Executar script para adicionar conta SLAVE ao grupo")
        logger.info("   3. Executar sincronização de roles")
        
        return {
            'master_account_id': master_account_id,
            'sync_group_id': sync_group_id,
            'master_subdomain': master_subdomain
        }
        
    except Exception as e:
        logger.error(f"❌ Erro durante a configuração: {e}")
        return None

def verify_database():
    """Verifica o estado atual do banco"""
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        logger.info("🔍 VERIFICANDO estado do banco...")
        
        # Verificar contas
        cursor.execute("SELECT id, subdomain, account_role, is_master FROM kommo_accounts")
        accounts = cursor.fetchall()
        
        logger.info(f"📋 Contas cadastradas ({len(accounts)}):")
        for account in accounts:
            account_id, subdomain, role, is_master = account
            master_flag = "👑" if is_master else "👤"
            logger.info(f"   {master_flag} ID: {account_id}, Subdomain: {subdomain}, Role: {role}")
        
        # Verificar grupos
        cursor.execute("SELECT id, name, master_account_id FROM sync_groups")
        groups = cursor.fetchall()
        
        logger.info(f"🏷️ Grupos de sincronização ({len(groups)}):")
        for group in groups:
            group_id, name, master_id = group
            logger.info(f"   📁 ID: {group_id}, Nome: {name}, Master ID: {master_id}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    print("🚀 CONFIGURAÇÃO INICIAL DO BANCO - MASTER E SLAVE")
    print("=" * 60)
    print("📋 Este script irá:")
    print("   1. Limpar completamente o banco de dados")
    print("   2. Cadastrar a conta MASTER fornecida")
    print("   3. Criar grupo de sincronização")
    print("   4. Aguardar dados da conta SLAVE")
    print()
    
    confirm = input("❓ Deseja continuar? (s/N): ").lower().strip()
    
    if confirm in ['s', 'sim', 'y', 'yes']:
        result = clear_and_setup_database()
        if result:
            print()
            verify_database()
            print()
            print("✅ Configuração inicial concluída!")
            print("🔔 Agora forneça os dados da conta SLAVE para completar a configuração.")
    else:
        print("❌ Operação cancelada pelo usuário")
