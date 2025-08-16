#!/usr/bin/env python3
"""
Script para atualizar as roles existentes na slave com os status corretos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import create_app
from src.database import db
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService, KommoSyncService
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_roles_status.log')
    ]
)
logger = logging.getLogger(__name__)

def fix_roles_status():
    """Corrige os status das roles na slave"""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔧 Iniciando correção dos status das roles...")
            
            # Buscar contas
            master_account = KommoAccount.query.filter_by(subdomain='evoresultdev').first()
            slave_account = KommoAccount.query.filter_by(subdomain='testedev').first()
            
            if not master_account or not slave_account:
                logger.error("❌ Contas não encontradas!")
                return False
            
            # Criar APIs
            master_api = KommoAPIService(
                subdomain=master_account.subdomain,
                refresh_token=master_account.access_token
            )
            
            slave_api = KommoAPIService(
                subdomain=slave_account.subdomain,
                refresh_token=slave_account.access_token
            )
            
            # Obter configuração da master
            logger.info("📊 Extraindo configuração da master...")
            sync_service = KommoSyncService(master_api)
            master_config = sync_service.extract_master_configuration()
            
            # Construir mapeamentos (usar script test_complete_sync como base)
            logger.info("🗺️ Construindo mapeamentos de pipeline e estágios...")
            
            # Pipeline mappings
            master_pipelines = master_api.get_pipelines()
            slave_pipelines = slave_api.get_pipelines()
            
            pipeline_mappings = {}
            stage_mappings = {}
            
            master_by_name = {p['name']: p for p in master_pipelines}
            slave_by_name = {p['name']: p for p in slave_pipelines}
            
            for pipeline_name in master_by_name.keys():
                if pipeline_name in slave_by_name:
                    master_pipeline = master_by_name[pipeline_name]
                    slave_pipeline = slave_by_name[pipeline_name]
                    
                    pipeline_mappings[master_pipeline['id']] = slave_pipeline['id']
                    logger.info(f"📊 Pipeline mapping: {pipeline_name} ({master_pipeline['id']} -> {slave_pipeline['id']})")
                    
                    # Mapear estágios
                    try:
                        master_stages = master_api.get_pipeline_stages(master_pipeline['id'])
                        slave_stages = slave_api.get_pipeline_stages(slave_pipeline['id'])
                        
                        master_stages_by_name = {s['name']: s for s in master_stages}
                        slave_stages_by_name = {s['name']: s for s in slave_stages}
                        
                        for stage_name in master_stages_by_name.keys():
                            if stage_name in slave_stages_by_name:
                                master_stage = master_stages_by_name[stage_name]
                                slave_stage = slave_stages_by_name[stage_name]
                                stage_mappings[master_stage['id']] = slave_stage['id']
                                logger.debug(f"  🎭 Stage mapping: {stage_name} ({master_stage['id']} -> {slave_stage['id']})")
                    except Exception as e:
                        logger.warning(f"Erro ao mapear estágios da pipeline {pipeline_name}: {e}")
            
            logger.info(f"✅ Mapeamentos criados: {len(pipeline_mappings)} pipelines, {len(stage_mappings)} estágios")
            
            # Obter roles existentes na slave
            logger.info("🔐 Obtendo roles da slave...")
            slave_roles = slave_api.get_roles()
            
            # Atualizar cada role
            for master_role in master_config.get('roles', []):
                role_name = master_role['name']
                logger.info(f"\n🔐 Processando role: {role_name}")
                
                # Encontrar role correspondente na slave
                slave_role = None
                for sr in slave_roles:
                    if sr['name'] == role_name:
                        slave_role = sr
                        break
                
                if slave_role:
                    logger.info(f"✅ Role encontrada na slave (ID: {slave_role['id']})")
                    
                    # Mapear direitos usando o método corrigido
                    mapped_rights = master_api._map_role_rights(
                        master_role.get('rights', {}), 
                        pipeline_mappings, 
                        stage_mappings, 
                        slave_api
                    )
                    
                    # Preparar dados para atualização
                    role_update_data = {
                        'name': role_name,
                        'rights': mapped_rights
                    }
                    
                    # Atualizar role na slave
                    try:
                        logger.info(f"🔄 Atualizando role '{role_name}' com {len(mapped_rights.get('status_rights', []))} status_rights...")
                        
                        response = slave_api.update_role(slave_role['id'], role_update_data)
                        logger.info(f"✅ Role '{role_name}' atualizada com sucesso!")
                        
                        # Log dos status_rights atualizados
                        status_rights = mapped_rights.get('status_rights', [])
                        if status_rights:
                            by_pipeline = {}
                            for sr in status_rights:
                                pipeline_id = sr.get('pipeline_id')
                                if pipeline_id not in by_pipeline:
                                    by_pipeline[pipeline_id] = []
                                by_pipeline[pipeline_id].append(sr.get('status_id'))
                            
                            for pipeline_id, status_ids in by_pipeline.items():
                                # Encontrar nome da pipeline
                                pipeline_name = "DESCONHECIDA"
                                for p in slave_pipelines:
                                    if p['id'] == pipeline_id:
                                        pipeline_name = p['name']
                                        break
                                logger.info(f"   📊 Pipeline '{pipeline_name}': {len(status_ids)} status ({sorted(status_ids)})")
                        
                    except Exception as e:
                        logger.error(f"❌ Erro ao atualizar role '{role_name}': {e}")
                        continue
                else:
                    logger.warning(f"⚠️ Role '{role_name}' não encontrada na slave")
            
            logger.info("\n🎉 Correção dos status das roles concluída!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na correção: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = fix_roles_status()
    if success:
        print("\n✅ Correção executada com sucesso!")
    else:
        print("\n❌ Falha na correção!")
        sys.exit(1)
