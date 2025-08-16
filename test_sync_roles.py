#!/usr/bin/env python3
"""
Script para testar a sincronização de roles entre contas master e slave
Utiliza as contas evoresultdev (master) e testedev (slave)
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
        logging.FileHandler('sync_roles_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_sync_roles():
    """Testa a sincronização de roles entre master e slave"""
    
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("🔐 Iniciando teste de sincronização de roles...")
            
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
            
            # 2. Criar instâncias das APIs
            logger.info("🔧 Criando instâncias das APIs...")
            
            master_api = KommoAPIService(
                subdomain=master_account.subdomain,
                refresh_token=master_account.access_token  # Usando access_token como refresh_token
            )
            
            slave_api = KommoAPIService(
                subdomain=slave_account.subdomain,
                refresh_token=slave_account.access_token  # Usando access_token como refresh_token
            )
            
            # 3. Testar conectividade das APIs
            logger.info("🔍 Testando conectividade das APIs...")
            
            try:
                master_account_info = master_api.get_account_info()
                logger.info(f"✅ Master API funcionando: {master_account_info.get('name', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ Erro na API master: {e}")
                return False
                
            try:
                slave_account_info = slave_api.get_account_info()
                logger.info(f"✅ Slave API funcionando: {slave_account_info.get('name', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ Erro na API slave: {e}")
                return False
            
            # 4. Extrair roles da conta master
            logger.info("📋 Extraindo roles da conta master...")
            
            try:
                master_roles = master_api.get_roles()
                logger.info(f"✅ Encontradas {len(master_roles)} roles na master:")
                
                for role in master_roles:
                    logger.info(f"   🔐 {role['name']} (ID: {role['id']})")
                    # Log das permissões principais
                    rights = role.get('rights', {})
                    if rights:
                        main_rights = []
                        for key, value in rights.items():
                            if isinstance(value, dict):
                                permissions = [k for k, v in value.items() if v is True]
                                if permissions:
                                    main_rights.append(f"{key}: {', '.join(permissions[:3])}")
                            elif value is True:
                                main_rights.append(key)
                        
                        if main_rights:
                            logger.info(f"     📝 Principais permissões: {' | '.join(main_rights[:2])}")
                        
            except Exception as e:
                logger.error(f"❌ Erro ao extrair roles da master: {e}")
                return False
            
            # 5. Extrair roles da conta slave (antes da sincronização)
            logger.info("📋 Extraindo roles atuais da conta slave...")
            
            try:
                slave_roles_before = slave_api.get_roles()
                logger.info(f"✅ Encontradas {len(slave_roles_before)} roles na slave (antes):")
                
                for role in slave_roles_before:
                    logger.info(f"   🔐 {role['name']} (ID: {role['id']})")
                        
            except Exception as e:
                logger.error(f"❌ Erro ao extrair roles da slave: {e}")
                return False
            
            # 6. Criar serviço de sincronização
            logger.info("⚙️ Criando serviço de sincronização...")
            
            sync_service = KommoSyncService(master_api, batch_size=5, delay_between_batches=1.0)
            
            # 7. Extrair configuração completa da master (incluindo roles)
            logger.info("📊 Extraindo configuração completa da master...")
            
            try:
                master_config = sync_service.extract_master_configuration()
                
                roles_count = len(master_config.get('roles', []))
                pipelines_count = len(master_config.get('pipelines', []))
                
                logger.info(f"✅ Configuração extraída:")
                logger.info(f"   🔐 Roles: {roles_count}")
                logger.info(f"   📊 Pipelines: {pipelines_count}")
                
                # Log detalhado das roles extraídas
                for role in master_config.get('roles', []):
                    logger.info(f"   📝 Role extraída: {role['name']} (ID: {role['id']})")
                        
            except Exception as e:
                logger.error(f"❌ Erro ao extrair configuração da master: {e}")
                return False
            
            # 8. Verificar se existem roles para sincronizar
            if not master_config.get('roles'):
                logger.warning("⚠️ Nenhuma role encontrada na configuração da master")
                return False
            
            # 9. Testar sincronização de roles (implementar método específico se não existir)
            logger.info("🔄 Iniciando sincronização de roles...")
            
            try:
                # Verificar se existe método sync_roles_to_slave
                if hasattr(sync_service, 'sync_roles_to_slave'):
                    logger.info("✅ Método sync_roles_to_slave encontrado")
                    
                    # Carregar mapeamentos do banco de dados
                    logger.info("📊 Carregando mapeamentos do banco de dados...")
                    
                    try:
                        from sqlalchemy import text
                        
                        # Buscar mapeamentos de pipelines
                        pipeline_mappings_query = text("""
                        SELECT master_id, slave_id 
                        FROM sync_mappings 
                        WHERE type = 'pipeline' 
                        AND master_account_id = :master_id 
                        AND slave_account_id = :slave_id
                        """)
                        
                        result = db.session.execute(
                            pipeline_mappings_query, 
                            {"master_id": master_account.id, "slave_id": slave_account.id}
                        ).fetchall()
                        
                        pipeline_mappings = {row[0]: row[1] for row in result}
                        logger.info(f"✅ Carregados {len(pipeline_mappings)} mapeamentos de pipelines")
                        
                        # Buscar mapeamentos de etapas
                        stage_mappings_query = text("""
                        SELECT master_id, slave_id 
                        FROM sync_mappings 
                        WHERE type = 'stage' 
                        AND master_account_id = :master_id 
                        AND slave_account_id = :slave_id
                        """)
                        
                        result = db.session.execute(
                            stage_mappings_query, 
                            {"master_id": master_account.id, "slave_id": slave_account.id}
                        ).fetchall()
                        
                        stage_mappings = {row[0]: row[1] for row in result}
                        logger.info(f"✅ Carregados {len(stage_mappings)} mapeamentos de etapas")
                        
                        mappings = {
                            'pipelines': pipeline_mappings, 
                            'stages': stage_mappings, 
                            'roles': {}
                        }
                        
                    except Exception as e:
                        logger.error(f"❌ Erro ao carregar mapeamentos: {e}")
                        mappings = {'pipelines': {}, 'stages': {}, 'roles': {}}
                    
                    # Callback para acompanhar progresso
                    def progress_callback(progress):
                        logger.info(f"📈 Progresso: {progress['operation']} - {progress['processed']}/{progress['total']} ({progress['percentage']}%)")
                    
                    sync_results = sync_service.sync_roles_to_slave(
                        slave_api, 
                        master_config, 
                        mappings, 
                        progress_callback=progress_callback
                    )
                    
                    logger.info(f"🎯 Resultados da sincronização de roles:")
                    logger.info(f"   ✅ Criadas: {sync_results.get('created', 0)}")
                    logger.info(f"   🔄 Atualizadas: {sync_results.get('updated', 0)}")
                    logger.info(f"   ⏭️ Ignoradas: {sync_results.get('skipped', 0)}")
                    logger.info(f"   🗑️ Deletadas: {sync_results.get('deleted', 0)}")
                    
                    if sync_results.get('errors'):
                        logger.warning(f"⚠️ Erros encontrados: {len(sync_results['errors'])}")
                        for error in sync_results['errors'][:3]:  # Mostrar apenas os primeiros 3 erros
                            logger.warning(f"   ❌ {error}")
                else:
                    logger.warning("⚠️ Método sync_roles_to_slave não implementado ainda")
                    logger.info("ℹ️ Simulando sincronização de roles...")
                    
                    # Simular comparação manual
                    slave_role_names = {role['name'] for role in slave_roles_before}
                    master_role_names = {role['name'] for role in master_config['roles']}
                    
                    roles_to_create = master_role_names - slave_role_names
                    roles_to_update = master_role_names & slave_role_names
                    roles_to_delete = slave_role_names - master_role_names
                    
                    logger.info(f"📊 Análise de sincronização:")
                    logger.info(f"   🆕 Roles a criar: {len(roles_to_create)} - {list(roles_to_create)}")
                    logger.info(f"   🔄 Roles a atualizar: {len(roles_to_update)} - {list(roles_to_update)}")
                    logger.info(f"   🗑️ Roles a deletar: {len(roles_to_delete)} - {list(roles_to_delete)}")
                    
            except Exception as e:
                logger.error(f"❌ Erro na sincronização de roles: {e}")
                return False
            
            # 10. Verificar roles na slave após sincronização
            logger.info("🔍 Verificando roles na slave após sincronização...")
            
            try:
                slave_roles_after = slave_api.get_roles()
                logger.info(f"✅ Roles na slave após sincronização: {len(slave_roles_after)}")
                
                for role in slave_roles_after:
                    logger.info(f"   🔐 {role['name']} (ID: {role['id']})")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao verificar roles pós-sincronização: {e}")
                return False
            
            logger.info("🎉 Teste de sincronização de roles concluído com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro geral no teste: {e}")
            return False

if __name__ == "__main__":
    success = test_sync_roles()
    if success:
        print("\n✅ Teste de sincronização de roles executado com sucesso!")
    else:
        print("\n❌ Falha no teste de sincronização de roles!")
        sys.exit(1)
