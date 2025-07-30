#!/usr/bin/env python3
"""
Script para corrigir mapeamento de estágios para IDs padrão do Kommo
Remove estágios duplicados e mapeia corretamente para os IDs padrão (1, 142, 143)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging
import time
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_stage_mappings():
    """
    Corrige mapeamento de estágios para IDs padrão do Kommo
    """
    logger.info("🔧 Iniciando correção de mapeamento de estágios...")
    
    with app.app_context():
        # Buscar conta slave
        account = KommoAccount.query.filter_by(is_master=False).first()
        
        if not account:
            logger.error("❌ Nenhuma conta slave encontrada")
            return
        
        logger.info(f"🔍 Processando conta: {account.subdomain}")
        
        # Criar instância da API
        api = KommoAPIService(account.subdomain, account.refresh_token)
        
        # Buscar pipelines
        pipelines = api.get_pipelines()
        
        total_fixed = 0
        
        for pipeline in pipelines:
            pipeline_id = pipeline['id']
            pipeline_name = pipeline['name']
            
            logger.info(f"\n🔄 Corrigindo pipeline: {pipeline_name} (ID: {pipeline_id})")
            
            # Obter estágios
            existing_stages_list = api.get_pipeline_stages(pipeline_id)
            
            # Mapear estágios por nome e tipo
            stages_by_name = {}
            incoming_stages = []
            won_stages = []
            lost_stages = []
            
            for stage in existing_stages_list:
                stage_name = stage['name'].strip().lower()
                stage_id = stage['id']
                stage_type = stage.get('type', 0)
                is_editable = stage.get('is_editable', True)
                
                logger.info(f"  📋 Estágio: '{stage['name']}' (ID: {stage_id}, Type: {stage_type}, Editable: {is_editable})")
                
                # Identificar estágios de entrada (type=1)
                if (stage_name in ['incoming leads', 'etapa de leads de entrada', 'leads de entrada'] or 
                    stage_type == 1):
                    incoming_stages.append(stage)
                
                # Identificar estágios de vitória
                elif (stage_name in ['venda ganha', 'fechado - ganho', 'closed - won', 'won', 'ganho'] or
                      stage_id == 142):
                    won_stages.append(stage)
                
                # Identificar estágios de perda
                elif (stage_name in ['venda perdida', 'fechado - perdido', 'closed - lost', 'lost', 'perdido'] or
                      stage_id == 143):
                    lost_stages.append(stage)
            
            # Corrigir duplicações
            stages_to_remove = []
            
            # 1. Corrigir estágios de entrada - manter apenas o com ID 1 ou o primeiro
            logger.info(f"  🔍 Encontrados {len(incoming_stages)} estágios de entrada")
            if len(incoming_stages) > 1:
                # Procurar um com ID 1
                id_1_stage = next((s for s in incoming_stages if s['id'] == 1), None)
                if id_1_stage:
                    # Remover todos exceto o ID 1
                    stages_to_remove.extend([s for s in incoming_stages if s['id'] != 1])
                    logger.info(f"    ✅ Mantendo estágio de entrada com ID 1")
                else:
                    # Manter o primeiro, remover o resto
                    stages_to_remove.extend(incoming_stages[1:])
                    logger.info(f"    ✅ Mantendo primeiro estágio de entrada (ID: {incoming_stages[0]['id']})")
            
            # 2. Corrigir estágios de vitória - manter apenas o com ID 142
            logger.info(f"  🔍 Encontrados {len(won_stages)} estágios de vitória")
            if len(won_stages) > 1:
                # Remover todos exceto o ID 142
                stages_to_remove.extend([s for s in won_stages if s['id'] != 142])
                logger.info(f"    ✅ Mantendo apenas 'Closed - won' (ID: 142)")
            
            # 3. Corrigir estágios de perda - manter apenas o com ID 143
            logger.info(f"  🔍 Encontrados {len(lost_stages)} estágios de perda")
            if len(lost_stages) > 1:
                # Remover todos exceto o ID 143
                stages_to_remove.extend([s for s in lost_stages if s['id'] != 143])
                logger.info(f"    ✅ Mantendo apenas 'Closed - lost' (ID: 143)")
            
            # Remover estágios duplicados
            if stages_to_remove:
                logger.info(f"  🧹 Removendo {len(stages_to_remove)} estágios duplicados...")
                
                for stage in stages_to_remove:
                    try:
                        headers = {
                            'Authorization': f'Bearer {api.refresh_token}',
                            'Content-Type': 'application/json'
                        }
                        
                        delete_url = f'https://{account.subdomain}.kommo.com/api/v4/leads/pipelines/{pipeline_id}/statuses/{stage["id"]}'
                        
                        response = requests.delete(delete_url, headers=headers)
                        
                        if response.status_code in [200, 204]:
                            logger.info(f"    ✅ Removido: '{stage['name']}' (ID: {stage['id']})")
                            total_fixed += 1
                        else:
                            logger.warning(f"    ❌ Erro ao remover '{stage['name']}': {response.status_code}")
                            if response.text:
                                logger.warning(f"       Resposta: {response.text}")
                        
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"    ❌ Erro ao remover '{stage['name']}': {e}")
            else:
                logger.info(f"  ✅ Nenhuma correção necessária")
        
        logger.info(f"\n✅ Correção concluída! {total_fixed} estágios corrigidos")

if __name__ == '__main__':
    fix_stage_mappings()
