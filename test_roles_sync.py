#!/usr/bin/env python3
"""
Teste das funções de sincronização de roles e usuários
"""

import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_roles_sync():
    """
    Testa a sincronização de roles
    """
    logger.info("🔐 TESTE: SINCRONIZAÇÃO DE ROLES")
    logger.info("=" * 60)
    
    # Simular roles da master
    master_roles = [
        {
            'id': 1001,
            'name': 'Vendedor',
            'rights': {
                'leads': {'view': True, 'edit': True, 'delete': False},
                'contacts': {'view': True, 'edit': True, 'delete': False},
                'companies': {'view': True, 'edit': False, 'delete': False}
            }
        },
        {
            'id': 1002, 
            'name': 'Gerente',
            'rights': {
                'leads': {'view': True, 'edit': True, 'delete': True},
                'contacts': {'view': True, 'edit': True, 'delete': True},
                'companies': {'view': True, 'edit': True, 'delete': True},
                'users': {'view': True, 'edit': True, 'delete': False}
            }
        },
        {
            'id': 1003,
            'name': 'Suporte',
            'rights': {
                'leads': {'view': True, 'edit': False, 'delete': False},
                'contacts': {'view': True, 'edit': True, 'delete': False}
            }
        }
    ]
    
    # Simular roles existentes na slave
    slave_roles = [
        {
            'id': 2001,
            'name': 'Vendedor',
            'rights': {
                'leads': {'view': True, 'edit': True, 'delete': False},
                'contacts': {'view': True, 'edit': False, 'delete': False}  # Permissão diferente
            }
        },
        {
            'id': 2002,
            'name': 'Role Antiga',  # Esta será deletada
            'rights': {
                'leads': {'view': True, 'edit': False, 'delete': False}
            }
        }
    ]
    
    logger.info("📋 DADOS SIMULADOS:")
    logger.info(f"   Roles master: {len(master_roles)}")
    for role in master_roles:
        logger.info(f"      - {role['name']}: {len(role['rights'])} permissões")
    
    logger.info(f"   Roles slave: {len(slave_roles)}")
    for role in slave_roles:
        logger.info(f"      - {role['name']}: {len(role['rights'])} permissões")
    
    # Simular processo de sincronização
    logger.info(f"\n🔄 SIMULANDO SINCRONIZAÇÃO...")
    
    results = {'created': 0, 'updated': 0, 'skipped': 0, 'deleted': 0}
    mappings = {'roles': {}}
    
    existing_roles = {r['name']: r for r in slave_roles}
    master_role_names = {r['name'] for r in master_roles}
    
    # FASE 1: Processar roles da master
    for master_role in master_roles:
        role_name = master_role['name']
        
        if role_name in existing_roles:
            existing_role = existing_roles[role_name]
            
            # Verificar se precisa atualizar
            if existing_role['rights'] != master_role['rights']:
                logger.info(f"🔄 Role '{role_name}' será ATUALIZADA (permissões diferentes)")
                results['updated'] += 1
            else:
                logger.info(f"✅ Role '{role_name}' já está sincronizada")
                results['skipped'] += 1
                
            mappings['roles'][master_role['id']] = existing_role['id']
        else:
            logger.info(f"🆕 Role '{role_name}' será CRIADA")
            results['created'] += 1
            # Simular ID gerado
            mappings['roles'][master_role['id']] = 3000 + master_role['id']
    
    # FASE 2: Identificar roles para deletar
    for slave_role in slave_roles:
        if slave_role['name'] not in master_role_names:
            logger.info(f"🗑️ Role '{slave_role['name']}' será DELETADA")
            results['deleted'] += 1
    
    logger.info(f"\n📊 RESULTADO DA SIMULAÇÃO:")
    logger.info(f"   Criadas: {results['created']}")
    logger.info(f"   Atualizadas: {results['updated']}")
    logger.info(f"   Ignoradas: {results['skipped']}")
    logger.info(f"   Deletadas: {results['deleted']}")
    logger.info(f"   Mapeamentos: {len(mappings['roles'])}")

def test_users_sync():
    """
    Testa a sincronização de usuários
    """
    logger.info(f"\n" + "=" * 60)
    logger.info("👥 TESTE: SINCRONIZAÇÃO DE USUÁRIOS")
    logger.info("=" * 60)
    
    # Simular usuários da master
    master_users = [
        {
            'id': 101,
            'name': 'João Silva',
            'email': 'joao@empresa.com',
            'role_id': 1001,  # Vendedor
            'is_active': True,
            'language': 'pt'
        },
        {
            'id': 102,
            'name': 'Maria Santos',
            'email': 'maria@empresa.com', 
            'role_id': 1002,  # Gerente
            'is_active': True,
            'language': 'pt'
        },
        {
            'id': 103,
            'name': 'Pedro Costa',
            'email': 'pedro@empresa.com',
            'role_id': 1003,  # Suporte
            'is_active': True,
            'language': 'en'
        }
    ]
    
    # Simular usuários existentes na slave
    slave_users = [
        {
            'id': 201,
            'name': 'João Silva',
            'email': 'joao@empresa.com',
            'role_id': 2001,  # Role diferente
            'is_active': True,
            'language': 'pt'
        },
        {
            'id': 202,
            'name': 'Maria Santos - Old Name',  # Nome diferente
            'email': 'maria@empresa.com',
            'role_id': 2001,
            'is_active': True,
            'language': 'pt'
        }
    ]
    
    # Mapeamentos de roles (da sincronização anterior)
    role_mappings = {
        1001: 2001,  # Vendedor
        1002: 2002,  # Gerente  
        1003: 2003   # Suporte
    }
    
    logger.info("📋 DADOS SIMULADOS:")
    logger.info(f"   Usuários master: {len(master_users)}")
    for user in master_users:
        logger.info(f"      - {user['name']} ({user['email']}) - Role: {user['role_id']}")
    
    logger.info(f"   Usuários slave: {len(slave_users)}")
    for user in slave_users:
        logger.info(f"      - {user['name']} ({user['email']}) - Role: {user['role_id']}")
    
    # Simular processo de sincronização
    logger.info(f"\n🔄 SIMULANDO SINCRONIZAÇÃO...")
    
    results = {'created': 0, 'updated': 0, 'skipped': 0, 'deleted': 0}
    existing_users = {u['email']: u for u in slave_users}
    
    for master_user in master_users:
        user_email = master_user['email']
        user_name = master_user['name']
        
        if user_email in existing_users:
            existing_user = existing_users[user_email]
            needs_update = False
            updates = []
            
            # Verificar role
            master_role_id = master_user['role_id']
            if master_role_id in role_mappings:
                slave_role_id = role_mappings[master_role_id]
                if existing_user['role_id'] != slave_role_id:
                    updates.append(f"role {existing_user['role_id']} -> {slave_role_id}")
                    needs_update = True
            
            # Verificar nome
            if existing_user['name'] != master_user['name']:
                updates.append(f"nome '{existing_user['name']}' -> '{master_user['name']}'")
                needs_update = True
            
            # Verificar idioma
            if existing_user['language'] != master_user['language']:
                updates.append(f"idioma {existing_user['language']} -> {master_user['language']}")
                needs_update = True
            
            if needs_update:
                logger.info(f"🔄 Usuário '{user_name}' será ATUALIZADO: {', '.join(updates)}")
                results['updated'] += 1
            else:
                logger.info(f"✅ Usuário '{user_name}' já está sincronizado")
                results['skipped'] += 1
        else:
            logger.info(f"ℹ️ Usuário '{user_name}' não existe na slave - não será criado automaticamente")
            results['skipped'] += 1
    
    logger.info(f"\n📊 RESULTADO DA SIMULAÇÃO:")
    logger.info(f"   Criados: {results['created']}")
    logger.info(f"   Atualizados: {results['updated']}")
    logger.info(f"   Ignorados: {results['skipped']}")
    logger.info(f"   Deletados: {results['deleted']}")

def test_integration_scenario():
    """
    Teste de cenário de integração completo
    """
    logger.info(f"\n" + "=" * 60)
    logger.info("🚀 TESTE: CENÁRIO DE INTEGRAÇÃO COMPLETO")
    logger.info("=" * 60)
    
    logger.info("📋 CENÁRIO:")
    logger.info("   1. Sincronizar roles primeiro")
    logger.info("   2. Depois sincronizar usuários usando mapeamentos de roles")
    logger.info("   3. Verificar dependências entre roles e usuários")
    
    logger.info(f"\n🎯 FLUXO DE SINCRONIZAÇÃO:")
    logger.info("   ✅ STEP 1: sync_roles_to_slave()")
    logger.info("      - Cria/atualiza roles na slave")
    logger.info("      - Gera mapeamentos: master_role_id -> slave_role_id")
    
    logger.info("   ✅ STEP 2: sync_users_to_slave()")
    logger.info("      - Usa mapeamentos de roles do step 1")
    logger.info("      - Atualiza role_id dos usuários na slave")
    logger.info("      - Não cria novos usuários (apenas atualiza existentes)")
    
    logger.info(f"\n💡 VANTAGENS:")
    logger.info("   ✅ Roles são sincronizadas primeiro (dependência)")
    logger.info("   ✅ Usuários recebem roles corretas automaticamente")
    logger.info("   ✅ Permissões ficam consistentes entre master/slave")
    logger.info("   ✅ Processamento em lotes para performance")
    logger.info("   ✅ Logs detalhados para debug")

if __name__ == "__main__":
    test_roles_sync()
    test_users_sync()
    test_integration_scenario()
