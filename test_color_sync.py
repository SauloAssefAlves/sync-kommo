#!/usr/bin/env python3
"""
Script para testar se as cores dos status da master estão sendo sincronizadas corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup
from src.services.kommo_api import KommoAPIService, KommoSyncService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_color_sync():
    """
    Testa se as cores dos estágios estão sendo sincronizadas corretamente
    """
    logger.info("🎨 Testando sincronização de cores dos estágios...")
    
    with app.app_context():
        # Buscar contas master e slave
        master_account = KommoAccount.query.filter_by(is_master=True).first()
        slave_accounts = KommoAccount.query.filter_by(is_master=False).all()
        
        if not master_account:
            logger.error("❌ Conta master não encontrada")
            return
            
        if not slave_accounts:
            logger.error("❌ Nenhuma conta slave encontrada")
            return
        
        logger.info(f"🔍 Master: {master_account.subdomain}")
        logger.info(f"🔍 Slaves: {[acc.subdomain for acc in slave_accounts]}")
        
        # Criar instâncias da API
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        sync_service = KommoSyncService(master_api)
        
        # Extrair configuração da master
        logger.info("📊 Extraindo configuração da master...")
        master_config = sync_service.extract_master_configuration()
        
        # Mostrar cores dos pipelines da master
        logger.info("\n🎨 CORES DOS ESTÁGIOS NA MASTER:")
        for pipeline in master_config['pipelines']:
            logger.info(f"📋 Pipeline: {pipeline['name']}")
            for stage in pipeline['stages']:
                logger.info(f"  🎯 Estágio: {stage['name']} - Cor: {stage['color']}")
        
        # Testar sincronização com uma conta slave
        if slave_accounts:
            slave_account = slave_accounts[0]  # Usar primeira slave para teste
            logger.info(f"\n🔄 Testando sincronização com: {slave_account.subdomain}")
            
            slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
            
            if not slave_api.test_connection():
                logger.error(f"❌ Falha na conexão com a conta slave {slave_account.subdomain}")
                return
            
            # Executar sincronização de pipelines
            logger.info("🚀 Iniciando sincronização de pipelines...")
            mappings = {'pipelines': {}, 'stages': {}}
            
            try:
                results = sync_service.sync_pipelines_to_slave(
                    slave_api, 
                    master_config, 
                    mappings
                )
                
                logger.info(f"📊 Resultados da sincronização: {results}")
                
                # Verificar se as cores foram aplicadas corretamente
                logger.info("\n✅ Verificando cores aplicadas na slave...")
                slave_pipelines = slave_api.get_pipelines()
                
                for slave_pipeline in slave_pipelines:
                    # Encontrar pipeline correspondente na master
                    master_pipeline = None
                    for mp in master_config['pipelines']:
                        if mp['name'] == slave_pipeline['name']:
                            master_pipeline = mp
                            break
                    
                    if master_pipeline:
                        logger.info(f"📋 Verificando pipeline: {slave_pipeline['name']}")
                        slave_stages = slave_api.get_pipeline_stages(slave_pipeline['id'])
                        
                        for slave_stage in slave_stages:
                            # Encontrar estágio correspondente na master
                            master_stage = None
                            for ms in master_pipeline['stages']:
                                if ms['name'] == slave_stage['name']:
                                    master_stage = ms
                                    break
                            
                            if master_stage:
                                master_color = master_stage['color']
                                slave_color = slave_stage.get('color', 'N/A')
                                match = master_color == slave_color
                                status = "✅" if match else "❌"
                                logger.info(f"  {status} {slave_stage['name']}: Master={master_color} | Slave={slave_color}")
                            else:
                                logger.info(f"  ⚠️ Estágio '{slave_stage['name']}' não encontrado na master")
                
            except Exception as e:
                logger.error(f"❌ Erro durante sincronização: {e}")
                
        logger.info("\n✅ Teste de sincronização de cores concluído!")

if __name__ == "__main__":
    test_color_sync()
