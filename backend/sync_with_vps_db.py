#!/usr/bin/env python3
"""
Script para copiar banco da VPS e executar sincronização localmente
"""

import subprocess
import os
import logging
import sys
import shutil
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def copy_vps_database():
    """
    Copiar banco de dados da VPS para uso local
    """
    logger.info("📥 Copiando banco de dados da VPS...")
    
    # Caminhos
    vps_db_path = "/home/sync-kommo/instance/app.db"
    local_db_dir = os.path.join(os.path.dirname(__file__), "src", "database")
    local_db_path = os.path.join(local_db_dir, "vps_app.db")
    
    # Criar diretório se não existir
    Path(local_db_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Comando SCP para copiar o banco
        scp_command = [
            "scp",
            f"root@89.116.186.230:{vps_db_path}",
            local_db_path
        ]
        
        logger.info(f"📡 Executando: {' '.join(scp_command)}")
        result = subprocess.run(scp_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ Banco copiado para: {local_db_path}")
            return local_db_path
        else:
            logger.error(f"❌ Erro no SCP: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro ao copiar banco: {e}")
        return None

def run_sync_with_vps_database():
    """
    Executar sincronização usando banco copiado da VPS
    """
    logger.info("🚀 EXECUTANDO SINCRONIZAÇÃO COM BANCO DA VPS...")
    
    # Copiar banco da VPS
    local_db_path = copy_vps_database()
    if not local_db_path:
        logger.error("❌ Falha ao copiar banco da VPS")
        return
    
    # Atualizar configuração temporariamente
    original_db_path = os.path.join(os.path.dirname(__file__), "src", "database", "app.db")
    backup_db_path = os.path.join(os.path.dirname(__file__), "src", "database", "app_backup.db")
    
    try:
        # Fazer backup do banco local se existir
        if os.path.exists(original_db_path):
            shutil.copy2(original_db_path, backup_db_path)
            logger.info("📋 Backup do banco local criado")
        
        # Usar banco da VPS
        shutil.copy2(local_db_path, original_db_path)
        logger.info("🔄 Banco da VPS configurado")
        
        # Executar sincronização
        logger.info("🔄 Iniciando sincronização...")
        
        # Importar e executar
        sys.path.append(os.path.dirname(__file__))
        from src.main import app
        from src.models.kommo_account import KommoAccount, SyncGroup
        from src.services.kommo_api import KommoAPIService, KommoSyncService
        
        with app.app_context():
            # Buscar grupo de teste
            group = SyncGroup.query.filter_by(name='Teste').first()
            if not group:
                logger.error("❌ Grupo 'Teste' não encontrado")
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
    
    finally:
        # Restaurar banco original
        if os.path.exists(backup_db_path):
            shutil.copy2(backup_db_path, original_db_path)
            os.remove(backup_db_path)
            logger.info("🔄 Banco local restaurado")
        
        # Limpar arquivo temporário
        if os.path.exists(local_db_path):
            os.remove(local_db_path)
            logger.info("🧹 Arquivo temporário removido")

if __name__ == "__main__":
    run_sync_with_vps_database()
