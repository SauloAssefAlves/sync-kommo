#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para simular testes de sincronização de roles usando as contas importadas

Este script:
1. Usa as contas importadas (evoresultdev como master, testedev como slave)
2. Simula a sincronização de roles entre elas
3. Testa a funcionalidade sync_roles_to_slave com dados reais
4. Valida mapeamentos e diagnósticos
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import db
from src.models.kommo_account import KommoAccount, SyncGroup, PipelineMapping, StageMapping
from src.services.kommo_api import KommoSyncService, KommoAPIService

def create_mock_api_service(subdomain: str):
    """Cria um mock do serviço de API para testes"""
    
    class MockKommoAPIService:
        def __init__(self, subdomain):
            self.subdomain = subdomain
            
        def get_roles(self):
            """Simula roles específicas para cada conta"""
            if self.subdomain == "evoresultdev":  # Master account
                return [
                    {
                        'id': 1001,
                        'name': 'Vendedor Senior',
                        'rights': {
                            'leads': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'D'},
                            'contacts': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'D'},
                            'companies': {'view': 'A', 'edit': 'G', 'add': 'G', 'delete': 'N'},
                            'tasks': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'G'},
                            'mail_access': True,
                            'catalog_access': False,
                            'files_access': True,
                            'status_rights': [
                                {
                                    'entity_type': 'leads',
                                    'pipeline_id': 2001,  # Master pipeline ID
                                    'status_id': 3001,    # Master status ID
                                    'rights': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'G'}
                                },
                                {
                                    'entity_type': 'leads',
                                    'pipeline_id': 2001,
                                    'status_id': 3002,
                                    'rights': {'view': 'A', 'edit': 'A', 'add': 'N', 'delete': 'N'}
                                },
                                {
                                    'entity_type': 'leads',
                                    'pipeline_id': 2002,  # Segundo pipeline
                                    'status_id': 3003,
                                    'rights': {'view': 'A', 'edit': 'G', 'add': 'G', 'delete': 'N'}
                                }
                            ]
                        }
                    },
                    {
                        'id': 1002,
                        'name': 'Manager',
                        'rights': {
                            'leads': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'A'},
                            'contacts': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'A'},
                            'companies': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'A'},
                            'tasks': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'A'},
                            'mail_access': True,
                            'catalog_access': True,
                            'files_access': True,
                            'status_rights': [
                                {
                                    'entity_type': 'leads',
                                    'pipeline_id': 2001,
                                    'status_id': 3001,
                                    'rights': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'A'}
                                },
                                {
                                    'entity_type': 'leads',
                                    'pipeline_id': 2001,
                                    'status_id': 3002,
                                    'rights': {'view': 'A', 'edit': 'A', 'add': 'A', 'delete': 'A'}
                                }
                            ]
                        }
                    }
                ]
            else:  # Slave account (testedev)
                return [
                    {
                        'id': 2001,
                        'name': 'Vendedor Senior',  # Role que já existe
                        'rights': {
                            'leads': {'view': 'A', 'edit': 'G', 'add': 'G', 'delete': 'N'},
                            'contacts': {'view': 'A', 'edit': 'G', 'add': 'G', 'delete': 'N'},
                            'status_rights': []
                        }
                    }
                ]
        
        def create_role(self, role_data):
            """Simula criação de role"""
            new_id = 2000 + len(role_data.get('rights', {}).get('status_rights', [])) + 1
            print(f"   🔧 MOCK: Criando role '{role_data['name']}' com ID {new_id}")
            print(f"   📊 Status rights: {len(role_data.get('rights', {}).get('status_rights', []))}")
            return {'id': new_id, 'name': role_data['name']}
        
        def update_role(self, role_id, role_data):
            """Simula atualização de role"""
            print(f"   🔧 MOCK: Atualizando role ID {role_id} -> '{role_data['name']}'")
            print(f"   📊 Status rights: {len(role_data.get('rights', {}).get('status_rights', []))}")
            return {'id': role_id, 'name': role_data['name']}
    
    return MockKommoAPIService(subdomain)

def create_mock_mappings():
    """Cria mapeamentos mock para teste"""
    return {
        'pipelines': {
            2001: 5001,  # Master pipeline 2001 -> Slave pipeline 5001
            2002: 5002   # Master pipeline 2002 -> Slave pipeline 5002
        },
        'stages': {
            3001: 6001,  # Master status 3001 -> Slave status 6001
            3002: 6002,  # Master status 3002 -> Slave status 6002
            3003: 6003   # Master status 3003 -> Slave status 6003
        },
        'custom_field_groups': {},
        'roles': {}
    }

def create_test_mappings_in_database():
    """Cria mapeamentos de teste no banco de dados"""
    try:
        print("💾 Criando mapeamentos de teste no banco de dados...")
        
        sync_group_id = 3  # Grupo "Teste"
        slave_account_id = 2  # Conta testedev
        
        # Criar mapeamentos de pipelines
        pipeline_mappings = [
            (2001, 5001),  # Master -> Slave
            (2002, 5002)
        ]
        
        for master_id, slave_id in pipeline_mappings:
            existing = PipelineMapping.query.filter_by(
                sync_group_id=sync_group_id,
                master_pipeline_id=master_id,
                slave_account_id=slave_account_id
            ).first()
            
            if not existing:
                mapping = PipelineMapping(
                    sync_group_id=sync_group_id,
                    master_pipeline_id=master_id,
                    slave_account_id=slave_account_id,
                    slave_pipeline_id=slave_id
                )
                db.session.add(mapping)
                print(f"   📊 Pipeline mapping: {master_id} -> {slave_id}")
        
        # Criar mapeamentos de estágios
        stage_mappings = [
            (3001, 6001),  # Master -> Slave
            (3002, 6002),
            (3003, 6003)
        ]
        
        for master_id, slave_id in stage_mappings:
            existing = StageMapping.query.filter_by(
                sync_group_id=sync_group_id,
                master_stage_id=master_id,
                slave_account_id=slave_account_id
            ).first()
            
            if not existing:
                mapping = StageMapping(
                    sync_group_id=sync_group_id,
                    master_stage_id=master_id,
                    slave_account_id=slave_account_id,
                    slave_stage_id=slave_id
                )
                db.session.add(mapping)
                print(f"   🎭 Stage mapping: {master_id} -> {slave_id}")
        
        db.session.commit()
        print("✅ Mapeamentos de teste criados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar mapeamentos de teste: {e}")
        db.session.rollback()

def test_sync_roles_scenario_1():
    """Teste 1: Sincronização básica com mapeamentos vazios"""
    print("\n" + "="*60)
    print("🧪 TESTE 1: Sincronização com mapeamentos vazios")
    print("="*60)
    
    # Configurar APIs mock
    master_api = create_mock_api_service("evoresultdev")
    slave_api = create_mock_api_service("testedev")
    
    # Criar serviço de sincronização
    sync_service = KommoSyncService(master_api)
    
    # Extrair configuração da master
    print("📖 Extraindo roles da conta master...")
    master_config = {'roles': master_api.get_roles()}
    print(f"✅ {len(master_config['roles'])} roles encontradas na master")
    
    # Mapeamentos vazios (simula quando não há sync de pipelines)
    empty_mappings = {'pipelines': {}, 'stages': {}, 'roles': {}}
    
    # Executar sincronização
    print("\n🔄 Executando sync_roles_to_slave com mapeamentos vazios...")
    results = sync_service.sync_roles_to_slave(
        slave_api=slave_api,
        master_config=master_config,
        mappings=empty_mappings,
        sync_group_id=3,
        slave_account_id=2
    )
    
    print("\n📊 RESULTADOS DO TESTE 1:")
    print(f"   ➕ Roles criadas: {results['created']}")
    print(f"   🔄 Roles atualizadas: {results['updated']}")
    print(f"   ⚠️ Avisos: {len(results['warnings'])}")
    print(f"   ❌ Erros: {len(results['errors'])}")
    
    if results['errors']:
        print("\n❌ ERROS ENCONTRADOS:")
        for error in results['errors']:
            print(f"   • {error}")
    
    if results['warnings']:
        print("\n⚠️ AVISOS:")
        for warning in results['warnings']:
            print(f"   • {warning}")

def test_sync_roles_scenario_2():
    """Teste 2: Sincronização com mapeamentos do banco de dados"""
    print("\n" + "="*60)
    print("🧪 TESTE 2: Sincronização com mapeamentos do banco")
    print("="*60)
    
    # Configurar APIs mock
    master_api = create_mock_api_service("evoresultdev")
    slave_api = create_mock_api_service("testedev")
    
    # Criar serviço de sincronização
    sync_service = KommoSyncService(master_api)
    
    # Extrair configuração da master
    print("📖 Extraindo roles da conta master...")
    master_config = {'roles': master_api.get_roles()}
    
    # Mapeamentos vazios inicialmente
    mappings = {'pipelines': {}, 'stages': {}, 'roles': {}}
    
    # Executar sincronização (deve carregar mapeamentos do banco)
    print("\n🔄 Executando sync_roles_to_slave (deve carregar do banco)...")
    results = sync_service.sync_roles_to_slave(
        slave_api=slave_api,
        master_config=master_config,
        mappings=mappings,
        sync_group_id=3,
        slave_account_id=2
    )
    
    print("\n📊 RESULTADOS DO TESTE 2:")
    print(f"   ➕ Roles criadas: {results['created']}")
    print(f"   🔄 Roles atualizadas: {results['updated']}")
    print(f"   ⚠️ Avisos: {len(results['warnings'])}")
    print(f"   ❌ Erros: {len(results['errors'])}")
    
    # Mostrar mapeamentos carregados
    final_pipelines = len(mappings.get('pipelines', {}))
    final_stages = len(mappings.get('stages', {}))
    print(f"\n🗺️ MAPEAMENTOS FINAIS:")
    print(f"   📊 Pipelines: {final_pipelines}")
    print(f"   🎭 Stages: {final_stages}")
    
    if final_pipelines > 0:
        print(f"   📊 Pipelines: {mappings['pipelines']}")
    if final_stages > 0:
        print(f"   🎭 Stages: {mappings['stages']}")

def test_sync_roles_scenario_3():
    """Teste 3: Sincronização com mapeamentos pré-carregados"""
    print("\n" + "="*60)
    print("🧪 TESTE 3: Sincronização com mapeamentos pré-carregados")
    print("="*60)
    
    # Configurar APIs mock
    master_api = create_mock_api_service("evoresultdev")
    slave_api = create_mock_api_service("testedev")
    
    # Criar serviço de sincronização
    sync_service = KommoSyncService(master_api)
    
    # Extrair configuração da master
    print("📖 Extraindo roles da conta master...")
    master_config = {'roles': master_api.get_roles()}
    
    # Usar mapeamentos mock
    mappings = create_mock_mappings()
    print(f"\n🗺️ Usando mapeamentos pré-carregados:")
    print(f"   📊 Pipelines: {mappings['pipelines']}")
    print(f"   🎭 Stages: {mappings['stages']}")
    
    # Executar sincronização
    print("\n🔄 Executando sync_roles_to_slave com mapeamentos válidos...")
    results = sync_service.sync_roles_to_slave(
        slave_api=slave_api,
        master_config=master_config,
        mappings=mappings,
        sync_group_id=3,
        slave_account_id=2
    )
    
    print("\n📊 RESULTADOS DO TESTE 3:")
    print(f"   ➕ Roles criadas: {results['created']}")
    print(f"   🔄 Roles atualizadas: {results['updated']}")
    print(f"   ⚠️ Avisos: {len(results['warnings'])}")
    print(f"   ❌ Erros: {len(results['errors'])}")
    
    if results['warnings']:
        print("\n⚠️ AVISOS:")
        for warning in results['warnings']:
            print(f"   • {warning}")

def test_roles_with_suspicious_ids():
    """Teste 4: Detectar IDs suspeitos em roles"""
    print("\n" + "="*60)
    print("🧪 TESTE 4: Detecção de IDs suspeitos")
    print("="*60)
    
    # Criar API mock com IDs suspeitos
    class MockAPIWithSuspiciousIDs:
        def __init__(self):
            self.subdomain = "evoresultdev"
            
        def get_roles(self):
            return [
                {
                    'id': 1001,
                    'name': 'Role com IDs suspeitos',
                    'rights': {
                        'leads': {'view': 'A', 'edit': 'A'},
                        'status_rights': [
                            {
                                'entity_type': 'leads',
                                'pipeline_id': 2001,
                                'status_id': 896123,  # ID suspeito (parece ser da slave)
                                'rights': {'view': 'A', 'edit': 'A'}
                            },
                            {
                                'entity_type': 'leads',
                                'pipeline_id': 2001,
                                'status_id': 897456,  # Outro ID suspeito
                                'rights': {'view': 'A', 'edit': 'G'}
                            },
                            {
                                'entity_type': 'leads',
                                'pipeline_id': 2001,
                                'status_id': 3001,  # ID normal
                                'rights': {'view': 'A', 'edit': 'A'}
                            }
                        ]
                    }
                }
            ]
    
    master_api = MockAPIWithSuspiciousIDs()
    slave_api = create_mock_api_service("testedev")
    
    sync_service = KommoSyncService(master_api)
    master_config = {'roles': master_api.get_roles()}
    mappings = create_mock_mappings()
    
    print("🔍 Testando detecção de IDs suspeitos...")
    results = sync_service.sync_roles_to_slave(
        slave_api=slave_api,
        master_config=master_config,
        mappings=mappings,
        sync_group_id=3,
        slave_account_id=2
    )
    
    print("\n📊 RESULTADOS DO TESTE 4:")
    print(f"   ⚠️ Avisos detectados: {len(results['warnings'])}")
    
    if results['warnings']:
        print("\n🚨 IDs SUSPEITOS DETECTADOS:")
        for warning in results['warnings']:
            if "ID SUSPEITO" in warning:
                print(f"   • {warning}")

def main():
    """Função principal"""
    print("🧪 SIMULAÇÃO DE TESTES - SYNC ROLES")
    print("Usando contas importadas do servidor remoto")
    print("=" * 60)
    
    # Inicializar contexto da aplicação
    from src.main import app
    
    with app.app_context():
        try:
            # Verificar contas disponíveis
            print("👥 Contas disponíveis para teste:")
            accounts = KommoAccount.query.all()
            for account in accounts:
                role_icon = "👑" if account.account_role == 'master' else "🔗"
                group_name = account.sync_group.name if account.sync_group else "Sem grupo"
                print(f"   {role_icon} {account.subdomain} ({account.account_role}) - {group_name}")
            
            # Verificar grupo de teste
            test_group = SyncGroup.query.filter_by(name="Teste").first()
            if test_group:
                print(f"\n📁 Grupo de teste: {test_group.name} (ID: {test_group.id})")
                print(f"   👑 Master: {test_group.master_account.subdomain if test_group.master_account else 'Não definida'}")
                print(f"   🔗 Slaves: {len(test_group.slave_accounts)} conta(s)")
            
            # Criar mapeamentos de teste no banco
            create_test_mappings_in_database()
            
            # Executar cenários de teste
            test_sync_roles_scenario_1()  # Sem mapeamentos
            test_sync_roles_scenario_2()  # Com mapeamentos do banco
            test_sync_roles_scenario_3()  # Com mapeamentos pré-carregados
            test_roles_with_suspicious_ids()  # Detecção de IDs suspeitos
            
            print("\n" + "="*60)
            print("✅ TODOS OS TESTES CONCLUÍDOS!")
            print("📋 RESUMO DOS CENÁRIOS TESTADOS:")
            print("   1. ❌ Mapeamentos vazios (deve falhar)")
            print("   2. ✅ Carregamento automático do banco")
            print("   3. ✅ Mapeamentos pré-carregados")
            print("   4. ⚠️ Detecção de IDs suspeitos")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Erro durante os testes: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
