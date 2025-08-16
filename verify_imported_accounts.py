"""
📊 VERIFICADOR DE CONTAS IMPORTADAS
Valida e mostra detalhes das contas clonadas no banco local
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

def verify_imported_accounts():
    """Verifica as contas importadas no banco local"""
    db_path = os.path.join('src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return
    
    print("📊 VERIFICAÇÃO DAS CONTAS IMPORTADAS")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # === ESTATÍSTICAS GERAIS ===
    print("📈 ESTATÍSTICAS GERAIS:")
    
    cursor.execute('SELECT COUNT(*) FROM kommo_accounts')
    total_accounts = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM kommo_accounts WHERE account_role = "master"')
    master_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM kommo_accounts WHERE account_role = "slave"')
    slave_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sync_groups')
    groups_count = cursor.fetchone()[0]
    
    print(f"   👥 Total de contas: {total_accounts}")
    print(f"   👑 Contas Master: {master_count}")
    print(f"   🔗 Contas Slave: {slave_count}")
    print(f"   📁 Grupos de sincronização: {groups_count}")
    
    # === DETALHES DAS CONTAS ===
    print(f"\n👥 DETALHES DAS CONTAS:")
    print("-" * 40)
    
    cursor.execute('''
        SELECT ka.id, ka.subdomain, ka.account_role, ka.access_token,
               ka.refresh_token, ka.token_expires_at, ka.sync_group_id,
               ka.is_master, ka.created_at
        FROM kommo_accounts ka
        ORDER BY ka.account_role DESC, ka.id
    ''')
    
    accounts = cursor.fetchall()
    for account in accounts:
        (account_id, subdomain, role, access_token, refresh_token, 
         expires_at, group_id, is_master, created_at) = account
        
        print(f"\n🏷️ CONTA #{account_id}: {subdomain}")
        print(f"   📍 Role: {role} (is_master: {bool(is_master)})")
        print(f"   🔑 Access Token: {access_token[:30]}...")
        print(f"   🔄 Refresh Token: {refresh_token[:30]}...")
        print(f"   ⏰ Token expira: {expires_at}")
        print(f"   📁 Grupo: {group_id if group_id else 'Sem grupo'}")
        print(f"   📅 Criado: {created_at}")
    
    # === DETALHES DOS GRUPOS ===
    print(f"\n📁 DETALHES DOS GRUPOS:")
    print("-" * 40)
    
    cursor.execute('''
        SELECT sg.id, sg.name, sg.description, sg.master_account_id,
               sg.is_active, sg.created_at, ka.subdomain as master_subdomain
        FROM sync_groups sg
        LEFT JOIN kommo_accounts ka ON sg.master_account_id = ka.id
        ORDER BY sg.id
    ''')
    
    groups = cursor.fetchall()
    for group in groups:
        (group_id, name, description, master_id, is_active, 
         created_at, master_subdomain) = group
        
        print(f"\n📂 GRUPO #{group_id}: {name}")
        print(f"   📝 Descrição: {description}")
        print(f"   👑 Master: {master_subdomain} (ID: {master_id})")
        print(f"   ✅ Ativo: {bool(is_active)}")
        print(f"   📅 Criado: {created_at}")
        
        # Buscar slaves associadas
        cursor.execute('''
            SELECT id, subdomain, account_role 
            FROM kommo_accounts 
            WHERE sync_group_id = ?
            ORDER BY subdomain
        ''', (group_id,))
        
        slaves = cursor.fetchall()
        if slaves:
            print(f"   🔗 Slaves associadas: {len(slaves)}")
            for slave in slaves:
                slave_id, slave_subdomain, slave_role = slave
                print(f"      • {slave_subdomain} ({slave_role}) - ID: {slave_id}")
        else:
            print(f"   🔗 Slaves associadas: 0")
    
    # === VALIDAÇÕES ===
    print(f"\n✅ VALIDAÇÕES:")
    print("-" * 40)
    
    validations = []
    
    # 1. Verificar se todas as contas têm tokens
    cursor.execute('''
        SELECT COUNT(*) FROM kommo_accounts 
        WHERE access_token IS NULL OR access_token = '' 
           OR refresh_token IS NULL OR refresh_token = ''
    ''')
    accounts_without_tokens = cursor.fetchone()[0]
    
    if accounts_without_tokens == 0:
        validations.append("✅ Todas as contas têm tokens válidos")
    else:
        validations.append(f"❌ {accounts_without_tokens} contas sem tokens")
    
    # 2. Verificar consistência is_master vs account_role
    cursor.execute('''
        SELECT COUNT(*) FROM kommo_accounts 
        WHERE (account_role = 'master' AND is_master = 0) 
           OR (account_role = 'slave' AND is_master = 1)
    ''')
    inconsistent_roles = cursor.fetchone()[0]
    
    if inconsistent_roles == 0:
        validations.append("✅ Roles consistentes entre account_role e is_master")
    else:
        validations.append(f"❌ {inconsistent_roles} contas com roles inconsistentes")
    
    # 3. Verificar se grupos têm masters válidos
    cursor.execute('''
        SELECT COUNT(*) FROM sync_groups sg
        LEFT JOIN kommo_accounts ka ON sg.master_account_id = ka.id
        WHERE ka.id IS NULL OR ka.account_role != 'master'
    ''')
    invalid_masters = cursor.fetchone()[0]
    
    if invalid_masters == 0:
        validations.append("✅ Todos os grupos têm masters válidos")
    else:
        validations.append(f"❌ {invalid_masters} grupos com masters inválidos")
    
    # 4. Verificar slaves órfãs (sem grupo)
    cursor.execute('''
        SELECT COUNT(*) FROM kommo_accounts 
        WHERE account_role = 'slave' AND sync_group_id IS NULL
    ''')
    orphan_slaves = cursor.fetchone()[0]
    
    if orphan_slaves == 0:
        validations.append("✅ Todas as slaves estão associadas a grupos")
    else:
        validations.append(f"⚠️ {orphan_slaves} slaves sem grupo (órfãs)")
    
    for validation in validations:
        print(f"   {validation}")
    
    # === MAPEAMENTOS ===
    print(f"\n🗺️ MAPEAMENTOS EXISTENTES:")
    print("-" * 40)
    
    cursor.execute('SELECT COUNT(*) FROM pipeline_mappings')
    pipeline_mappings = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM stage_mappings')
    stage_mappings = cursor.fetchone()[0]
    
    print(f"   📊 Pipeline mappings: {pipeline_mappings}")
    print(f"   🎭 Stage mappings: {stage_mappings}")
    
    if pipeline_mappings == 0 and stage_mappings == 0:
        print("   💡 Nenhum mapeamento encontrado - execute sincronização de pipelines")
    
    # === PRÓXIMOS PASSOS ===
    print(f"\n🚀 PRÓXIMOS PASSOS RECOMENDADOS:")
    print("-" * 40)
    
    steps = [
        "1. 🔄 Executar sincronização de pipelines entre master e slave",
        "2. 🎯 Testar conectividade com as APIs das contas importadas", 
        "3. 📊 Sincronizar dados (leads, contatos, etc.)",
        "4. ✅ Validar funcionamento completo do sistema"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    # === COMANDOS ÚTEIS ===
    print(f"\n💡 COMANDOS ÚTEIS:")
    print("-" * 40)
    
    commands = [
        "# Testar APIs das contas:",
        "python test_api_connectivity.py",
        "",
        "# Sincronizar pipelines:",
        "POST /api/sync/trigger com sync_type='pipelines'",
        "",
        "# Ver logs detalhados:",
        "python view_sync_logs.py"
    ]
    
    for command in commands:
        print(f"   {command}")
    
    conn.close()
    
    # === SALVAR RELATÓRIO ===
    print(f"\n💾 Salvando relatório de verificação...")
    
    verification_report = {
        'verification_timestamp': datetime.now().isoformat(),
        'database_path': db_path,
        'statistics': {
            'total_accounts': total_accounts,
            'master_accounts': master_count,
            'slave_accounts': slave_count,
            'sync_groups': groups_count,
            'pipeline_mappings': pipeline_mappings,
            'stage_mappings': stage_mappings
        },
        'validations': {
            'accounts_without_tokens': accounts_without_tokens,
            'inconsistent_roles': inconsistent_roles,
            'invalid_group_masters': invalid_masters,
            'orphan_slaves': orphan_slaves
        },
        'ready_for_sync': (accounts_without_tokens == 0 and 
                          inconsistent_roles == 0 and 
                          invalid_masters == 0)
    }
    
    with open('verification_report.json', 'w', encoding='utf-8') as f:
        json.dump(verification_report, f, indent=2, ensure_ascii=False)
    
    print("📄 Relatório de verificação salvo em: verification_report.json")
    
    print("\n" + "="*60)
    if verification_report['ready_for_sync']:
        print("🎉 CONTAS IMPORTADAS E VALIDADAS COM SUCESSO!")
        print("✅ Sistema pronto para sincronização")
    else:
        print("⚠️ CONTAS IMPORTADAS COM ALGUNS PROBLEMAS")
        print("🔧 Verifique as validações acima antes de continuar")
    print("="*60)

if __name__ == "__main__":
    verify_imported_accounts()
