#!/usr/bin/env python3
"""
Script para adicionar conta SLAVE ao grupo de sincronização existente
"""

import os
import sys
from datetime import datetime, timedelta
import logging

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importar Flask app e modelos
try:
    from src.main import app
    from src.database import db
    from src.models.kommo_account import KommoAccount, SyncGroup
except ImportError as e:
    print(f"❌ Erro ao importar módulos Flask: {e}")
    sys.exit(1)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_slave_account():
    """
    Adiciona conta slave ao grupo de sincronização existente
    """
    try:
        with app.app_context():
            logger.info("🔗 Conectado ao banco usando Flask app context...")
            
            # Dados da conta SLAVE
            slave_subdomain = "testedev"
            slave_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjE2NmVhZTJkNzg5MGQzODI3OTE5YzVmODAxYTQ2YTljY2IwZDhmZTUzM2I2OTAwOTQwNjA5ZmZlZjUwZjhkMTEzNjRkZjM5ZGYxNWE0M2I1In0.eyJhdWQiOiJhZWFiMzFkYS00MDU1LTRhNDgtOGNmMy0wYjNmMzA1YzVjMmUiLCJqdGkiOiIxNjZlYWUyZDc4OTBkMzgyNzkxOWM1ZjgwMWE0NmE5Y2NiMGQ4ZmU1MzNiNjkwMDk0MDYwOWZmZWY1MGY4ZDExMzY0ZGYzOWRmMTVhNDNiNSIsImlhdCI6MTc1NTMwMzQ0NCwibmJmIjoxNzU1MzAzNDQ0LCJleHAiOjE3ODM2NDE2MDAsInN1YiI6IjEwMjgxNTk5IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjM0OTE4NTg3LCJiYXNlX2RvbWFpbiI6ImtvbW1vLmNvbSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwidXNlcl9mbGFncyI6MSwiaGFzaF91dWlkIjoiYWU5ZGFmMTctZGNlOS00YTQwLTgxYjQtZDI1ZDBhYWJmZWNiIiwiYXBpX2RvbWFpbiI6ImFwaS1jLmtvbW1vLmNvbSJ9.g0HwizUa3cqPtSmHF7XnShTsCSBc3iCpK81RlIenMdVsn3UwH-cZB8gmYaTihaCRJgq53fq_nCl9Qwv3sViCv6a6gJvO38thjEOeH8-FSQBwBCcrfCB-wFaXE_TzLdy8JekAMl10400TirnaL7bDpXg55jM8lWlfG2ggrYMFwv_WOofgmXWo5qtB42N37c2xw6yzcvedzZHZ9u-W4LiTGTnEUbIfu8IMslhZ3xjqDPxfqZK94Hj77LqWmH-eIbDLXeqdeHneFI5oJUUSXSfEE0UFIZ6ji6WogD7XiYCB68uKkfbZRPrKQHSccA8irk2HM7I4fm-Mra9EcJzB9WM2Gw"
            
            # Data de expiração (definir para 1 ano no futuro)
            expires_at = datetime.now() + timedelta(days=365)
            
            # Encontrar o grupo de sincronização existente
            sync_group = SyncGroup.query.filter_by(is_active=True).first()
            
            if not sync_group:
                logger.error("❌ Nenhum grupo de sincronização ativo encontrado!")
                logger.info("ℹ️ Execute primeiro o script para criar a conta master e grupo")
                return None
            
            logger.info(f"📁 Grupo encontrado: '{sync_group.name}' (ID: {sync_group.id})")
            
            # Verificar se a conta slave já existe
            existing_slave = KommoAccount.query.filter_by(subdomain=slave_subdomain).first()
            
            if existing_slave:
                logger.info(f"⚠️ Conta slave '{slave_subdomain}' já existe (ID: {existing_slave.id})")
                
                # Atualizar o token e associar ao grupo
                existing_slave.access_token = slave_token
                existing_slave.token_expires_at = expires_at
                existing_slave.account_role = "slave"
                existing_slave.is_master = False
                existing_slave.sync_group_id = sync_group.id
                existing_slave.updated_at = datetime.now()
                
                slave_account_id = existing_slave.id
                logger.info(f"✅ Conta slave atualizada e associada ao grupo {sync_group.id}")
            else:
                # Criar nova conta SLAVE
                new_slave = KommoAccount(
                    subdomain=slave_subdomain,
                    access_token=slave_token,
                    refresh_token="refresh_token_placeholder",
                    token_expires_at=expires_at,
                    account_role="slave",
                    is_master=False,
                    sync_group_id=sync_group.id
                )
                
                db.session.add(new_slave)
                db.session.flush()  # Para obter o ID sem fazer commit
                
                slave_account_id = new_slave.id
                logger.info(f"✅ Nova conta SLAVE cadastrada: {slave_subdomain} (ID: {slave_account_id})")
            
            # Commit de todas as mudanças
            db.session.commit()
            
            logger.info("🎯 CONTA SLAVE ADICIONADA COM SUCESSO!")
            logger.info("📊 RESUMO FINAL:")
            logger.info(f"   👑 Grupo: '{sync_group.name}' (ID: {sync_group.id})")
            logger.info(f"   👑 Master: {sync_group.master_account.subdomain} (ID: {sync_group.master_account_id})")
            logger.info(f"   👤 Slave: {slave_subdomain} (ID: {slave_account_id})")
            logger.info("")
            logger.info("🔔 PRÓXIMOS PASSOS:")
            logger.info("   1. Executar sincronização de roles")
            logger.info("   2. Testar o sistema de sincronização")
            
            return {
                'slave_account_id': slave_account_id,
                'sync_group_id': sync_group.id,
                'master_account_id': sync_group.master_account_id,
                'slave_subdomain': slave_subdomain
            }
            
    except Exception as e:
        logger.error(f"❌ Erro durante a configuração: {e}")
        db.session.rollback()
        return None

def verify_complete_setup():
    """Verifica o setup completo do sistema"""
    try:
        with app.app_context():
            logger.info("🔍 VERIFICANDO CONFIGURAÇÃO COMPLETA...")
            
            # Verificar contas
            accounts = KommoAccount.query.all()
            
            logger.info(f"📋 Contas cadastradas ({len(accounts)}):")
            for account in accounts:
                master_flag = "👑" if account.is_master else "👤"
                group_info = f" | Grupo: {account.sync_group_id}" if account.sync_group_id else " | Sem grupo"
                logger.info(f"   {master_flag} ID: {account.id}, Subdomain: {account.subdomain}, Role: {account.account_role}{group_info}")
            
            # Verificar grupos
            groups = SyncGroup.query.all()
            
            logger.info(f"🏷️ Grupos de sincronização ({len(groups)}):")
            for group in groups:
                logger.info(f"   📁 ID: {group.id}, Nome: {group.name}")
                logger.info(f"      👑 Master: {group.master_account.subdomain} (ID: {group.master_account_id})")
                
                # Contar slaves no grupo
                slaves = KommoAccount.query.filter_by(sync_group_id=group.id, account_role='slave').all()
                logger.info(f"      👤 Slaves: {len(slaves)} contas")
                for slave in slaves:
                    logger.info(f"         - {slave.subdomain} (ID: {slave.id})")
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    print("🚀 ADICIONANDO CONTA SLAVE AO GRUPO")
    print("=" * 50)
    print("📋 Este script irá:")
    print("   1. Localizar grupo de sincronização existente")
    print("   2. Cadastrar/atualizar conta SLAVE")
    print("   3. Associar slave ao grupo")
    print()
    
    result = add_slave_account()
    if result:
        print()
        verify_complete_setup()
        print()
        print("✅ Sistema de sincronização configurado!")
        print("🎯 Master e Slave prontos para sincronização de roles.")
    else:
        print("❌ Erro na configuração da conta slave!")
