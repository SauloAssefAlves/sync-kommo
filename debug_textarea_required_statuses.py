#!/usr/bin/env python3
"""
Script específico para diagnosticar problemas com campos de texto longo e required_statuses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging

# Configurar logging detalhado
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_textarea_fields():
    """
    Debug específico para campos de texto longo com required_statuses
    """
    logger.info("🔍 DEBUG: Investigando campos de texto longo com required_statuses")
    
    with app.app_context():
        # Buscar contas
        master_account = KommoAccount.query.filter_by(is_master=True).first()
        slave_accounts = KommoAccount.query.filter_by(is_master=False).all()
        
        if not master_account or not slave_accounts:
            logger.error("❌ Contas não encontradas")
            return
        
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        
        logger.info("🔍 STEP 1: Verificando campos de texto longo na MASTER...")
        
        try:
            master_fields = master_api.get_custom_fields()
            textarea_fields = []
            
            for field in master_fields:
                if field.get('type') == 'textarea':
                    textarea_fields.append(field)
            
            logger.info(f"✅ Encontrados {len(textarea_fields)} campos de texto longo na master")
            
            if not textarea_fields:
                logger.info("ℹ️ Nenhum campo de texto longo encontrado")
                return
            
            # Analisar cada campo
            for field in textarea_fields:
                field_name = field.get('name', 'Sem nome')
                field_id = field.get('id')
                required_statuses = field.get('required_statuses', [])
                
                logger.info(f"\n📝 CAMPO: '{field_name}' (ID: {field_id})")
                logger.info(f"   Tipo: {field.get('type')}")
                logger.info(f"   Código: {field.get('code', 'Sem código')}")
                logger.info(f"   Required statuses: {len(required_statuses)}")
                
                if required_statuses:
                    logger.info(f"   📋 Required statuses detalhados:")
                    for i, rs in enumerate(required_statuses, 1):
                        pipeline_id = rs.get('pipeline_id')
                        status_id = rs.get('status_id')
                        logger.info(f"      {i}. Pipeline ID: {pipeline_id}, Status ID: {status_id}")
                        
                        # Verificar se existem na master
                        try:
                            master_pipelines = master_api.get_pipelines()
                            pipeline_exists = any(p['id'] == pipeline_id for p in master_pipelines)
                            
                            if pipeline_exists:
                                pipeline_name = next(p['name'] for p in master_pipelines if p['id'] == pipeline_id)
                                logger.info(f"         ✅ Pipeline '{pipeline_name}' existe na master")
                                
                                master_stages = master_api.get_pipeline_stages(pipeline_id)
                                status_exists = any(s['id'] == status_id for s in master_stages)
                                
                                if status_exists:
                                    status_name = next(s['name'] for s in master_stages if s['id'] == status_id)
                                    logger.info(f"         ✅ Status '{status_name}' existe na master")
                                else:
                                    logger.error(f"         ❌ Status {status_id} NÃO existe na master!")
                            else:
                                logger.error(f"         ❌ Pipeline {pipeline_id} NÃO existe na master!")
                                
                        except Exception as check_error:
                            logger.error(f"         ❌ Erro ao verificar: {check_error}")
                else:
                    logger.info(f"   ℹ️ Campo sem required_statuses específicos")
            
            # STEP 2: Verificar nas escravas
            logger.info(f"\n🔍 STEP 2: Verificando correspondência nas SLAVES...")
            
            for slave_account in slave_accounts:
                logger.info(f"\n🔸 Analisando slave: {slave_account.subdomain}")
                slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
                
                if not slave_api.test_connection():
                    logger.warning(f"   ⚠️ Conexão falhou com {slave_account.subdomain}")
                    continue
                
                try:
                    slave_fields = slave_api.get_custom_fields()
                    slave_pipelines = slave_api.get_pipelines()
                    
                    logger.info(f"   📊 Slave tem {len(slave_fields)} campos e {len(slave_pipelines)} pipelines")
                    
                    # Verificar cada campo de texto longo
                    for master_field in textarea_fields:
                        master_field_name = master_field.get('name')
                        master_required_statuses = master_field.get('required_statuses', [])
                        
                        # Procurar campo correspondente na slave
                        slave_field = next((f for f in slave_fields if f.get('name') == master_field_name), None)
                        
                        if slave_field:
                            slave_required_statuses = slave_field.get('required_statuses', [])
                            logger.info(f"   📝 Campo '{master_field_name}' encontrado na slave:")
                            logger.info(f"      Master required_statuses: {len(master_required_statuses)}")
                            logger.info(f"      Slave required_statuses: {len(slave_required_statuses)}")
                            
                            # Comparar required_statuses
                            if master_required_statuses and not slave_required_statuses:
                                logger.warning(f"      ⚠️ Campo na slave NÃO tem required_statuses que existem na master")
                                logger.info(f"      🔍 Investigando mapeamento necessário...")
                                
                                for rs in master_required_statuses:
                                    master_pipeline_id = rs.get('pipeline_id')
                                    master_status_id = rs.get('status_id')
                                    
                                    # Encontrar pipeline correspondente na slave por nome
                                    master_pipelines = master_api.get_pipelines()
                                    master_pipeline = next((p for p in master_pipelines if p['id'] == master_pipeline_id), None)
                                    
                                    if master_pipeline:
                                        slave_pipeline = next((p for p in slave_pipelines if p['name'] == master_pipeline['name']), None)
                                        
                                        if slave_pipeline:
                                            logger.info(f"         ✅ Pipeline mapeável: '{master_pipeline['name']}' ({master_pipeline_id} → {slave_pipeline['id']})")
                                            
                                            # Verificar status
                                            master_stages = master_api.get_pipeline_stages(master_pipeline_id)
                                            master_status = next((s for s in master_stages if s['id'] == master_status_id), None)
                                            
                                            if master_status:
                                                slave_stages = slave_api.get_pipeline_stages(slave_pipeline['id'])
                                                slave_status = next((s for s in slave_stages if s['name'] == master_status['name']), None)
                                                
                                                if slave_status:
                                                    logger.info(f"         ✅ Status mapeável: '{master_status['name']}' ({master_status_id} → {slave_status['id']})")
                                                    logger.info(f"         📋 Required status correto seria:")
                                                    logger.info(f"            pipeline_id: {slave_pipeline['id']}")
                                                    logger.info(f"            status_id: {slave_status['id']}")
                                                else:
                                                    logger.error(f"         ❌ Status '{master_status['name']}' não encontrado na slave")
                                            else:
                                                logger.error(f"         ❌ Status {master_status_id} não encontrado na master")
                                        else:
                                            logger.error(f"         ❌ Pipeline '{master_pipeline['name']}' não encontrado na slave")
                                    else:
                                        logger.error(f"         ❌ Pipeline {master_pipeline_id} não encontrado na master")
                        else:
                            logger.warning(f"   ❌ Campo '{master_field_name}' NÃO encontrado na slave")
                            logger.info(f"      📋 Campo precisa ser criado na slave com mapeamento correto")
                
                except Exception as slave_error:
                    logger.error(f"   ❌ Erro ao analisar slave {slave_account.subdomain}: {slave_error}")
            
        except Exception as e:
            logger.error(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    debug_textarea_fields()
