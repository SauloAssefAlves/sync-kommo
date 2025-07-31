import requests
import time
import re
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging

logger = logging.getLogger(__name__)

# Imports para salvamento no banco
from src.database import db
from src.models.kommo_account import PipelineMapping, StageMapping, CustomFieldMapping

class KommoAPIService:
    """Serviço para interagir com a API do Kommo usando refresh_token diretamente nos headers"""
    
    def __init__(self, subdomain: str, refresh_token: str):
        self.subdomain = subdomain
        self.refresh_token = refresh_token
        self.base_url = f"https://{subdomain}.kommo.com/api/v4"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Faz uma requisição para a API do Kommo usando refresh_token diretamente nos headers"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Usar refresh_token diretamente no header Authorization
        headers = {
            'Authorization': f'Bearer {self.refresh_token}',
            'Content-Type': 'application/json'
        }
        
        logger.debug(f"Fazendo requisição {method} para {url}")
        logger.debug(f"Usando refresh_token: {self.refresh_token[:20]}...")
        
        try:
            response = requests.request(method, url, json=data, params=params, headers=headers)
            
            logger.debug(f"Status da resposta: {response.status_code}")
            
            # Tratamento de rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limit atingido. Aguardando {retry_after} segundos...")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, data, params)
            
            # Log detalhado em caso de erro
            if not response.ok:
                logger.error(f"Erro HTTP {response.status_code} para {url}")
                logger.error(f"Resposta: {response.text}")
            
            response.raise_for_status()
            
            # Para operações DELETE que retornam 204 No Content ou respostas vazias
            if method.upper() == 'DELETE' and (response.status_code == 204 or not response.text.strip()):
                logger.debug(f"DELETE bem-sucedido - Status {response.status_code}, resposta vazia")
                return {'success': True, 'status_code': response.status_code}
            
            # Para outras respostas vazias
            if not response.text.strip():
                logger.warning(f"Resposta vazia para {method} {url} - Status {response.status_code}")
                return {'success': True, 'status_code': response.status_code}
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}")
            raise
        except ValueError as e:
            # Erro de parsing JSON - pode ser resposta vazia válida
            if method.upper() == 'DELETE' and response.status_code in [200, 204]:
                logger.debug(f"DELETE bem-sucedido com resposta não-JSON - Status {response.status_code}")
                return {'success': True, 'status_code': response.status_code}
            logger.error(f"Erro ao fazer parse JSON da resposta de {url}: {e}")
            logger.error(f"Conteúdo da resposta: '{response.text}'")
            raise
    
    def get_pipelines(self) -> List[Dict]:
        """Obtém todos os pipelines da conta"""
        response = self._make_request('GET', '/leads/pipelines')
        return response.get('_embedded', {}).get('pipelines', [])
    
    def get_pipeline_stages(self, pipeline_id: int) -> List[Dict]:
        """Obtém todos os estágios de um pipeline específico"""
        # Tentar obter informações sobre campos obrigatórios nos estágios
        params = {'with': 'required_fields'}
        response = self._make_request('GET', f'/leads/pipelines/{pipeline_id}/statuses', params=params)
        stages = response.get('_embedded', {}).get('statuses', [])
        
        # Log para debug
        logger.debug(f"Obtidos {len(stages)} estágios para pipeline {pipeline_id}")
        for stage in stages:
            if stage.get('required_fields'):
                logger.info(f"🎯 ESTÁGIO COM CAMPOS OBRIGATÓRIOS: '{stage['name']}' tem campos obrigatórios: {stage['required_fields']}")
        
        return stages
    
    def create_pipeline(self, pipeline_data: Dict) -> Dict:
        """Cria um novo pipeline"""
        return self._make_request('POST', '/leads/pipelines', data=[pipeline_data])
    
    def update_pipeline(self, pipeline_id: int, pipeline_data: Dict) -> Dict:
        """Atualiza um pipeline existente"""
        return self._make_request('PATCH', f'/leads/pipelines/{pipeline_id}', data=pipeline_data)
    
    def create_pipeline_stage(self, pipeline_id: int, stage_data: Dict) -> Dict:
        """Cria um novo estágio em um pipeline"""
        return self._make_request('POST', f'/leads/pipelines/{pipeline_id}/statuses', data=[stage_data])
    
    def update_pipeline_stage(self, pipeline_id: int, stage_id: int, stage_data: Dict) -> Dict:
        """Atualiza um estágio existente"""
        return self._make_request('PATCH', f'/leads/pipelines/{pipeline_id}/statuses/{stage_id}', data=stage_data)
    
    def delete_pipeline_stage(self, stage_id: int) -> Dict:
        """Deleta um estágio de pipeline"""
        return self._make_request('DELETE', f'/leads/pipelines/statuses/{stage_id}')
    
    def get_custom_fields(self, entity_type: str) -> List[Dict]:
        """Obtém todos os campos personalizados para uma entidade (leads, contacts, companies)"""
        # Adicionar parâmetros para obter informações completas dos campos
        params = {
            'with': 'required_statuses,enums'  # Tentar obter required_statuses e enums
        }
        response = self._make_request('GET', f'/{entity_type}/custom_fields', params=params)
        fields = response.get('_embedded', {}).get('custom_fields', [])
        
        # Log para debug
        logger.debug(f"Obtidos {len(fields)} campos para {entity_type}")
        for field in fields:
            if field.get('required_statuses'):
                logger.info(f"📋 Campo '{field['name']}' tem required_statuses na API: {field['required_statuses']}")
        
        return fields
    
    def get_custom_field_groups(self, entity_type: str) -> List[Dict]:
        """Obtém todos os grupos de campos personalizados para uma entidade"""
        try:
            # A API do Kommo para grupos pode usar diferentes endpoints
            # Tentar primeiro o endpoint padrão
            response = self._make_request('GET', f'/{entity_type}/custom_fields/groups')
            logger.debug(f"Resposta bruta da API para grupos de {entity_type}: {response}")
            
            # Tentar diferentes estruturas de resposta
            groups = response.get('_embedded', {}).get('custom_field_groups', [])
            if not groups:
                # Tentar estrutura alternativa
                groups = response.get('custom_field_groups', [])
            if not groups:
                # Se ainda não encontrou, verificar se é uma lista direta
                if isinstance(response, list):
                    groups = response
            if not groups:
                # Tentar endpoint alternativo se o primeiro não retornou nada
                logger.warning(f"Nenhum grupo encontrado no endpoint padrão para {entity_type}, tentando endpoint alternativo...")
                response = self._make_request('GET', f'/api/v4/{entity_type}/custom_fields/groups')
                groups = response.get('_embedded', {}).get('custom_field_groups', [])
            
            logger.info(f"Encontrados {len(groups)} grupos de campos para {entity_type}")
            if groups:
                logger.debug(f"Primeiro grupo: {groups[0] if groups else 'Nenhum'}")
            else:
                logger.warning(f"❌ NENHUM grupo de campos encontrado para {entity_type}!")
                logger.debug(f"Estrutura completa da resposta: {response}")
            
            return groups
        except Exception as e:
            logger.error(f"Erro ao obter grupos de campos para {entity_type}: {e}")
            return []
    
    def create_custom_field_group(self, entity_type: str, group_data: Dict) -> Dict:
        """Cria um novo grupo de campos personalizados"""
        return self._make_request('POST', f'/{entity_type}/custom_fields/groups', data=[group_data])
    
    def update_custom_field_group(self, entity_type: str, group_id: int, group_data: Dict) -> Dict:
        """Atualiza um grupo de campos personalizados existente"""
        return self._make_request('PATCH', f'/{entity_type}/custom_fields/groups/{group_id}', data=group_data)
    
    def delete_custom_field_group(self, entity_type: str, group_id: int) -> Dict:
        """Deleta um grupo de campos personalizados"""
        return self._make_request('DELETE', f'/{entity_type}/custom_fields/groups/{group_id}')
    
    def create_custom_field(self, entity_type: str, field_data: Dict) -> Dict:
        """Cria um novo campo personalizado"""
        return self._make_request('POST', f'/{entity_type}/custom_fields', data=[field_data])
    
    def update_custom_field(self, entity_type: str, field_id: int, field_data: Dict) -> Dict:
        """Atualiza um campo personalizado existente"""
        return self._make_request('PATCH', f'/{entity_type}/custom_fields/{field_id}', data=field_data)
    
    def delete_custom_field(self, entity_type: str, field_id: int) -> Dict:
        """Deleta um campo personalizado"""
        return self._make_request('DELETE', f'/{entity_type}/custom_fields/{field_id}')
    
    def delete_pipeline(self, pipeline_id: int) -> Dict:
        """Deleta um pipeline"""
        return self._make_request('DELETE', f'/leads/pipelines/{pipeline_id}')
    
    def test_connection(self) -> bool:
        """Testa se a conexão com a API está funcionando"""
        try:
            self._make_request('GET', '/account')
            return True
        except Exception as e:
            logger.error(f"Falha no teste de conexão: {e}")
            return False

class KommoSyncService:
    """Serviço principal para sincronização entre contas Kommo"""
    
    def __init__(self, master_api: KommoAPIService, batch_size: int = 10, delay_between_batches: float = 2.0):
        self.master_api = master_api
        self.entity_types = ['leads', 'contacts', 'companies']
        self.batch_size = batch_size  # Quantos itens processar por lote
        self.delay_between_batches = delay_between_batches  # Delay em segundos entre lotes
        self._stop_sync = False  # Flag para parar sincronização
        
    def stop_sync(self):
        """Para a sincronização em andamento"""
        self._stop_sync = True
        logger.info("🛑 Solicitação de parada da sincronização recebida")
    
    def _process_in_batches(self, items: List[Any], process_func: Callable, operation_name: str, 
                           results: Dict, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Processa uma lista de itens em lotes com delay entre eles
        
        Args:
            items: Lista de itens para processar
            process_func: Função que processa um item individual
            operation_name: Nome da operação para logs
            results: Dicionário de resultados para atualizar
            progress_callback: Função opcional para callback de progresso
        """
        total_items = len(items)
        processed = 0
        
        if total_items == 0:
            logger.info(f"📦 Nenhum item para processar em {operation_name}")
            return results
            
        logger.info(f"📦 Iniciando processamento em lotes: {total_items} {operation_name}")
        logger.info(f"⚙️ Configuração: {self.batch_size} itens por lote, {self.delay_between_batches}s de delay")
        
        # Dividir em lotes
        for i in range(0, total_items, self.batch_size):
            if self._stop_sync:
                logger.warning(f"🛑 Sincronização interrompida pelo usuário em {operation_name}")
                break
                
            batch = items[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_items + self.batch_size - 1) // self.batch_size
            
            logger.info(f"📦 Processando lote {batch_num}/{total_batches} ({len(batch)} itens)")
            
            # Processar itens do lote atual
            batch_results = {'success': 0, 'errors': 0}
            for item in batch:
                if self._stop_sync:
                    break
                    
                try:
                    process_func(item, results)
                    batch_results['success'] += 1
                    processed += 1
                except Exception as e:
                    logger.error(f"Erro ao processar item em {operation_name}: {e}")
                    batch_results['errors'] += 1
                    if 'errors' not in results:
                        results['errors'] = []
                    results['errors'].append(str(e))
            
            # Callback de progresso
            if progress_callback:
                progress = {
                    'operation': operation_name,
                    'processed': processed,
                    'total': total_items,
                    'percentage': round((processed / total_items) * 100, 1),
                    'current_batch': batch_num,
                    'total_batches': total_batches,
                    'batch_results': batch_results
                }
                progress_callback(progress)
            
            logger.info(f"✅ Lote {batch_num} concluído: {batch_results['success']} sucessos, {batch_results['errors']} erros")
            
            # Delay entre lotes (exceto no último)
            if i + self.batch_size < total_items and not self._stop_sync:
                logger.info(f"⏳ Aguardando {self.delay_between_batches}s antes do próximo lote...")
                time.sleep(self.delay_between_batches)
        
        logger.info(f"📦 {operation_name} concluído: {processed}/{total_items} itens processados")
        return results
    
    def extract_master_configuration(self) -> Dict[str, Any]:
        """Extrai todas as configurações da conta mestre"""
        config = {
            'pipelines': [],
            'custom_fields': {},
            'custom_field_groups': {}
        }
        
        # Extrair pipelines e seus estágios
        pipelines = self.master_api.get_pipelines()
        for pipeline in pipelines:
            pipeline_data = {
                'id': pipeline['id'],
                'name': pipeline['name'],
                'sort': max(1, min(10000, pipeline.get('sort', 1))),  # Garantir range válido
                'is_main': pipeline.get('is_main', False),
                'is_unsorted_on': pipeline.get('is_unsorted_on', True),
                'stages': []
            }
            
            # Extrair estágios do pipeline
            stages = self.master_api.get_pipeline_stages(pipeline['id'])
            for i, stage in enumerate(stages):
                # Verificar se deve usar ID padrão do Kommo
                default_stage_id = self._get_default_stage_id(stage['name'], stage.get('type', 0))
                
                stage_data = {
                    'name': stage['name'],
                    'sort': max(1, min(10000, stage.get('sort', i + 1))),  # Garantir range válido
                    'color': stage.get('color', '#99ccff'),  # Cor padrão se não tiver
                    'type': stage.get('type', 0)
                }
                
                # Preservar ID da master para mapeamento, mas usar ID padrão quando aplicável
                stage_data['id'] = stage['id']  # ID original da master para mapeamento
                if default_stage_id:
                    stage_data['default_id'] = default_stage_id  # ID padrão para usar na slave
                    logger.debug(f"Estágio '{stage['name']}' usará ID padrão {default_stage_id}")
                
                pipeline_data['stages'].append(stage_data)
            
            config['pipelines'].append(pipeline_data)
        
        # Extrair grupos de campos e campos personalizados para cada tipo de entidade
        for entity_type in self.entity_types:
            logger.info(f"🔍 Extraindo configuração para {entity_type}...")
            
            # 1. Extrair grupos de campos primeiro
            logger.debug(f"Buscando grupos de campos para {entity_type}...")
            field_groups = self.master_api.get_custom_field_groups(entity_type)
            config['custom_field_groups'][entity_type] = []
            
            logger.info(f"Encontrados {len(field_groups)} grupos de campos para {entity_type}")
            
            for group in field_groups:
                group_data = {
                    'id': group['id'],
                    'name': group['name'],
                    'sort': group.get('sort', 0)
                    # NOTA: is_collapsed removido - API do Kommo não suporta este campo
                }
                config['custom_field_groups'][entity_type].append(group_data)
                logger.debug(f"Grupo extraído: {group['name']} (ID: {group['id']})")
            
            # 2. Extrair campos personalizados
            custom_fields = self.master_api.get_custom_fields(entity_type)
            config['custom_fields'][entity_type] = []
            
            for field in custom_fields:
                field_data = {
                    'id': field['id'],
                    'name': field['name'],
                    'type': field['type'],
                    'code': field.get('code'),
                    'sort': field.get('sort', 0),
                    'is_required': field.get('is_required', False),
                    'group_id': field.get('group_id'),  # ID do grupo ao qual pertence
                    'required_statuses': field.get('required_statuses', []),  # Estágios específicos onde é obrigatório
                    'enums': []
                }
                
                # Log específico para campos com required_statuses
                if field.get('required_statuses'):
                    logger.info(f"🎯 CAMPO COM REQUIRED_STATUSES ENCONTRADO: '{field['name']}' tem {len(field['required_statuses'])} configurações")
                    for rs in field['required_statuses']:
                        logger.debug(f"  - Pipeline ID: {rs.get('pipeline_id')}, Status ID: {rs.get('status_id')}")
                else:
                    logger.debug(f"Campo '{field['name']}' sem required_statuses específicos")
                
                # Tratar enums de forma mais segura
                if field.get('enums'):
                    for enum_item in field['enums']:
                        if isinstance(enum_item, dict):
                            enum_data = {
                                'value': enum_item.get('value', ''),
                                'sort': enum_item.get('sort', 0)
                            }
                            # Não incluir ID do enum para evitar conflitos
                            field_data['enums'].append(enum_data)
                
                config['custom_fields'][entity_type].append(field_data)
        
        return config
    
    def sync_pipelines_to_slave(self, slave_api: KommoAPIService, master_config: Dict, 
                               mappings: Dict, progress_callback: Optional[Callable] = None, 
                               sync_group_id: Optional[int] = None, slave_account_id: Optional[int] = None) -> Dict:
        """Sincroniza pipelines da conta mestre para uma conta escrava - COM PROCESSAMENTO EM LOTES"""
        logger.info("📊 Iniciando sincronização de pipelines em lotes...")
        results = {'created': 0, 'updated': 0, 'skipped': 0, 'deleted': 0, 'errors': []}
        
        # Reset da flag de parada
        self._stop_sync = False
        
        try:
            # Obter pipelines existentes na conta escrava
            existing_pipelines = {p['name']: p for p in slave_api.get_pipelines()}
            master_pipeline_names = {p['name'] for p in master_config['pipelines']}
            
            # FASE 1: Criar/Atualizar pipelines da master EM LOTES
            def process_pipeline(master_pipeline, results):
                pipeline_name = master_pipeline['name']
                logger.info(f"🔄 Processando pipeline: {pipeline_name}")
                
                try:
                    if pipeline_name in existing_pipelines:
                        # Pipeline já existe - apenas armazenar mapeamento
                        existing_pipeline = existing_pipelines[pipeline_name]
                        slave_pipeline_id = existing_pipeline['id']
                        logger.info(f"Pipeline '{pipeline_name}' já existe (slave_id: {slave_pipeline_id})")
                        results['skipped'] += 1
                    else:
                        # Criar novo pipeline
                        stages_data = []
                        kommo_colors = [
                            '#fffeb2', '#fffd7f', '#fff000', '#ffeab2', '#ffdc7f', '#ffce5a',
                            '#ffdbdb', '#ffc8c8', '#ff8f92', '#d6eaff', '#c1e0ff', '#98cbff',
                            '#ebffb1', '#deff81', '#87f2c0', '#f9deff', '#f3beff', '#ccc8f9',
                            '#eb93ff', '#f2f3f4', '#e6e8ea'
                        ]
                        
                        def get_valid_kommo_color(master_color, fallback_index):
                            """Retorna uma cor válida do Kommo baseada na cor da master ou fallback inteligente"""
                            # Se a cor da master é válida, usar ela
                            if master_color and master_color.lower() in [c.lower() for c in kommo_colors]:
                                return master_color
                            
                            # Se não é válida, tentar mapear para cor similar
                            if master_color:
                                master_color_lower = master_color.lower()
                                
                                # Mapear cores azuis para cores azuis válidas do Kommo
                                if any(blue_hint in master_color_lower for blue_hint in ['blue', 'azul']) or master_color_lower in ['#0000ff', '#0066ff', '#4169e1']:
                                    return '#98cbff'  # Azul forte do Kommo
                                
                                # Mapear cores verdes para cores verdes válidas do Kommo  
                                if any(green_hint in master_color_lower for green_hint in ['green', 'verde']) or master_color_lower in ['#00ff00', '#008000', '#32cd32']:
                                    return '#87f2c0'  # Verde forte do Kommo
                                
                                # Mapear cores vermelhas/rosas para cores vermelhas válidas do Kommo
                                if any(red_hint in master_color_lower for red_hint in ['red', 'vermelho', '#ff0000', '#dc143c', '#b22222']):
                                    return '#ff8f92'  # Rosa forte do Kommo
                                
                                # Mapear cores roxas para cores roxas válidas do Kommo
                                if any(purple_hint in master_color_lower for purple_hint in ['purple', 'roxo', '#800080', '#9932cc', '#8a2be2']):
                                    return '#eb93ff'  # Magenta do Kommo
                                
                                # Mapear cores amarelas para cores amarelas válidas do Kommo
                                if any(yellow_hint in master_color_lower for yellow_hint in ['yellow', 'amarelo', '#ffff00', '#ffd700', '#fff8dc']):
                                    return '#fff000'  # Amarelo forte do Kommo
                                
                                # Mapear cores laranjas para cores laranjas válidas do Kommo
                                if any(orange_hint in master_color_lower for orange_hint in ['orange', 'laranja', '#ffa500', '#ff8c00', '#ff7f50']):
                                    return '#ffce5a'  # Laranja forte do Kommo
                            
                            # Se nenhum mapeamento específico, usar fallback por índice
                            return kommo_colors[fallback_index % len(kommo_colors)]
                        
                        processed_stage_index = 0  # Contador para estágios realmente processados
                        for i, master_stage in enumerate(master_pipeline['stages']):
                            # IGNORAR COMPLETAMENTE estágios especiais (IDs 142/143, type=1, etc.)
                            if self._should_ignore_stage(master_stage):
                                logger.info(f"🚫 Ignorando estágio especial '{master_stage['name']}' - será gerenciado automaticamente pelo Kommo")
                                continue
                                
                            stage_data = {
                                'name': master_stage['name'],
                                'sort': max(1, min(10000, master_stage.get('sort', i + 1))),
                                'type': master_stage.get('type', 0)
                            }
                            
                            # Usar a cor do stage da master validada (usar contador de estágios processados para fallback)
                            master_color = master_stage.get('color')
                            valid_color = get_valid_kommo_color(master_color, processed_stage_index)
                            stage_data['color'] = valid_color
                            logger.debug(f"Estágio '{master_stage['name']}' - Cor master: '{master_color}' -> Cor válida: '{valid_color}' (índice processado: {processed_stage_index})")
                            
                            processed_stage_index += 1  # Incrementar apenas para estágios processados
                                
                            stages_data.append(stage_data)
                        
                        pipeline_data = {
                            'name': master_pipeline['name'],
                            'sort': max(1, min(10000, master_pipeline.get('sort', 1))),
                            'is_main': master_pipeline.get('is_main', False),
                            'is_unsorted_on': master_pipeline.get('is_unsorted_on', True),
                            '_embedded': {'statuses': stages_data}
                        }
                        
                        logger.info(f"Criando pipeline '{pipeline_name}' com {len(stages_data)} estágios")
                        response = slave_api.create_pipeline(pipeline_data)
                        slave_pipeline_id = response['_embedded']['pipelines'][0]['id']
                        results['created'] += 1
                        
                        # Sincronizar nomes dos estágios automáticos criados pelo Kommo
                        # DESABILITADO: Os estágios especiais (142, 143) são gerenciados automaticamente pelo Kommo
                        # self._sync_automatic_stage_names(slave_api, master_pipeline, slave_pipeline_id)
                        logger.info(f"ℹ️ Sincronização de nomes automáticos desabilitada - Kommo gerencia os estágios especiais automaticamente")
                        
                        # Armazenar mapeamentos dos estágios criados
                        created_stages = response['_embedded']['pipelines'][0]['_embedded']['statuses']
                        if 'stages' not in mappings:
                            mappings['stages'] = {}
                        
                        # Mapear estágios criados - APENAS os que foram realmente enviados (ignorando especiais)
                        created_stage_index = 0
                        for master_stage in master_pipeline['stages']:
                            # IGNORAR COMPLETAMENTE estágios especiais no mapeamento
                            if self._should_ignore_stage(master_stage):
                                logger.debug(f"🚫 Ignorando mapeamento do estágio especial '{master_stage['name']}' - gerenciado pelo Kommo")
                                continue
                            
                            # Mapear estágios normais para IDs gerados pela API
                            if created_stage_index < len(created_stages):
                                slave_stage_id = created_stages[created_stage_index]['id']
                                master_stage_id = master_stage['id']
                                mappings['stages'][master_stage_id] = slave_stage_id
                                logger.info(f"✅ Mapeando estágio '{master_stage['name']}' -> ID slave {slave_stage_id}")
                                created_stage_index += 1
                    
                    # Armazenar mapeamento do pipeline
                    mappings['pipelines'][master_pipeline['id']] = slave_pipeline_id
                    
                    # Se pipeline já existia, sincronizar estágios separadamente
                    if pipeline_name in existing_pipelines:
                        self._sync_pipeline_stages(slave_api, master_pipeline, slave_pipeline_id, mappings)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar pipeline '{pipeline_name}': {e}")
                    raise
            
            # Processar pipelines em lotes
            self._process_in_batches(
                items=master_config['pipelines'],
                process_func=process_pipeline,
                operation_name="pipelines",
                results=results,
                progress_callback=progress_callback
            )
            
            if self._stop_sync:
                return results
            
            # FASE 2: Deletar pipelines que existem na escrava mas NÃO existem na master - EM LOTES
            pipelines_to_delete = []
            for slave_pipeline_name, slave_pipeline in existing_pipelines.items():
                if slave_pipeline_name not in master_pipeline_names:
                    if not slave_pipeline.get('is_main', False):
                        pipelines_to_delete.append(slave_pipeline)
            
            def delete_pipeline(pipeline_to_delete, results):
                pipeline_name = pipeline_to_delete['name']
                pipeline_id = pipeline_to_delete['id']
                logger.info(f"🗑️ Deletando pipeline '{pipeline_name}' (ID: {pipeline_id})")
                
                try:
                    delete_response = slave_api.delete_pipeline(pipeline_id)
                    if delete_response.get('success') or delete_response.get('status_code') in [200, 204]:
                        results['deleted'] += 1
                        logger.info(f"Pipeline '{pipeline_name}' deletado com sucesso")
                    else:
                        results['deleted'] += 1  # Considerar como sucesso
                        
                except Exception as e:
                    error_str = str(e).lower()
                    if any(phrase in error_str for phrase in ['not found', '404', 'does not exist']):
                        results['deleted'] += 1
                    else:
                        logger.error(f"Erro ao deletar pipeline '{pipeline_name}': {e}")
                        raise
            
            if pipelines_to_delete:
                logger.info(f"🗑️ Iniciando exclusão de {len(pipelines_to_delete)} pipelines em lotes...")
                self._process_in_batches(
                    items=pipelines_to_delete,
                    process_func=delete_pipeline,
                    operation_name="exclusão de pipelines",
                    results=results,
                    progress_callback=progress_callback
                )
            
        except Exception as e:
            logger.error(f"Erro geral na sincronização de pipelines: {e}")
            results['errors'].append(str(e))
        
        # Salvar mapeamentos no banco de dados se os IDs foram fornecidos
        if sync_group_id and slave_account_id:
            try:
                self._save_mappings_to_database(mappings, sync_group_id, slave_account_id)
            except Exception as e:
                logger.error(f"Erro ao salvar mapeamentos no banco: {e}")
                # Não falhar a sincronização por causa do erro de salvamento
        
        logger.info(f"📊 Sincronização de pipelines concluída: {results}")
        return results
    
    def _sync_pipeline_stages(self, slave_api: KommoAPIService, master_pipeline: Dict, slave_pipeline_id: int, mappings: Dict):
        """Sincroniza estágios de um pipeline específico - SINCRONIZAÇÃO BIDIRECIONAL"""
        logger.info(f"Sincronizando estágios do pipeline '{master_pipeline['name']}' (slave_id: {slave_pipeline_id})")
        
        # Obter estágios existentes na conta escrava usando o ID correto da conta escrava
        existing_stages_list = slave_api.get_pipeline_stages(slave_pipeline_id)
        existing_stages = {s['name']: s for s in existing_stages_list}
        
        # Criar conjunto dos nomes dos estágios da master para comparação
        master_stage_names = {stage['name'] for stage in master_pipeline['stages']}
        
        logger.info(f"📋 Pipeline '{master_pipeline['name']}' - Estágios existentes na slave: {list(existing_stages.keys())}")
        logger.info(f"📋 Pipeline '{master_pipeline['name']}' - Estágios da master: {list(master_stage_names)}")
        logger.info(f"📋 Pipeline '{master_pipeline['name']}' - Total de estágios mestre: {len(master_pipeline['stages'])}")
        
        # Cores oficiais da documentação do Kommo (COM #)
        kommo_colors = [
            '#fffeb2', '#fffd7f', '#fff000', '#ffeab2', '#ffdc7f', '#ffce5a',
            '#ffdbdb', '#ffc8c8', '#ff8f92', '#d6eaff', '#c1e0ff', '#98cbff',
            '#ebffb1', '#deff81', '#87f2c0', '#f9deff', '#f3beff', '#ccc8f9',
            '#eb93ff', '#f2f3f4', '#e6e8ea'
        ]
        
        def get_valid_kommo_color(master_color, fallback_index):
            """Retorna uma cor válida do Kommo baseada na cor da master ou fallback inteligente"""
            # Se a cor da master é válida, usar ela
            if master_color and master_color.lower() in [c.lower() for c in kommo_colors]:
                return master_color
            
            # Se não é válida, tentar mapear para cor similar
            if master_color:
                master_color_lower = master_color.lower()
                
            # Mapear cores azuis para cores azuis válidas do Kommo
            if any(blue_hint in master_color_lower for blue_hint in ['blue', 'azul']) or master_color_lower in ['#0000ff', '#0066ff', '#4169e1']:
                return '#98cbff'  # Azul forte do Kommo
            
            # Mapear cores verdes para cores verdes válidas do Kommo  
            if any(green_hint in master_color_lower for green_hint in ['green', 'verde']) or master_color_lower in ['#00ff00', '#008000', '#32cd32']:
                return '#87f2c0'  # Verde forte do Kommo                # Mapear cores vermelhas/rosas para cores vermelhas válidas do Kommo
                if any(red_hint in master_color_lower for red_hint in ['red', 'vermelho', '#ff0000', '#dc143c', '#b22222']):
                    return '#ff8f92'  # Rosa forte do Kommo
                
                # Mapear cores roxas para cores roxas válidas do Kommo
                if any(purple_hint in master_color_lower for purple_hint in ['purple', 'roxo', '#800080', '#9932cc', '#8a2be2']):
                    return '#eb93ff'  # Magenta do Kommo
                
                # Mapear cores amarelas para cores amarelas válidas do Kommo
                if any(yellow_hint in master_color_lower for yellow_hint in ['yellow', 'amarelo', '#ffff00', '#ffd700', '#fff8dc']):
                    return '#fff000'  # Amarelo forte do Kommo
                
                # Mapear cores laranjas para cores laranjas válidas do Kommo
                if any(orange_hint in master_color_lower for orange_hint in ['orange', 'laranja', '#ffa500', '#ff8c00', '#ff7f50']):
                    return '#ffce5a'  # Laranja forte do Kommo
            
            # Se nenhum mapeamento específico, usar fallback por índice
            return kommo_colors[fallback_index % len(kommo_colors)]
        
        # FASE 1: Criar/Atualizar estágios da master que estão faltando na slave
        processed_stage_index = 0  # Contador para estágios realmente processados
        for i, master_stage in enumerate(master_pipeline['stages']):
            try:
                stage_name = master_stage['name']
                stage_type = master_stage.get('type', 0)
                logger.info(f"🔄 Processando estágio {i+1}/{len(master_pipeline['stages'])}: '{stage_name}' (type: {stage_type})")
                
                # IGNORAR COMPLETAMENTE estágios especiais (IDs 142/143, type=1, etc.)
                if self._should_ignore_stage(master_stage):
                    logger.info(f"🚫 Ignorando estágio especial '{stage_name}' - será gerenciado automaticamente pelo Kommo")
                    continue
                
                # Preparar dados do estágio sem IDs da conta mestre
                stage_data = {
                    'name': master_stage['name'],
                    'sort': max(1, min(10000, master_stage.get('sort', i + 1))),  # Garantir range válido
                    'type': stage_type
                }
                
                # Usar a cor do stage da master validada (usar contador de estágios processados para fallback)
                master_color = master_stage.get('color')
                valid_color = get_valid_kommo_color(master_color, processed_stage_index)
                stage_data['color'] = valid_color
                logger.debug(f"Estágio '{stage_name}' - Cor master: '{master_color}' -> Cor válida: '{valid_color}' (índice processado: {processed_stage_index})")
                
                processed_stage_index += 1  # Incrementar apenas para estágios processados
                
                # Verificar se estágio já existe (verificação detalhada)
                stage_exists = stage_name in existing_stages
                logger.info(f"🔍 Estágio '{stage_name}' existe? {stage_exists}")
                
                if stage_exists:
                    # Estágio já existe - apenas armazenar mapeamento
                    existing_stage = existing_stages[stage_name]
                    slave_stage_id = existing_stage['id']
                    logger.info(f"✅ Estágio '{stage_name}' já existe (slave_id: {slave_stage_id})")
                    
                    # Armazenar mapeamento sem criar novo estágio
                    if 'stages' not in mappings:
                        mappings['stages'] = {}
                    # Usar ID do master stage
                    master_stage_id = master_stage['id']
                    mappings['stages'][master_stage_id] = slave_stage_id
                else:
                    # Criar novo estágio na conta escrava
                    logger.info(f"🆕 Criando estágio '{stage_name}' no pipeline {slave_pipeline_id}")
                    logger.debug(f"Dados do estágio: {stage_data}")
                    response = slave_api.create_pipeline_stage(slave_pipeline_id, stage_data)
                    slave_stage_id = response['_embedded']['statuses'][0]['id']
                    logger.info(f"✅ Estágio '{stage_name}' criado com ID: {slave_stage_id}")
                    
                    # Armazenar mapeamento para o estágio recém-criado
                    if 'stages' not in mappings:
                        mappings['stages'] = {}
                    # Usar ID do master stage
                    master_stage_id = master_stage['id']
                    mappings['stages'][master_stage_id] = slave_stage_id
                
            except Exception as e:
                logger.error(f"Erro ao sincronizar estágio '{master_stage['name']}': {e}")
                logger.error(f"Pipeline escrava ID: {slave_pipeline_id}, Estágio mestre: {master_stage}")
                # Continuar com próximo estágio mesmo se este falhar
        
        # FASE 2: Remover estágios que existem na slave mas NÃO existem na master
        stages_to_delete = []
        for slave_stage_name, slave_stage in existing_stages.items():
            if slave_stage_name not in master_stage_names:
                logger.debug(f"🔍 Estágio '{slave_stage_name}' não existe na master - verificando se deve ser ignorado...")
                
                # IGNORAR COMPLETAMENTE estágios especiais - nunca tentar excluir
                if self._should_ignore_stage(slave_stage):
                    logger.info(f"� Estágio especial '{slave_stage_name}' (ID: {slave_stage.get('id')}) será mantido - gerenciado automaticamente pelo Kommo")
                else:
                    logger.info(f"� Estágio '{slave_stage_name}' será excluído (não é especial)")
                    stages_to_delete.append(slave_stage)
            else:
                logger.debug(f"✅ Estágio '{slave_stage_name}' existe na master - mantendo")
        
        if stages_to_delete:
            logger.info(f"🗑️ Encontrados {len(stages_to_delete)} estágios para excluir do pipeline '{master_pipeline['name']}'")
            for stage_to_delete in stages_to_delete:
                try:
                    stage_name = stage_to_delete['name']
                    stage_id = stage_to_delete['id']
                    
                    logger.info(f"🗑️ Excluindo estágio '{stage_name}' (ID: {stage_id}) da slave")
                    
                    # Chamar API para deletar o estágio
                    delete_response = slave_api.delete_pipeline_stage(stage_id)
                    
                    if delete_response.get('success') or delete_response.get('status_code') in [200, 204]:
                        logger.info(f"✅ Estágio '{stage_name}' excluído com sucesso")
                    else:
                        logger.warning(f"⚠️ Resposta inesperada ao excluir estágio '{stage_name}': {delete_response}")
                        
                except Exception as e:
                    error_str = str(e).lower()
                    stage_name = stage_to_delete.get('name', 'Desconhecido')
                    stage_id = stage_to_delete.get('id', 'N/A')
                    
                    # Verificar se é erro 404 - estágio já foi removido
                    if any(phrase in error_str for phrase in ['not found', '404', 'does not exist']):
                        logger.info(f"ℹ️ Estágio '{stage_name}' já foi removido ou não existe")
                    else:
                        logger.error(f"❌ Erro ao excluir estágio '{stage_name}': {e}")
                        # Continuar com próximo estágio mesmo se este falhar
        else:
            logger.info(f"✅ Nenhum estágio excedente encontrado no pipeline '{master_pipeline['name']}'")
    
    def _should_ignore_stage(self, stage: Dict) -> bool:
        """
        Verifica se um estágio deve ser completamente ignorado durante a sincronização.
        Estágios especiais do sistema (Won=142, Lost=143) são gerenciados automaticamente pelo Kommo.
        """
        stage_id = stage.get('id')
        stage_type = stage.get('type', 0)
        stage_name = stage.get('name', '').lower()
        
        # REGRA 1: Ignorar por ID direto (MAIS IMPORTANTE)
        if stage_id in [142, 143]:
            logger.debug(f"🚫 Ignorando estágio por ID especial: {stage_id} - '{stage_name}'")
            return True
            
        # REGRA 2: Ignorar estágios type=1 (incoming leads) - criados automaticamente
        if stage_type == 1:
            logger.debug(f"🚫 Ignorando estágio type=1: '{stage_name}' - criado automaticamente pelo Kommo")
            return True
            
        # REGRA 3: Ignorar por nome (padrões conhecidos de estágios especiais)
        special_patterns = [
            'incoming leads', 'incoming', 'etapa de leads de entrada', 'leads de entrada', 'entrada',
            'venda ganha', 'fechado - ganho', 'closed - won', 'won', 'successful', 'sucesso',
            'venda perdida', 'fechado - perdido', 'closed - lost', 'lost', 'unsuccessful', 'fracasso'
        ]
        
        for pattern in special_patterns:
            if pattern in stage_name:
                logger.debug(f"🚫 Ignorando estágio por padrão de nome: '{pattern}' em '{stage_name}'")
                return True
                
        return False
    def _is_system_stage(self, stage: Dict) -> bool:
        """
        Verifica se um estágio é um estágio especial do sistema (Won=142, Lost=143, Incoming=1)
        NOTA: Esta função é mantida para compatibilidade. Use _should_ignore_stage() para novo código.
        """
        return self._should_ignore_stage(stage)

    def _get_default_stage_id(self, stage_name: str, stage_type: int) -> int:
        """Retorna o ID padrão do Kommo para estágios especiais (Incoming=1, Won=142, Lost=143)"""
        stage_name_lower = stage_name.lower()
        
        # Estágio inicial (Incoming leads) - ID 1
        incoming_patterns = ['incoming leads', 'incoming', 'etapa de leads de entrada', 'leads de entrada', 'entrada']
        for pattern in incoming_patterns:
            if pattern in stage_name_lower:
                return 1
        
        # Estágios de vitória (Won) - ID 142
        won_patterns = ['won', 'ganho', 'ganha', 'venda ganha', 'fechado - ganho', 'successful', 'sucesso']
        for pattern in won_patterns:
            if pattern in stage_name_lower:
                return 142
                
        # Estágios de perda (Lost) - ID 143  
        lost_patterns = ['lost', 'perdido', 'perdida', 'venda perdida', 'fechado - perdido', 'unsuccessful', 'fracasso']
        for pattern in lost_patterns:
            if pattern in stage_name_lower:
                return 143
                
        # Verificar por tipo também (1 = ganho, 2 = perda)
        if stage_type == 1:
            return 142
        elif stage_type == 2:
            return 143
            
        return None
    
    def _save_mappings_to_database(self, mappings: Dict, sync_group_id: int, slave_account_id: int):
        """Salva os mapeamentos de pipelines e estágios no banco de dados"""
        try:
            logger.info(f"💾 Salvando mapeamentos no banco de dados para o grupo {sync_group_id}")
            
            # Salvar mapeamentos de pipelines
            if 'pipelines' in mappings:
                for master_pipeline_id, slave_pipeline_id in mappings['pipelines'].items():
                    # Verificar se o mapeamento já existe
                    existing_mapping = PipelineMapping.query.filter_by(
                        sync_group_id=sync_group_id,
                        master_pipeline_id=master_pipeline_id,
                        slave_account_id=slave_account_id
                    ).first()
                    
                    if not existing_mapping:
                        # Criar novo mapeamento
                        pipeline_mapping = PipelineMapping(
                            sync_group_id=sync_group_id,
                            master_pipeline_id=master_pipeline_id,
                            slave_account_id=slave_account_id,
                            slave_pipeline_id=slave_pipeline_id
                        )
                        db.session.add(pipeline_mapping)
                        logger.debug(f"📊 Adicionado mapeamento de pipeline: {master_pipeline_id} -> {slave_pipeline_id}")
                    else:
                        # Atualizar mapeamento existente se necessário
                        if existing_mapping.slave_pipeline_id != slave_pipeline_id:
                            existing_mapping.slave_pipeline_id = slave_pipeline_id
                            logger.debug(f"📊 Atualizado mapeamento de pipeline: {master_pipeline_id} -> {slave_pipeline_id}")
            
            # Salvar mapeamentos de estágios
            if 'stages' in mappings:
                for master_stage_id, slave_stage_id in mappings['stages'].items():
                    # Verificar se o mapeamento já existe
                    existing_mapping = StageMapping.query.filter_by(
                        sync_group_id=sync_group_id,
                        master_stage_id=master_stage_id,
                        slave_account_id=slave_account_id
                    ).first()
                    
                    if not existing_mapping:
                        # Criar novo mapeamento
                        stage_mapping = StageMapping(
                            sync_group_id=sync_group_id,
                            master_stage_id=master_stage_id,
                            slave_account_id=slave_account_id,
                            slave_stage_id=slave_stage_id
                        )
                        db.session.add(stage_mapping)
                        logger.debug(f"📊 Adicionado mapeamento de estágio: {master_stage_id} -> {slave_stage_id}")
                    else:
                        # Atualizar mapeamento existente se necessário
                        if existing_mapping.slave_stage_id != slave_stage_id:
                            existing_mapping.slave_stage_id = slave_stage_id
                            logger.debug(f"📊 Atualizado mapeamento de estágio: {master_stage_id} -> {slave_stage_id}")
            
            # Commitar todas as mudanças
            db.session.commit()
            
            pipeline_count = len(mappings.get('pipelines', {}))
            stage_count = len(mappings.get('stages', {}))
            logger.info(f"✅ Mapeamentos salvos no banco: {pipeline_count} pipelines, {stage_count} estágios")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mapeamentos no banco: {e}")
            db.session.rollback()
            raise
    
    def _load_mappings_from_database(self, sync_group_id, slave_account_id):
        """Carrega mapeamentos existentes do banco de dados"""
        try:
            logger.info(f"📖 Carregando mapeamentos do banco para grupo {sync_group_id}, conta {slave_account_id}")
            
            mappings = {'pipelines': {}, 'stages': {}, 'custom_field_groups': {}}
            
            # Carregar mapeamentos de pipelines
            pipeline_mappings = PipelineMapping.query.filter_by(
                sync_group_id=sync_group_id,
                slave_account_id=slave_account_id
            ).all()
            
            for mapping in pipeline_mappings:
                mappings['pipelines'][mapping.master_pipeline_id] = mapping.slave_pipeline_id
                logger.debug(f"📊 Pipeline mapping: {mapping.master_pipeline_id} -> {mapping.slave_pipeline_id}")
            
            # Carregar mapeamentos de estágios
            stage_mappings = StageMapping.query.filter_by(
                sync_group_id=sync_group_id,
                slave_account_id=slave_account_id
            ).all()
            
            for mapping in stage_mappings:
                mappings['stages'][mapping.master_stage_id] = mapping.slave_stage_id
                logger.debug(f"🎭 Stage mapping: {mapping.master_stage_id} -> {mapping.slave_stage_id}")
            
            pipeline_count = len(mappings['pipelines'])
            stage_count = len(mappings['stages'])
            logger.info(f"✅ Mapeamentos carregados do banco: {pipeline_count} pipelines, {stage_count} estágios")
            
            return mappings
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar mapeamentos do banco: {e}")
            return {'pipelines': {}, 'stages': {}, 'custom_field_groups': {}}
    
    def _sync_automatic_stage_names(self, slave_api: KommoAPIService, master_pipeline: Dict, slave_pipeline_id: int):
        """
        [FUNÇÃO DESABILITADA] Sincroniza nomes dos estágios automáticos criados pelo Kommo (type=1, ID=142, ID=143)
        
        MOTIVO DA DESABILITAÇÃO:
        Os estágios especiais do Kommo (Won=142, Lost=143) são gerenciados automaticamente pelo sistema
        e seus nomes são definidos de acordo com o idioma da conta (PT: "Venda ganha/perdida", EN: "Closed - won/lost").
        Tentar modificá-los manualmente causa erros HTTP 400 "NotSupportedChoice".
        
        Esta função está mantida apenas para documentação e possível uso futuro se necessário.
        """
        logger.info(f"🚫 _sync_automatic_stage_names está desabilitada - estágios especiais são gerenciados pelo Kommo")
        return  # Função desabilitada
        
        # Código original mantido para referência (não executado)
        logger.info(f"🔄 Sincronizando nomes dos estágios automáticos do pipeline '{master_pipeline['name']}'")
        
        try:
            # Obter estágios da master e slave após criação
            master_stages = master_pipeline['stages']
            slave_stages = slave_api.get_pipeline_stages(slave_pipeline_id)
            
            # Mapear estágios especiais da master
            master_incoming_name = None
            master_won_name = None
            master_lost_name = None
            
            for stage in master_stages:
                if stage.get('type') == 1:  # Incoming leads
                    master_incoming_name = stage['name']
                elif stage.get('name', '').lower() in ['venda ganha', 'fechado - ganho', 'won', 'successful']:
                    master_won_name = stage['name']
                elif stage.get('name', '').lower() in ['venda perdida', 'fechado - perdido', 'lost', 'unsuccessful']:
                    master_lost_name = stage['name']
            
            logger.info(f"  📋 Master - Incoming: '{master_incoming_name}', Won: '{master_won_name}', Lost: '{master_lost_name}'")
            
            # Atualizar estágios especiais na slave se os nomes forem diferentes
            for stage in slave_stages:
                stage_id = stage['id']
                stage_name = stage['name']
                stage_type = stage.get('type', 0)
                
                new_name = None
                
                # Verificar se precisa atualizar o nome (apenas se forem diferentes)
                if stage_type == 1 and master_incoming_name and stage_name != master_incoming_name:
                    new_name = master_incoming_name
                    logger.info(f"  🔄 Atualizando Type 1: '{stage_name}' → '{new_name}'")
                    
                elif stage_id == 142 and master_won_name and stage_name != master_won_name:
                    new_name = master_won_name
                    logger.info(f"  🔄 Atualizando ID 142: '{stage_name}' → '{new_name}'")
                    
                elif stage_id == 143 and master_lost_name and stage_name != master_lost_name:
                    new_name = master_lost_name
                    logger.info(f"  🔄 Atualizando ID 143: '{stage_name}' → '{new_name}'")
                
                # Atualizar o nome se necessário
                if new_name:
                    try:
                        update_data = {'name': new_name}
                        slave_api.update_pipeline_stage(slave_pipeline_id, stage_id, update_data)
                        logger.info(f"    ✅ Estágio atualizado: '{stage_name}' → '{new_name}'")
                        
                    except Exception as e:
                        logger.warning(f"    ❌ Erro ao atualizar estágio '{stage_name}': {e}")
                        
        except Exception as e:
            logger.error(f"Erro ao sincronizar nomes automáticos do pipeline '{master_pipeline['name']}': {e}")
    
    def sync_custom_field_groups_to_slave(self, slave_api: KommoAPIService, master_config: Dict, 
                                         mappings: Dict, progress_callback: Optional[Callable] = None) -> Dict:
        """Sincroniza grupos de campos personalizados da conta mestre para uma conta escrava - COM LOTES"""
        logger.info("📁 Iniciando sincronização de grupos de campos em lotes...")
        results = {'created': 0, 'updated': 0, 'skipped': 0, 'deleted': 0, 'errors': []}
        
        # Reset da flag de parada
        self._stop_sync = False
        
        for entity_type in self.entity_types:
            if self._stop_sync:
                break
                
            try:
                logger.info(f"🗂️ Sincronizando grupos de campos para {entity_type} em lotes...")
                
                master_groups = master_config['custom_field_groups'].get(entity_type, [])
                if not master_groups:
                    logger.info(f"Nenhum grupo encontrado para {entity_type}")
                    continue
                
                existing_groups = {g['name']: g for g in slave_api.get_custom_field_groups(entity_type)}
                master_group_names = {g['name'] for g in master_groups}
                
                # FASE 1: Criar/Atualizar grupos da master EM LOTES
                def process_group(master_group, results):
                    group_name = master_group['name']
                    logger.info(f"🔄 Processando grupo: {group_name}")
                    
                    try:
                        group_data = {
                            'name': master_group['name'],
                            'sort': master_group.get('sort', 0)
                        }
                        
                        if group_name in existing_groups:
                            # Grupo já existe - verificar se precisa atualizar
                            existing_group = existing_groups[group_name]
                            slave_group_id = existing_group['id']
                            
                            update_data = {}
                            needs_update = False
                            
                            if existing_group.get('sort', 0) != group_data['sort']:
                                update_data['sort'] = group_data['sort']
                                needs_update = True
                            
                            if needs_update:
                                logger.info(f"🔄 Atualizando grupo '{group_name}' (ID: {slave_group_id})")
                                slave_api.update_custom_field_group(entity_type, slave_group_id, update_data)
                                results['updated'] += 1
                            else:
                                results['skipped'] += 1
                        else:
                            # Criar novo grupo
                            logger.info(f"🆕 Criando grupo '{group_name}' para {entity_type}")
                            response = slave_api.create_custom_field_group(entity_type, group_data)
                            slave_group_id = response['_embedded']['custom_field_groups'][0]['id']
                            results['created'] += 1
                        
                        # Armazenar mapeamento do grupo
                        if 'custom_field_groups' not in mappings:
                            mappings['custom_field_groups'] = {}
                        if entity_type not in mappings['custom_field_groups']:
                            mappings['custom_field_groups'][entity_type] = {}
                        mappings['custom_field_groups'][entity_type][master_group['id']] = slave_group_id
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar grupo '{group_name}': {e}")
                        raise
                
                # Processar grupos em lotes
                self._process_in_batches(
                    items=master_groups,
                    process_func=process_group,
                    operation_name=f"grupos de {entity_type}",
                    results=results,
                    progress_callback=progress_callback
                )
                
                if self._stop_sync:
                    break
                
                # FASE 2: Deletar grupos que existem na escrava mas NÃO existem na master - EM LOTES
                groups_to_delete = []
                for slave_group_name, slave_group in existing_groups.items():
                    if slave_group_name not in master_group_names:
                        groups_to_delete.append(slave_group)
                
                def delete_group(group_to_delete, results):
                    group_name = group_to_delete['name']
                    group_id = group_to_delete['id']
                    logger.info(f"🗑️ Deletando grupo '{group_name}' de {entity_type} (ID: {group_id})")
                    
                    try:
                        delete_response = slave_api.delete_custom_field_group(entity_type, group_id)
                        if delete_response.get('success') or delete_response.get('status_code') in [200, 204]:
                            results['deleted'] += 1
                        else:
                            results['deleted'] += 1  # Considerar como sucesso
                    except Exception as e:
                        error_str = str(e).lower()
                        if any(phrase in error_str for phrase in ['not found', '404']):
                            results['deleted'] += 1
                        else:
                            logger.error(f"Erro ao deletar grupo '{group_name}': {e}")
                            raise
                
                if groups_to_delete:
                    logger.info(f"🗑️ Iniciando exclusão de {len(groups_to_delete)} grupos de {entity_type}...")
                    self._process_in_batches(
                        items=groups_to_delete,
                        process_func=delete_group,
                        operation_name=f"exclusão de grupos de {entity_type}",
                        results=results,
                        progress_callback=progress_callback
                    )
                
            except Exception as e:
                logger.error(f"Erro na sincronização de grupos para {entity_type}: {e}")
                results['errors'].append(str(e))
        
        logger.info(f"📁 Sincronização de grupos concluída: {results}")
        return results
    
    def sync_custom_fields_to_slave(self, slave_api: KommoAPIService, master_config: Dict, 
                                   mappings: Dict, progress_callback: Optional[Callable] = None,
                                   sync_group_id: Optional[int] = None, 
                                   slave_account_id: Optional[int] = None) -> Dict:
        """Sincroniza campos personalizados da conta mestre para uma conta escrava (criar/atualizar + deletar excesso)
        
        NOTA: Este método também sincroniza os grupos de campos AUTOMATICAMENTE antes de sincronizar os campos,
        garantindo que as dependências estejam corretas.
        """
        # Carregar mapeamentos existentes do banco se disponível
        if sync_group_id and slave_account_id:
            logger.info("🔄 Carregando mapeamentos do banco de dados para processamento de required_statuses...")
            database_mappings = self._load_mappings_from_database(sync_group_id, slave_account_id)
            # Mesclar com os mapeamentos já existentes (priorizando os do banco)
            mappings.update(database_mappings)
        
        results = {'created': 0, 'updated': 0, 'skipped': 0, 'deleted': 0, 'errors': []}
        
        # PRIMEIRO: Sincronizar grupos de campos (dependência obrigatória)
        logger.info("🔄 Sincronizando grupos de campos automaticamente antes dos campos...")
        groups_results = self.sync_custom_field_groups_to_slave(slave_api, master_config, mappings, progress_callback)
        logger.info(f"Grupos sincronizados: {groups_results['created']} criados, {groups_results['updated']} atualizados, {groups_results['skipped']} ignorados, {groups_results['deleted']} deletados")
        
        # Adicionar resultados dos grupos ao resultado final
        results['groups_created'] = groups_results['created']
        results['groups_updated'] = groups_results['updated']
        results['groups_skipped'] = groups_results['skipped']
        results['groups_deleted'] = groups_results['deleted']
        results['groups_errors'] = groups_results['errors']
        
        # Campos padrão do sistema que não devem ser sincronizados
        system_codes = ['PHONE', 'EMAIL', 'POSITION', 'WEB', 'IM', 'ADDRESS']
        
        for entity_type in self.entity_types:
            try:
                logger.info(f"🏷️ Sincronizando campos personalizados para {entity_type}...")
                
                # Obter campos existentes na conta escrava
                all_slave_fields = slave_api.get_custom_fields(entity_type)
                existing_fields_by_name = {f['name']: f for f in all_slave_fields}
                existing_fields_by_code = {f.get('code'): f for f in all_slave_fields if f.get('code')}
                
                # Criar conjunto de nomes de campos da master para comparação
                master_field_names = {f['name'] for f in master_config['custom_fields'][entity_type]}
                master_field_codes = {f.get('code') for f in master_config['custom_fields'][entity_type] if f.get('code')}
                
                # FASE 1: Criar/Atualizar campos da master
                for master_field in master_config['custom_fields'][entity_type]:
                    try:
                        field_name = master_field['name']
                        field_code = master_field.get('code', '')
                        field_type = master_field['type']
                        
                        # Verificar se o tipo é suportado pela API do Kommo (conforme documentação oficial)
                        supported_types = [
                            'text', 'numeric', 'checkbox', 'select', 'multiselect', 'date', 'date_time',
                            'url', 'textarea', 'radiobutton', 'streetaddress', 'smart_address',
                            'legal_entity', 'price', 'monetary', 'category', 'file', 'multitext',
                            'tracking_data', 'linked_entity', 'chained_list'
                        ]
                        
                        # Tipos problemáticos que devem ser convertidos
                        type_conversions = {
                            'birthday_date': 'date',  # birthday_date não existe, usar date
                            'birthday': 'date',       # birthday não é suportado, usar date
                            'datetime': 'date_time',  # datetime deve ser date_time
                        }
                        
                        # Aplicar conversões de tipo se necessário
                        if field_type in type_conversions:
                            original_type = field_type
                            field_type = type_conversions[field_type]
                            logger.info(f"Convertendo tipo '{original_type}' para '{field_type}' para campo '{field_name}'")
                        
                        if field_type not in supported_types:
                            logger.warning(f"Tipo de campo '{field_type}' não suportado pela API do Kommo para campo '{field_name}'. Convertendo para 'text'.")
                            field_type = 'text'  # Fallback para tipo texto
                        
                        # Pular campos do sistema
                        if field_code and field_code.upper() in system_codes:
                            logger.info(f"Pulando campo do sistema '{field_name}' (código: {field_code})")
                            results['skipped'] += 1
                            continue
                        
                        # Preparar dados básicos do campo
                        field_data = {
                            'name': master_field['name'],
                            'type': field_type,  # Usar o tipo validado
                            'sort': master_field.get('sort', 0),
                            'is_required': master_field.get('is_required', False)
                        }
                        
                        # Só adicionar código se não for um campo do sistema
                        if field_code and field_code.upper() not in system_codes:
                            field_data['code'] = field_code
                        
                        # Tratamento específico para campos monetários
                        if field_type == 'monetary':
                            # Campos monetários requerem o parâmetro 'currency'
                            # Se existir no campo master, usar o mesmo, senão usar USD como padrão
                            currency = master_field.get('currency', 'USD')
                            field_data['currency'] = currency
                            logger.info(f"💰 Campo monetário '{field_name}' configurado com moeda: {currency}")
                        
                        # Mapear required_statuses (estágios específicos onde é obrigatório)
                        if master_field.get('required_statuses'):
                            mapped_required_statuses = []
                            logger.info(f"🎯 Mapeando required_statuses para campo '{field_name}':")
                            logger.info(f"   Master required_statuses: {master_field['required_statuses']}")
                            logger.info(f"   Mapeamentos disponíveis - Pipelines: {len(mappings.get('pipelines', {}))}, Stages: {len(mappings.get('stages', {}))}")
                            
                            for req_status in master_field['required_statuses']:
                                master_status_id = req_status.get('status_id')
                                master_pipeline_id = req_status.get('pipeline_id')
                                
                                logger.info(f"   🔍 Processando: pipeline={master_pipeline_id}, status={master_status_id}")
                                
                                # Verificar se é um estágio especial que deve ser ignorado
                                stage_info = {'id': master_status_id}  # Criar objeto mínimo para teste
                                if self._should_ignore_stage(stage_info):
                                    logger.info(f"   🚫 Ignorando required_status com estágio especial {master_status_id} - gerenciado pelo Kommo")
                                    continue
                                
                                # Mapear pipeline_id da master para escrava
                                if master_pipeline_id and master_pipeline_id in mappings.get('pipelines', {}):
                                    slave_pipeline_id = mappings['pipelines'][master_pipeline_id]
                                    logger.debug(f"   ✅ Pipeline mapeado: {master_pipeline_id} -> {slave_pipeline_id}")
                                    
                                    # Mapear status_id da master para escrava
                                    if master_status_id and master_status_id in mappings.get('stages', {}):
                                        slave_status_id = mappings['stages'][master_status_id]
                                        logger.debug(f"   ✅ Status mapeado: {master_status_id} -> {slave_status_id}")
                                        
                                        mapped_status = {
                                            'status_id': slave_status_id,
                                            'pipeline_id': slave_pipeline_id
                                        }
                                        mapped_required_statuses.append(mapped_status)
                                        logger.info(f"   ✅ Required_status mapeado com sucesso: pipeline {master_pipeline_id}->{slave_pipeline_id}, status {master_status_id}->{slave_status_id}")
                                    else:
                                        logger.warning(f"   ❌ Status {master_status_id} não encontrado nos mapeamentos - pulando required_status")
                                        logger.debug(f"   📋 Status disponíveis: {list(mappings.get('stages', {}).keys())[:10]}...")
                                else:
                                    logger.warning(f"   ❌ Pipeline {master_pipeline_id} não encontrado nos mapeamentos - pulando required_status")
                                    logger.debug(f"   📋 Pipelines disponíveis: {list(mappings.get('pipelines', {}).keys())[:10]}...")
                            
                            if mapped_required_statuses:
                                logger.info(f"🎯 Campo '{field_name}' tem {len(mapped_required_statuses)} required_statuses mapeados")
                                
                                # Log detalhado dos dados que serão enviados
                                logger.info(f"📤 Dados mapeados para envio:")
                                for i, rs in enumerate(mapped_required_statuses, 1):
                                    logger.info(f"   {i}. pipeline_id: {rs['pipeline_id']}, status_id: {rs['status_id']}")
                                
                                # VALIDAÇÃO REAL: verificar se os IDs existem na slave
                                logger.info(f"🔍 Validando IDs na conta slave REAL...")
                                valid_required_statuses = []
                                
                                try:
                                    # Obter pipelines e stages reais da slave
                                    real_slave_pipelines = slave_api.get_pipelines()
                                    logger.debug(f"Pipelines disponíveis na slave: {[p['id'] for p in real_slave_pipelines[:5]]}...")
                                    
                                    for mapped_status in mapped_required_statuses:
                                        slave_status_id = mapped_status['status_id']
                                        slave_pipeline_id = mapped_status['pipeline_id']
                                        
                                        logger.info(f"   🔍 Validando pipeline_id: {slave_pipeline_id}, status_id: {slave_status_id}")
                                        
                                        # Verificar se pipeline existe
                                        pipeline_exists = any(p['id'] == slave_pipeline_id for p in real_slave_pipelines)
                                        
                                        if pipeline_exists:
                                            logger.debug(f"      ✅ Pipeline {slave_pipeline_id} existe na slave")
                                            
                                            # Verificar se status existe no pipeline
                                            try:
                                                real_slave_stages = slave_api.get_pipeline_stages(slave_pipeline_id)
                                                status_exists = any(s['id'] == slave_status_id for s in real_slave_stages)
                                                
                                                if status_exists:
                                                    logger.info(f"      ✅ VÁLIDO: pipeline {slave_pipeline_id}, status {slave_status_id}")
                                                    valid_required_statuses.append(mapped_status)
                                                else:
                                                    logger.error(f"      ❌ Status {slave_status_id} NÃO existe no pipeline {slave_pipeline_id}")
                                                    logger.debug(f"         Status disponíveis: {[s['id'] for s in real_slave_stages[:5]]}...")
                                            except Exception as stage_error:
                                                logger.error(f"      ❌ Erro ao obter stages do pipeline {slave_pipeline_id}: {stage_error}")
                                        else:
                                            logger.error(f"      ❌ Pipeline {slave_pipeline_id} NÃO existe na slave")
                                            logger.debug(f"         Pipelines disponíveis: {[p['id'] for p in real_slave_pipelines[:5]]}...")
                                
                                except Exception as validation_error:
                                    logger.error(f"❌ Erro na validação real: {validation_error}")
                                    # Em caso de erro na validação, não usar required_statuses
                                    valid_required_statuses = []
                                
                                if valid_required_statuses:
                                    field_data['required_statuses'] = valid_required_statuses
                                    logger.info(f"✅ Campo '{field_name}' será criado com {len(valid_required_statuses)} required_statuses VALIDADOS")
                                else:
                                    logger.warning(f"❌ NENHUM required_status válido encontrado - campo será criado SEM restrições específicas")
                                    logger.info(f"ℹ️ Campo '{field_name}' estará disponível em todos os estágios")
                            else:
                                logger.warning(f"❌ Nenhum required_status válido para campo '{field_name}' - campo não será obrigatório em estágios específicos")
                                # NÃO incluir required_statuses vazios ou inválidos
                                if 'required_statuses' in field_data:
                                    del field_data['required_statuses']
                                    logger.info(f"🗑️ Removido required_statuses inválidos do campo '{field_name}'")
                        
                        # Relacionar campo ao grupo correto na conta escrava
                        logger.debug(f"🔍 Verificando grupo para campo '{field_name}': master_group_id={master_field.get('group_id')}")
                        if master_field.get('group_id'):
                            # Verificar se temos o mapeamento do grupo
                            logger.debug(f"Mapeamentos disponíveis: {mappings.get('custom_field_groups', {}).get(entity_type, {})}")
                            if ('custom_field_groups' in mappings and 
                                entity_type in mappings['custom_field_groups'] and 
                                master_field['group_id'] in mappings['custom_field_groups'][entity_type]):
                                slave_group_id = mappings['custom_field_groups'][entity_type][master_field['group_id']]
                                field_data['group_id'] = slave_group_id
                                logger.info(f"✅ Campo '{field_name}' será relacionado ao grupo ID {slave_group_id} (master: {master_field['group_id']})")
                            else:
                                logger.warning(f"❌ Grupo {master_field['group_id']} não encontrado nos mapeamentos para campo '{field_name}' - campo será criado sem grupo")
                                logger.debug(f"Mapeamentos existentes: {mappings.get('custom_field_groups', {})}")
                                # NÃO incluir group_id se o grupo não existe
                        else:
                            logger.debug(f"Campo '{field_name}' não tem group_id na master")
                        
                        # Validações específicas por tipo de campo
                        if field_type in ['select', 'multiselect', 'radiobutton']:
                            # Só adicionar enums para campos que realmente suportam
                            if master_field.get('enums'):
                                clean_enums = []
                                for enum_item in master_field['enums']:
                                    if isinstance(enum_item, dict):
                                        # Remover ID e manter apenas valor e sort
                                        enum_data = {
                                            'value': enum_item.get('value', ''),
                                            'sort': enum_item.get('sort', 0)
                                        }
                                        clean_enums.append(enum_data)
                                    else:
                                        # Se for string simples
                                        clean_enums.append({'value': str(enum_item), 'sort': 0})
                                
                                if clean_enums:
                                    field_data['enums'] = clean_enums
                        else:
                            # Para outros tipos, verificar se há enums desnecessários
                            if master_field.get('enums'):
                                logger.warning(f"Campo '{field_name}' do tipo '{field_type}' tem enums, mas este tipo não suporta. Ignorando enums.")
                        
                        # Log dos dados que serão enviados
                        logger.debug(f"Dados preparados para campo '{field_name}': {field_data}")
                        
                        # ESTRATÉGIA ROBUSTA: Verificar se campo já existe - múltiplas tentativas
                        existing_field = None
                        slave_field_id = None
                        match_method = ""
                        
                        # 1. Tentar encontrar por código (mais confiável)
                        if field_code:
                            for slave_field in all_slave_fields:
                                if slave_field.get('code') == field_code:
                                    existing_field = slave_field
                                    slave_field_id = existing_field['id']
                                    match_method = f"código '{field_code}'"
                                    logger.info(f"✅ Campo encontrado por código '{field_code}': {existing_field['name']} (ID: {slave_field_id})")
                                    break
                        
                        # 2. Se não encontrou por código, tentar por nome EXATO
                        if not existing_field:
                            for slave_field in all_slave_fields:
                                if slave_field.get('name') == field_name:
                                    existing_field = slave_field
                                    slave_field_id = existing_field['id']
                                    match_method = f"nome exato '{field_name}'"
                                    logger.info(f"✅ Campo encontrado por nome exato '{field_name}' (ID: {slave_field_id})")
                                    break
                        
                        # 3. Busca por nome similar (case-insensitive e similaridade)
                        if not existing_field:
                            for slave_field in all_slave_fields:
                                slave_name = slave_field.get('name', '').lower().strip()
                                master_name = field_name.lower().strip()
                                
                                # Verificar similaridade exata
                                if slave_name == master_name:
                                    existing_field = slave_field
                                    slave_field_id = existing_field['id']
                                    match_method = f"nome similar '{slave_field['name']}'"
                                    logger.info(f"✅ Campo encontrado por nome similar '{slave_field['name']}' -> '{field_name}' (ID: {slave_field_id})")
                                    break
                                
                                # Verificar se um nome contém o outro (para casos como popo -> popopa)
                                elif (len(slave_name) >= 3 and len(master_name) >= 3 and 
                                      (slave_name in master_name or master_name in slave_name) and
                                      abs(len(slave_name) - len(master_name)) <= 3):  # Diferença máxima de 3 caracteres
                                    existing_field = slave_field
                                    slave_field_id = existing_field['id']
                                    match_method = f"nome parcialmente similar '{slave_field['name']}'"
                                    logger.info(f"✅ Campo encontrado por similaridade '{slave_field['name']}' -> '{field_name}' (ID: {slave_field_id})")
                                    break
                        
                        # 4. Busca por tipo + nome normalizado (remove espaços/caracteres especiais)
                        if not existing_field:
                            import re
                            master_normalized = re.sub(r'[^a-zA-Z0-9]', '', field_name.lower())
                            for slave_field in all_slave_fields:
                                slave_normalized = re.sub(r'[^a-zA-Z0-9]', '', slave_field.get('name', '').lower())
                                slave_type = slave_field.get('type', '')
                                
                                # Verificar se o tipo convertido é compatível
                                compatible_type = (slave_type == field_type or 
                                                 (slave_type == 'date' and master_field['type'] == 'birthday') or
                                                 (slave_type == 'date_time' and master_field['type'] == 'datetime'))
                                
                                if compatible_type and slave_normalized == master_normalized and len(master_normalized) > 2:
                                    existing_field = slave_field
                                    slave_field_id = existing_field['id']
                                    match_method = f"tipo+nome normalizado '{slave_field['name']}'"
                                    logger.info(f"✅ Campo encontrado por tipo+nome normalizado '{slave_field['name']}' -> '{field_name}' (ID: {slave_field_id})")
                                    break
                        
                        # 5. ÚLTIMA TENTATIVA: Busca por características + similaridade de strings
                        if not existing_field:
                            # Função para calcular similaridade simples
                            def string_similarity(s1, s2):
                                s1, s2 = s1.lower(), s2.lower()
                                if len(s1) == 0 or len(s2) == 0:
                                    return 0
                                # Calcular quantos caracteres em comum têm
                                common = sum(1 for a, b in zip(s1, s2) if a == b)
                                max_len = max(len(s1), len(s2))
                                return common / max_len
                            
                            for slave_field in all_slave_fields:
                                slave_name = slave_field.get('name', '')
                                slave_type = slave_field.get('type', '')
                                
                                # Verificar se o tipo convertido é compatível
                                compatible_type = (slave_type == field_type or 
                                                 (slave_type == 'date' and master_field['type'] == 'birthday') or
                                                 (slave_type == 'date_time' and master_field['type'] == 'datetime'))
                                
                                # Se tipo compatível e similaridade alta (>= 70%)
                                similarity = string_similarity(slave_name, field_name)
                                if compatible_type and similarity >= 0.7 and len(slave_name) >= 3:
                                    existing_field = slave_field
                                    slave_field_id = existing_field['id']
                                    match_method = f"alta similaridade ({similarity:.0%}) '{slave_field['name']}'"
                                    logger.info(f"✅ Campo encontrado por alta similaridade '{slave_field['name']}' -> '{field_name}' (ID: {slave_field_id}, {similarity:.0%})")
                                    break
                        
                        # Log final do resultado da busca
                        if existing_field:
                            logger.info(f"🎯 CAMPO EXISTENTE identificado: {match_method}")
                        else:
                            logger.info(f"🆕 NOVO CAMPO será criado: '{field_name}' (não encontrado na conta escrava)")
                            logger.debug(f"Campos existentes na escrava: {[f.get('name') for f in all_slave_fields]}")
                        
                        if existing_field:
                            # Campo já existe - verificar todas as propriedades que podem ser diferentes
                            logger.info(f"🔄 Campo EXISTENTE encontrado por {match_method} - processando atualizações...")
                            needs_update = False
                            update_data = {}
                            
                            # Verificar se o nome mudou
                            if existing_field['name'] != field_name:
                                update_data['name'] = field_name
                                needs_update = True
                                logger.info(f"Nome do campo será atualizado: '{existing_field['name']}' -> '{field_name}'")
                            
                            # Verificar se o sort mudou
                            existing_sort = existing_field.get('sort', 0)
                            new_sort = master_field.get('sort', 0)
                            if existing_sort != new_sort:
                                update_data['sort'] = new_sort
                                needs_update = True
                                logger.info(f"Sort do campo '{field_name}' será atualizado: {existing_sort} -> {new_sort}")
                            
                            # Verificar se is_required mudou
                            existing_required = existing_field.get('is_required', False)
                            new_required = master_field.get('is_required', False)
                            if existing_required != new_required:
                                update_data['is_required'] = new_required
                                needs_update = True
                                logger.info(f"is_required do campo '{field_name}' será atualizado: {existing_required} -> {new_required}")
                            
                            # Verificar se required_statuses mudaram
                            existing_required_statuses = existing_field.get('required_statuses', [])
                            new_required_statuses = field_data.get('required_statuses', [])
                            
                            # Normalizar para comparação (ordenar por status_id e pipeline_id)
                            existing_normalized = sorted([
                                (rs.get('status_id'), rs.get('pipeline_id')) 
                                for rs in existing_required_statuses
                            ])
                            new_normalized = sorted([
                                (rs.get('status_id'), rs.get('pipeline_id')) 
                                for rs in new_required_statuses
                            ])
                            
                            if existing_normalized != new_normalized:
                                update_data['required_statuses'] = new_required_statuses
                                needs_update = True
                                logger.info(f"🎯 required_statuses do campo '{field_name}' serão atualizados")
                                logger.debug(f"Existentes: {existing_required_statuses}")
                                logger.debug(f"Novos: {new_required_statuses}")
                            
                            # Verificar se o código mudou (se permitido)
                            existing_code = existing_field.get('code', '')
                            new_code = field_code
                            if new_code and existing_code != new_code and new_code.upper() not in system_codes:
                                update_data['code'] = new_code
                                needs_update = True
                                logger.info(f"Código do campo '{field_name}' será atualizado: '{existing_code}' -> '{new_code}'")
                            
                            # Verificar se o group_id mudou
                            existing_group_id = existing_field.get('group_id')
                            new_group_id = field_data.get('group_id')
                            logger.debug(f"🔍 Verificando grupo do campo '{field_name}': existente={existing_group_id}, novo={new_group_id}")
                            if existing_group_id != new_group_id:
                                if new_group_id:
                                    # Campo será movido para um novo grupo
                                    update_data['group_id'] = new_group_id
                                    needs_update = True
                                    logger.info(f"📁 Grupo do campo '{field_name}' será atualizado: {existing_group_id} -> {new_group_id}")
                                elif existing_group_id:
                                    # Campo deveria ser removido do grupo, mas API não suporta group_id=null
                                    # Vamos pular esta atualização e manter o campo no grupo atual
                                    logger.warning(f"Campo '{field_name}' deveria ser removido do grupo {existing_group_id}, mas API do Kommo não suporta group_id=null. Mantendo no grupo atual.")
                                    # NÃO adicionar group_id aos update_data para evitar o erro
                            else:
                                logger.debug(f"Grupo do campo '{field_name}' não mudou ({existing_group_id})")
                            
                            # Verificar se os enums mudaram (para campos select/multiselect/radiobutton)
                            if field_type in ['select', 'multiselect', 'radiobutton'] and master_field.get('enums'):
                                existing_enums = existing_field.get('enums', [])
                                new_enums = []
                                
                                # Preparar novos enums limpos
                                for enum_item in master_field['enums']:
                                    if isinstance(enum_item, dict):
                                        enum_data = {
                                            'value': enum_item.get('value', ''),
                                            'sort': enum_item.get('sort', 0)
                                        }
                                        new_enums.append(enum_data)
                                    else:
                                        new_enums.append({'value': str(enum_item), 'sort': 0})
                                
                                # Comparar enums existentes com novos
                                existing_values = set()
                                for e in existing_enums:
                                    if isinstance(e, dict):
                                        existing_values.add(e.get('value', ''))
                                    else:
                                        existing_values.add(str(e))
                                
                                new_values = {e['value'] for e in new_enums}
                                
                                if existing_values != new_values:
                                    update_data['enums'] = new_enums
                                    needs_update = True
                                    logger.info(f"Enums do campo '{field_name}' serão atualizados")
                                    logger.debug(f"Enums existentes: {sorted(existing_values)}")
                                    logger.debug(f"Novos enums: {sorted(new_values)}")
                            
                            # Verificar se o tipo mudou - FORÇAR atualização se os dados estão diferentes
                            if existing_field['type'] != field_type:
                                logger.warning(f"Tipo do campo '{field_name}' é diferente (existente: {existing_field['type']}, novo: {field_type}). Tipos não podem ser alterados via API, mas forçando outras atualizações.")
                                # Mesmo que não possa alterar o tipo, pode haver outras mudanças
                                needs_update = True
                            
                            # SEMPRE atualizar se houver qualquer diferença detectada OU se for conversão de tipo
                            if needs_update or master_field['type'] != existing_field['type']:
                                logger.info(f"ATUALIZANDO campo existente '{field_name}' (ID: {slave_field_id}) - diferenças detectadas")
                                logger.debug(f"Dados da atualização: {update_data}")
                                if update_data:  # Só fazer UPDATE se há dados para atualizar
                                    slave_api.update_custom_field(entity_type, slave_field_id, update_data)
                                    results['updated'] += 1
                                    logger.info(f"Campo '{field_name}' atualizado com sucesso")
                                else:
                                    logger.info(f"Campo '{field_name}' - nenhuma propriedade alterável detectada")
                                    results['skipped'] += 1
                            else:
                                results['skipped'] += 1
                                logger.info(f"Campo '{field_name}' já está sincronizado")
                        
                        else:
                            # Criar novo campo
                            logger.info(f"🆕 Criando campo '{field_name}' para {entity_type}")
                            logger.info(f"Dados do campo ANTES do envio: {field_data}")
                            if field_data.get('group_id'):
                                logger.info(f"🏷️ Campo será criado COM grupo ID: {field_data['group_id']}")
                            else:
                                logger.info(f"❌ Campo será criado SEM grupo (group_id não definido)")
                            
                            if field_data.get('required_statuses'):
                                logger.info(f"🎯 Campo será criado COM {len(field_data['required_statuses'])} required_statuses específicos")
                                for rs in field_data['required_statuses']:
                                    logger.debug(f"  - Pipeline ID: {rs.get('pipeline_id')}, Status ID: {rs.get('status_id')}")
                            else:
                                logger.info(f"❌ Campo será criado SEM required_statuses específicos")
                            
                            logger.debug(f"Tipo original: {master_field['type']} -> Tipo enviado: {field_type}")
                            response = slave_api.create_custom_field(entity_type, field_data)
                            slave_field_id = response['_embedded']['custom_fields'][0]['id']
                            results['created'] += 1
                            logger.info(f"✅ Campo '{field_name}' criado com ID: {slave_field_id}")
                            
                            # Verificar se o campo foi criado com configurações corretas
                            created_field = response['_embedded']['custom_fields'][0]
                            
                            if field_data.get('group_id'):
                                actual_group_id = created_field.get('group_id')
                                expected_group_id = field_data['group_id']
                                if actual_group_id == expected_group_id:
                                    logger.info(f"✅ Campo '{field_name}' criado no grupo correto: {actual_group_id}")
                                else:
                                    logger.error(f"❌ Campo '{field_name}' NÃO foi criado no grupo correto! Esperado: {expected_group_id}, Atual: {actual_group_id}")
                            
                            if field_data.get('required_statuses'):
                                actual_required_statuses = created_field.get('required_statuses', [])
                                expected_count = len(field_data['required_statuses'])
                                actual_count = len(actual_required_statuses)
                                if actual_count == expected_count:
                                    logger.info(f"✅ Campo '{field_name}' criado com {actual_count} required_statuses corretos")
                                else:
                                    logger.error(f"❌ Campo '{field_name}' NÃO foi criado com required_statuses corretos! Esperado: {expected_count}, Atual: {actual_count}")
                                    logger.debug(f"Expected: {field_data['required_statuses']}")
                                    logger.debug(f"Actual: {actual_required_statuses}")
                            
                        
                        # Armazenar mapeamento
                        if 'custom_fields' not in mappings:
                            mappings['custom_fields'] = {}
                        if entity_type not in mappings['custom_fields']:
                            mappings['custom_fields'][entity_type] = {}
                        mappings['custom_fields'][entity_type][master_field['id']] = slave_field_id
                        
                    except Exception as e:
                        error_msg = f"Erro ao sincronizar campo '{master_field['name']}' para {entity_type}: {e}"
                        
                        # Tratamento específico para erros de required_statuses
                        if ("required_statuses" in str(e) or 
                            "NotSupportedChoice" in str(e) or 
                            "status_id" in str(e) or 
                            "pipeline_id" in str(e)):
                            
                            logger.error(f"❌ ERRO DE REQUIRED_STATUSES: {error_msg}")
                            logger.error(f"🔍 Problema com validação de pipeline_id/status_id nos required_statuses")
                            
                            # Log dos dados que causaram erro
                            if field_data.get('required_statuses'):
                                logger.error(f"📋 Required_statuses que causaram erro:")
                                for rs in field_data['required_statuses']:
                                    logger.error(f"   - pipeline_id: {rs.get('pipeline_id')}, status_id: {rs.get('status_id')}")
                            
                            # Tentar criar o campo sem required_statuses como fallback
                            logger.info(f"🔄 Tentando criar campo '{master_field['name']}' SEM required_statuses como fallback...")
                            try:
                                # Remover required_statuses dos dados
                                fallback_field_data = field_data.copy()
                                if 'required_statuses' in fallback_field_data:
                                    del fallback_field_data['required_statuses']
                                
                                logger.info(f"📤 Criando campo SEM required_statuses:")
                                logger.info(f"   Nome: {fallback_field_data.get('name')}")
                                logger.info(f"   Tipo: {fallback_field_data.get('type')}")
                                logger.info(f"   Grupo: {fallback_field_data.get('group_id', 'Sem grupo')}")
                                
                                fallback_response = slave_api.create_custom_field(entity_type, fallback_field_data)
                                slave_field_id = fallback_response['_embedded']['custom_fields'][0]['id']
                                
                                logger.warning(f"⚠️ Campo '{master_field['name']}' criado SEM required_statuses específicos (ID: {slave_field_id})")
                                logger.info(f"ℹ️ Campo estará disponível em todos os estágios do funil")
                                
                                results['created'] += 1
                                
                                # Armazenar mapeamento mesmo assim
                                if 'custom_fields' not in mappings:
                                    mappings['custom_fields'] = {}
                                if entity_type not in mappings['custom_fields']:
                                    mappings['custom_fields'][entity_type] = {}
                                mappings['custom_fields'][entity_type][master_field['id']] = slave_field_id
                                
                            except Exception as fallback_error:
                                logger.error(f"❌ Fallback também falhou: {fallback_error}")
                                results['errors'] += 1
                        else:
                            logger.error(error_msg)
                            results['errors'] += 1
                        
                        if progress_callback:
                            progress_callback(f"❌ Erro no campo '{master_field['name']}': {e}")
                
                # FASE 2: Deletar campos que existem na escrava mas NÃO existem na master
                fields_to_delete = []
                for slave_field in all_slave_fields:
                    slave_field_name = slave_field.get('name', '')
                    slave_field_code = slave_field.get('code', '')
                    
                    # Pular campos do sistema
                    if slave_field_code and slave_field_code.upper() in system_codes:
                        continue
                    
                    # Verificar se o campo da escrava existe na master (por nome ou código)
                    found_in_master = False
                    
                    # Verificar por nome
                    if slave_field_name in master_field_names:
                        found_in_master = True
                    
                    # Verificar por código
                    elif slave_field_code and slave_field_code in master_field_codes:
                        found_in_master = True
                    
                    # Verificar por similaridade (mesmo algoritmo usado na detecção)
                    else:
                        for master_field in master_config['custom_fields'][entity_type]:
                            master_name = master_field['name'].lower().strip()
                            slave_name = slave_field_name.lower().strip()
                            
                            # Verificar similaridade exata ou parcial
                            if (slave_name == master_name or 
                                (len(slave_name) >= 3 and len(master_name) >= 3 and 
                                 (slave_name in master_name or master_name in slave_name) and
                                 abs(len(slave_name) - len(master_name)) <= 3)):
                                found_in_master = True
                                break
                            
                            # Verificar alta similaridade (≥70%)
                            def string_similarity(s1, s2):
                                s1, s2 = s1.lower(), s2.lower()
                                if len(s1) == 0 or len(s2) == 0:
                                    return 0
                                common = sum(1 for a, b in zip(s1, s2) if a == b)
                                max_len = max(len(s1), len(s2))
                                return common / max_len
                            
                            similarity = string_similarity(slave_name, master_name)
                            if similarity >= 0.7 and len(slave_name) >= 3:
                                found_in_master = True
                                break
                    
                    # Se não foi encontrado na master, marcar para exclusão
                    if not found_in_master:
                        fields_to_delete.append(slave_field)
                
                # Executar exclusões
                for field_to_delete in fields_to_delete:
                    try:
                        field_name = field_to_delete['name']
                        field_id = field_to_delete['id']
                        logger.info(f"🗑️ Deletando campo '{field_name}' de {entity_type} (ID: {field_id}) - não existe na master")
                        
                        # Tentar deletar o campo
                        delete_response = slave_api.delete_custom_field(entity_type, field_id)
                        
                        # Verificar se a exclusão foi bem-sucedida
                        if delete_response.get('success') or delete_response.get('status_code') in [200, 204]:
                            results['deleted'] += 1
                            logger.info(f"Campo '{field_name}' deletado com sucesso")
                        else:
                            logger.warning(f"Resposta inesperada ao deletar campo '{field_name}': {delete_response}")
                            results['deleted'] += 1  # Considerar como sucesso se não houve erro
                            
                    except Exception as e:
                        # Verificar se o erro indica que o campo não existe mais
                        error_str = str(e).lower()
                        if any(phrase in error_str for phrase in ['not found', '404', 'does not exist', 'já foi deletado']):
                            logger.info(f"Campo '{field_name}' já foi deletado ou não existe mais")
                            results['deleted'] += 1
                        else:
                            error_msg = f"Erro ao deletar campo '{field_name}' de {entity_type}: {e}"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                        
            except Exception as e:
                error_msg = f"Erro ao sincronizar campos personalizados para {entity_type}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        # Log do resumo final incluindo grupos
        total_groups = results.get('groups_created', 0) + results.get('groups_updated', 0) + results.get('groups_skipped', 0) + results.get('groups_deleted', 0)
        total_fields = results['created'] + results['updated'] + results['skipped'] + results['deleted']
        
        if total_groups > 0:
            logger.info(f"✅ Sincronização de campos COMPLETA! Grupos: {results.get('groups_created', 0)} criados, {results.get('groups_updated', 0)} atualizados, {results.get('groups_skipped', 0)} ignorados, {results.get('groups_deleted', 0)} deletados")
        logger.info(f"✅ Campos: {results['created']} criados, {results['updated']} atualizados, {results['skipped']} ignorados, {results['deleted']} deletados")
        
        return results
    
    def sync_all_to_slave(self, slave_api: KommoAPIService, master_config: Dict, 
                         progress_callback: Optional[Callable] = None,
                         sync_group_id: Optional[int] = None, 
                         slave_account_id: Optional[int] = None) -> Dict:
        """
        Sincroniza TODA a configuração da master para uma conta escrava - COM PROCESSAMENTO EM LOTES
        
        Args:
            slave_api: API da conta escrava
            master_config: Configuração extraída da conta mestre
            progress_callback: Função opcional para receber updates de progresso
            sync_group_id: ID do grupo de sincronização (opcional)
            slave_account_id: ID da conta slave (opcional)
        """
        logger.info("🚀 Iniciando sincronização COMPLETA em lotes da conta mestre para escrava...")
        
        # Reset da flag de parada
        self._stop_sync = False
        
        # Carregar mapeamentos existentes do banco se disponível
        if sync_group_id and slave_account_id:
            mappings = self._load_mappings_from_database(sync_group_id, slave_account_id)
        else:
            mappings = {'pipelines': {}, 'stages': {}, 'custom_field_groups': {}}
        total_results = {
            'pipelines': {'created': 0, 'updated': 0, 'skipped': 0, 'deleted': 0, 'errors': []},
            'custom_field_groups': {'created': 0, 'updated': 0, 'skipped': 0, 'deleted': 0, 'errors': []},
            'custom_fields': {'created': 0, 'updated': 0, 'skipped': 0, 'deleted': 0, 'errors': []}
        }
        
        try:
            # FASE 1: Sincronizar pipelines (independentes)
            if not self._stop_sync:
                logger.info("📊 FASE 1: Sincronizando pipelines em lotes...")
                pipeline_results = self.sync_pipelines_to_slave(slave_api, master_config, mappings, progress_callback)
                total_results['pipelines'] = pipeline_results
                logger.info(f"Pipelines: {pipeline_results['created']} criados, {pipeline_results['updated']} atualizados, "
                           f"{pipeline_results['skipped']} ignorados, {pipeline_results['deleted']} deletados")
            
            # FASE 2: Sincronizar grupos de campos (os campos dependem deles)
            if not self._stop_sync:
                logger.info("📁 FASE 2: Sincronizando grupos de campos em lotes...")
                groups_results = self.sync_custom_field_groups_to_slave(slave_api, master_config, mappings, progress_callback)
                total_results['custom_field_groups'] = groups_results
                logger.info(f"Grupos: {groups_results['created']} criados, {groups_results['updated']} atualizados, "
                           f"{groups_results['skipped']} ignorados, {groups_results['deleted']} deletados")
            
            # FASE 3: Sincronizar campos personalizados (agora que os grupos já existem)
            if not self._stop_sync:
                logger.info("🏷️ FASE 3: Sincronizando campos personalizados em lotes...")
                fields_results = self.sync_custom_fields_to_slave(slave_api, master_config, mappings, progress_callback)
                total_results['custom_fields'] = fields_results
                logger.info(f"Campos: {fields_results['created']} criados, {fields_results['updated']} atualizados, "
                           f"{fields_results['skipped']} ignorados, {fields_results['deleted']} deletados")
            
            # Calcular totais
            total_created = sum(results['created'] for results in total_results.values())
            total_updated = sum(results['updated'] for results in total_results.values())
            total_skipped = sum(results['skipped'] for results in total_results.values())
            total_deleted = sum(results['deleted'] for results in total_results.values())
            total_errors = sum(len(results['errors']) for results in total_results.values())
            
            if self._stop_sync:
                logger.warning("🛑 SINCRONIZAÇÃO INTERROMPIDA PELO USUÁRIO")
            else:
                logger.info("✅ SINCRONIZAÇÃO COMPLETA FINALIZADA EM LOTES!")
            
            logger.info(f"📊 RESUMO TOTAL: {total_created} criados, {total_updated} atualizados, "
                       f"{total_skipped} ignorados, {total_deleted} deletados, {total_errors} erros")
            
            # Adicionar totais ao resultado
            total_results['summary'] = {
                'total_created': total_created,
                'total_updated': total_updated,
                'total_skipped': total_skipped,
                'total_deleted': total_deleted,
                'total_errors': total_errors,
                'interrupted': self._stop_sync
            }
            
        except Exception as e:
            logger.error(f"Erro geral na sincronização completa: {e}")
            total_results['general_error'] = str(e)
        
        return total_results

