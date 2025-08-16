#!/usr/bin/env python3
"""
Script para comparar status IDs da Role 1 entre master e slave
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compare_role1_statuses():
    """Compara status IDs da Role 1 entre master e slave"""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔍 Comparando status IDs da Role 1...")
            
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
            
            # Buscar Role 1
            master_roles = master_api.get_roles()
            slave_roles = slave_api.get_roles()
            
            master_role1 = None
            slave_role1 = None
            
            for role in master_roles:
                if role['name'].lower() == 'role 1':
                    master_role1 = role
                    break
            
            for role in slave_roles:
                if role['name'].lower() == 'role 1':
                    slave_role1 = role
                    break
            
            if not master_role1 or not slave_role1:
                logger.error("❌ Role 1 não encontrada!")
                return
            
            logger.info(f"✅ Role 1 encontrada - Master ID: {master_role1['id']}, Slave ID: {slave_role1['id']}")
            
            # Extrair permissões básicas (não status_rights)
            master_rights = master_role1.get('rights', {})
            slave_rights = slave_role1.get('rights', {})
            
            # Buscar informações dos pipelines e status para identificar nomes
            logger.info("📊 Buscando informações dos pipelines...")
            
            master_pipelines = master_api.get_pipelines()
            slave_pipelines = slave_api.get_pipelines()
            
            # Criar dicionários de lookup para status -> nome
            master_status_names = {}
            slave_status_names = {}
            
            # Para master
            for pipeline in master_pipelines:
                try:
                    stages = master_api.get_pipeline_stages(pipeline['id'])
                    for stage in stages:
                        master_status_names[stage['id']] = {
                            'name': stage['name'],
                            'pipeline': pipeline['name']
                        }
                except Exception as e:
                    logger.debug(f"Erro ao buscar etapas da pipeline {pipeline['id']}: {e}")
            
            # Para slave
            for pipeline in slave_pipelines:
                try:
                    stages = slave_api.get_pipeline_stages(pipeline['id'])
                    for stage in stages:
                        slave_status_names[stage['id']] = {
                            'name': stage['name'],
                            'pipeline': pipeline['name']
                        }
                except Exception as e:
                    logger.debug(f"Erro ao buscar etapas da pipeline {pipeline['id']}: {e}")
            
            logger.info("\n" + "="*100)
            logger.info("📊 COMPARAÇÃO DE PERMISSÕES BÁSICAS - ROLE 1")
            logger.info("="*100)
            
            # Extrair todas as chaves de permissões básicas (exceto status_rights)
            all_basic_rights = set()
            
            for key in master_rights.keys():
                if key != 'status_rights' and isinstance(master_rights[key], dict):
                    all_basic_rights.add(key)
            
            for key in slave_rights.keys():
                if key != 'status_rights' and isinstance(slave_rights[key], dict):
                    all_basic_rights.add(key)
            
            # Separar por categorias
            status_rights = set()
            other_rights = set()
            
            for right in all_basic_rights:
                if right.startswith('status_'):
                    status_rights.add(right)
                else:
                    other_rights.add(right)
            
            # Mostrar permissões gerais primeiro
            if other_rights:
                logger.info("\n🏢 PERMISSÕES GERAIS:")
                for right in sorted(other_rights):
                    master_perms = master_rights.get(right, {})
                    slave_perms = slave_rights.get(right, {})
                    
                    logger.info(f"\n{right}:")
                    logger.info(f"   Master: {master_perms}")
                    logger.info(f"   Slave:  {slave_perms}")
                    
                    if master_perms != slave_perms:
                        logger.info("   ⚠️  DIFERENÇA DETECTADA!")
            
            # Mostrar permissões de status
            if status_rights:
                logger.info(f"\n🎯 PERMISSÕES DE STATUS ({len(status_rights)} encontradas):")
                
                for right in sorted(status_rights):
                    # Extrair status_id do nome da chave
                    status_id_str = right.replace('status_', '')
                    try:
                        status_id = int(status_id_str)
                    except:
                        status_id = status_id_str
                    
                    # Buscar nome do status
                    master_info = master_status_names.get(status_id, {})
                    slave_info = slave_status_names.get(status_id, {})
                    
                    status_name = master_info.get('name') or slave_info.get('name') or f"Status {status_id}"
                    pipeline_name = master_info.get('pipeline') or slave_info.get('pipeline') or "Pipeline desconhecida"
                    
                    master_perms = master_rights.get(right, {})
                    slave_perms = slave_rights.get(right, {})
                    
                    # Verificar se é etapa de lead
                    is_lead = any(keyword in status_name.lower() for keyword in ['lead', 'entrada', 'incoming', 'novo'])
                    lead_icon = "🎪" if is_lead else "📋"
                    
                    logger.info(f"\n{lead_icon} {status_name} (Pipeline: {pipeline_name}, ID: {status_id}):")
                    logger.info(f"   Master: {master_perms}")
                    logger.info(f"   Slave:  {slave_perms}")
                    
                    if master_perms != slave_perms:
                        logger.info("   ⚠️  DIFERENÇA DETECTADA!")
                        
                        # Mostrar diferenças específicas
                        all_keys = set(master_perms.keys()) | set(slave_perms.keys())
                        for key in all_keys:
                            master_val = master_perms.get(key, 'AUSENTE')
                            slave_val = slave_perms.get(key, 'AUSENTE')
                            if master_val != slave_val:
                                logger.info(f"      {key}: Master={master_val} vs Slave={slave_val}")
            
            # === ANÁLISE DE STATUS_RIGHTS ===
            logger.info("\n" + "="*100)
            logger.info("🎭 ANÁLISE DE STATUS_RIGHTS")
            logger.info("="*100)
            
            master_status_rights = master_rights.get('status_rights', [])
            slave_status_rights = slave_rights.get('status_rights', [])
            
            logger.info(f"📊 Master tem {len(master_status_rights)} status_rights")
            logger.info(f"📊 Slave tem {len(slave_status_rights)} status_rights")
            
            # Agrupar por status_id para comparação
            master_by_status = {}
            slave_by_status = {}
            
            for sr in master_status_rights:
                status_id = sr.get('status_id')
                pipeline_id = sr.get('pipeline_id')
                key = f"{status_id}_p{pipeline_id}"
                master_by_status[key] = sr
            
            for sr in slave_status_rights:
                status_id = sr.get('status_id')
                pipeline_id = sr.get('pipeline_id')
                key = f"{status_id}_p{pipeline_id}"
                slave_by_status[key] = sr
            
            all_status_keys = set(master_by_status.keys()) | set(slave_by_status.keys())
            
            logger.info(f"\n📋 Comparando {len(all_status_keys)} status_rights únicos:")
            
            for key in sorted(all_status_keys):
                parts = key.split('_p')
                status_id = int(parts[0])
                pipeline_id = int(parts[1])
                
                master_sr = master_by_status.get(key, {})
                slave_sr = slave_by_status.get(key, {})
                
                # Buscar nome do status
                status_info = master_status_names.get(status_id) or slave_status_names.get(status_id)
                status_name = status_info.get('name', f"Status {status_id}") if status_info else f"Status {status_id}"
                pipeline_name = status_info.get('pipeline', f"Pipeline {pipeline_id}") if status_info else f"Pipeline {pipeline_id}"
                
                # Verificar se é etapa de lead
                is_lead = any(keyword in status_name.lower() for keyword in ['lead', 'entrada', 'incoming', 'novo'])
                lead_icon = "🎪" if is_lead else "📋"
                
                logger.info(f"\n{lead_icon} {status_name} (Pipeline: {pipeline_name}, Status: {status_id}, Pipeline: {pipeline_id}):")
                
                if master_sr:
                    master_clean = {k: v for k, v in master_sr.items() if k not in ['status_id', 'pipeline_id']}
                    logger.info(f"   Master: {master_clean}")
                else:
                    logger.info("   Master: AUSENTE")
                
                if slave_sr:
                    slave_clean = {k: v for k, v in slave_sr.items() if k not in ['status_id', 'pipeline_id']}
                    logger.info(f"   Slave:  {slave_clean}")
                else:
                    logger.info("   Slave:  AUSENTE")
                
                if master_sr != slave_sr:
                    logger.info("   ⚠️  DIFERENÇA DETECTADA!")
            
            # === RESUMO ===
            logger.info("\n" + "="*100)
            logger.info("📈 RESUMO DA COMPARAÇÃO")
            logger.info("="*100)
            
            logger.info(f"🏢 Permissões gerais: {len(other_rights)} encontradas")
            logger.info(f"🎯 Permissões de status básicas: {len(status_rights)} encontradas")
            logger.info(f"🎭 Status_rights: Master={len(master_status_rights)}, Slave={len(slave_status_rights)}")
            
            # Contar etapas de lead
            lead_statuses = [r for r in status_rights if any(keyword in master_status_names.get(int(r.replace('status_', '')), {}).get('name', '').lower() for keyword in ['lead', 'entrada', 'incoming', 'novo'])]
            logger.info(f"🎪 Permissões de etapas de lead: {len(lead_statuses)} encontradas")
            
            logger.info("\n🎉 Comparação completa!")
                
        except Exception as e:
            logger.error(f"❌ Erro geral: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    compare_role1_statuses()
