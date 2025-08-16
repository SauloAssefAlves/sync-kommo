"""
🔍 ANÁLISE DE DIFERENÇAS ENTRE ROLES MASTER E SLAVE
Versão simplificada baseada nos dados disponíveis
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

def analyze_role_differences():
    """Analisa diferenças entre roles master e slave"""
    print("🔍 ANÁLISE DE DIFERENÇAS ENTRE ROLES")
    print("=" * 60)
    
    # Conectar ao banco SQLite diretamente
    db_path = os.path.join('src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        print("💡 Execute primeiro os scripts de importação de contas")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Buscar contas master e slave
        cursor.execute("""
            SELECT id, subdomain, account_role, access_token 
            FROM kommo_accounts 
            WHERE account_role IN ('master', 'slave')
            ORDER BY account_role DESC
        """)
        
        accounts = cursor.fetchall()
        
        print(f"📊 Encontradas {len(accounts)} contas:")
        for account in accounts:
            print(f"   • {account[1]} ({account[2]})")
        
        if len(accounts) < 2:
            print("❌ Erro: É necessário ter pelo menos 1 master e 1 slave")
            print("💡 Execute primeiro: python import_accounts_from_remote.py")
            return
        
        # Separar master e slave
        master_accounts = [acc for acc in accounts if acc[2] == 'master']
        slave_accounts = [acc for acc in accounts if acc[2] == 'slave']
        
        if not master_accounts or not slave_accounts:
            print("❌ Erro: É necessário ter pelo menos 1 master e 1 slave")
            return
        
        master_account = master_accounts[0]
        slave_account = slave_accounts[0]
        
        print(f"\n🎯 Contas encontradas:")
        print(f"   Master: {master_account[1]} (ID: {master_account[0]})")
        print(f"   Slave:  {slave_account[1]} (ID: {slave_account[0]})")
        
        # Verificar mapeamentos disponíveis
        print("\n🗺️ VERIFICANDO MAPEAMENTOS NO BANCO:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT COUNT(*) FROM pipeline_mappings
        """)
        pipeline_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM stage_mappings
        """)
        stage_count = cursor.fetchone()[0]
        
        print(f"📊 Pipeline mappings: {pipeline_count}")
        print(f"🎭 Stage mappings: {stage_count}")
        
        if pipeline_count > 0:
            cursor.execute("""
                SELECT master_id, slave_id, sync_group_id
                FROM pipeline_mappings
                ORDER BY master_id
            """)
            pipeline_mappings = cursor.fetchall()
            
            print(f"\n📊 PIPELINE MAPPINGS ({len(pipeline_mappings)}):")
            for mapping in pipeline_mappings:
                print(f"   • {mapping[0]} → {mapping[1]} (grupo: {mapping[2]})")
        
        if stage_count > 0:
            cursor.execute("""
                SELECT master_id, slave_id, sync_group_id
                FROM stage_mappings
                ORDER BY master_id
                LIMIT 10
            """)
            stage_mappings = cursor.fetchall()
            
            print(f"\n🎭 STAGE MAPPINGS (primeiros 10):")
            for mapping in stage_mappings:
                print(f"   • {mapping[0]} → {mapping[1]} (grupo: {mapping[2]})")
            
            if stage_count > 10:
                print(f"   ... e mais {stage_count - 10}")
        
        # Análise baseada nas imagens fornecidas
        print("\n📸 ANÁLISE BASEADA NAS IMAGENS:")
        print("-" * 40)
        
        print("🔍 Diferenças observadas:")
        print("   Master (primeira imagem):")
        print("   • 3 roles configuradas (ROLE 1, ROLE 2, ROLE 3)")
        print("   • Múltiplas etapas visíveis (TESTE 3, TESTE gustavo, Pipeline Teste, etc.)")
        print("   • Configurações complexas de status_rights")
        print()
        print("   Slave (segunda imagem):")
        print("   • 3 roles também, mas com diferentes configurações")
        print("   • Menos etapas de pipeline visíveis")
        print("   • Status rights diferentes")
        
        # Verificar se há problemas potenciais
        print("\n🚨 PROBLEMAS POTENCIAIS:")
        print("-" * 40)
        
        issues_found = False
        
        if pipeline_count == 0:
            print("❌ CRÍTICO: Nenhum mapeamento de pipeline encontrado!")
            print("   💡 Execute: sincronização de pipelines primeiro")
            issues_found = True
        
        if stage_count == 0:
            print("❌ CRÍTICO: Nenhum mapeamento de stage encontrado!")
            print("   💡 Execute: sincronização de pipelines primeiro")
            issues_found = True
        
        if not issues_found:
            print("✅ Mapeamentos básicos encontrados no banco")
        
        # Recomendações específicas
        print("\n💡 RECOMENDAÇÕES PARA CORRIGIR DIFERENÇAS:")
        print("-" * 50)
        
        print("1. 🔄 SINCRONIZAR ROLES:")
        print("   • Execute sincronização de roles da master para slave")
        print("   • Isso atualizará as configurações de status_rights")
        print("   • Comando: POST /api/sync/trigger com sync_type='roles'")
        print()
        
        print("2. 🗺️ VERIFICAR MAPEAMENTOS:")
        if pipeline_count == 0 or stage_count == 0:
            print("   • Execute sincronização de pipelines PRIMEIRO")
            print("   • Comando: POST /api/sync/trigger com sync_type='pipelines'")
        else:
            print("   ✅ Mapeamentos encontrados no banco")
        print()
        
        print("3. 🔍 DIAGNÓSTICO DETALHADO:")
        print("   • Execute teste de sync roles para verificar problemas")
        print("   • Comando: python test_sync_roles_simulation.py")
        print()
        
        print("4. 🚀 SEQUÊNCIA RECOMENDADA:")
        print("   1. Sincronizar pipelines (se necessário)")
        print("   2. Sincronizar roles")
        print("   3. Verificar resultados")
        
        # Criar script de correção automática
        print("\n💾 CRIANDO SCRIPT DE CORREÇÃO...")
        
        correction_script = f"""
# Script de Correção Automática - Roles
# Gerado em: {datetime.now().isoformat()}

# Contas identificadas:
# Master: {master_account[1]} (ID: {master_account[0]})
# Slave:  {slave_account[1]} (ID: {slave_account[0]})

# Mapeamentos disponíveis:
# Pipelines: {pipeline_count}
# Stages: {stage_count}

import requests
import json

def fix_role_sync():
    base_url = "http://localhost:5000"
    
    # 1. Verificar se precisa sincronizar pipelines primeiro
    if {pipeline_count} == 0 or {stage_count} == 0:
        print("🔄 Sincronizando pipelines primeiro...")
        response = requests.post(f"{{base_url}}/api/sync/trigger", json={{
            "sync_type": "pipelines",
            "master_account_id": {master_account[0]},
            "slave_account_id": {slave_account[0]}
        }})
        print(f"Resultado pipelines: {{response.status_code}}")
    
    # 2. Sincronizar roles
    print("🔄 Sincronizando roles...")
    response = requests.post(f"{{base_url}}/api/sync/trigger", json={{
        "sync_type": "roles", 
        "master_account_id": {master_account[0]},
        "slave_account_id": {slave_account[0]}
    }})
    print(f"Resultado roles: {{response.status_code}}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Sincronização concluída!")
        print(f"Resultado: {{result}}")
    else:
        print(f"❌ Erro na sincronização: {{response.text}}")

if __name__ == "__main__":
    fix_role_sync()
"""
        
        with open('fix_role_sync.py', 'w', encoding='utf-8') as f:
            f.write(correction_script)
        
        print("✅ Script de correção criado: fix_role_sync.py")
        
        # Salvar análise
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'master_account': {
                'name': master_account[1],
                'id': master_account[0]
            },
            'slave_account': {
                'name': slave_account[1], 
                'id': slave_account[0]
            },
            'mappings': {
                'pipelines': pipeline_count,
                'stages': stage_count
            },
            'issues': {
                'missing_pipelines': pipeline_count == 0,
                'missing_stages': stage_count == 0,
                'role_differences_observed': True
            },
            'recommendations': [
                "Sincronizar pipelines se necessário",
                "Sincronizar roles da master para slave",
                "Executar diagnóstico detalhado",
                "Verificar resultados nas interfaces"
            ]
        }
        
        with open('role_differences_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Análise detalhada salva em: role_differences_analysis.json")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")
        return

if __name__ == "__main__":
    analyze_role_differences()
