#!/usr/bin/env python3
"""
Script para verificar as cores dos estágios na conta master
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

def check_master_colors():
    """Verificar as cores dos estágios na conta master"""
    
    with app.app_context():
        # Buscar conta master
        master_account = KommoAccount.query.filter_by(subdomain='evoresultdev').first()
        if not master_account:
            logger.error("❌ Conta master evoresultdev não encontrada")
            return
        
        logger.info(f"🔍 Verificando cores da conta master: {master_account.subdomain}")
        
        # Criar API
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        
        # Buscar todos os pipelines
        pipelines = master_api.get_pipelines()
        logger.info(f"📋 Encontrados {len(pipelines)} pipelines na master")
        
        for pipeline in pipelines:
            logger.info(f"\n📋 Pipeline: '{pipeline['name']}' (ID: {pipeline['id']})")
            
            # Buscar estágios do pipeline
            stages = master_api.get_pipeline_stages(pipeline['id'])
            for stage in stages:
                stage_name = stage['name']
                stage_color = stage.get('color', 'N/A')
                stage_type = stage.get('type', 0)
                stage_id = stage['id']
                
                logger.info(f"  🎨 '{stage_name}' (ID: {stage_id}) - Cor: {stage_color} (Type: {stage_type})")

if __name__ == "__main__":
    check_master_colors()
