#!/usr/bin/env python3
"""
Script para atualizar o esquema do banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.database import db

def update_database_schema():
    """Atualiza o esquema do banco de dados"""
    with app.app_context():
        print("🔄 Atualizando esquema do banco de dados...")
        
        try:
            # Criar todas as tabelas
            db.create_all()
            print("✅ Esquema do banco de dados atualizado com sucesso!")
            
            # Verificar se as tabelas foram criadas
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n📊 Tabelas encontradas: {len(tables)}")
            for table in tables:
                columns = inspector.get_columns(table)
                print(f"   - {table} ({len(columns)} colunas)")
                
        except Exception as e:
            print(f"❌ Erro ao atualizar esquema: {e}")
            return False
            
        return True

if __name__ == "__main__":
    update_database_schema()
