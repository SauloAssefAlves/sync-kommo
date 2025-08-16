"""
🔐 SERVIÇO DE SINCRONIZAÇÃO DE ROLES
Função independente para sincronizar roles entre master e slave
"""

import os
import sys
import logging
from typing import Dict, Optional, Callable

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

logger = logging.getLogger(__name__)

def sync_roles_between_accounts(master_account_id: int, slave_account_id: int, 
                               sync_group_id: int, progress_callback: Optional[Callable] = None) -> Dict:
    """
    🔐 SINCRONIZAÇÃO DE ROLES ENTRE CONTAS
    
    Sincroniza roles da conta master para slave, criando primeiro os mapeamentos
    de pipelines e status necessários.
    
    Args:
        master_account_id: ID da conta master no banco local
        slave_account_id: ID da conta slave no banco local  
        sync_group_id: ID do grupo de sincronização
        progress_callback: Callback para atualização de progresso
        
    Returns:
        Dict com resultados da sincronização
    """
    logger.info("🔐 Iniciando sincronização de roles...")
    results = {
        'pipelines_mapped': 0,
        'stages_mapped': 0,
        'roles_created': 0,
        'roles_updated': 0,
        'roles_skipped': 0,
        'errors': [],
        'warnings': []
    }
    
    try:
        # === IMPORTS ===
        from src.services.kommo_api import KommoAPIService
        from src.models.kommo_account import KommoAccount, PipelineMapping, StageMapping
        from src.database import db
        
        # === FASE 1: OBTER DADOS DAS CONTAS DO BANCO LOCAL ===
        logger.info("📊 Obtendo dados das contas do banco local...")
        
        master_account = KommoAccount.query.get(master_account_id)
        slave_account = KommoAccount.query.get(slave_account_id)
        
        if not master_account:
            error_msg = f"Conta master ID {master_account_id} não encontrada"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
            
        if not slave_account:
            error_msg = f"Conta slave ID {slave_account_id} não encontrada"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
        
        logger.info(f"Master: {master_account.subdomain}")
        logger.info(f"Slave: {slave_account.subdomain}")
        
        # === FASE 2: CRIAR INSTÂNCIAS DAS APIs ===
        logger.info("🔗 Conectando às APIs das contas...")
        
        master_api = KommoAPIService(master_account.subdomain, master_account.access_token)
        slave_api = KommoAPIService(slave_account.subdomain, slave_account.access_token)
        
        # === FASE 3: MAPEAR PIPELINES ===
        logger.info("📊 Mapeando pipelines master → slave...")
        
        if progress_callback:
            progress_callback({'operation': 'Mapeando pipelines', 'percentage': 10})
        
        try:
            master_pipelines = master_api.get_pipelines()
            slave_pipelines = slave_api.get_pipelines()
            
            logger.info(f"Master tem {len(master_pipelines)} pipelines")
            logger.info(f"Slave tem {len(slave_pipelines)} pipelines")
            
            # Mapear pipelines por nome
            pipeline_mappings = {}
            for master_pipeline in master_pipelines:
                master_name = master_pipeline['name']
                master_id = master_pipeline['id']
                
                # Procurar pipeline correspondente na slave
                slave_pipeline = next((p for p in slave_pipelines if p['name'] == master_name), None)
                
                if slave_pipeline:
                    slave_id = slave_pipeline['id']
                    pipeline_mappings[master_id] = slave_id
                    logger.info(f"Pipeline mapeado: '{master_name}' {master_id} → {slave_id}")
                    
                    # Salvar no banco
                    _save_pipeline_mapping(master_id, slave_id, sync_group_id)
                    results['pipelines_mapped'] += 1
                else:
                    warning = f"Pipeline '{master_name}' não encontrado na slave"
                    logger.warning(warning)
                    results['warnings'].append(warning)
            
            logger.info(f"✅ {len(pipeline_mappings)} pipelines mapeados")
            
        except Exception as e:
            error_msg = f"Erro ao mapear pipelines: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
        
        # === FASE 4: MAPEAR STAGES/STATUS ===
        logger.info("🎭 Mapeando stages/status master → slave...")
        
        if progress_callback:
            progress_callback({'operation': 'Mapeando stages', 'percentage': 30})
        
        stage_mappings = {}
        
        try:
            for master_pipeline_id, slave_pipeline_id in pipeline_mappings.items():
                logger.info(f"Mapeando stages do pipeline {master_pipeline_id} → {slave_pipeline_id}")
                
                master_stages = master_api.get_pipeline_stages(master_pipeline_id)
                slave_stages = slave_api.get_pipeline_stages(slave_pipeline_id)
                
                # Mapear stages por nome
                for master_stage in master_stages:
                    master_stage_name = master_stage['name']
                    master_stage_id = master_stage['id']
                    
                    # Procurar stage correspondente na slave
                    slave_stage = next((s for s in slave_stages if s['name'] == master_stage_name), None)
                    
                    if slave_stage:
                        slave_stage_id = slave_stage['id']
                        stage_mappings[master_stage_id] = slave_stage_id
                        logger.info(f"Stage mapeado: '{master_stage_name}' {master_stage_id} → {slave_stage_id}")
                        
                        # Salvar no banco
                        _save_stage_mapping(master_stage_id, slave_stage_id, sync_group_id)
                        results['stages_mapped'] += 1
                    else:
                        warning = f"Stage '{master_stage_name}' não encontrado na slave"
                        logger.warning(warning)
                        results['warnings'].append(warning)
            
            logger.info(f"✅ {len(stage_mappings)} stages mapeados")
            
        except Exception as e:
            error_msg = f"Erro ao mapear stages: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
        
        # === FASE 5: SINCRONIZAR ROLES ===
        logger.info("🔐 Sincronizando roles master → slave...")
        
        if progress_callback:
            progress_callback({'operation': 'Sincronizando roles', 'percentage': 60})
        
        try:
            master_roles = master_api.get_roles()
            slave_roles = slave_api.get_roles()
            
            logger.info(f"Master tem {len(master_roles)} roles")
            logger.info(f"Slave tem {len(slave_roles)} roles")
            
            # Indexar roles da slave por nome
            slave_roles_by_name = {role['name']: role for role in slave_roles}
            
            # Processar cada role da master
            for role_index, master_role in enumerate(master_roles, 1):
                role_name = master_role['name']
                logger.info(f"[{role_index}/{len(master_roles)}] Processando role: '{role_name}'")
                
                if progress_callback:
                    progress_callback({
                        'operation': f'Processando role {role_name}',
                        'percentage': 60 + (role_index / len(master_roles)) * 30
                    })
                
                try:
                    # Preparar dados da role
                    role_data = _prepare_role_data(master_role, pipeline_mappings, stage_mappings)
                    
                    if role_name in slave_roles_by_name:
                        # Atualizar role existente
                        slave_role = slave_roles_by_name[role_name]
                        slave_role_id = slave_role['id']
                        
                        logger.info(f"Atualizando role existente: '{role_name}' (ID: {slave_role_id})")
                        updated_role = slave_api.update_role(slave_role_id, role_data)
                        
                        if updated_role:
                            results['roles_updated'] += 1
                            logger.info(f"✅ Role '{role_name}' atualizada com sucesso")
                        else:
                            error = f"Falha ao atualizar role '{role_name}'"
                            logger.error(error)
                            results['errors'].append(error)
                    else:
                        # Criar nova role
                        logger.info(f"Criando nova role: '{role_name}'")
                        new_role = slave_api.create_role(role_data)
                        
                        if new_role:
                            results['roles_created'] += 1
                            logger.info(f"✅ Role '{role_name}' criada com sucesso")
                        else:
                            error = f"Falha ao criar role '{role_name}'"
                            logger.error(error)
                            results['errors'].append(error)
                            
                except Exception as role_error:
                    error = f"Erro ao processar role '{role_name}': {role_error}"
                    logger.error(error)
                    results['errors'].append(error)
                    continue
            
        except Exception as e:
            error_msg = f"Erro ao sincronizar roles: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
        
        # === FASE 6: FINALIZAÇÃO ===
        if progress_callback:
            progress_callback({'operation': 'Finalizando', 'percentage': 100})
        
        logger.info("🎉 Sincronização de roles concluída!")
        logger.info(f"📊 Resultados:")
        logger.info(f"   Pipelines mapeados: {results['pipelines_mapped']}")
        logger.info(f"   Stages mapeados: {results['stages_mapped']}")
        logger.info(f"   Roles criadas: {results['roles_created']}")
        logger.info(f"   Roles atualizadas: {results['roles_updated']}")
        logger.info(f"   Avisos: {len(results['warnings'])}")
        logger.info(f"   Erros: {len(results['errors'])}")
        
        return results
        
    except Exception as e:
        error_msg = f"Erro geral na sincronização de roles: {e}"
        logger.error(error_msg)
        results['errors'].append(error_msg)
        return results

def _prepare_role_data(master_role: Dict, pipeline_mappings: Dict, stage_mappings: Dict) -> Dict:
    """Prepara dados da role para envio à slave, mapeando IDs"""
    role_name = master_role['name']
    logger.info(f"Preparando dados para role: '{role_name}'")
    
    role_data = {
        'name': master_role['name'],
        'rights': {}
    }
    
    master_rights = master_role.get('rights', {})
    
    # Copiar direitos básicos
    for entity in ['leads', 'contacts', 'companies', 'tasks']:
        if entity in master_rights:
            role_data['rights'][entity] = master_rights[entity].copy()
    
    # Copiar direitos de acesso
    access_rights = ['mail_access', 'catalog_access', 'files_access']
    for access_right in access_rights:
        role_data['rights'][access_right] = master_rights.get(access_right, False)
    
    # Mapear status_rights (CRÍTICO)
    if master_rights.get('status_rights'):
        logger.info(f"Mapeando {len(master_rights['status_rights'])} status_rights...")
        
        mapped_status_rights = []
        successful_mappings = 0
        failed_mappings = 0
        
        for sr in master_rights['status_rights']:
            master_pipeline_id = sr.get('pipeline_id')
            master_status_id = sr.get('status_id')
            entity_type = sr.get('entity_type', 'leads')
            rights = sr.get('rights', {})
            
            # Mapear pipeline_id
            slave_pipeline_id = pipeline_mappings.get(master_pipeline_id)
            if not slave_pipeline_id:
                logger.warning(f"Pipeline {master_pipeline_id} não encontrado nos mapeamentos")
                failed_mappings += 1
                continue
            
            # Mapear status_id
            slave_status_id = stage_mappings.get(master_status_id)
            if not slave_status_id:
                logger.warning(f"Status {master_status_id} não encontrado nos mapeamentos")
                failed_mappings += 1
                continue
            
            # Criar status_right mapeado
            mapped_status_right = {
                'entity_type': entity_type,
                'pipeline_id': slave_pipeline_id,
                'status_id': slave_status_id,
                'rights': rights
            }
            
            mapped_status_rights.append(mapped_status_right)
            successful_mappings += 1
            
            logger.debug(f"Mapeado: pipeline {master_pipeline_id}→{slave_pipeline_id}, status {master_status_id}→{slave_status_id}")
        
        logger.info(f"Status rights: {successful_mappings}/{len(master_rights['status_rights'])} mapeados")
        
        if failed_mappings > 0:
            logger.warning(f"{failed_mappings} status_rights falharam no mapeamento")
        
        role_data['rights']['status_rights'] = mapped_status_rights
    else:
        role_data['rights']['status_rights'] = []
    
    return role_data

def _save_pipeline_mapping(master_id: int, slave_id: int, sync_group_id: int):
    """Salva mapeamento de pipeline no banco"""
    try:
        from src.models.kommo_account import PipelineMapping
        from src.database import db
        
        # Verificar se já existe
        existing = PipelineMapping.query.filter_by(
            master_id=master_id,
            sync_group_id=sync_group_id
        ).first()
        
        if existing:
            # Atualizar
            existing.slave_id = slave_id
            logger.debug(f"Atualizando mapeamento pipeline: {master_id} → {slave_id}")
        else:
            # Criar novo
            mapping = PipelineMapping(
                master_id=master_id,
                slave_id=slave_id,
                sync_group_id=sync_group_id
            )
            db.session.add(mapping)
            logger.debug(f"Criando mapeamento pipeline: {master_id} → {slave_id}")
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Erro ao salvar mapeamento pipeline: {e}")
        if 'db' in locals():
            db.session.rollback()

def _save_stage_mapping(master_id: int, slave_id: int, sync_group_id: int):
    """Salva mapeamento de stage no banco"""
    try:
        from src.models.kommo_account import StageMapping
        from src.database import db
        
        # Verificar se já existe
        existing = StageMapping.query.filter_by(
            master_id=master_id,
            sync_group_id=sync_group_id
        ).first()
        
        if existing:
            # Atualizar
            existing.slave_id = slave_id
            logger.debug(f"Atualizando mapeamento stage: {master_id} → {slave_id}")
        else:
            # Criar novo
            mapping = StageMapping(
                master_id=master_id,
                slave_id=slave_id,
                sync_group_id=sync_group_id
            )
            db.session.add(mapping)
            logger.debug(f"Criando mapeamento stage: {master_id} → {slave_id}")
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Erro ao salvar mapeamento stage: {e}")
        if 'db' in locals():
            db.session.rollback()

if __name__ == "__main__":
    print("Este é um módulo de serviço. Use import para importar a função sync_roles_between_accounts")
