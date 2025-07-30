#!/usr/bin/env python3
"""
Script para excluir pipelines específicos das contas master e slave
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup
from src.services.kommo_api import KommoAPIService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_pipelines(account):
    """Lista todos os pipelines de uma conta"""
    try:
        api = KommoAPIService(
            client_id=account.client_id,
            client_secret=account.client_secret,
            redirect_uri=account.redirect_uri,
            access_token=account.access_token,
            refresh_token=account.refresh_token,
            base_domain=account.subdomain
        )
        
        pipelines = api.get_pipelines()
        logger.info(f"📊 Conta {account.subdomain} ({account.role}) - {len(pipelines)} pipelines encontrados:")
        
        for pipeline in pipelines:
            logger.info(f"  - ID: {pipeline['id']}, Nome: '{pipeline['name']}', Principal: {pipeline.get('is_main', False)}")
        
        return api, pipelines
    except Exception as e:
        logger.error(f"❌ Erro ao listar pipelines da conta {account.subdomain}: {e}")
        return None, []

def delete_pipeline_by_name(api, pipelines, pipeline_name, account_subdomain):
    """Exclui um pipeline específico pelo nome"""
    try:
        # Encontrar o pipeline pelo nome
        target_pipeline = None
        for pipeline in pipelines:
            if pipeline['name'].lower() == pipeline_name.lower():
                target_pipeline = pipeline
                break
        
        if not target_pipeline:
            logger.warning(f"⚠️ Pipeline '{pipeline_name}' não encontrado na conta {account_subdomain}")
            return False
        
        # Verificar se não é o pipeline principal
        if target_pipeline.get('is_main', False):
            logger.error(f"❌ Não é possível excluir o pipeline principal '{pipeline_name}' da conta {account_subdomain}")
            return False
        
        # Excluir o pipeline
        pipeline_id = target_pipeline['id']
        logger.info(f"🗑️ Excluindo pipeline '{pipeline_name}' (ID: {pipeline_id}) da conta {account_subdomain}...")
        
        response = api.delete_pipeline(pipeline_id)
        
        if response.get('success') or response.get('status_code') in [200, 204]:
            logger.info(f"✅ Pipeline '{pipeline_name}' excluído com sucesso da conta {account_subdomain}")
            return True
        else:
            logger.warning(f"⚠️ Resposta inesperada ao excluir pipeline '{pipeline_name}': {response}")
            return True  # Considerar como sucesso mesmo com resposta inesperada
        
    except Exception as e:
        error_str = str(e).lower()
        if any(phrase in error_str for phrase in ['not found', '404', 'does not exist']):
            logger.info(f"ℹ️ Pipeline '{pipeline_name}' já foi removido ou não existe na conta {account_subdomain}")
            return True
        else:
            logger.error(f"❌ Erro ao excluir pipeline '{pipeline_name}' da conta {account_subdomain}: {e}")
            return False

def main():
    """Função principal para excluir pipelines de teste"""
    # Pipelines a serem excluídos
    pipelines_to_delete = ["funil teste", "teste 2"]
    
    logger.info("🚀 Iniciando exclusão de pipelines de teste...")
    logger.info(f"🎯 Pipelines a excluir: {pipelines_to_delete}")
    
    # Obter todas as contas
    accounts = get_all_accounts()
    
    if not accounts:
        logger.error("❌ Nenhuma conta encontrada no banco de dados")
        return
    
    logger.info(f"📋 {len(accounts)} contas encontradas no sistema")
    
    total_deleted = 0
    
    # Processar cada conta
    for account in accounts:
        logger.info(f"\n🔄 Processando conta: {account.subdomain} ({account.role})")
        
        # Listar pipelines existentes
        api, pipelines = list_pipelines(account)
        
        if not api:
            logger.error(f"❌ Falha ao conectar com a conta {account.subdomain}")
            continue
        
        # Tentar excluir cada pipeline de teste
        for pipeline_name in pipelines_to_delete:
            if delete_pipeline_by_name(api, pipelines, pipeline_name, account.subdomain):
                total_deleted += 1
    
    logger.info(f"\n✅ Processo concluído! {total_deleted} pipelines excluídos no total")

if __name__ == "__main__":
    main()
