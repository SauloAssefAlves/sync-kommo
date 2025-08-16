"""
🔄 IMPORTADOR DE CONTAS REMOTO → LOCAL
Clona as contas master e slave do servidor remoto para o banco local
"""

import os
import sys
import json
import requests
import sqlite3
from datetime import datetime

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def fetch_remote_accounts():
    """Busca as contas do servidor remoto"""
    remote_url = "http://89.116.186.230:5000/api/sync/accounts/"
    
    print("🌐 Conectando ao servidor remoto...")
    print(f"📡 URL: {remote_url}")
    
    try:
        response = requests.get(remote_url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        accounts = data.get('accounts', [])
        
        print(f"✅ Conectado com sucesso!")
        print(f"📊 Encontradas {len(accounts)} contas no servidor remoto")
        
        return accounts
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar com servidor remoto: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar resposta JSON: {e}")
        return None

def setup_local_database():
    """Configura o banco de dados local"""
    db_path = os.path.join('src', 'database', 'app.db')
    
    # Criar diretório se não existir
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    print(f"💾 Configurando banco local: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Criar tabelas se não existirem
    print("📋 Criando/verificando estrutura das tabelas...")
    
    # Tabela de grupos de sincronização
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            master_account_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (master_account_id) REFERENCES kommo_accounts (id)
        )
    ''')
    
    # Tabela de contas Kommo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kommo_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subdomain VARCHAR(100) UNIQUE NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            token_expires_at DATETIME NOT NULL,
            sync_group_id INTEGER,
            account_role VARCHAR(20) DEFAULT 'slave',
            is_master BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sync_group_id) REFERENCES sync_groups (id)
        )
    ''')
    
    # Tabelas de mapeamentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            master_id INTEGER NOT NULL,
            slave_id INTEGER NOT NULL,
            sync_group_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sync_group_id) REFERENCES sync_groups (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stage_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            master_id INTEGER NOT NULL,
            slave_id INTEGER NOT NULL,
            sync_group_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sync_group_id) REFERENCES sync_groups (id)
        )
    ''')
    
    conn.commit()
    print("✅ Estrutura do banco criada/verificada")
    
    return conn

def clear_existing_data(conn):
    """Limpa dados existentes"""
    cursor = conn.cursor()
    
    print("🗑️ Limpando dados existentes...")
    
    # Limpar na ordem correta (respeitando foreign keys)
    tables = ['stage_mappings', 'pipeline_mappings', 'kommo_accounts', 'sync_groups']
    
    for table in tables:
        cursor.execute(f'DELETE FROM {table}')
        print(f"   • Limpou tabela: {table}")
    
    conn.commit()
    print("✅ Dados existentes removidos")

def import_account_to_local(conn, account_data, account_role):
    """Importa uma conta para o banco local"""
    cursor = conn.cursor()
    
    subdomain = account_data.get('subdomain', '')
    access_token = account_data.get('access_token', '')
    refresh_token = account_data.get('refresh_token', '')
    
    # Calcular data de expiração (30 dias a partir de agora)
    from datetime import datetime, timedelta
    expires_at = datetime.now() + timedelta(days=30)
    
    print(f"📥 Importando conta {account_role}: {subdomain}")
    
    try:
        cursor.execute('''
            INSERT INTO kommo_accounts (
                subdomain, access_token, refresh_token, token_expires_at,
                account_role, is_master, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            subdomain,
            access_token, 
            refresh_token,
            expires_at,
            account_role,
            1 if account_role == 'master' else 0,
            datetime.now(),
            datetime.now()
        ))
        
        account_id = cursor.lastrowid
        conn.commit()
        
        print(f"   ✅ Conta importada com ID: {account_id}")
        return account_id
        
    except sqlite3.IntegrityError as e:
        print(f"   ❌ Erro ao importar conta {subdomain}: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Erro inesperado ao importar conta {subdomain}: {e}")
        return None

def create_sync_group(conn, master_account_id, group_name="Grupo Principal"):
    """Cria um grupo de sincronização"""
    cursor = conn.cursor()
    
    print(f"📁 Criando grupo de sincronização: {group_name}")
    
    try:
        cursor.execute('''
            INSERT INTO sync_groups (
                name, description, master_account_id, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            group_name,
            "Grupo criado automaticamente durante importação",
            master_account_id,
            True,
            datetime.now(),
            datetime.now()
        ))
        
        group_id = cursor.lastrowid
        conn.commit()
        
        print(f"   ✅ Grupo criado com ID: {group_id}")
        return group_id
        
    except Exception as e:
        print(f"   ❌ Erro ao criar grupo: {e}")
        return None

def assign_slave_to_group(conn, slave_account_id, sync_group_id):
    """Associa conta slave ao grupo"""
    cursor = conn.cursor()
    
    print(f"🔗 Associando conta slave ID {slave_account_id} ao grupo ID {sync_group_id}")
    
    try:
        cursor.execute('''
            UPDATE kommo_accounts 
            SET sync_group_id = ?, updated_at = ?
            WHERE id = ?
        ''', (sync_group_id, datetime.now(), slave_account_id))
        
        conn.commit()
        print(f"   ✅ Associação realizada")
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao associar slave ao grupo: {e}")
        return False

def show_imported_data(conn):
    """Mostra os dados importados"""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 RESUMO DOS DADOS IMPORTADOS")
    print("="*60)
    
    # Contas
    cursor.execute('SELECT COUNT(*) FROM kommo_accounts')
    total_accounts = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM kommo_accounts WHERE account_role = "master"')
    master_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM kommo_accounts WHERE account_role = "slave"')
    slave_count = cursor.fetchone()[0]
    
    print(f"👥 CONTAS: {total_accounts} total ({master_count} master, {slave_count} slave)")
    
    # Detalhes das contas
    cursor.execute('''
        SELECT id, subdomain, account_role, sync_group_id, created_at
        FROM kommo_accounts 
        ORDER BY account_role DESC, id
    ''')
    
    accounts = cursor.fetchall()
    for account in accounts:
        account_id, subdomain, role, group_id, created_at = account
        group_info = f"grupo {group_id}" if group_id else "sem grupo"
        print(f"   • {subdomain} ({role}) - ID: {account_id} - {group_info}")
    
    # Grupos
    cursor.execute('SELECT COUNT(*) FROM sync_groups')
    total_groups = cursor.fetchone()[0]
    
    print(f"\n📁 GRUPOS: {total_groups} total")
    
    if total_groups > 0:
        cursor.execute('''
            SELECT sg.id, sg.name, sg.master_account_id, ka.subdomain,
                   COUNT(slave_ka.id) as slave_count
            FROM sync_groups sg
            LEFT JOIN kommo_accounts ka ON sg.master_account_id = ka.id  
            LEFT JOIN kommo_accounts slave_ka ON sg.id = slave_ka.sync_group_id
            GROUP BY sg.id, sg.name, sg.master_account_id, ka.subdomain
            ORDER BY sg.id
        ''')
        
        groups = cursor.fetchall()
        for group in groups:
            group_id, name, master_id, master_subdomain, slave_count = group
            print(f"   • {name} (ID: {group_id}) - Master: {master_subdomain} - {slave_count} slave(s)")
    
    print("="*60)

def main():
    """Função principal"""
    print("🔄 IMPORTADOR DE CONTAS REMOTO → LOCAL")
    print("=" * 60)
    
    # 1. Buscar contas do servidor remoto
    remote_accounts = fetch_remote_accounts()
    if not remote_accounts:
        print("❌ Falha ao obter contas do servidor remoto. Abortando.")
        return
    
    # Mostrar contas encontradas
    print("\n📋 CONTAS ENCONTRADAS NO SERVIDOR REMOTO:")
    for i, account in enumerate(remote_accounts, 1):
        subdomain = account.get('subdomain', 'N/A')
        role = account.get('account_role', account.get('is_master', False))
        if isinstance(role, bool):
            role = 'master' if role else 'slave'
        print(f"   {i}. {subdomain} ({role})")
    
    # 2. Configurar banco local
    conn = setup_local_database()
    
    # 3. Limpar dados existentes
    clear_existing_data(conn)
    
    # 4. Identificar e importar contas
    master_accounts = []
    slave_accounts = []
    
    for account in remote_accounts:
        role = account.get('account_role')
        if not role:
            # Fallback para campo is_master
            is_master = account.get('is_master', False)
            role = 'master' if is_master else 'slave'
        
        if role == 'master':
            master_accounts.append(account)
        else:
            slave_accounts.append(account)
    
    print(f"\n🎯 CLASSIFICAÇÃO: {len(master_accounts)} master(s), {len(slave_accounts)} slave(s)")
    
    # 5. Importar contas master
    imported_masters = []
    for master_account in master_accounts:
        master_id = import_account_to_local(conn, master_account, 'master')
        if master_id:
            imported_masters.append(master_id)
    
    # 6. Importar contas slave
    imported_slaves = []
    for slave_account in slave_accounts:
        slave_id = import_account_to_local(conn, slave_account, 'slave')
        if slave_id:
            imported_slaves.append(slave_id)
    
    # 7. Criar grupo de sincronização se há master e slave
    if imported_masters and imported_slaves:
        master_id = imported_masters[0]  # Usar primeira master
        group_id = create_sync_group(conn, master_id, "Grupo Importado")
        
        if group_id:
            # Associar todas as slaves ao grupo
            for slave_id in imported_slaves:
                assign_slave_to_group(conn, slave_id, group_id)
    
    # 8. Mostrar resumo
    show_imported_data(conn)
    
    # 9. Salvar relatório
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ka.id, ka.subdomain, ka.account_role, ka.access_token,
               sg.id as group_id, sg.name as group_name
        FROM kommo_accounts ka
        LEFT JOIN sync_groups sg ON ka.sync_group_id = sg.id
        ORDER BY ka.account_role DESC, ka.id
    ''')
    
    accounts_report = []
    for row in cursor.fetchall():
        account_id, subdomain, role, token, group_id, group_name = row
        accounts_report.append({
            'id': account_id,
            'subdomain': subdomain,
            'role': role,
            'token_preview': token[:20] + "..." if token else None,
            'group_id': group_id,
            'group_name': group_name
        })
    
    report = {
        'import_timestamp': datetime.now().isoformat(),
        'source_url': 'http://89.116.186.230:5000/api/sync/accounts/',
        'accounts_imported': len(accounts_report),
        'masters': len([a for a in accounts_report if a['role'] == 'master']),
        'slaves': len([a for a in accounts_report if a['role'] == 'slave']),
        'accounts': accounts_report
    }
    
    with open('import_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("📄 Relatório detalhado salvo em: import_report.json")
    
    conn.close()
    print("\n✅ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")

if __name__ == "__main__":
    main()
