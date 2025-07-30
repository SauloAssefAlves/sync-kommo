#!/usr/bin/env python3
"""
Script simplificado para limpar estágios duplicados usando a API diretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging
import time

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_duplicate_stages_in_account(account):
    """
    Limpa estágios duplicados em uma conta específica
    """
    try:
        logger.info(f"🔍 Verificando conta: {account.subdomain}")
        
        # Criar instância da API
        api = KommoAPIService(account.subdomain, account.refresh_token)
        
        # Buscar pipelines
        pipelines = api.get_pipelines()
        logger.info(f"📋 Encontrados {len(pipelines)} pipelines")
        
        total_removed = 0
        
        for pipeline in pipelines:
            pipeline_id = pipeline['id']
            pipeline_name = pipeline['name']
            
            logger.info(f"\n🔄 Verificando pipeline: {pipeline_name} (ID: {pipeline_id})")
            
            # Buscar estágios do pipeline
            stages = api.get_pipeline_stages(pipeline_id)
            if not stages:
                logger.warning(f"⚠️ Não foi possível obter estágios do pipeline {pipeline_name}")
                continue
            
            # Identificar estágios problemáticos
            duplicates_to_remove = []
            
            for stage in stages:
                stage_name = stage['name'].strip()
                stage_id = stage['id']
                
                # Padrões de estágios duplicados/problemáticos
                problematic_patterns = [
                    'Closed - won',
                    'Closed - lost', 
                    'INCOMING LEADS',
                    'CLOSED - WON',
                    'CLOSED - LOST'
                ]
                
                # Verificar se é um estágio problemático
                is_problematic = any(pattern in stage_name for pattern in problematic_patterns)
                
                # Mas não remover se for um dos IDs padrão do sistema (1, 142, 143)
                if is_problematic and stage_id not in [1, 142, 143]:
                    duplicates_to_remove.append({
                        'id': stage_id,
                        'name': stage_name
                    })
                    logger.info(f"  🗑️ Marcando para remoção: '{stage_name}' (ID: {stage_id})")
            
            # Remover os duplicados
            if duplicates_to_remove:
                logger.info(f"  🧹 Removendo {len(duplicates_to_remove)} estágios duplicados...")
                
                for duplicate in duplicates_to_remove:
                    try:
                        result = api.delete_pipeline_stage(duplicate['id'])
                        
                        if result.get('success') or result.get('status_code') in [200, 204] or not result.get('error'):
                            logger.info(f"    ✅ Removido: '{duplicate['name']}'")
                            total_removed += 1
                        else:
                            logger.warning(f"    ⚠️ Falha ao remover '{duplicate['name']}': {result}")
                        
                        # Delay para evitar rate limit
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"    ❌ Erro ao remover '{duplicate['name']}': {e}")
            else:
                logger.info(f"  ✅ Nenhum duplicado encontrado no pipeline '{pipeline_name}'")
        
        logger.info(f"✅ Conta {account.subdomain}: {total_removed} estágios duplicados removidos")
        return total_removed
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar conta {account.subdomain}: {e}")
        return 0

def main():
    """Função principal para limpar estágios duplicados"""
    logger.info("🧹 Iniciando limpeza de estágios duplicados...")
    
    with app.app_context():
        # Buscar todas as contas slaves
        accounts = KommoAccount.query.filter_by(is_master=False).all()
        
        if not accounts:
            logger.warning("⚠️ Nenhuma conta slave encontrada no banco de dados")
            return
        
        logger.info(f"📋 {len(accounts)} contas slaves encontradas")
        
        total_removed = 0
        
        # Processar cada conta slave
        for account in accounts:
            removed = clean_duplicate_stages_in_account(account)
            total_removed += removed
        
        logger.info(f"\n✅ Limpeza concluída! {total_removed} estágios duplicados removidos no total")

if __name__ == '__main__':
    main()
