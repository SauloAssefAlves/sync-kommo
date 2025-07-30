#!/usr/bin/env python3
"""
Script para migração manual do banco de dados SQLite
"""

import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def manual_migration():
    """Migração manual para adicionar colunas ao banco SQLite"""
    
    db_path = 'src/database/app.db'
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    print("🔄 Iniciando migração manual do banco de dados...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se as colunas já existem
        cursor.execute("PRAGMA table_info(kommo_accounts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📊 Colunas atuais: {columns}")
        
        # Adicionar coluna sync_group_id se não existir
        if 'sync_group_id' not in columns:
            print("➕ Adicionando coluna sync_group_id...")
            cursor.execute("ALTER TABLE kommo_accounts ADD COLUMN sync_group_id INTEGER")
            print("   ✅ Coluna sync_group_id adicionada")
        else:
            print("   ✅ Coluna sync_group_id já existe")
        
        # Adicionar coluna account_role se não existir
        if 'account_role' not in columns:
            print("➕ Adicionando coluna account_role...")
            cursor.execute("ALTER TABLE kommo_accounts ADD COLUMN account_role VARCHAR(20)")
            print("   ✅ Coluna account_role adicionada")
        else:
            print("   ✅ Coluna account_role já existe")
        
        # Verificar tabela sync_groups
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_groups'")
        if not cursor.fetchone():
            print("➕ Criando tabela sync_groups...")
            cursor.execute("""
                CREATE TABLE sync_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    master_account_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (master_account_id) REFERENCES kommo_accounts(id)
                )
            """)
            print("   ✅ Tabela sync_groups criada")
        else:
            print("   ✅ Tabela sync_groups já existe")
        
        # Verificar outras tabelas de mapeamento
        for table_name in ['pipeline_mappings', 'stage_mappings', 'custom_field_mappings', 'sync_logs']:
            cursor.execute(f"PRAGMA table_info({table_name})")
            table_columns = [column[1] for column in cursor.fetchall()]
            
            if 'sync_group_id' not in table_columns:
                print(f"➕ Adicionando sync_group_id à tabela {table_name}...")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN sync_group_id INTEGER")
                print(f"   ✅ Coluna sync_group_id adicionada à {table_name}")
            else:
                print(f"   ✅ Coluna sync_group_id já existe em {table_name}")
        
        # Salvar mudanças
        conn.commit()
        print("\n✅ Migração concluída com sucesso!")
        
        # Verificar estrutura final
        cursor.execute("PRAGMA table_info(kommo_accounts)")
        final_columns = [column[1] for column in cursor.fetchall()]
        print(f"\n📊 Estrutura final da tabela kommo_accounts:")
        for col in final_columns:
            print(f"   - {col}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        return False

if __name__ == "__main__":
    manual_migration()
