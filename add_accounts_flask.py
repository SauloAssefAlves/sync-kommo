#!/usr/bin/env python3
"""
Script para cadastrar contas Master e Slave usando Flask app context
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
    print("Tentando importar diretamente...")
    sys.exit(1)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_accounts_with_flask():
    """
    Adiciona contas usando o contexto do Flask e SQLAlchemy
    """
    try:
        with app.app_context():
            logger.info("🔗 Conectado ao banco usando Flask app context...")
            
            # Dados da conta MASTER
            master_subdomain = "evoresultdev"
            master_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImQ4MzcxYzYzYzQ1YjBkM2I2NzE1MzY1MTc0OWQ4ZDNjYjllNDAzZTNlMGM2YmU4ZGZmMWQ1OTc5YmZkYTQwODk5ZDNkOTdmNjc3YzU2MGVjIn0.eyJhdWQiOiIxNmZjYWYxYS0yOTk3LTQ1MTUtYTM1Zi1iODU1YjQwNGUwN2MiLCJqdGkiOiJkODM3MWM2M2M0NWIwZDNiNjcxNTM2NTE3NDlkOGQzY2I5ZTQwM2UzZTBjNmJlOGRmZjFkNTk3OWJmZGE0MDg5OWQzZDk3ZjY3N2M1NjBlYyIsImlhdCI6MTc1NDU4NTQ0OSwibmJmIjoxNzU0NTg1NDQ5LCJleHAiOjE4MDY2MjQwMDAsInN1YiI6IjEwMjgxNTk5IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyMDg0NDkxLCJiYXNlX2RvbWFpbiI6ImtvbW1vLmNvbSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwidXNlcl9mbGFncyI6MSwiaGFzaF91dWlkIjoiNmZiYzkyYmMtYWEyYy00ODcwLTgzY2QtMmM2NzRhNDgzODVlIiwiYXBpX2RvbWFpbiI6ImFwaS1jLmtvbW1vLmNvbSJ9.q4muJ1DhltOp1vPX1k4jabgizHUAW79O8gHL7osw5Yp93cDcLFSC42e_zleXn0QUCv7jq9MWJKxqdRT_H05AGqLZFVNJKbb9XbziJvnJE3C2p2MiSRnxWHu7ZoSlSn7Rlm-yCH0168sTBnX5-O39lnki829kPeUrGJzk5TjduK-6Xwy0Rjs_K0kScy3r58VUCbyDRWCgP1pkvj3MdOMriYk8C38GFDqtEMMRwM_GYa3yCL5H9CgGKiCvytuJBsYHKP7RSKB-28RxIVlw4nUZuvyzEkNBsHaIWNRDpq8f8Dx5tYOJCibEhvaoCiqDaKm6162Rn_gtM85yNy26B3fnSA"
            
            # Data de expiração (definir para 1 ano no futuro)
            expires_at = datetime.now() + timedelta(days=365)
            
            # Verificar se a conta master já existe
            existing_master = KommoAccount.query.filter_by(subdomain=master_subdomain).first()
            
            if existing_master:
                logger.info(f"⚠️ Conta master '{master_subdomain}' já existe (ID: {existing_master.id})")
                
                # Atualizar o token da conta existente
                existing_master.access_token = master_token
                existing_master.token_expires_at = expires_at
                existing_master.updated_at = datetime.now()
                
                master_account_id = existing_master.id
                logger.info(f"✅ Token da conta master atualizado")
            else:
                # Criar nova conta MASTER
                new_master = KommoAccount(
                    subdomain=master_subdomain,
                    access_token=master_token,
                    refresh_token="refresh_token_placeholder",
                    token_expires_at=expires_at,
                    account_role="master",
                    is_master=True
                )
                
                db.session.add(new_master)
                db.session.flush()  # Para obter o ID sem fazer commit
                
                master_account_id = new_master.id
                logger.info(f"✅ Nova conta MASTER cadastrada: {master_subdomain} (ID: {master_account_id})")
            
            # Verificar se já existe um grupo de sincronização para esta conta master
            existing_group = SyncGroup.query.filter_by(master_account_id=master_account_id).first()
            
            if existing_group:
                sync_group_id = existing_group.id
                logger.info(f"⚠️ Grupo de sincronização já existe (ID: {sync_group_id})")
            else:
                # Criar grupo de sincronização
                new_group = SyncGroup(
                    name="Grupo Principal",
                    description="Grupo de sincronização principal - Master: evoresultdev",
                    master_account_id=master_account_id,
                    is_active=True
                )
                
                db.session.add(new_group)
                db.session.flush()  # Para obter o ID sem fazer commit
                
                sync_group_id = new_group.id
                logger.info(f"✅ Grupo de sincronização criado: ID {sync_group_id}")
            
            # Atualizar a conta master para associar ao grupo (se necessário)
            if existing_master:
                master_account = existing_master
            else:
                master_account = new_master
                
            if not master_account.sync_group_id or master_account.sync_group_id != sync_group_id:
                master_account.sync_group_id = sync_group_id
                master_account.updated_at = datetime.now()
            
            # Commit de todas as mudanças
            db.session.commit()
            
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

def verify_database_with_flask():
    """Verifica o estado atual do banco usando Flask"""
    try:
        with app.app_context():
            logger.info("🔍 VERIFICANDO estado do banco...")
            
            # Verificar contas
            accounts = KommoAccount.query.all()
            
            logger.info(f"📋 Contas cadastradas ({len(accounts)}):")
            for account in accounts:
                master_flag = "👑" if account.is_master else "👤"
                logger.info(f"   {master_flag} ID: {account.id}, Subdomain: {account.subdomain}, Role: {account.account_role}")
            
            # Verificar grupos
            groups = SyncGroup.query.all()
            
            logger.info(f"🏷️ Grupos de sincronização ({len(groups)}):")
            for group in groups:
                logger.info(f"   📁 ID: {group.id}, Nome: {group.name}, Master ID: {group.master_account_id}")
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    print("🚀 CADASTRO DE CONTAS USANDO FLASK")
    print("=" * 50)
    print("📋 Este script irá:")
    print("   1. Usar contexto Flask para acessar banco")
    print("   2. Cadastrar/atualizar a conta MASTER")
    print("   3. Criar/verificar grupo de sincronização")
    print()
    
    result = add_accounts_with_flask()
    if result:
        print()
        verify_database_with_flask()
        print()
        print("✅ Configuração concluída!")
        print("🔔 Agora forneça os dados da conta SLAVE.")
    else:
        print("❌ Erro na configuração!")
