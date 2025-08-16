#!/usr/bin/env python3
"""
Script para comparar Role 1 da master e slave em detalhes
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

def compare_role_1():
    """Compara Role 1 da master e slave em detalhes"""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔍 Comparando Role 1 da master e slave...")
            
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
            
            # Buscar todas as roles
            logger.info("\n📋 BUSCANDO ROLES...")
            master_roles = master_api.get_roles()
            slave_roles = slave_api.get_roles()
            
            logger.info(f"✅ Master tem {len(master_roles)} roles")
            logger.info(f"✅ Slave tem {len(slave_roles)} roles")
            
            # Encontrar Role 1 na master
            master_role1 = None
            for role in master_roles:
                if role['name'].lower() == 'role 1':
                    master_role1 = role
                    break
            
            # Encontrar Role 1 na slave
            slave_role1 = None
            for role in slave_roles:
                if role['name'].lower() == 'role 1':
                    slave_role1 = role
                    break
            
            if not master_role1:
                logger.error("❌ Role 1 não encontrada na master!")
                # Mostrar roles disponíveis
                logger.info("📋 Roles disponíveis na master:")
                for role in master_roles:
                    logger.info(f"   🔐 {role['name']} (ID: {role['id']})")
                return
            
            if not slave_role1:
                logger.error("❌ Role 1 não encontrada na slave!")
                # Mostrar roles disponíveis
                logger.info("📋 Roles disponíveis na slave:")
                for role in slave_roles:
                    logger.info(f"   🔐 {role['name']} (ID: {role['id']})")
                return
            
            # === MOSTRAR ROLE 1 DA MASTER ===
            logger.info("\n" + "="*80)
            logger.info("🎯 ROLE 1 DA MASTER (EVORESULTDEV)")
            logger.info("="*80)
            logger.info(f"📝 Nome: {master_role1['name']}")
            logger.info(f"🆔 ID: {master_role1['id']}")
            
            # Mostrar rights básicos
            rights = master_role1.get('rights', {})
            logger.info(f"\n📊 PERMISSÕES BÁSICAS:")
            
            for key, value in rights.items():
                if key != 'status_rights':
                    if isinstance(value, dict):
                        permissions = [k for k, v in value.items() if v is True]
                        if permissions:
                            logger.info(f"   {key}: {permissions}")
                        else:
                            logger.info(f"   {key}: {value}")
                    else:
                        logger.info(f"   {key}: {value}")
            
            # Mostrar status_rights detalhadamente
            status_rights = rights.get('status_rights', [])
            logger.info(f"\n🎭 STATUS_RIGHTS ({len(status_rights)} entradas):")
            
            # Agrupar por pipeline
            pipeline_groups = {}
            for sr in status_rights:
                pipeline_id = sr.get('pipeline_id')
                if pipeline_id not in pipeline_groups:
                    pipeline_groups[pipeline_id] = []
                pipeline_groups[pipeline_id].append(sr)
            
            for pipeline_id, rights_list in pipeline_groups.items():
                logger.info(f"\n   📊 Pipeline ID: {pipeline_id} ({len(rights_list)} status_rights)")
                
                for i, sr in enumerate(rights_list):
                    status_id = sr.get('status_id')
                    edit = sr.get('edit', 'N/A')
                    view = sr.get('view', 'N/A')
                    delete = sr.get('delete', 'N/A')
                    export = sr.get('export', 'N/A')
                    
                    logger.info(f"      {i+1:2d}. Status {status_id}: edit={edit}, view={view}, delete={delete}, export={export}")
            
            # === MOSTRAR ROLE 1 DA SLAVE ===
            logger.info("\n" + "="*80)
            logger.info("🎯 ROLE 1 DA SLAVE (TESTEDEV)")
            logger.info("="*80)
            logger.info(f"📝 Nome: {slave_role1['name']}")
            logger.info(f"🆔 ID: {slave_role1['id']}")
            
            # Mostrar rights básicos
            rights = slave_role1.get('rights', {})
            logger.info(f"\n📊 PERMISSÕES BÁSICAS:")
            
            for key, value in rights.items():
                if key != 'status_rights':
                    if isinstance(value, dict):
                        permissions = [k for k, v in value.items() if v is True]
                        if permissions:
                            logger.info(f"   {key}: {permissions}")
                        else:
                            logger.info(f"   {key}: {value}")
                    else:
                        logger.info(f"   {key}: {value}")
            
            # Mostrar status_rights detalhadamente
            status_rights = rights.get('status_rights', [])
            logger.info(f"\n🎭 STATUS_RIGHTS ({len(status_rights)} entradas):")
            
            # Agrupar por pipeline
            pipeline_groups = {}
            for sr in status_rights:
                pipeline_id = sr.get('pipeline_id')
                if pipeline_id not in pipeline_groups:
                    pipeline_groups[pipeline_id] = []
                pipeline_groups[pipeline_id].append(sr)
            
            for pipeline_id, rights_list in pipeline_groups.items():
                logger.info(f"\n   📊 Pipeline ID: {pipeline_id} ({len(rights_list)} status_rights)")
                
                for i, sr in enumerate(rights_list):
                    status_id = sr.get('status_id')
                    edit = sr.get('edit', 'N/A')
                    view = sr.get('view', 'N/A')
                    delete = sr.get('delete', 'N/A')
                    export = sr.get('export', 'N/A')
                    
                    logger.info(f"      {i+1:2d}. Status {status_id}: edit={edit}, view={view}, delete={delete}, export={export}")
            
            # === COMPARAÇÃO ===
            logger.info("\n" + "="*80)
            logger.info("📊 COMPARAÇÃO")
            logger.info("="*80)
            
            master_status_rights = master_role1.get('rights', {}).get('status_rights', [])
            slave_status_rights = slave_role1.get('rights', {}).get('status_rights', [])
            
            logger.info(f"📈 Master tem {len(master_status_rights)} status_rights")
            logger.info(f"📈 Slave tem {len(slave_status_rights)} status_rights")
            
            # Contar por pipeline
            master_pipelines = set(sr.get('pipeline_id') for sr in master_status_rights)
            slave_pipelines = set(sr.get('pipeline_id') for sr in slave_status_rights)
            
            logger.info(f"🔧 Master tem pipelines: {sorted(master_pipelines)}")
            logger.info(f"🔧 Slave tem pipelines: {sorted(slave_pipelines)}")
            
            # Pipelines em comum
            common_pipelines = master_pipelines & slave_pipelines
            only_master = master_pipelines - slave_pipelines
            only_slave = slave_pipelines - master_pipelines
            
            logger.info(f"✅ Pipelines em comum: {sorted(common_pipelines)}")
            if only_master:
                logger.info(f"⚠️ Apenas na master: {sorted(only_master)}")
            if only_slave:
                logger.info(f"⚠️ Apenas na slave: {sorted(only_slave)}")
            
            # === ANÁLISE DE ETAPAS DE LEADS ===
            logger.info(f"\n🎪 ANÁLISE DAS ETAPAS DE LEADS:")
            
            # Buscar informações das pipelines para identificar etapas de leads
            try:
                master_pipelines_info = master_api.get_pipelines()
                slave_pipelines_info = slave_api.get_pipelines()
                
                for pipeline_id in common_pipelines:
                    logger.info(f"\n   📊 Pipeline {pipeline_id}:")
                    
                    # Buscar etapas da pipeline
                    try:
                        master_stages = master_api.get_pipeline_stages(pipeline_id)
                        
                        # Encontrar etapas de leads
                        lead_stages = [s for s in master_stages if any(keyword in s['name'].lower() for keyword in ['lead', 'entrada', 'incoming', 'novo'])]
                        
                        if lead_stages:
                            logger.info(f"      🎪 Etapas de leads encontradas: {len(lead_stages)}")
                            for stage in lead_stages:
                                stage_id = stage['id']
                                stage_name = stage['name']
                                
                                # Verificar se esta etapa está nos status_rights
                                master_has = any(sr.get('status_id') == stage_id for sr in master_status_rights if sr.get('pipeline_id') == pipeline_id)
                                slave_has = any(sr.get('status_id') == stage_id for sr in slave_status_rights if sr.get('pipeline_id') == pipeline_id)
                                
                                master_icon = "✅" if master_has else "❌"
                                slave_icon = "✅" if slave_has else "❌"
                                
                                logger.info(f"         {stage_name} (ID: {stage_id}): Master {master_icon} | Slave {slave_icon}")
                        else:
                            logger.info(f"      ℹ️ Nenhuma etapa de lead detectada")
                            
                    except Exception as e:
                        logger.error(f"      ❌ Erro ao analisar pipeline {pipeline_id}: {e}")
                        
            except Exception as e:
                logger.error(f"❌ Erro ao analisar etapas de leads: {e}")
            
            logger.info("\n🎉 Comparação completa!")
                
        except Exception as e:
            logger.error(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    compare_role_1()
