#!/usr/bin/env python3
"""
Script para debug dos pipelines e etapas de leads
Analisa especificamente pipelines de incoming leads
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import create_app
from src.database import db
from src.models.kommo_account import KommoAccount
from src.services.kommo_api import KommoAPIService
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_pipelines_leads():
    """Debug dos pipelines e etapas relacionadas a leads"""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔍 Analisando pipelines e leads...")
            
            # Buscar contas
            master_account = KommoAccount.query.filter_by(subdomain='evoresultdev').first()
            slave_account = KommoAccount.query.filter_by(subdomain='testedev').first()
            
            if not master_account or not slave_account:
                logger.error("❌ Contas não encontradas!")
                return
            
            # Criar APIs
            master_api = KommoAPIService(
                subdomain=master_account.subdomain,
                refresh_token=master_account.access_token
            )
            
            slave_api = KommoAPIService(
                subdomain=slave_account.subdomain,
                refresh_token=slave_account.access_token
            )
            
            # 1. Analisar pipelines da master
            logger.info("\n📊 PIPELINES DA MASTER:")
            master_pipelines = master_api.get_pipelines()
            
            for pipeline in master_pipelines:
                pipeline_id = pipeline['id']
                pipeline_name = pipeline['name']
                is_main = pipeline.get('is_main', False)
                
                logger.info(f"\n🔧 Pipeline: {pipeline_name} (ID: {pipeline_id}) - Main: {is_main}")
                
                # Buscar etapas desta pipeline
                try:
                    stages = master_api.get_pipeline_stages(pipeline_id)
                    logger.info(f"   📋 Etapas ({len(stages)}):")
                    
                    for stage in stages:
                        stage_id = stage['id']
                        stage_name = stage['name']
                        color = stage.get('color', 'N/A')
                        sort = stage.get('sort', 'N/A')
                        
                        logger.info(f"      🎯 {stage_name} (ID: {stage_id}) - Sort: {sort}, Color: {color}")
                        
                        # Verificar se é relacionado a leads
                        if any(keyword in stage_name.lower() for keyword in ['lead', 'entrada', 'incoming', 'novo']):
                            logger.info(f"         🎪 *** ETAPA DE LEAD DETECTADA! ***")
                            
                except Exception as e:
                    logger.error(f"   ❌ Erro ao buscar etapas da pipeline {pipeline_id}: {e}")
            
            # 2. Analisar pipelines da slave
            logger.info("\n📊 PIPELINES DA SLAVE:")
            slave_pipelines = slave_api.get_pipelines()
            
            for pipeline in slave_pipelines:
                pipeline_id = pipeline['id']
                pipeline_name = pipeline['name']
                is_main = pipeline.get('is_main', False)
                
                logger.info(f"\n🔧 Pipeline: {pipeline_name} (ID: {pipeline_id}) - Main: {is_main}")
                
                # Buscar etapas desta pipeline
                try:
                    stages = slave_api.get_pipeline_stages(pipeline_id)
                    logger.info(f"   📋 Etapas ({len(stages)}):")
                    
                    for stage in stages:
                        stage_id = stage['id']
                        stage_name = stage['name']
                        color = stage.get('color', 'N/A')
                        sort = stage.get('sort', 'N/A')
                        
                        logger.info(f"      🎯 {stage_name} (ID: {stage_id}) - Sort: {sort}, Color: {color}")
                        
                        # Verificar se é relacionado a leads
                        if any(keyword in stage_name.lower() for keyword in ['lead', 'entrada', 'incoming', 'novo']):
                            logger.info(f"         🎪 *** ETAPA DE LEAD DETECTADA! ***")
                            
                except Exception as e:
                    logger.error(f"   ❌ Erro ao buscar etapas da pipeline {pipeline_id}: {e}")
            
            # 3. Comparar mapeamentos atuais
            logger.info("\n🗺️ ANÁLISE DE MAPEAMENTOS:")
            
            # Buscar mapeamentos existentes do banco
            try:
                from src.database import db
                
                # Query para pegar mapeamentos de pipelines
                from sqlalchemy import text
                
                pipeline_mappings_query = text("""
                SELECT master_id, slave_id, type 
                FROM sync_mappings 
                WHERE type = 'pipeline' 
                AND master_account_id = :master_id 
                AND slave_account_id = :slave_id
                """)
                
                result = db.session.execute(
                    pipeline_mappings_query, 
                    {"master_id": master_account.id, "slave_id": slave_account.id}
                ).fetchall()
                
                logger.info(f"📊 Mapeamentos de pipelines no banco: {len(result)}")
                pipeline_mappings = {}
                for row in result:
                    pipeline_mappings[row[0]] = row[1]
                    logger.info(f"   🔗 Pipeline {row[0]} -> {row[1]}")
                
                # Query para pegar mapeamentos de etapas
                stage_mappings_query = text("""
                SELECT master_id, slave_id, type 
                FROM sync_mappings 
                WHERE type = 'stage' 
                AND master_account_id = :master_id 
                AND slave_account_id = :slave_id
                """)
                
                result = db.session.execute(
                    stage_mappings_query, 
                    {"master_id": master_account.id, "slave_id": slave_account.id}
                ).fetchall()
                
                logger.info(f"📊 Mapeamentos de etapas no banco: {len(result)}")
                stage_mappings = {}
                for row in result:
                    stage_mappings[row[0]] = row[1]
                    logger.info(f"   🔗 Etapa {row[0]} -> {row[1]}")
                
                # 4. Verificar quais etapas de leads estão mapeadas
                logger.info("\n🎪 VERIFICAÇÃO DE ETAPAS DE LEADS:")
                
                for pipeline in master_pipelines:
                    pipeline_id = pipeline['id']
                    pipeline_name = pipeline['name']
                    
                    if pipeline_id in pipeline_mappings:
                        slave_pipeline_id = pipeline_mappings[pipeline_id]
                        logger.info(f"\n✅ Pipeline mapeado: {pipeline_name} ({pipeline_id} -> {slave_pipeline_id})")
                        
                        # Verificar etapas de leads desta pipeline
                        try:
                            stages = master_api.get_pipeline_stages(pipeline_id)
                            
                            for stage in stages:
                                stage_id = stage['id']
                                stage_name = stage['name']
                                
                                # Verificar se é etapa de lead
                                is_lead_stage = any(keyword in stage_name.lower() for keyword in ['lead', 'entrada', 'incoming', 'novo'])
                                
                                if is_lead_stage:
                                    if stage_id in stage_mappings:
                                        slave_stage_id = stage_mappings[stage_id]
                                        logger.info(f"   ✅ Etapa de lead mapeada: {stage_name} ({stage_id} -> {slave_stage_id})")
                                    else:
                                        logger.warning(f"   ❌ Etapa de lead NÃO mapeada: {stage_name} (ID: {stage_id})")
                        
                        except Exception as e:
                            logger.error(f"   ❌ Erro ao verificar etapas da pipeline {pipeline_id}: {e}")
                    else:
                        logger.warning(f"❌ Pipeline NÃO mapeado: {pipeline_name} (ID: {pipeline_id})")
                
            except Exception as e:
                logger.error(f"❌ Erro ao analisar mapeamentos: {e}")
                
        except Exception as e:
            logger.error(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    debug_pipelines_leads()
