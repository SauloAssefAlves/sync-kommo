#!/usr/bin/env python3
"""
Script simples para testar apenas a atualização de cores (backend)
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

def simple_color_test():
    """Teste simples para atualizar a cor de um estágio"""
    
    with app.app_context():
        # Conta slave (testedev)
        slave_account = KommoAccount.query.filter_by(subdomain='testedev').first()
        if not slave_account:
            logger.error("❌ Conta testedev não encontrada")
            return
        
        # Criar API
        slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
        
        # Buscar pipeline e estágio específico para teste
        pipelines = slave_api.get_pipelines()
        pipeline = next((p for p in pipelines if p['name'] == 'TESTE gustavo'), None)
        
        if not pipeline:
            logger.error("❌ Pipeline 'TESTE gustavo' não encontrado")
            return
        
        stages = slave_api.get_pipeline_stages(pipeline['id'])
        test_stage = next((s for s in stages if s['name'] == 'testando'), None)
        
        if not test_stage:
            logger.error("❌ Estágio 'testando' não encontrado")
            return
        
        logger.info(f"📋 Estágio encontrado: {test_stage['name']} (ID: {test_stage['id']}) - Cor atual: {test_stage.get('color', 'N/A')}")
        
        # Tentar atualizar a cor
        nova_cor = '#f9deff'  # Cor rosa claro que estava na master
        logger.info(f"🎨 Tentando atualizar cor para: {nova_cor}")
        
        try:
            # Testar o método de atualização (com 3 parâmetros: pipeline_id, stage_id, data)
            result = slave_api.update_pipeline_stage(pipeline['id'], test_stage['id'], {'color': nova_cor})
            logger.info(f"✅ Cor atualizada com sucesso: {result}")
            
            # Verificar se a cor foi realmente atualizada
            updated_stages = slave_api.get_pipeline_stages(pipeline['id'])
            updated_stage = next((s for s in updated_stages if s['name'] == 'testando'), None)
            logger.info(f"✅ Cor após atualização: {updated_stage.get('color', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar cor: {e}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    simple_color_test()
