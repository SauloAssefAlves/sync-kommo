#!/usr/bin/env python3
"""
Script para verificar e comparar os status das pipelines entre master e slave
para entender o problema dos status padrão nas roles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import create_app
from src.database import db
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('status_comparison.log')
    ]
)
logger = logging.getLogger(__name__)

def compare_pipeline_statuses():
    """Compara os status das pipelines entre master e slave"""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔍 Iniciando comparação de status das pipelines...")
            
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
            
            # Obter pipelines de ambas as contas
            logger.info("📊 Obtendo pipelines da master...")
            master_pipelines = master_api.get_pipelines()
            
            logger.info("📊 Obtendo pipelines da slave...")
            slave_pipelines = slave_api.get_pipelines()
            
            logger.info(f"✅ Master: {len(master_pipelines)} pipelines")
            logger.info(f"✅ Slave: {len(slave_pipelines)} pipelines")
            
            # Buscar estágios para cada pipeline
            logger.info("📊 Obtendo estágios das pipelines...")
            
            for pipeline in master_pipelines:
                try:
                    stages = master_api.get_pipeline_stages(pipeline['id'])
                    pipeline['stages'] = stages
                    logger.debug(f"Master pipeline '{pipeline['name']}': {len(stages)} estágios")
                except Exception as e:
                    logger.warning(f"Erro ao obter estágios da master pipeline {pipeline['name']}: {e}")
                    pipeline['stages'] = []
            
            for pipeline in slave_pipelines:
                try:
                    stages = slave_api.get_pipeline_stages(pipeline['id'])
                    pipeline['stages'] = stages
                    logger.debug(f"Slave pipeline '{pipeline['name']}': {len(stages)} estágios")
                except Exception as e:
                    logger.warning(f"Erro ao obter estágios da slave pipeline {pipeline['name']}: {e}")
                    pipeline['stages'] = []
            
            # Criar dicionários por nome para comparação
            master_by_name = {p['name']: p for p in master_pipelines}
            slave_by_name = {p['name']: p for p in slave_pipelines}
            
            # Comparar status de cada pipeline
            logger.info("\n🔄 Comparando status das pipelines...")
            
            for pipeline_name in master_by_name.keys():
                if pipeline_name in slave_by_name:
                    master_pipeline = master_by_name[pipeline_name]
                    slave_pipeline = slave_by_name[pipeline_name]
                    
                    logger.info(f"\n📊 PIPELINE: {pipeline_name}")
                    logger.info(f"   Master ID: {master_pipeline['id']} | Slave ID: {slave_pipeline['id']}")
                    
                    # Comparar status/estágios
                    master_stages = master_pipeline.get('stages', [])
                    slave_stages = slave_pipeline.get('stages', [])
                    
                    logger.info(f"   📋 Master: {len(master_stages)} estágios | Slave: {len(slave_stages)} estágios")
                    
                    # Mapear estágios por nome
                    master_stages_by_name = {s['name']: s for s in master_stages}
                    slave_stages_by_name = {s['name']: s for s in slave_stages}
                    
                    logger.info(f"   📝 MASTER STAGES:")
                    for i, stage in enumerate(master_stages):
                        logger.info(f"      {i+1}. {stage['name']} (ID: {stage['id']}) - Tipo: {stage.get('type', 'N/A')}")
                    
                    logger.info(f"   📝 SLAVE STAGES:")
                    for i, stage in enumerate(slave_stages):
                        logger.info(f"      {i+1}. {stage['name']} (ID: {stage['id']}) - Tipo: {stage.get('type', 'N/A')}")
                    
                    # Identificar diferenças nos estágios
                    master_stage_names = set(master_stages_by_name.keys())
                    slave_stage_names = set(slave_stages_by_name.keys())
                    
                    missing_in_slave = master_stage_names - slave_stage_names
                    extra_in_slave = slave_stage_names - master_stage_names
                    common_stages = master_stage_names & slave_stage_names
                    
                    if missing_in_slave:
                        logger.info(f"   ⚠️ Estágios faltando na slave: {list(missing_in_slave)}")
                    
                    if extra_in_slave:
                        logger.info(f"   ⚠️ Estágios extras na slave: {list(extra_in_slave)}")
                    
                    if common_stages:
                        logger.info(f"   ✅ Estágios em comum: {len(common_stages)}")
                        
                        # Verificar mapeamento de IDs para estágios comuns
                        logger.info(f"   🎭 MAPEAMENTO DE ESTÁGIOS:")
                        for stage_name in sorted(common_stages):
                            master_stage = master_stages_by_name[stage_name]
                            slave_stage = slave_stages_by_name[stage_name]
                            logger.info(f"      '{stage_name}': {master_stage['id']} -> {slave_stage['id']}")
                else:
                    logger.warning(f"⚠️ Pipeline '{pipeline_name}' existe na master mas não na slave")
            
            # Verificar roles e seus status_rights
            logger.info("\n🔐 Verificando roles e seus status_rights...")
            
            master_roles = master_api.get_roles()
            slave_roles = slave_api.get_roles()
            
            logger.info(f"📊 Master: {len(master_roles)} roles | Slave: {len(slave_roles)} roles")
            
            # Focar em roles com status_rights
            logger.info("\n🎯 ANÁLISE DE STATUS_RIGHTS NAS ROLES:")
            
            for role in slave_roles:
                role_name = role['name']
                logger.info(f"\n🔐 ROLE: {role_name} (ID: {role['id']})")
                
                rights = role.get('rights', {})
                status_rights = rights.get('status_rights', [])
                
                if status_rights:
                    logger.info(f"   📋 Status rights ({len(status_rights)} itens):")
                    
                    # Agrupar por pipeline
                    by_pipeline = {}
                    for sr in status_rights:
                        pipeline_id = sr.get('pipeline_id')
                        status_id = sr.get('status_id')
                        if pipeline_id not in by_pipeline:
                            by_pipeline[pipeline_id] = []
                        by_pipeline[pipeline_id].append(status_id)
                    
                    for pipeline_id, status_ids in by_pipeline.items():
                        # Encontrar nome da pipeline
                        pipeline_name = "DESCONHECIDA"
                        for p in slave_pipelines:
                            if p['id'] == pipeline_id:
                                pipeline_name = p['name']
                                break
                        
                        logger.info(f"      Pipeline '{pipeline_name}' (ID: {pipeline_id}): status {status_ids}")
                        
                        # Verificar se os status_ids correspondem aos estágios da pipeline
                        if pipeline_name in slave_by_name:
                            pipeline_stages = slave_by_name[pipeline_name].get('stages', [])
                            stage_ids = [s['id'] for s in pipeline_stages]
                            
                            valid_status = [sid for sid in status_ids if sid in stage_ids or sid in [142, 143, 1]]
                            invalid_status = [sid for sid in status_ids if sid not in stage_ids and sid not in [142, 143, 1]]
                            
                            if invalid_status:
                                logger.warning(f"         ⚠️ Status inválidos: {invalid_status}")
                                # Mostrar quais estágios existem na pipeline
                                logger.info(f"         📋 Estágios disponíveis na pipeline: {stage_ids}")
                            if valid_status:
                                logger.info(f"         ✅ Status válidos: {valid_status}")
                else:
                    logger.info(f"   📋 Nenhum status_rights definido")
            
            logger.info("\n🎉 Comparação de status concluída!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na comparação: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = compare_pipeline_statuses()
    if success:
        print("\n✅ Comparação executada com sucesso!")
    else:
        print("\n❌ Falha na comparação!")
        sys.exit(1)
