#!/usr/bin/env python3
"""
Script para limpar estágios duplicados usando a mesma lógica da sincronização
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

def clean_duplicate_stages_advanced():
    """
    Limpa estágios duplicados usando chamada direta à API
    """
    logger.info("🧹 Iniciando limpeza avançada de estágios duplicados...")
    
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
        
        total_removed = 0
        
        for pipeline in pipelines:
            pipeline_id = pipeline['id']
            pipeline_name = pipeline['name']
            
            logger.info(f"\n🔄 Verificando pipeline: {pipeline_name} (ID: {pipeline_id})")
            
            # Obter estágios usando o mesmo método da sincronização
            existing_stages_list = api.get_pipeline_stages(pipeline_id)
            logger.info(f"📋 Estágios encontrados: {[(s['name'], s['id']) for s in existing_stages_list]}")
            
            # Identificar duplicados por nome
            seen_names = set()
            duplicates_to_remove = []
            
            for stage in existing_stages_list:
                stage_name = stage['name'].strip()
                stage_id = stage['id']
                
                # Se já vimos este nome antes, é um duplicado
                if stage_name in seen_names:
                    # Não remover estágios com IDs padrão (1, 142, 143)
                    if stage_id not in [1, 142, 143]:
                        duplicates_to_remove.append({
                            'id': stage_id,
                            'name': stage_name,
                            'pipeline_id': pipeline_id
                        })
                        logger.info(f"  🗑️ Duplicado marcado para remoção: '{stage_name}' (ID: {stage_id})")
                    else:
                        logger.info(f"  🛡️ Estágio duplicado protegido: '{stage_name}' (ID: {stage_id})")
                else:
                    seen_names.add(stage_name)
                    logger.debug(f"  ✅ Primeira ocorrência: '{stage_name}' (ID: {stage_id})")
            
            # Remover duplicados usando API direta
            if duplicates_to_remove:
                logger.info(f"  🧹 Removendo {len(duplicates_to_remove)} estágios...")
                
                for duplicate in duplicates_to_remove:
                    try:
                        # Usar API direta para deletar estágio
                        headers = {
                            'Authorization': f'Bearer {api.refresh_token}',
                            'Content-Type': 'application/json'
                        }
                        
                        delete_url = f'https://{account.subdomain}.kommo.com/api/v4/leads/pipelines/{duplicate["pipeline_id"]}/statuses/{duplicate["id"]}'
                        
                        response = requests.delete(delete_url, headers=headers)
                        
                        if response.status_code in [200, 204]:
                            logger.info(f"    ✅ Removido: '{duplicate['name']}'")
                            total_removed += 1
                        else:
                            logger.warning(f"    ❌ Erro ao remover '{duplicate['name']}': {response.status_code}")
                            logger.warning(f"       Resposta: {response.text}")
                        
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"    ❌ Erro ao remover '{duplicate['name']}': {e}")
            else:
                logger.info(f"  ✅ Nenhum duplicado encontrado")
        
        logger.info(f"\n✅ Limpeza concluída! {total_removed} estágios removidos")

if __name__ == '__main__':
    clean_duplicate_stages_advanced()
