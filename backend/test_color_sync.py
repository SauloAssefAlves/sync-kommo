#!/usr/bin/env python3
"""
Script para testar a sincronização de cores entre master e slave
"""

import sys
import os
# Adicionar pasta root para acesso ao banco principal
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.models.kommo_account import KommoAccount, SyncGroup
from src.services.kommo_api import KommoAPIService, KommoSyncService
import logging

# Configurar logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

def test_color_sync():
    """Testa sincronização de cores de pipeline"""
    logger.info("=== TESTE DE SINCRONIZAÇÃO DE CORES ===")
    
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
        
        logger.info(f"👤 Master: {master_account.subdomain}")
        logger.info(f"👤 Slave: {slave_account.subdomain}")
        
        # Criar instâncias das APIs
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
        
        logger.info("\n🔍 VERIFICANDO CORES DOS PIPELINES MASTER:")
        master_pipelines = master_api.get_pipelines()
        for pipeline in master_pipelines:
            logger.info(f"\n📋 Pipeline Master: {pipeline['name']} (ID: {pipeline['id']})")
            stages = master_api.get_pipeline_stages(pipeline['id'])
            for stage in stages:
                color = stage.get('color', 'N/A')
                stage_type = stage.get('type', 0)
                logger.info(f"  🎨 Estágio: '{stage['name']}' - Cor: {color} (Type: {stage_type})")
        
        logger.info("\n🔍 VERIFICANDO CORES DOS PIPELINES SLAVE (ANTES):")
        slave_pipelines = slave_api.get_pipelines()
        for pipeline in slave_pipelines:
            logger.info(f"\n📋 Pipeline Slave: {pipeline['name']} (ID: {pipeline['id']})")
            stages = slave_api.get_pipeline_stages(pipeline['id'])
            for stage in stages:
                color = stage.get('color', 'N/A')
                stage_type = stage.get('type', 0)
                logger.info(f"  🎨 Estágio: '{stage['name']}' - Cor: {color} (Type: {stage_type})")
        
        # Executar sincronização com logs detalhados
        logger.info("\n🔄 EXECUTANDO SINCRONIZAÇÃO COM CORES...")
        sync_service = KommoSyncService()
        
        try:
            result = sync_service.sync_pipelines_to_slave(
                master_api, 
                slave_api, 
                group.id, 
                slave_account.id
            )
            logger.info(f"✅ Sincronização concluída: {result}")
        except Exception as e:
            logger.error(f"❌ Erro na sincronização: {e}")
            return
        
        logger.info("\n🔍 VERIFICANDO CORES DOS PIPELINES SLAVE (DEPOIS):")
        slave_pipelines = slave_api.get_pipelines()
        for pipeline in slave_pipelines:
            logger.info(f"\n📋 Pipeline Slave: {pipeline['name']} (ID: {pipeline['id']})")
            stages = slave_api.get_pipeline_stages(pipeline['id'])
            for stage in stages:
                color = stage.get('color', 'N/A')
                stage_type = stage.get('type', 0)
                logger.info(f"  🎨 Estágio: '{stage['name']}' - Cor: {color} (Type: {stage_type})")
        
        logger.info("\n✅ TESTE DE CORES CONCLUÍDO!")

if __name__ == "__main__":
    test_color_sync()
