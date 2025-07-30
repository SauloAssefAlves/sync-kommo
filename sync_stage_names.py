#!/usr/bin/env python3
"""
Script para sincronizar nomes dos estágios automáticos do sistema (type=1, ID=142, ID=143)
com os nomes correspondentes da conta master
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_system_stage_names():
    """
    Sincroniza nomes dos estágios automáticos do sistema com a master
    """
    logger.info("🔄 Iniciando sincronização de nomes dos estágios do sistema...")
    
    with app.app_context():
        # Buscar contas master e slave
        master_account = KommoAccount.query.filter_by(is_master=True).first()
        slave_account = KommoAccount.query.filter_by(is_master=False).first()
        
        if not master_account or not slave_account:
            logger.error("❌ Conta master ou slave não encontrada")
            return
        
        logger.info(f"🔍 Master: {master_account.subdomain}")
        logger.info(f"🔍 Slave: {slave_account.subdomain}")
        
        # Criar instâncias da API
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
        
        # Buscar pipelines da master e slave
        master_pipelines = master_api.get_pipelines()
        slave_pipelines = slave_api.get_pipelines()
        
        logger.info(f"📋 Master tem {len(master_pipelines)} pipelines")
        logger.info(f"📋 Slave tem {len(slave_pipelines)} pipelines")
        
        total_updated = 0
        
        # Para cada pipeline da slave, encontrar o correspondente na master
        for slave_pipeline in slave_pipelines:
            slave_pipeline_id = slave_pipeline['id']
            slave_pipeline_name = slave_pipeline['name'].strip()
            
            # Encontrar pipeline correspondente na master pelo nome
            master_pipeline = None
            for mp in master_pipelines:
                if mp['name'].strip().lower() == slave_pipeline_name.lower():
                    master_pipeline = mp
                    break
            
            if not master_pipeline:
                logger.warning(f"⚠️ Pipeline '{slave_pipeline_name}' não encontrado na master")
                continue
            
            logger.info(f"\n🔄 Sincronizando estágios do pipeline: {slave_pipeline_name}")
            
            # Obter estágios da master e slave
            master_stages = master_api.get_pipeline_stages(master_pipeline['id'])
            slave_stages = slave_api.get_pipeline_stages(slave_pipeline_id)
            
            # Mapear estágios especiais da master
            master_incoming_name = None
            master_won_name = None
            master_lost_name = None
            
            for stage in master_stages:
                if stage.get('type') == 1:  # Incoming leads
                    master_incoming_name = stage['name']
                elif stage.get('id') == 142:  # Won
                    master_won_name = stage['name']
                elif stage.get('id') == 143:  # Lost
                    master_lost_name = stage['name']
            
            logger.info(f"  📋 Master - Incoming: '{master_incoming_name}'")
            logger.info(f"  📋 Master - Won: '{master_won_name}'")
            logger.info(f"  📋 Master - Lost: '{master_lost_name}'")
            
            # Atualizar estágios especiais na slave
            for stage in slave_stages:
                stage_id = stage['id']
                stage_name = stage['name']
                stage_type = stage.get('type', 0)
                
                new_name = None
                
                # Verificar se precisa atualizar o nome
                if stage_type == 1 and master_incoming_name and stage_name != master_incoming_name:
                    new_name = master_incoming_name
                    logger.info(f"  🔄 Type 1: '{stage_name}' → '{new_name}'")
                    
                elif stage_id == 142 and master_won_name and stage_name != master_won_name:
                    new_name = master_won_name
                    logger.info(f"  🔄 ID 142: '{stage_name}' → '{new_name}'")
                    
                elif stage_id == 143 and master_lost_name and stage_name != master_lost_name:
                    new_name = master_lost_name
                    logger.info(f"  🔄 ID 143: '{stage_name}' → '{new_name}'")
                
                # Atualizar o nome se necessário
                if new_name:
                    try:
                        headers = {
                            'Authorization': f'Bearer {slave_api.refresh_token}',
                            'Content-Type': 'application/json'
                        }
                        
                        update_data = {
                            'name': new_name
                        }
                        
                        update_url = f'https://{slave_account.subdomain}.kommo.com/api/v4/leads/pipelines/{slave_pipeline_id}/statuses/{stage_id}'
                        
                        response = requests.patch(update_url, json=update_data, headers=headers)
                        
                        if response.status_code in [200, 204]:
                            logger.info(f"    ✅ Atualizado: '{stage_name}' → '{new_name}'")
                            total_updated += 1
                        else:
                            logger.warning(f"    ❌ Erro ao atualizar '{stage_name}': {response.status_code}")
                            if response.text:
                                logger.warning(f"       Resposta: {response.text}")
                                
                    except Exception as e:
                        logger.error(f"    ❌ Erro ao atualizar estágio '{stage_name}': {e}")
        
        logger.info(f"\n✅ Sincronização concluída! {total_updated} estágios renomeados")

if __name__ == '__main__':
    sync_system_stage_names()
