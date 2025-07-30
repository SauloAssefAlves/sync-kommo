#!/usr/bin/env python3
"""
Script para executar sincronização diretamente na VPS via SSH
"""

import subprocess
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def run_sync_on_vps():
    """
    Executar sincronização diretamente na VPS via SSH
    """
    logger.info("🚀 EXECUTANDO SINCRONIZAÇÃO NA VPS...")
    
    # Comando para executar na VPS
    vps_command = """
cd /home/sync-kommo && python3 -c "
import sys
sys.path.append('.')
from src.main import app
from src.models.kommo_account import KommoAccount, SyncGroup
from src.services.kommo_api import KommoAPIService, KommoSyncService
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

with app.app_context():
    # Buscar grupo de teste
    group = SyncGroup.query.filter_by(name='Teste').first()
    if not group:
        logger.error('❌ Grupo Teste não encontrado')
        exit(1)
    
    logger.info(f'📁 Grupo: {group.name} (ID: {group.id})')
    
    # Buscar contas master e slave
    master_account = group.master_account
    slave_accounts = group.slave_accounts
    
    if not slave_accounts:
        logger.error('❌ Nenhuma conta slave encontrada')
        exit(1)
    
    slave_account = slave_accounts[0]
    
    if master_account.id == slave_account.id:
        all_slaves = [s for s in slave_accounts if s.id != master_account.id]
        if all_slaves:
            slave_account = all_slaves[0]
            logger.info(f'✅ Usando conta slave diferente: {slave_account.subdomain}')
        else:
            logger.error('❌ Todas as contas slave são iguais à master')
            exit(1)
    
    logger.info(f'👤 Master: {master_account.subdomain}')
    logger.info(f'👤 Slave: {slave_account.subdomain}')
    
    # Criar instâncias das APIs
    master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
    slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
    
    # Executar sincronização completa
    logger.info('🔄 EXECUTANDO SINCRONIZAÇÃO COMPLETA DE FUNIS COM CORES...')
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
        logger.info(f'✅ Sincronização concluída: {result}')
    except Exception as e:
        logger.error(f'❌ Erro na sincronização: {e}')
        import traceback
        logger.error(f'Traceback: {traceback.format_exc()}')
"
"""
    
    try:
        logger.info("📡 Conectando à VPS via SSH...")
        
        # Executar comando na VPS via SSH
        ssh_command = [
            "ssh", 
            "root@89.116.186.230",
            vps_command
        ]
        
        result = subprocess.run(
            ssh_command, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minutos de timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Comando executado com sucesso na VPS!")
            logger.info("📤 SAÍDA:")
            print(result.stdout)
        else:
            logger.error(f"❌ Erro na execução: {result.stderr}")
            if result.stdout:
                logger.info(f"Saída parcial: {result.stdout}")
                
    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout na execução do comando SSH")
    except Exception as e:
        logger.error(f"❌ Erro na conexão SSH: {e}")

def check_vps_status():
    """
    Verificar status do serviço na VPS
    """
    logger.info("🔍 Verificando status da VPS...")
    
    try:
        # Verificar se o serviço está rodando
        status_command = [
            "ssh", 
            "root@89.116.186.230",
            "pm2 status sync-kommo"
        ]
        
        result = subprocess.run(status_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Status do serviço:")
            print(result.stdout)
        else:
            logger.warning(f"⚠️ Possível problema no serviço: {result.stderr}")
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Executar sincronização na VPS")
    parser.add_argument("--status", action="store_true", help="Verificar apenas o status")
    parser.add_argument("--sync", action="store_true", help="Executar sincronização")
    
    args = parser.parse_args()
    
    if args.status:
        check_vps_status()
    elif args.sync:
        run_sync_on_vps()
    else:
        # Por padrão, executar sincronização
        run_sync_on_vps()
