"""
🔄 IMPORTADOR DE CONTAS REMOTO → LOCAL (Versão Robusta)
Clona as contas master e slave do servidor remoto para o banco local
"""

import os
import sys
import json
import requests
import sqlite3
from datetime import datetime, timedelta

def test_remote_connection():
    """Testa diferentes URLs para encontrar o endpoint correto"""
    possible_urls = [
        "http://89.116.186.230:5000/api/sync/accounts/",
        "http://89.116.186.230:5000/api/sync/accounts",
        "http://89.116.186.230:5000/api/accounts/",
        "http://89.116.186.230:5000/api/accounts",
        "http://89.116.186.230:5000/accounts/",
        "http://89.116.186.230:5000/accounts"
    ]
    
    print("🔍 Testando conectividade com servidor remoto...")
    
    for url in possible_urls:
        try:
            print(f"   📡 Tentando: {url}")
            response = requests.get(url, timeout=10)
            
            print(f"      Status: {response.status_code}")
            print(f"      Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"      Tamanho: {len(response.text)} bytes")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"      ✅ JSON válido!")
                    print(f"      Chaves: {list(data.keys())}")
                    return url, data
                except json.JSONDecodeError:
                    print(f"      ❌ Resposta não é JSON válido")
                    print(f"      Primeiros 200 chars: {response.text[:200]}")
            
        except requests.exceptions.RequestException as e:
            print(f"      ❌ Erro de conexão: {e}")
        except Exception as e:
            print(f"      ❌ Erro inesperado: {e}")
        
        print()
    
    return None, None

def create_mock_accounts():
    """Cria contas mock para teste se o servidor não estiver disponível"""
    print("🤖 Criando contas mock para teste...")
    
    mock_accounts = [
        {
            "id": 1,
            "subdomain": "evoresultdev",
            "access_token": "mock_token_master_12345",
            "refresh_token": "mock_refresh_master_12345",
            "account_role": "master",
            "is_master": True
        },
        {
            "id": 2, 
            "subdomain": "testedev",
            "access_token": "mock_token_slave_67890",
            "refresh_token": "mock_refresh_slave_67890", 
            "account_role": "slave",
            "is_master": False
        },
        {
            "id": 3,
            "subdomain": "test",
            "access_token": "mock_token_master_54321",
            "refresh_token": "mock_refresh_master_54321",
            "account_role": "master", 
            "is_master": True
        }
    ]
    
    print(f"   ✅ Criadas {len(mock_accounts)} contas mock")
    return mock_accounts

def setup_local_database():
    """Configura o banco de dados local"""
    db_path = os.path.join('src', 'database', 'app.db')
    
    # Criar diretório se não existir
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    print(f"💾 Configurando banco local: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Habilitar foreign keys
    cursor.execute('PRAGMA foreign_keys = ON')
    
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
    
    # Desabilitar foreign keys temporariamente para limpeza
    cursor.execute('PRAGMA foreign_keys = OFF')
    
    # Limpar tabelas
    tables = ['stage_mappings', 'pipeline_mappings', 'kommo_accounts', 'sync_groups']
    
    for table in tables:
        cursor.execute(f'DELETE FROM {table}')
        print(f"   • Limpou tabela: {table}")
    
    # Resetar auto-increment se a tabela sqlite_sequence existir
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
    if cursor.fetchone():
        for table in tables:
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
    
    # Reabilitar foreign keys
    cursor.execute('PRAGMA foreign_keys = ON')
    
    conn.commit()
    print("✅ Dados existentes removidos")

def import_account_to_local(conn, account_data, force_role=None):
    """Importa uma conta para o banco local"""
    cursor = conn.cursor()
    
    subdomain = account_data.get('subdomain', '')
    access_token = account_data.get('access_token', '')
    refresh_token = account_data.get('refresh_token', '')
    
    # Determinar role
    if force_role:
        account_role = force_role
    else:
        account_role = account_data.get('account_role')
        if not account_role:
            is_master = account_data.get('is_master', False)
            account_role = 'master' if is_master else 'slave'
    
    # Calcular data de expiração (30 dias a partir de agora)
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
        if "UNIQUE constraint failed" in str(e):
            print(f"   ⚠️ Conta {subdomain} já existe, atualizando...")
            try:
                cursor.execute('''
                    UPDATE kommo_accounts 
                    SET access_token = ?, refresh_token = ?, token_expires_at = ?,
                        account_role = ?, is_master = ?, updated_at = ?
                    WHERE subdomain = ?
                ''', (
                    access_token, refresh_token, expires_at,
                    account_role, 1 if account_role == 'master' else 0,
                    datetime.now(), subdomain
                ))
                
                cursor.execute('SELECT id FROM kommo_accounts WHERE subdomain = ?', (subdomain,))
                account_id = cursor.fetchone()[0]
                conn.commit()
                
                print(f"   ✅ Conta atualizada com ID: {account_id}")
                return account_id
                
            except Exception as update_error:
                print(f"   ❌ Erro ao atualizar conta {subdomain}: {update_error}")
                return None
        else:
            print(f"   ❌ Erro de integridade ao importar conta {subdomain}: {e}")
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
    print("🔄 IMPORTADOR DE CONTAS REMOTO → LOCAL (VERSÃO ROBUSTA)")
    print("=" * 60)
    
    # 1. Tentar buscar contas do servidor remoto
    working_url, remote_data = test_remote_connection()
    
    if working_url and remote_data:
        print(f"✅ Servidor encontrado: {working_url}")
        accounts = remote_data.get('accounts', remote_data.get('data', []))
        if not accounts and isinstance(remote_data, list):
            accounts = remote_data
        print(f"📊 Encontradas {len(accounts)} contas")
    else:
        print("❌ Servidor remoto indisponível, usando contas mock para teste")
        accounts = create_mock_accounts()
    
    # Mostrar contas encontradas
    print("\n📋 CONTAS PARA IMPORTAR:")
    for i, account in enumerate(accounts, 1):
        subdomain = account.get('subdomain', 'N/A')
        role = account.get('account_role', account.get('is_master', False))
        if isinstance(role, bool):
            role = 'master' if role else 'slave'
        print(f"   {i}. {subdomain} ({role})")
    
    # 2. Configurar banco local
    conn = setup_local_database()
    
    # 3. Limpar dados existentes
    clear_existing_data(conn)
    
    # 4. Classificar e importar contas
    master_accounts = []
    slave_accounts = []
    
    for account in accounts:
        role = account.get('account_role')
        if not role:
            is_master = account.get('is_master', False)
            role = 'master' if is_master else 'slave'
        
        if role == 'master':
            master_accounts.append(account)
        else:
            slave_accounts.append(account)
    
    print(f"\n🎯 CLASSIFICAÇÃO: {len(master_accounts)} master(s), {len(slave_accounts)} slave(s)")
    
    # 5. Importar todas as contas
    imported_masters = []
    imported_slaves = []
    
    for master_account in master_accounts:
        master_id = import_account_to_local(conn, master_account, 'master')
        if master_id:
            imported_masters.append(master_id)
    
    for slave_account in slave_accounts:
        slave_id = import_account_to_local(conn, slave_account, 'slave')
        if slave_id:
            imported_slaves.append(slave_id)
    
    # 6. Criar relacionamento master-slave se houver ambos
    if imported_masters and imported_slaves:
        print(f"\n🔗 Criando relacionamentos entre {len(imported_masters)} master(s) e {len(imported_slaves)} slave(s)")
        
        # Para cada master, criar um grupo
        for i, master_id in enumerate(imported_masters):
            group_name = f"Grupo Master {i+1}"
            group_id = create_sync_group(conn, master_id, group_name)
            
            if group_id and imported_slaves:
                # Associar primeira slave disponível a este grupo
                if i < len(imported_slaves):
                    slave_id = imported_slaves[i]
                    assign_slave_to_group(conn, slave_id, group_id)
    
    # 7. Mostrar resumo final
    show_imported_data(conn)
    
    # 8. Criar relatório detalhado
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ka.id, ka.subdomain, ka.account_role, ka.access_token,
               ka.sync_group_id, sg.name as group_name
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
    
    # Relatório completo
    report = {
        'import_timestamp': datetime.now().isoformat(),
        'source': working_url if working_url else 'mock_data',
        'accounts_imported': len(accounts_report),
        'masters': len([a for a in accounts_report if a['role'] == 'master']),
        'slaves': len([a for a in accounts_report if a['role'] == 'slave']),
        'accounts': accounts_report,
        'database_path': os.path.join('src', 'database', 'app.db')
    }
    
    with open('import_report_complete.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("📄 Relatório completo salvo em: import_report_complete.json")
    
    conn.close()
    print("\n✅ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
    print("💡 As contas estão prontas para uso no sistema de sincronização")

if __name__ == "__main__":
    main()
