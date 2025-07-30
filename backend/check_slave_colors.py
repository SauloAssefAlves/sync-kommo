#!/usr/bin/env python3
"""
Script para verificar as cores dos estágios na conta slave
"""

# Forçar o uso do código do root
import sys
import os
root_path = r'c:\Users\Assefalu\code\kommo-sync-system'
sys.path.insert(0, root_path)

from src.main import app
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_slave_colors():
    """Verificar as cores dos estágios na conta slave"""
    
    with app.app_context():
        # Buscar conta slave
        slave_account = KommoAccount.query.filter_by(subdomain='testedev').first()
        if not slave_account:
            logger.error("❌ Conta slave testedev não encontrada")
            return
        
        logger.info(f"🔍 Verificando cores da conta slave: {slave_account.subdomain}")
        
        # Criar API
        slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
        
        # Buscar todos os pipelines
        pipelines = slave_api.get_pipelines()
        logger.info(f"📋 Encontrados {len(pipelines)} pipelines na slave")
        
        for pipeline in pipelines:
            logger.info(f"\n📋 Pipeline: '{pipeline['name']}' (ID: {pipeline['id']})")
            
            # Buscar estágios do pipeline
            stages = slave_api.get_pipeline_stages(pipeline['id'])
            for stage in stages:
                stage_name = stage['name']
                stage_color = stage.get('color', 'N/A')
                stage_type = stage.get('type', 0)
                stage_id = stage['id']
                
                logger.info(f"  🎨 '{stage_name}' (ID: {stage_id}) - Cor: {stage_color} (Type: {stage_type})")

if __name__ == "__main__":
    check_slave_colors()
