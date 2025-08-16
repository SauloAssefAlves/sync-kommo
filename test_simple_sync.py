"""
🔐 TESTE SIMPLES DE SINCRONIZAÇÃO DE ROLES
"""

import os
import sys
import sqlite3

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_simple():
    """Teste simples sem Flask"""
    print("🔐 TESTE SIMPLES DE SYNC ROLES")
    print("=" * 50)
    
    # Verificar banco
    db_path = os.path.join('src', 'database', 'app.db')
    if not os.path.exists(db_path):
        print(f"❌ Banco não encontrado: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar contas
    cursor.execute('''
        SELECT id, subdomain, account_role, sync_group_id
        FROM kommo_accounts 
        ORDER BY account_role DESC, id
    ''')
    
    accounts = cursor.fetchall()
    print(f"📊 Encontradas {len(accounts)} contas:")
    
    for account in accounts:
        account_id, subdomain, role, group_id = account
        print(f"   • {subdomain} ({role}) - ID: {account_id} - Grupo: {group_id}")
    
    # Buscar grupos
    cursor.execute('''
        SELECT sg.id, sg.name, sg.master_account_id, ka.subdomain
        FROM sync_groups sg
        JOIN kommo_accounts ka ON sg.master_account_id = ka.id
        WHERE sg.is_active = 1
    ''')
    
    groups = cursor.fetchall()
    print(f"\n📁 Encontrados {len(groups)} grupos:")
    
    for group in groups:
        group_id, name, master_id, master_subdomain = group
        print(f"   • {name} - Master: {master_subdomain}")
        
        # Buscar slaves
        cursor.execute('''
            SELECT id, subdomain 
            FROM kommo_accounts 
            WHERE sync_group_id = ? AND account_role = 'slave'
        ''', (group_id,))
        
        slaves = cursor.fetchall()
        for slave_id, slave_subdomain in slaves:
            print(f"     └─ Slave: {slave_subdomain}")
    
    conn.close()
    
    if not groups:
        print("❌ Nenhum grupo encontrado")
        return
    
    # Usar primeiro grupo
    test_group = groups[0]
    group_id, group_name, master_id, master_subdomain = test_group
    
    print(f"\n🎯 Testando com grupo: {group_name}")
    print(f"   Master: {master_subdomain} (ID: {master_id})")
    
    # Buscar slave do grupo
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, subdomain 
        FROM kommo_accounts 
        WHERE sync_group_id = ? AND account_role = 'slave'
        LIMIT 1
    ''', (group_id,))
    
    slave_result = cursor.fetchone()
    if not slave_result:
        print("❌ Nenhuma slave encontrada")
        conn.close()
        return
    
    slave_id, slave_subdomain = slave_result
    print(f"   Slave: {slave_subdomain} (ID: {slave_id})")
    
    conn.close()
    
    print(f"\n🚀 Dados para sync roles:")
    print(f"   Master ID: {master_id}")
    print(f"   Slave ID: {slave_id}")
    print(f"   Grupo ID: {group_id}")
    
    print(f"\n✅ Teste concluído! Use estes IDs para sincronizar roles.")

if __name__ == "__main__":
    test_simple()
