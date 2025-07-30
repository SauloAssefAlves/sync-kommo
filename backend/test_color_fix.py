#!/usr/bin/env python3
"""
Teste específico para corrigir uma cor inválida
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

def test_color_fix():
    """Testar correção de cor inválida"""
    
    with app.app_context():
        # Conta slave (testedev)
        slave_account = KommoAccount.query.filter_by(subdomain='testedev').first()
        if not slave_account:
            logger.error("❌ Conta testedev não encontrada")
            return
        
        # Criar API
        slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
        
        # Buscar pipeline "Funil de vendas" que tem cores inválidas
        pipelines = slave_api.get_pipelines()
        pipeline = next((p for p in pipelines if p['name'] == 'Funil de vendas'), None)
        
        if not pipeline:
            logger.error("❌ Pipeline 'Funil de vendas' não encontrado")
            return
        
        # Buscar estágio "Contato inicial" que tem cor inválida #99ccff
        stages = slave_api.get_pipeline_stages(pipeline['id'])
        target_stage = next((s for s in stages if s['name'] == 'Contato inicial'), None)
        
        if not target_stage:
            logger.error("❌ Estágio 'Contato inicial' não encontrado")
            return
        
        logger.info(f"📋 Estágio encontrado: {target_stage['name']} (ID: {target_stage['id']}) - Cor atual: {target_stage.get('color', 'N/A')}")
        
        # Tentar atualizar para a cor correta #98cbff (válida)
        nova_cor_valida = '#98cbff'  # Cor válida equivalente
        logger.info(f"🎨 Tentando atualizar cor inválida #99ccff para cor válida: {nova_cor_valida}")
        
        try:
            result = slave_api.update_pipeline_stage(pipeline['id'], target_stage['id'], {'color': nova_cor_valida})
            logger.info(f"✅ Cor atualizada com sucesso: {result.get('color', 'N/A')}")
            
            # Verificar se a cor foi realmente atualizada
            updated_stages = slave_api.get_pipeline_stages(pipeline['id'])
            updated_stage = next((s for s in updated_stages if s['name'] == 'Contato inicial'), None)
            logger.info(f"✅ Cor após atualização: {updated_stage.get('color', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar cor: {e}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_color_fix()
