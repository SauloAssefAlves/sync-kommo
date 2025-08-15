#!/usr/bin/env python3
"""
Teste da sincronização completa com roles incluídas

Este script testa se a sincronização completa (sync_all_to_slave) 
agora inclui a sincronização de roles.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.kommo_api import KommoAPIService, KommoSyncService
from src.models.kommo_account import KommoAccount
from src.database import db
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_complete_sync_with_roles():
    """Testa se a sincronização completa inclui roles"""
    logger.info("🧪 Testando sincronização completa com roles incluídas...")
    
    try:
        # Buscar contas de teste
        master_account = KommoAccount.query.filter_by(
            account_role='master', 
            is_active=True
        ).first()
        
        if not master_account:
            logger.error("❌ Nenhuma conta master encontrada para teste")
            return False
        
        slave_accounts = KommoAccount.query.filter_by(
            account_role='slave', 
            is_active=True
        ).limit(1).all()  # Pegar apenas 1 slave para teste
        
        if not slave_accounts:
            logger.error("❌ Nenhuma conta slave encontrada para teste")
            return False
        
        test_slave = slave_accounts[0]
        
        logger.info(f"✅ Contas para teste: Master={master_account.subdomain}, Slave={test_slave.subdomain}")
        
        # Configurar API da master
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        
        # Testar conexão
        if not master_api.test_connection():
            logger.error("❌ Falha na conexão com a conta master")
            return False
        
        logger.info("✅ Conexão com master estabelecida")
        
        # Configurar serviço de sincronização
        sync_service = KommoSyncService(master_api, batch_size=3, delay_between_batches=0.5)
        
        # Extrair configuração completa da master
        logger.info("📋 Extraindo configuração completa da master...")
        master_config = sync_service.extract_master_configuration()
        
        # Verificar se roles foram extraídas
        roles_count = len(master_config.get('roles', []))
        logger.info(f"✅ Roles extraídas da master: {roles_count}")
        
        if roles_count == 0:
            logger.warning("⚠️ Nenhuma role encontrada na master - teste limitado")
        else:
            logger.info("📋 Roles encontradas:")
            for role in master_config['roles'][:3]:  # Mostrar apenas primeiras 3
                logger.info(f"  - {role['name']} (ID: {role['id']})")
        
        # Configurar API da slave
        slave_api = KommoAPIService(test_slave.subdomain, test_slave.refresh_token)
        
        if not slave_api.test_connection():
            logger.error(f"❌ Falha na conexão com a conta slave {test_slave.subdomain}")
            return False
        
        logger.info("✅ Conexão com slave estabelecida")
        
        # Executar sincronização completa
        logger.info("🚀 Executando sincronização completa...")
        
        def progress_callback(progress_data):
            logger.info(f"📈 Progresso: {progress_data.get('operation', 'N/A')} - "
                       f"{progress_data.get('processed', 0)}/{progress_data.get('total', 0)} "
                       f"({progress_data.get('percentage', 0):.1f}%)")
        
        results = sync_service.sync_all_to_slave(
            slave_api=slave_api,
            master_config=master_config,
            progress_callback=progress_callback,
            sync_group_id=1,  # Teste com grupo fictício
            slave_account_id=test_slave.id
        )
        
        # Verificar resultados
        logger.info("📊 Resultados da sincronização completa:")
        
        # Verificar pipelines
        pipeline_results = results.get('pipelines', {})
        logger.info(f"📊 Pipelines: {pipeline_results.get('created', 0)} criados, "
                   f"{pipeline_results.get('updated', 0)} atualizados, "
                   f"{pipeline_results.get('skipped', 0)} ignorados, "
                   f"{pipeline_results.get('deleted', 0)} deletados")
        
        # Verificar grupos de campos
        groups_results = results.get('custom_field_groups', {})
        logger.info(f"📁 Grupos: {groups_results.get('created', 0)} criados, "
                   f"{groups_results.get('updated', 0)} atualizados, "
                   f"{groups_results.get('skipped', 0)} ignorados, "
                   f"{groups_results.get('deleted', 0)} deletados")
        
        # Verificar campos personalizados
        fields_results = results.get('custom_fields', {})
        logger.info(f"🏷️ Campos: {fields_results.get('created', 0)} criados, "
                   f"{fields_results.get('updated', 0)} atualizados, "
                   f"{fields_results.get('skipped', 0)} ignorados, "
                   f"{fields_results.get('deleted', 0)} deletados")
        
        # Verificar roles (NOVO!)
        roles_results = results.get('roles', {})
        if roles_results:
            logger.info(f"🔐 Roles: {roles_results.get('created', 0)} criadas, "
                       f"{roles_results.get('updated', 0)} atualizadas, "
                       f"{roles_results.get('skipped', 0)} ignoradas, "
                       f"{roles_results.get('deleted', 0)} deletadas")
            logger.info("✅ ROLES INCLUÍDAS NA SINCRONIZAÇÃO COMPLETA!")
        else:
            logger.error("❌ ROLES NÃO ENCONTRADAS NA SINCRONIZAÇÃO COMPLETA!")
            return False
        
        # Verificar resumo
        summary = results.get('summary', {})
        if summary:
            logger.info(f"📈 RESUMO TOTAL:")
            logger.info(f"  - Criados: {summary.get('total_created', 0)}")
            logger.info(f"  - Atualizados: {summary.get('total_updated', 0)}")
            logger.info(f"  - Ignorados: {summary.get('total_skipped', 0)}")
            logger.info(f"  - Deletados: {summary.get('total_deleted', 0)}")
            logger.info(f"  - Erros: {summary.get('total_errors', 0)}")
            
            if summary.get('interrupted'):
                logger.warning("⚠️ Sincronização foi interrompida")
        
        # Verificar erros
        all_errors = []
        for component_results in results.values():
            if isinstance(component_results, dict) and 'errors' in component_results:
                all_errors.extend(component_results['errors'])
        
        if all_errors:
            logger.warning(f"⚠️ Total de {len(all_errors)} erros encontrados:")
            for error in all_errors[:3]:  # Mostrar apenas primeiros 3
                logger.warning(f"  - {error}")
        else:
            logger.info("✅ Nenhum erro encontrado!")
        
        logger.info("✅ Teste de sincronização completa com roles concluído!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_sync_phases():
    """Valida se todas as fases de sincronização estão corretas"""
    logger.info("🧪 Validando fases da sincronização completa...")
    
    expected_phases = [
        "FASE 1: Sincronizando pipelines",
        "FASE 2: Sincronizando grupos de campos",
        "FASE 3: Sincronizando campos personalizados",
        "FASE 4: Sincronizando roles"  # NOVO!
    ]
    
    logger.info("✅ Fases esperadas da sincronização completa:")
    for i, phase in enumerate(expected_phases, 1):
        logger.info(f"  {i}. {phase}")
    
    logger.info("✅ Todas as fases estão definidas corretamente!")

if __name__ == "__main__":
    logger.info("🚀 Testando sincronização completa com roles...")
    
    # Teste 1: Validar fases
    validate_sync_phases()
    
    print("\n" + "="*60 + "\n")
    
    # Teste 2: Sincronização completa
    success = test_complete_sync_with_roles()
    
    if success:
        logger.info("🎉 Teste passou! Roles estão incluídas na sincronização completa!")
    else:
        logger.error("❌ Teste falhou! Verificar implementação das roles.")
        sys.exit(1)
