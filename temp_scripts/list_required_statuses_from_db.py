#!/usr/bin/env python3
"""
Lista os required_statuses das contas master e slave usando dados do banco local
"""

import sqlite3
import requests
import logging
import sys
import json
from typing import Dict, List, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleKommoAPI:
    """API simples do Kommo para este script"""
    
    def __init__(self, subdomain: str, access_token: str):
        self.subdomain = subdomain
        self.access_token = access_token
        self.base_url = f"https://{subdomain}.kommo.com/api/v4"
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Faz uma requisição para a API do Kommo"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.request(method, url, params=params, headers=headers)
            
            if response.status_code == 401:
                logger.error(f"❌ Token inválido ou expirado para {self.subdomain}")
                raise Exception("Token inválido ou expirado")
            elif response.status_code == 402:
                logger.error(f"❌ Conta {self.subdomain} requer pagamento")
                raise Exception("Conta requer pagamento")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}")
            raise
    
    def get_pipelines(self) -> List[Dict]:
        """Obtém todos os pipelines"""
        response = self._make_request('GET', '/leads/pipelines')
        return response.get('_embedded', {}).get('pipelines', [])
    
    def get_pipeline_stages(self, pipeline_id: int) -> List[Dict]:
        """Obtém todos os estágios de um pipeline específico"""
        response = self._make_request('GET', f'/leads/pipelines/{pipeline_id}/statuses')
        return response.get('_embedded', {}).get('statuses', [])
    
    def get_custom_fields(self, entity_type: str = 'leads') -> List[Dict]:
        """Obtém campos customizados com required_statuses"""
        params = {'with': 'required_statuses,enums'}
        response = self._make_request('GET', f'/{entity_type}/custom_fields', params=params)
        return response.get('_embedded', {}).get('custom_fields', [])

def get_accounts_from_database() -> List[Dict]:
    """Obtém contas do banco de dados SQLite"""
    db_path = "src/database/app.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        cursor = conn.cursor()
        
        # Verificar tabelas disponíveis
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 Tabelas encontradas no banco: {tables}")
        
        # Tentar encontrar a tabela de contas
        account_table = None
        for table_name in ['kommo_account', 'accounts', 'kommo_accounts']:
            if table_name in tables:
                account_table = table_name
                break
        
        if not account_table:
            logger.error("❌ Tabela de contas não encontrada")
            return []
        
        logger.info(f"📋 Usando tabela: {account_table}")
        
        # Obter estrutura da tabela
        cursor.execute(f"PRAGMA table_info({account_table});")
        columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"📋 Colunas disponíveis: {columns}")
        
        # Buscar contas
        cursor.execute(f"SELECT * FROM {account_table} ORDER BY id")
        rows = cursor.fetchall()
        
        accounts = []
        for row in rows:
            account = dict(row)
            accounts.append(account)
            logger.info(f"📊 Conta encontrada: {account.get('subdomain', 'N/A')} (ID: {account.get('id', 'N/A')})")
        
        conn.close()
        return accounts
        
    except Exception as e:
        logger.error(f"❌ Erro ao acessar banco de dados: {e}")
        return []

def analyze_account_required_statuses(api: SimpleKommoAPI, account_name: str) -> Dict:
    """Analisa os required_statuses de uma conta"""
    logger.info(f"🔍 Analisando required_statuses da conta: {account_name}")
    
    try:
        # Obter pipelines
        pipelines = api.get_pipelines()
        pipelines_by_id = {p['id']: p for p in pipelines}
        
        logger.info(f"📊 Pipelines encontrados: {len(pipelines)}")
        for pipeline in pipelines:
            logger.info(f"   - {pipeline['name']} (ID: {pipeline['id']})")
        
        # Obter estágios de cada pipeline para referência
        all_stages = {}
        for pipeline in pipelines:
            try:
                stages = api.get_pipeline_stages(pipeline['id'])
                all_stages[pipeline['id']] = {s['id']: s for s in stages}
                
                # Verificar se há status especiais
                special_stages = [s for s in stages if s['id'] in [142, 143, 1]]
                if special_stages:
                    logger.info(f"   Pipeline '{pipeline['name']}': {len(stages)} estágios (⭐ {len(special_stages)} especiais)")
                    for special in special_stages:
                        logger.info(f"      🎯 Status especial: {special['id']} - {special['name']}")
                else:
                    logger.info(f"   Pipeline '{pipeline['name']}': {len(stages)} estágios")
                    
            except Exception as e:
                logger.warning(f"   Erro ao obter estágios do pipeline {pipeline['id']}: {e}")
                all_stages[pipeline['id']] = {}
        
        # Obter campos customizados
        entities = ['leads', 'contacts', 'companies']
        all_required_statuses = {}
        
        for entity in entities:
            logger.info(f"\n🔍 Verificando campos de {entity}...")
            
            try:
                fields = api.get_custom_fields(entity)
                logger.info(f"   Campos encontrados: {len(fields)}")
                
                fields_with_required = []
                for field in fields:
                    if field.get('required_statuses'):
                        fields_with_required.append(field)
                        
                        # Verificar se há status especiais nos required_statuses
                        special_in_required = [rs for rs in field['required_statuses'] if rs.get('status_id') in [142, 143, 1]]
                        if special_in_required:
                            logger.info(f"   📋 Campo '{field['name']}' tem {len(field['required_statuses'])} required_statuses (⭐ {len(special_in_required)} especiais)")
                            for special in special_in_required:
                                status_names = {142: "Won", 143: "Lost", 1: "Incoming"}
                                status_name = status_names.get(special['status_id'], "ESPECIAL")
                                logger.info(f"      🎯 Required status especial: {special['status_id']} ({status_name})")
                        else:
                            logger.info(f"   📋 Campo '{field['name']}' tem {len(field['required_statuses'])} required_statuses")
                
                all_required_statuses[entity] = fields_with_required
                logger.info(f"   Total com required_statuses: {len(fields_with_required)}")
                
            except Exception as e:
                logger.error(f"   ❌ Erro ao obter campos de {entity}: {e}")
                all_required_statuses[entity] = []
        
        return {
            'account_name': account_name,
            'pipelines': pipelines_by_id,
            'stages': all_stages,
            'required_statuses': all_required_statuses
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao analisar conta {account_name}: {e}")
        return {
            'account_name': account_name,
            'pipelines': {},
            'stages': {},
            'required_statuses': {},
            'error': str(e)
        }

def print_detailed_analysis(account_data: Dict):
    """Imprime análise detalhada dos required_statuses"""
    account_name = account_data['account_name']
    pipelines = account_data.get('pipelines', {})
    stages = account_data.get('stages', {})
    required_statuses = account_data.get('required_statuses', {})
    
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 ANÁLISE DETALHADA - {account_name.upper()}")
    logger.info(f"{'='*80}")
    
    if 'error' in account_data:
        logger.error(f"❌ Erro na conta: {account_data['error']}")
        return
    
    total_fields_with_required = 0
    total_required_statuses = 0
    status_usage = {}
    special_statuses_found = []
    
    for entity, fields in required_statuses.items():
        if not fields:
            logger.info(f"\n📂 {entity.upper()}: Nenhum campo com required_statuses")
            continue
            
        logger.info(f"\n📂 {entity.upper()}: {len(fields)} campos com required_statuses")
        total_fields_with_required += len(fields)
        
        for field in fields:
            field_name = field['name']
            field_type = field.get('type', 'unknown')
            req_statuses = field.get('required_statuses', [])
            
            logger.info(f"\n   🏷️ Campo: '{field_name}' ({field_type})")
            logger.info(f"      Required statuses: {len(req_statuses)}")
            
            total_required_statuses += len(req_statuses)
            
            for i, rs in enumerate(req_statuses, 1):
                status_id = rs.get('status_id')
                pipeline_id = rs.get('pipeline_id')
                
                # Contar uso do status
                if status_id not in status_usage:
                    status_usage[status_id] = 0
                status_usage[status_id] += 1
                
                # Verificar se é status especial
                if status_id in [142, 143, 1]:
                    special_statuses_found.append({
                        'status_id': status_id,
                        'pipeline_id': pipeline_id,
                        'field_name': field_name,
                        'entity': entity
                    })
                
                # Obter nomes
                pipeline_name = "DESCONHECIDA"
                if pipeline_id in pipelines:
                    pipeline_name = pipelines[pipeline_id]['name']
                
                status_name = "DESCONHECIDO"
                if status_id in [142, 143, 1]:
                    status_names = {142: "Won", 143: "Lost", 1: "Incoming"}
                    status_name = status_names.get(status_id, "ESPECIAL")
                elif pipeline_id in stages and status_id in stages[pipeline_id]:
                    status_name = stages[pipeline_id][status_id]['name']
                
                status_type = "🎯 ESPECIAL" if status_id in [142, 143, 1] else "📝 NORMAL"
                logger.info(f"         {i}. Pipeline '{pipeline_name}' (ID: {pipeline_id})")
                logger.info(f"            Status '{status_name}' (ID: {status_id}) [{status_type}]")
    
    # Resumo geral
    logger.info(f"\n📈 RESUMO GERAL:")
    logger.info(f"   Total de campos com required_statuses: {total_fields_with_required}")
    logger.info(f"   Total de required_statuses configurados: {total_required_statuses}")
    logger.info(f"   Status únicos utilizados: {len(status_usage)}")
    
    # Status especiais encontrados
    if special_statuses_found:
        logger.info(f"\n⭐ STATUS ESPECIAIS ENCONTRADOS ({len(special_statuses_found)}):")
        status_142_count = len([s for s in special_statuses_found if s['status_id'] == 142])
        status_143_count = len([s for s in special_statuses_found if s['status_id'] == 143])
        status_1_count = len([s for s in special_statuses_found if s['status_id'] == 1])
        
        if status_142_count > 0:
            logger.info(f"   🎯 Status 142 (Won): usado {status_142_count}x em required_statuses")
        if status_143_count > 0:
            logger.info(f"   🎯 Status 143 (Lost): usado {status_143_count}x em required_statuses")
        if status_1_count > 0:
            logger.info(f"   🎯 Status 1 (Incoming): usado {status_1_count}x em required_statuses")
            
        logger.info(f"\n   📋 Detalhes dos status especiais:")
        for special in special_statuses_found:
            status_names = {142: "Won", 143: "Lost", 1: "Incoming"}
            status_name = status_names.get(special['status_id'], "ESPECIAL")
            pipeline_name = pipelines.get(special['pipeline_id'], {}).get('name', 'DESCONHECIDA')
            
            logger.info(f"      🎯 Status {special['status_id']} ({status_name})")
            logger.info(f"         📂 Campo: {special['field_name']} ({special['entity']})")
            logger.info(f"         📊 Pipeline: {pipeline_name} (ID: {special['pipeline_id']})")
    else:
        logger.info(f"\n📝 ❌ NENHUM STATUS ESPECIAL (142, 143, 1) ENCONTRADO NOS REQUIRED_STATUSES!")
        logger.info(f"   💡 Isso pode indicar que os status especiais não estão sendo usados ou mapeados corretamente")

def main():
    """Função principal"""
    logger.info("🚀 ANALISADOR DE REQUIRED_STATUSES (USANDO BANCO LOCAL)")
    logger.info("=" * 80)
    
    try:
        # Obter contas do banco de dados
        accounts = get_accounts_from_database()
        
        if len(accounts) < 2:
            logger.error("❌ Necessário pelo menos 2 contas para comparar master e slave")
            logger.info(f"📊 Contas encontradas: {len(accounts)}")
            for acc in accounts:
                logger.info(f"   - {acc.get('subdomain', 'N/A')}")
            return
        
        # Usar as duas primeiras contas como master e slave
        master_account = accounts[0]
        slave_account = accounts[1]
        
        logger.info(f"📊 Contas selecionadas:")
        logger.info(f"   Master: {master_account.get('subdomain', 'N/A')}")
        logger.info(f"   Slave: {slave_account.get('subdomain', 'N/A')}")
        
        # Verificar se temos tokens
        master_token = master_account.get('access_token') or master_account.get('token')
        slave_token = slave_account.get('access_token') or slave_account.get('token')
        
        if not master_token or not slave_token:
            logger.error("❌ Tokens não encontrados nas contas do banco")
            logger.info("📋 Campos disponíveis na conta master:")
            for key in master_account.keys():
                logger.info(f"   - {key}: {str(master_account[key])[:50]}...")
            return
        
        # Criar instâncias das APIs
        logger.info(f"\n🔗 Conectando às APIs...")
        
        master_api = SimpleKommoAPI(master_account['subdomain'], master_token)
        slave_api = SimpleKommoAPI(slave_account['subdomain'], slave_token)
        
        # Analisar ambas as contas
        logger.info(f"\n🔍 Iniciando análise das contas...")
        
        master_data = analyze_account_required_statuses(master_api, f"MASTER ({master_account['subdomain']})")
        slave_data = analyze_account_required_statuses(slave_api, f"SLAVE ({slave_account['subdomain']})")
        
        # Imprimir análises detalhadas
        print_detailed_analysis(master_data)
        print_detailed_analysis(slave_data)
        
        # Comparação final
        logger.info(f"\n{'='*80}")
        logger.info(f"🔄 COMPARAÇÃO MASTER vs SLAVE")
        logger.info(f"{'='*80}")
        
        master_fields = sum(len(fields) for fields in master_data.get('required_statuses', {}).values())
        slave_fields = sum(len(fields) for fields in slave_data.get('required_statuses', {}).values())
        
        # Contar status especiais em cada conta
        master_special = []
        slave_special = []
        
        for entity, fields in master_data.get('required_statuses', {}).items():
            for field in fields:
                for rs in field.get('required_statuses', []):
                    if rs.get('status_id') in [142, 143, 1]:
                        master_special.append(rs)
        
        for entity, fields in slave_data.get('required_statuses', {}).items():
            for field in fields:
                for rs in field.get('required_statuses', []):
                    if rs.get('status_id') in [142, 143, 1]:
                        slave_special.append(rs)
        
        logger.info(f"📊 Campos com required_statuses:")
        logger.info(f"   Master: {master_fields}")
        logger.info(f"   Slave: {slave_fields}")
        logger.info(f"   Diferença: {master_fields - slave_fields}")
        
        logger.info(f"\n🎯 Status especiais (142, 143, 1) nos required_statuses:")
        logger.info(f"   Master: {len(master_special)}")
        logger.info(f"   Slave: {len(slave_special)}")
        logger.info(f"   Diferença: {len(master_special) - len(slave_special)}")
        
        if len(master_special) > len(slave_special):
            logger.warning(f"⚠️ Master tem mais status especiais em required_statuses que a slave")
            logger.info(f"💡 Isso indica que a correção implementada pode ser necessária")
        elif len(slave_special) > len(master_special):
            logger.warning(f"⚠️ Slave tem mais status especiais em required_statuses que a master")
        else:
            if len(master_special) > 0:
                logger.info(f"✅ Ambas as contas têm a mesma quantidade de status especiais nos required_statuses")
            else:
                logger.info(f"📝 Nenhuma conta tem status especiais nos required_statuses")
        
        # Salvar resultado
        result = {
            'master': master_data,
            'slave': slave_data,
            'comparison': {
                'master_fields': master_fields,
                'slave_fields': slave_fields,
                'master_special_statuses': len(master_special),
                'slave_special_statuses': len(slave_special),
                'difference': master_fields - slave_fields,
                'special_difference': len(master_special) - len(slave_special)
            }
        }
        
        with open('required_statuses_analysis_complete.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Análise completa salva em: required_statuses_analysis_complete.json")
            
    except Exception as e:
        logger.error(f"❌ Erro na análise: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
