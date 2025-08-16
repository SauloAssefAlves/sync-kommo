#!/usr/bin/env python3
"""
Script para cadastrar contas Master e Slave no banco local
Apenas insere as contas sem limpar o banco
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_accounts():
    """
    Conecta ao banco e adiciona as contas master e slave
    """
    db_path = 'app.db'
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔗 Conectado ao banco de dados...")
        
        # Dados da conta MASTER
        master_subdomain = "evoresultdev"
        master_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImQ4MzcxYzYzYzQ1YjBkM2I2NzE1MzY1MTc0OWQ4ZDNjYjllNDAzZTNlMGM2YmU4ZGZmMWQ1OTc5YmZkYTQwODk5ZDNkOTdmNjc3YzU2MGVjIn0.eyJhdWQiOiIxNmZjYWYxYS0yOTk3LTQ1MTUtYTM1Zi1iODU1YjQwNGUwN2MiLCJqdGkiOiJkODM3MWM2M2M0NWIwZDNiNjcxNTM2NTE3NDlkOGQzY2I5ZTQwM2UzZTBjNmJlOGRmZjFkNTk3OWJmZGE0MDg5OWQzZDk3ZjY3N2M1NjBlYyIsImlhdCI6MTc1NDU4NTQ0OSwibmJmIjoxNzU0NTg1NDQ5LCJleHAiOjE4MDY2MjQwMDAsInN1YiI6IjEwMjgxNTk5IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyMDg0NDkxLCJiYXNlX2RvbWFpbiI6ImtvbW1vLmNvbSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwidXNlcl9mbGFncyI6MSwiaGFzaF91dWlkIjoiNmZiYzkyYmMtYWEyYy00ODcwLTgzY2QtMmM2NzRhNDgzODVlIiwiYXBpX2RvbWFpbiI6ImFwaS1jLmtvbW1vLmNvbSJ9.q4muJ1DhltOp1vPX1k4jabgizHUAW79O8gHL7osw5Yp93cDcLFSC42e_zleXn0QUCv7jq9MWJKxqdRT_H05AGqLZFVNJKbb9XbziJvnJE3C2p2MiSRnxWHu7ZoSlSn7Rlm-yCH0168sTBnX5-O39lnki829kPeUrGJzk5TjduK-6Xwy0Rjs_K0kScy3r58VUCbyDRWCgP1pkvj3MdOMriYk8C38GFDqtEMMRwM_GYa3yCL5H9CgGKiCvytuJBsYHKP7RSKB-28RxIVlw4nUZuvyzEkNBsHaIWNRDpq8f8Dx5tYOJCibEhvaoCiqDaKm6162Rn_gtM85yNy26B3fnSA"
        
        # Data de expiração (definir para 1 ano no futuro)
        expires_at = datetime.now() + timedelta(days=365)
        current_time = datetime.now()
        
        # Verificar se a conta master já existe
        cursor.execute("SELECT id FROM kommo_accounts WHERE subdomain = ?", (master_subdomain,))
        existing_master = cursor.fetchone()
        
        if existing_master:
            logger.info(f"⚠️ Conta master '{master_subdomain}' já existe (ID: {existing_master[0]})")
            master_account_id = existing_master[0]
            
            # Atualizar o token da conta existente
            cursor.execute("""
                UPDATE kommo_accounts 
                SET access_token = ?, token_expires_at = ?, updated_at = ?
                WHERE id = ?
            """, (master_token, expires_at, current_time, master_account_id))
            logger.info(f"✅ Token da conta master atualizado")
        else:
            # Inserir nova conta MASTER
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
            logger.info(f"✅ Nova conta MASTER cadastrada: {master_subdomain} (ID: {master_account_id})")
        
        # Verificar se já existe um grupo de sincronização para esta conta master
        cursor.execute("SELECT id FROM sync_groups WHERE master_account_id = ?", (master_account_id,))
        existing_group = cursor.fetchone()
        
        if existing_group:
            sync_group_id = existing_group[0]
            logger.info(f"⚠️ Grupo de sincronização já existe (ID: {sync_group_id})")
        else:
            # Criar grupo de sincronização com a conta master
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
        
        # Atualizar a conta master para associar ao grupo (se necessário)
        cursor.execute("""
            UPDATE kommo_accounts 
            SET sync_group_id = ?, updated_at = ?
            WHERE id = ? AND (sync_group_id IS NULL OR sync_group_id != ?)
        """, (sync_group_id, current_time, master_account_id, sync_group_id))
        
        # Commit das mudanças
        conn.commit()
        conn.close()
        
        logger.info("🎯 CONFIGURAÇÃO COMPLETA!")
        logger.info("📊 RESUMO:")
        logger.info(f"   ✅ Conta Master: {master_subdomain} (ID: {master_account_id})")
        logger.info(f"   ✅ Grupo de Sync: 'Grupo Principal' (ID: {sync_group_id})")
        logger.info("")
        logger.info("🔔 PRÓXIMOS PASSOS:")
        logger.info("   1. Fornecer subdomain e token da conta SLAVE")
        logger.info("   2. Executar sincronização de roles")
        
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
    print("🚀 CADASTRO DE CONTAS MASTER E SLAVE")
    print("=" * 50)
    print("📋 Este script irá:")
    print("   1. Conectar ao banco de dados existente")
    print("   2. Cadastrar/atualizar a conta MASTER")
    print("   3. Criar/verificar grupo de sincronização")
    print()
    
    result = add_accounts()
    if result:
        print()
        verify_database()
        print()
        print("✅ Configuração concluída!")
        print("🔔 Agora forneça os dados da conta SLAVE para completar.")
    else:
        print("❌ Erro na configuração!")
