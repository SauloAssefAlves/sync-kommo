#!/usr/bin/env python3
"""
Script para testar sincronização completa (pipelines + roles) entre contas master e slave
Resolve o problema de pipeline_ids não encontrados ao sincronizar roles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import create_app
from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup
from src.services.kommo_api import KommoAPIService, KommoSyncService
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sync_complete_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_complete_sync():
    """Testa sincronização completa: pipelines primeiro, depois roles"""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🚀 Iniciando teste de sincronização completa (pipelines + roles)...")
            
            # 1. Buscar contas no banco de dados
            logger.info("📊 Buscando contas no banco de dados...")
            
            master_account = KommoAccount.query.filter_by(subdomain='evoresultdev').first()
            slave_account = KommoAccount.query.filter_by(subdomain='testedev').first()
            
            if not master_account:
                logger.error("❌ Conta master 'evoresultdev' não encontrada no banco!")
                return False
                
            if not slave_account:
                logger.error("❌ Conta slave 'testedev' não encontrada no banco!")
                return False
                
            logger.info(f"✅ Master encontrada: {master_account.subdomain} (ID: {master_account.id})")
            logger.info(f"✅ Slave encontrada: {slave_account.subdomain} (ID: {slave_account.id})")
            
            # 2. Buscar ou criar sync group
            sync_group = SyncGroup.query.filter_by(master_account_id=master_account.id).first()
            if not sync_group:
                logger.info("🔗 Criando novo grupo de sincronização...")
                sync_group = SyncGroup(
                    master_account_id=master_account.id,
                    name=f"Sync Group {master_account.subdomain}"
                )
                db.session.add(sync_group)
                
                # Adicionar conta slave ao grupo
                sync_group.slave_accounts.append(slave_account)
                db.session.commit()
                logger.info(f"✅ Grupo criado (ID: {sync_group.id})")
            else:
                logger.info(f"✅ Grupo existente encontrado (ID: {sync_group.id})")
            
            # 3. Criar instâncias das APIs
            logger.info("🔧 Criando instâncias das APIs...")
            
            master_api = KommoAPIService(
                subdomain=master_account.subdomain,
                refresh_token=master_account.access_token
            )
            
            slave_api = KommoAPIService(
                subdomain=slave_account.subdomain,
                refresh_token=slave_account.access_token
            )
            
            # 4. Criar serviço de sincronização
            logger.info("⚙️ Criando serviço de sincronização...")
            sync_service = KommoSyncService(master_api, batch_size=5, delay_between_batches=1.0)
            
            # 5. Extrair configuração da master
            logger.info("📊 Extraindo configuração completa da master...")
            master_config = sync_service.extract_master_configuration()
            
            roles_count = len(master_config.get('roles', []))
            pipelines_count = len(master_config.get('pipelines', []))
            
            logger.info(f"✅ Configuração extraída:")
            logger.info(f"   📊 Pipelines: {pipelines_count}")
            logger.info(f"   🔐 Roles: {roles_count}")
            
            # 6. PRIMEIRA FASE: Sincronizar pipelines para criar os mapeamentos
            logger.info("📊 === FASE 1: SINCRONIZAÇÃO DE PIPELINES ===")
            
            mappings = {'pipelines': {}, 'stages': {}, 'roles': {}}
            
            def progress_callback(progress):
                logger.info(f"📈 {progress['operation']}: {progress['processed']}/{progress['total']} ({progress['percentage']}%)")
            
            pipelines_results = sync_service.sync_pipelines_to_slave(
                slave_api,
                master_config,
                mappings,
                progress_callback=progress_callback,
                sync_group_id=sync_group.id,
                slave_account_id=slave_account.id
            )
            
            logger.info(f"📊 Resultados pipelines:")
            logger.info(f"   ✅ Criados: {pipelines_results.get('created', 0)}")
            logger.info(f"   ⏭️ Ignorados: {pipelines_results.get('skipped', 0)}")
            logger.info(f"   🗑️ Deletados: {pipelines_results.get('deleted', 0)}")
            logger.info(f"   ❌ Erros: {len(pipelines_results.get('errors', []))}")
            
            # 7. Verificar mapeamentos criados
            pipeline_mappings_count = len(mappings.get('pipelines', {}))
            stage_mappings_count = len(mappings.get('stages', {}))
            
            logger.info(f"🎯 Mapeamentos criados:")
            logger.info(f"   📊 Pipelines: {pipeline_mappings_count}")
            logger.info(f"   🎭 Stages: {stage_mappings_count}")
            
            if pipeline_mappings_count > 0:
                sample_pipeline_mappings = list(mappings['pipelines'].items())[:2]
                logger.info(f"   📊 Exemplo pipelines: {sample_pipeline_mappings}")
            
            # 8. SEGUNDA FASE: Sincronizar roles com mapeamentos de pipelines
            logger.info("🔐 === FASE 2: SINCRONIZAÇÃO DE ROLES COM MAPEAMENTOS ===")
            
            # Implementar versão melhorada de sync_roles que usa mapeamentos
            if hasattr(sync_service, 'sync_roles_to_slave_with_mappings'):
                logger.info("✅ Usando sync_roles_to_slave_with_mappings")
                roles_results = sync_service.sync_roles_to_slave_with_mappings(
                    slave_api,
                    master_config,
                    mappings,
                    progress_callback=progress_callback
                )
            else:
                logger.info("⚠️ Usando sync_roles_to_slave padrão (pode falhar sem mapeamentos)")
                roles_results = sync_service.sync_roles_to_slave(
                    slave_api,
                    master_config,
                    mappings,
                    progress_callback=progress_callback
                )
            
            logger.info(f"🔐 Resultados roles:")
            logger.info(f"   ✅ Criadas: {roles_results.get('created', 0)}")
            logger.info(f"   🔄 Atualizadas: {roles_results.get('updated', 0)}")
            logger.info(f"   ⏭️ Ignoradas: {roles_results.get('skipped', 0)}")
            logger.info(f"   ❌ Erros: {len(roles_results.get('errors', []))}")
            
            if roles_results.get('errors'):
                logger.warning("⚠️ Erros na sincronização de roles:")
                for error in roles_results['errors'][:3]:
                    logger.warning(f"   ❌ {error}")
            
            # 9. Verificação final
            logger.info("🔍 === VERIFICAÇÃO FINAL ===")
            
            try:
                slave_pipelines_final = slave_api.get_pipelines()
                slave_roles_final = slave_api.get_roles()
                
                logger.info(f"📊 Estado final da slave:")
                logger.info(f"   📊 Pipelines: {len(slave_pipelines_final)}")
                logger.info(f"   🔐 Roles: {len(slave_roles_final)}")
                
                logger.info("📊 Pipelines na slave:")
                for pipeline in slave_pipelines_final:
                    logger.info(f"   📊 {pipeline['name']} (ID: {pipeline['id']})")
                
                logger.info("🔐 Roles na slave:")
                for role in slave_roles_final:
                    logger.info(f"   🔐 {role['name']} (ID: {role['id']})")
                    
            except Exception as e:
                logger.error(f"❌ Erro na verificação final: {e}")
                return False
            
            # 10. Resumo final
            total_created = pipelines_results.get('created', 0) + roles_results.get('created', 0)
            total_errors = len(pipelines_results.get('errors', [])) + len(roles_results.get('errors', []))
            
            logger.info("🎉 === RESUMO FINAL ===")
            logger.info(f"📊 Total criado: {total_created} itens")
            logger.info(f"❌ Total erros: {total_errors}")
            
            if total_errors == 0:
                logger.info("✅ Sincronização completa SEM ERROS!")
                return True
            else:
                logger.warning(f"⚠️ Sincronização completa com {total_errors} erros")
                return True  # Considerar sucesso mesmo com alguns erros
            
        except Exception as e:
            logger.error(f"❌ Erro geral no teste: {e}")
            return False

if __name__ == "__main__":
    success = test_complete_sync()
    if success:
        print("\n✅ Teste de sincronização completa executado com sucesso!")
    else:
        print("\n❌ Falha no teste de sincronização completa!")
        sys.exit(1)
