"""
🔐 TESTE DE SINCRONIZAÇÃO DE ROLES
Testa a nova função de sync roles usando as contas importadas
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_sync_roles():
    """Testa a sincronização de roles com as contas importadas"""
    print("🔐 TESTE DE SINCRONIZAÇÃO DE ROLES")
    print("=" * 60)
    
    # Verificar banco
    db_path = os.path.join('src', 'database', 'app.db')
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # === BUSCAR CONTAS IMPORTADAS ===
    print("📊 Buscando contas no banco local...")
    
    cursor.execute('''
        SELECT id, subdomain, account_role, access_token, sync_group_id
        FROM kommo_accounts 
        ORDER BY account_role DESC, id
    ''')
    
    accounts = cursor.fetchall()
    print(f"Encontradas {len(accounts)} contas:")
    
    master_accounts = []
    slave_accounts = []
    
    for account in accounts:
        account_id, subdomain, role, token, group_id = account
        print(f"   • {subdomain} ({role}) - ID: {account_id} - Grupo: {group_id}")
        
        if role == 'master':
            master_accounts.append(account)
        else:
            slave_accounts.append(account)
    
    if not master_accounts:
        print("❌ Nenhuma conta master encontrada")
        return
    
    if not slave_accounts:
        print("❌ Nenhuma conta slave encontrada")
        return
    
    # === BUSCAR GRUPOS DE SINCRONIZAÇÃO ===
    print(f"\n📁 Buscando grupos de sincronização...")
    
    cursor.execute('''
        SELECT sg.id, sg.name, sg.master_account_id, ka.subdomain as master_subdomain
        FROM sync_groups sg
        JOIN kommo_accounts ka ON sg.master_account_id = ka.id
        WHERE sg.is_active = 1
        ORDER BY sg.id
    ''')
    
    groups = cursor.fetchall()
    print(f"Encontrados {len(groups)} grupos ativos:")
    
    for group in groups:
        group_id, name, master_id, master_subdomain = group
        print(f"   • {name} (ID: {group_id}) - Master: {master_subdomain}")
        
        # Buscar slaves do grupo
        cursor.execute('''
            SELECT id, subdomain 
            FROM kommo_accounts 
            WHERE sync_group_id = ? AND account_role = 'slave'
        ''', (group_id,))
        
        group_slaves = cursor.fetchall()
        for slave_id, slave_subdomain in group_slaves:
            print(f"     └─ Slave: {slave_subdomain} (ID: {slave_id})")
    
    if not groups:
        print("❌ Nenhum grupo de sincronização encontrado")
        return
    
    # === ESCOLHER GRUPO PARA TESTE ===
    test_group = groups[0]  # Usar primeiro grupo
    group_id, group_name, master_id, master_subdomain = test_group
    
    print(f"\n🎯 Usando grupo para teste: {group_name}")
    print(f"   Master: {master_subdomain} (ID: {master_id})")
    
    # Buscar slave do grupo
    cursor.execute('''
        SELECT id, subdomain 
        FROM kommo_accounts 
        WHERE sync_group_id = ? AND account_role = 'slave'
        LIMIT 1
    ''', (group_id,))
    
    slave_result = cursor.fetchone()
    if not slave_result:
        print("❌ Nenhuma slave encontrada no grupo")
        return
    
    slave_id, slave_subdomain = slave_result
    print(f"   Slave: {slave_subdomain} (ID: {slave_id})")
    
    conn.close()
    
    # === EXECUTAR SINCRONIZAÇÃO ===
    print(f"\n🚀 Iniciando sincronização de roles...")
    print(f"   Master ID: {master_id}")
    print(f"   Slave ID: {slave_id}")
    print(f"   Grupo ID: {group_id}")
    
    try:
        # Importar a nova função independente
        from sync_roles_service import sync_roles_between_accounts
        
        # Callback para progresso
        def progress_callback(status):
            operation = status.get('operation', 'Processando')
            percentage = status.get('percentage', 0)
            print(f"   📊 {operation}... ({percentage:.1f}%)")
        
        # Executar sincronização
        results = sync_roles_between_accounts(
            master_account_id=master_id,
            slave_account_id=slave_id,
            sync_group_id=group_id,
            progress_callback=progress_callback
        )
        
        # === MOSTRAR RESULTADOS ===
        print(f"\n📊 RESULTADOS DA SINCRONIZAÇÃO:")
        print(f"   Pipelines mapeados: {results['pipelines_mapped']}")
        print(f"   Stages mapeados: {results['stages_mapped']}")
        print(f"   Roles criadas: {results['roles_created']}")
        print(f"   Roles atualizadas: {results['roles_updated']}")
        print(f"   Roles ignoradas: {results['roles_skipped']}")
        
        if results['warnings']:
            print(f"\n⚠️ AVISOS ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"   • {warning}")
        
        if results['errors']:
            print(f"\n❌ ERROS ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"   • {error}")
        else:
            print(f"\n✅ Sincronização concluída sem erros!")
        
        # === VERIFICAR MAPEAMENTOS CRIADOS ===
        print(f"\n🗺️ Verificando mapeamentos criados...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM pipeline_mappings WHERE sync_group_id = ?', (group_id,))
        pipeline_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM stage_mappings WHERE sync_group_id = ?', (group_id,))
        stage_count = cursor.fetchone()[0]
        
        print(f"   📊 Pipeline mappings: {pipeline_count}")
        print(f"   🎭 Stage mappings: {stage_count}")
        
        if pipeline_count > 0:
            print(f"\n📊 DETALHES DOS PIPELINE MAPPINGS:")
            cursor.execute('''
                SELECT master_id, slave_id 
                FROM pipeline_mappings 
                WHERE sync_group_id = ?
                ORDER BY master_id
            ''', (group_id,))
            
            for master_id, slave_id in cursor.fetchall():
                print(f"   • Pipeline: {master_id} → {slave_id}")
        
        if stage_count > 0:
            print(f"\n🎭 PRIMEIROS 10 STAGE MAPPINGS:")
            cursor.execute('''
                SELECT master_id, slave_id 
                FROM stage_mappings 
                WHERE sync_group_id = ?
                ORDER BY master_id
                LIMIT 10
            ''', (group_id,))
            
            for master_id, slave_id in cursor.fetchall():
                print(f"   • Stage: {master_id} → {slave_id}")
            
            if stage_count > 10:
                print(f"   ... e mais {stage_count - 10} mappings")
        
        conn.close()
        
        # === SALVAR RELATÓRIO ===
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'group_used': {
                'id': group_id,
                'name': group_name,
                'master_account_id': master_id,
                'slave_account_id': slave_id
            },
            'results': results,
            'mappings_created': {
                'pipelines': pipeline_count,
                'stages': stage_count
            }
        }
        
        with open('sync_roles_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: sync_roles_test_report.json")
        
        if results['errors']:
            print(f"\n⚠️ Teste concluído com erros - verifique os logs")
        else:
            print(f"\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sync_roles()
