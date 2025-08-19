#!/usr/bin/env python3
"""
Lista os required_statuses dos campos customizados das contas master e slave
Versão simplificada sem dependência do banco de dados
"""

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
        for special in special_statuses_found:
            status_names = {142: "Won", 143: "Lost", 1: "Incoming"}
            status_name = status_names.get(special['status_id'], "ESPECIAL")
            pipeline_name = pipelines.get(special['pipeline_id'], {}).get('name', 'DESCONHECIDA')
            
            logger.info(f"   🎯 Status {special['status_id']} ({status_name})")
            logger.info(f"      📂 Entidade: {special['entity']}")
            logger.info(f"      🏷️ Campo: {special['field_name']}")
            logger.info(f"      📊 Pipeline: {pipeline_name} (ID: {special['pipeline_id']})")
    else:
        logger.info(f"\n📝 Nenhum status especial (142, 143, 1) encontrado nos required_statuses")
    
    # Top status mais usados
    if status_usage:
        logger.info(f"\n🔥 TOP 10 STATUS MAIS UTILIZADOS:")
        sorted_statuses = sorted(status_usage.items(), key=lambda x: x[1], reverse=True)
        
        for i, (status_id, count) in enumerate(sorted_statuses[:10], 1):
            status_type = "ESPECIAL" if status_id in [142, 143, 1] else "NORMAL"
            logger.info(f"   {i}. Status {status_id}: usado {count}x ({status_type})")

def main():
    """Função principal"""
    logger.info("🚀 ANALISADOR DE REQUIRED_STATUSES")
    logger.info("=" * 80)
    
    # CONFIGURAÇÃO - ALTERE ESTAS INFORMAÇÕES
    # =====================================
    
    # Conta Master
    MASTER_SUBDOMAIN = "teste3"  # Substitua pelo subdomínio da master
    MASTER_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjY5MTY3NTVjZTZhYzU4MmYwOGI2ZWY4YmJhNzNhZGMxMzIzN2M1YzU3OGIwZDg3ZmE0MDg5MjRmMzU4YTU0NDQ5NzNmY2I4ZWM4M2M4ZmI5In0.eyJhdWQiOiI5OGZkNGQ3Yi1hYzVjLTQ4MzEtOGRjZC1mOGQ1MDI5NmI4ODUiLCJqdGkiOiI2OTE2NzU1Y2U2YWM1ODJmMDhiNmVmOGJiYTczYWRjMTMyMzdjNWM1NzhiMGQ4N2ZhNDA4OTI0ZjM1OGE1NDQ0OTczZmNiOGVjODNjOGZiOSIsImlhdCI6MTczNDU0MjA2NCwibmJmIjoxNzM0NTQyMDY0LCJleHAiOjE3NDI0MDQ4MDAsInN1YiI6IjU1MDI3MDAiLCJhY2NvdW50X2lkIjozMzMzNjE1NSwic2NvcGVzIjpbImNybSIsImZpbGVzIiwibm90aWZpY2F0aW9ucyJdfQ.Ai_Ky4MwY2xmv0vUJI6PKG_ZYGdgYX-4t5aJgHFz6zOqCPcXvdaA6oXPdBhNBZwQT82s7Qf9bNrJ4bFOlwdKNPKWQDSI8jO9r8b9nUsWVV3NUTfVFH3K7mN8vGgNUJGf5e0cZL7DWFO0BI2tnz-QQCl9SLn7bQrNJePM6VGrjdwQvuE0_qk3y9pE9RbOQ2sO7m_B3eGvr_tEyKaY_7kfSh3H5ZxGb7oSRQp-mZ4TP5H8YPG2JJNrQzGsQJrG7B5f8t0Ny7aKU_7Yw2LHYGFfPOqL2RQQrV8O8a6Ry_K"  # Substitua pelo token da master
    
    # Conta Slave
    SLAVE_SUBDOMAIN = "testesync"  # Substitua pelo subdomínio da slave
    SLAVE_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjJmYjM2N2ZmOTc0MzkzZTY0NTk1YWM2Y2IzMzVjZDU1ZWY5ZmRmN2RhNzEwOTI5NzU3ODI3MjliZDNlNzNhMzY1NDczODQ3M2Y5Yzg0ZGM0In0.eyJhdWQiOiI5OGZkNGQ3Yi1hYzVjLTQ4MzEtOGRjZC1mOGQ1MDI5NmI4ODUiLCJqdGkiOiIyZmIzNjdmZjk3NDM5M2U2NDU5NWFjNmNiMzM1Y2Q1NWVmOWZkZjdkYTcxMDkyOTc1NzgyNzI5YmQzZTczYTM2NTQ3Mzg0NzNmOWM4NGRjNCIsImlhdCI6MTczNDUzOTE2NCwibmJmIjoxNzM0NTM5MTY0LCJleHAiOjE3NDI0MDQ4MDAsInN1YiI6IjU1MDI3MDAiLCJhY2NvdW50X2lkIjozMzMzNzIwNSwic2NvcGVzIjpbImNybSIsImZpbGVzIiwibm90aWZpY2F0aW9ucyJdfQ.SJhp5_wqGj7lF9DRY4VKPSg8IfG9O9PGgBRnRHN0GZ4-IXz3mQyPB5B7p2DfXz4V8pJWjg-hQvhDR9B8XLZ4NZd5mJ_z5cQ3tF8cKZ0B9vG7HmY8rYfpNZ3VH5mQ9c8B_5W7Zz6F3J8nC5F9Y2LnY3X5VHFGpRZ8sJ5B2mK5Z8F4JnT9L7HZoKFgJ2V3mY5BfJ7WnZ6G8pL4Y7XFH9J5LnVGqB8cJ3m_r7D8nY6F5Z4LmH9W8VcZ5XnJKoG3rY5LZ9Qc"  # Substitua pelo token da slave
    
    # =====================================
    
    if not MASTER_TOKEN or not SLAVE_TOKEN:
        logger.error("❌ Por favor, configure os tokens das contas master e slave no script")
        logger.info("📝 Edite as variáveis MASTER_TOKEN e SLAVE_TOKEN no código")
        return
    
    try:
        # Criar instâncias das APIs
        logger.info(f"🔗 Conectando às contas...")
        logger.info(f"   Master: {MASTER_SUBDOMAIN}")
        logger.info(f"   Slave: {SLAVE_SUBDOMAIN}")
        
        master_api = SimpleKommoAPI(MASTER_SUBDOMAIN, MASTER_TOKEN)
        slave_api = SimpleKommoAPI(SLAVE_SUBDOMAIN, SLAVE_TOKEN)
        
        # Analisar ambas as contas
        logger.info(f"\n🔍 Iniciando análise das contas...")
        
        master_data = analyze_account_required_statuses(master_api, f"MASTER ({MASTER_SUBDOMAIN})")
        slave_data = analyze_account_required_statuses(slave_api, f"SLAVE ({SLAVE_SUBDOMAIN})")
        
        # Imprimir análises detalhadas
        print_detailed_analysis(master_data)
        print_detailed_analysis(slave_data)
        
        # Comparação final
        logger.info(f"\n{'='*80}")
        logger.info(f"🔄 COMPARAÇÃO MASTER vs SLAVE")
        logger.info(f"{'='*80}")
        
        master_fields = sum(len(fields) for fields in master_data.get('required_statuses', {}).values())
        slave_fields = sum(len(fields) for fields in slave_data.get('required_statuses', {}).values())
        
        logger.info(f"📊 Campos com required_statuses:")
        logger.info(f"   Master: {master_fields}")
        logger.info(f"   Slave: {slave_fields}")
        logger.info(f"   Diferença: {master_fields - slave_fields}")
        
        if master_fields > slave_fields:
            logger.warning(f"⚠️ Master tem mais campos com required_statuses que a slave")
            logger.info(f"💡 Isso pode indicar que nem todos os campos foram sincronizados")
        elif slave_fields > master_fields:
            logger.warning(f"⚠️ Slave tem mais campos com required_statuses que a master")
        else:
            logger.info(f"✅ Ambas as contas têm o mesmo número de campos com required_statuses")
        
        # Salvar resultado em arquivo JSON para análise posterior
        result = {
            'master': master_data,
            'slave': slave_data,
            'comparison': {
                'master_fields': master_fields,
                'slave_fields': slave_fields,
                'difference': master_fields - slave_fields
            }
        }
        
        with open('required_statuses_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n💾 Análise salva em: required_statuses_analysis.json")
            
    except Exception as e:
        logger.error(f"❌ Erro na análise: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
