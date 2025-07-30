#!/usr/bin/env python3
"""
Configuração para conectar ao banco de dados remoto da VPS
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from src.main import app
from src.models.kommo_account import KommoAccount, SyncGroup
from src.services.kommo_api import KommoAPIService, KommoSyncService
import logging

# Configurar logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def setup_remote_database():
    """
    Configurar conexão com banco de dados remoto da VPS
    """
    # Configuração para PostgreSQL na VPS (se estiver usando PostgreSQL)
    # ou SQLite remoto via SSH/SCP
    
    # Opção 1: PostgreSQL na VPS
    VPS_DATABASE_URL = "postgresql://username:password@89.116.186.230:5432/kommo_sync"
    
    # Opção 2: Copiar banco SQLite da VPS
    VPS_SQLITE_PATH = "/home/sync-kommo/instance/app.db"
    LOCAL_SQLITE_PATH = os.path.join(os.path.dirname(__file__), "src", "database", "vps_app.db")
    
    logger.info("🔧 Configurando conexão com banco de dados da VPS...")
    
    # Para SQLite: copiar arquivo do VPS
    import subprocess
    
    try:
        # Copiar banco de dados da VPS via SCP
        scp_command = [
            "scp", 
            "root@89.116.186.230:/home/sync-kommo/instance/app.db",
            LOCAL_SQLITE_PATH
        ]
        
        logger.info("📥 Copiando banco de dados da VPS...")
        result = subprocess.run(scp_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Banco de dados copiado com sucesso!")
            
            # Atualizar configuração do Flask para usar o banco copiado
            app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{LOCAL_SQLITE_PATH}"
            
            return True
        else:
            logger.error(f"❌ Erro ao copiar banco: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro na configuração: {e}")
        return False

def sync_with_vps_database():
    """
    Executar sincronização usando banco de dados da VPS
    """
    logger.info("🚀 INICIANDO SINCRONIZAÇÃO COM BANCO DA VPS")
    
    # Configurar banco remoto
    if not setup_remote_database():
        logger.error("❌ Falha ao configurar banco remoto")
        return
    
    with app.app_context():
        # Buscar grupo de teste
        group = SyncGroup.query.filter_by(name='Teste').first()
        if not group:
            logger.error("❌ Grupo 'Teste' não encontrado no banco da VPS")
            return
        
        logger.info(f"📁 Grupo: {group.name} (ID: {group.id})")
        
        # Buscar contas master e slave
        master_account = group.master_account
        slave_accounts = group.slave_accounts
        
        if not slave_accounts:
            logger.error("❌ Nenhuma conta slave encontrada")
            return
        
        slave_account = slave_accounts[0]
        
        if master_account.id == slave_account.id:
            all_slaves = [s for s in slave_accounts if s.id != master_account.id]
            if all_slaves:
                slave_account = all_slaves[0]
                logger.info(f"✅ Usando conta slave diferente: {slave_account.subdomain}")
            else:
                logger.error("❌ Todas as contas slave são iguais à master")
                return
        
        logger.info(f"👤 Master: {master_account.subdomain}")
        logger.info(f"👤 Slave: {slave_account.subdomain}")
        
        # Criar instâncias das APIs
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
        
        # Executar sincronização completa
        logger.info("🔄 EXECUTANDO SINCRONIZAÇÃO COMPLETA DE FUNIS COM CORES...")
        sync_service = KommoSyncService(master_api)
        
        try:
            # Obter configuração da master primeiro
            master_config = sync_service.extract_master_configuration()
            mappings = {'pipelines': {}, 'stages': {}}
            
            result = sync_service.sync_pipelines_to_slave(
                slave_api, 
                master_config,
                mappings,
                None,  # progress_callback
                group.id, 
                slave_account.id
            )
            logger.info(f"✅ Sincronização concluída: {result}")
            
        except Exception as e:
            logger.error(f"❌ Erro na sincronização: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    sync_with_vps_database()
