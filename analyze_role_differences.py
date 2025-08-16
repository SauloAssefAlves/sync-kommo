"""
🔍 ANÁLISE DE DIFERENÇAS ENTRE ROLES MASTER E SLAVE
Baseado nas imagens fornecidas pelo usuário
"""

import os
import sys
import json
from datetime import datetime

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import DatabaseManager
from src.services.kommo_api import KommoAPIService

def analyze_role_differences():
    """Analisa diferenças entre roles master e slave"""
    print("🔍 ANÁLISE DE DIFERENÇAS ENTRE ROLES")
    print("=" * 60)
    
    # Inicializar banco
    db_manager = DatabaseManager()
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Buscar contas master e slave
        cursor.execute("""
            SELECT id, account_name, account_type, api_token 
            FROM kommo_accounts 
            WHERE account_type IN ('master', 'slave')
            ORDER BY account_type DESC
        """)
        
        accounts = cursor.fetchall()
        
        print(f"📊 Encontradas {len(accounts)} contas:")
        for account in accounts:
            print(f"   • {account[1]} ({account[2]})")
        
        if len(accounts) < 2:
            print("❌ Erro: É necessário ter pelo menos 1 master e 1 slave")
            return
        
        # Separar master e slave
        master_accounts = [acc for acc in accounts if acc[2] == 'master']
        slave_accounts = [acc for acc in accounts if acc[2] == 'slave']
        
        if not master_accounts or not slave_accounts:
            print("❌ Erro: É necessário ter pelo menos 1 master e 1 slave")
            return
        
        master_account = master_accounts[0]
        slave_account = slave_accounts[0]
        
        print(f"\n🎯 Analisando:")
        print(f"   Master: {master_account[1]} (ID: {master_account[0]})")
        print(f"   Slave:  {slave_account[1]} (ID: {slave_account[0]})")
        
        # Criar APIs
        print("\n📡 Conectando às APIs...")
        try:
            master_api = KommoAPIService(master_account[3])  # token
            slave_api = KommoAPIService(slave_account[3])   # token
            
            # Obter roles de ambas as contas
            print("\n🔄 Obtendo roles...")
            master_roles = master_api.get_roles()
            slave_roles = slave_api.get_roles()
            
            print(f"   Master: {len(master_roles)} roles")
            print(f"   Slave:  {len(slave_roles)} roles")
            
            # Analisar diferenças
            print("\n📋 ROLES DA MASTER:")
            print("-" * 40)
            master_role_names = set()
            for i, role in enumerate(master_roles, 1):
                role_name = role.get('name', 'Sem nome')
                master_role_names.add(role_name)
                status_rights_count = len(role.get('rights', {}).get('status_rights', []))
                print(f"   {i}. {role_name} (ID: {role['id']}) - {status_rights_count} status_rights")
                
                # Analisar status_rights em detalhes
                if status_rights_count > 0:
                    print(f"      📊 Status Rights:")
                    for sr in role['rights']['status_rights'][:3]:  # Mostrar só os primeiros 3
                        pipeline_id = sr.get('pipeline_id', 'N/A')
                        status_id = sr.get('status_id', 'N/A')
                        entity = sr.get('entity_type', 'N/A')
                        print(f"         • {entity}: pipeline={pipeline_id}, status={status_id}")
                    if status_rights_count > 3:
                        print(f"         ... e mais {status_rights_count - 3}")
            
            print("\n📋 ROLES DA SLAVE:")
            print("-" * 40)
            slave_role_names = set()
            for i, role in enumerate(slave_roles, 1):
                role_name = role.get('name', 'Sem nome')
                slave_role_names.add(role_name)
                status_rights_count = len(role.get('rights', {}).get('status_rights', []))
                print(f"   {i}. {role_name} (ID: {role['id']}) - {status_rights_count} status_rights")
                
                # Analisar status_rights em detalhes
                if status_rights_count > 0:
                    print(f"      📊 Status Rights:")
                    for sr in role['rights']['status_rights'][:3]:  # Mostrar só os primeiros 3
                        pipeline_id = sr.get('pipeline_id', 'N/A')
                        status_id = sr.get('status_id', 'N/A')
                        entity = sr.get('entity_type', 'N/A')
                        print(f"         • {entity}: pipeline={pipeline_id}, status={status_id}")
                    if status_rights_count > 3:
                        print(f"         ... e mais {status_rights_count - 3}")
            
            # Análise de diferenças
            print("\n🔍 ANÁLISE DE DIFERENÇAS:")
            print("-" * 40)
            
            # Roles que estão na master mas não na slave
            missing_in_slave = master_role_names - slave_role_names
            if missing_in_slave:
                print(f"❌ Roles na MASTER que faltam na SLAVE: {missing_in_slave}")
            
            # Roles que estão na slave mas não na master
            extra_in_slave = slave_role_names - master_role_names
            if extra_in_slave:
                print(f"⚠️ Roles na SLAVE que não existem na MASTER: {extra_in_slave}")
            
            # Roles em comum
            common_roles = master_role_names & slave_role_names
            if common_roles:
                print(f"✅ Roles em comum: {common_roles}")
            
            # Verificar mapeamentos disponíveis
            print("\n🗺️ VERIFICANDO MAPEAMENTOS:")
            print("-" * 40)
            
            cursor.execute("""
                SELECT 
                    'pipeline' as type, master_id, slave_id, sync_group_id
                FROM pipeline_mappings
                UNION ALL
                SELECT 
                    'stage' as type, master_id, slave_id, sync_group_id
                FROM stage_mappings
                ORDER BY type, master_id
            """)
            
            mappings = cursor.fetchall()
            pipeline_mappings = [m for m in mappings if m[0] == 'pipeline']
            stage_mappings = [m for m in mappings if m[0] == 'stage']
            
            print(f"   📊 Pipeline mappings: {len(pipeline_mappings)}")
            for mapping in pipeline_mappings:
                print(f"      • {mapping[1]} → {mapping[2]} (grupo: {mapping[3]})")
            
            print(f"   🎭 Stage mappings: {len(stage_mappings)}")
            for mapping in stage_mappings[:5]:  # Mostrar só os primeiros 5
                print(f"      • {mapping[1]} → {mapping[2]} (grupo: {mapping[3]})")
            if len(stage_mappings) > 5:
                print(f"      ... e mais {len(stage_mappings) - 5}")
            
            # Detectar problemas potenciais
            print("\n🚨 PROBLEMAS POTENCIAIS:")
            print("-" * 40)
            
            issues_found = False
            
            # Verificar se há mapeamentos suficientes
            if len(pipeline_mappings) == 0:
                print("❌ CRÍTICO: Nenhum mapeamento de pipeline encontrado!")
                issues_found = True
            
            if len(stage_mappings) == 0:
                print("❌ CRÍTICO: Nenhum mapeamento de stage encontrado!")
                issues_found = True
            
            # Verificar IDs suspeitos nas roles da slave
            for role in slave_roles:
                for sr in role.get('rights', {}).get('status_rights', []):
                    status_id = str(sr.get('status_id', ''))
                    pipeline_id = str(sr.get('pipeline_id', ''))
                    
                    if status_id.startswith(('896', '897', '905')):
                        print(f"⚠️ ID SUSPEITO na role '{role['name']}': status_id={status_id}")
                        issues_found = True
                    
                    if pipeline_id.startswith(('896', '897', '905')):
                        print(f"⚠️ ID SUSPEITO na role '{role['name']}': pipeline_id={pipeline_id}")
                        issues_found = True
            
            if not issues_found:
                print("✅ Nenhum problema crítico detectado")
            
            # Recomendações
            print("\n💡 RECOMENDAÇÕES:")
            print("-" * 40)
            
            if missing_in_slave:
                print("🔄 Execute sincronização de roles para criar roles faltantes na slave")
            
            if len(pipeline_mappings) == 0 or len(stage_mappings) == 0:
                print("🔄 Execute sincronização de pipelines primeiro para criar mapeamentos")
            
            if issues_found:
                print("🔍 Execute diagnóstico detalhado dos status_rights das roles")
            
            print("\n💾 SALVANDO ANÁLISE...")
            
            # Salvar análise detalhada
            analysis_data = {
                'timestamp': datetime.now().isoformat(),
                'master_account': {
                    'name': master_account[1],
                    'id': master_account[0],
                    'roles_count': len(master_roles),
                    'role_names': list(master_role_names)
                },
                'slave_account': {
                    'name': slave_account[1],
                    'id': slave_account[0],
                    'roles_count': len(slave_roles),
                    'role_names': list(slave_role_names)
                },
                'differences': {
                    'missing_in_slave': list(missing_in_slave),
                    'extra_in_slave': list(extra_in_slave),
                    'common_roles': list(common_roles)
                },
                'mappings': {
                    'pipelines': len(pipeline_mappings),
                    'stages': len(stage_mappings)
                },
                'issues_found': issues_found
            }
            
            with open('role_analysis_report.json', 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, indent=2, ensure_ascii=False)
            
            print("✅ Análise salva em: role_analysis_report.json")
            
        except Exception as e:
            print(f"❌ Erro ao conectar APIs: {e}")
            return

if __name__ == "__main__":
    analyze_role_differences()
