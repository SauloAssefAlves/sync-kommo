from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from src.database import db
from src.models.kommo_account import KommoAccount, SyncLog, SyncGroup
from src.services.kommo_api import KommoAPIService, KommoSyncService

sync_bp = Blueprint('sync', __name__)
logger = logging.getLogger(__name__)

# Estado global da sincronização
global_sync_status = {
    'is_running': False,
    'sync_type': None,
    'current_status': 'idle',
    'progress': 0,
    'current_operation': '-',
    'current_batch': '-',
    'estimated_time': '-',
    'start_time': None,
    'total_items': 0,
    'processed_items': 0,
    'accounts_processed': 0,
    'total_accounts': 0,
    'results': {}
}

def update_global_status(status=None, progress=None, operation=None, batch=None, **kwargs):
    """Atualiza o status global da sincronização"""
    if status is not None:
        global_sync_status['current_status'] = status
    if progress is not None:
        global_sync_status['progress'] = progress
    if operation is not None:
        global_sync_status['current_operation'] = operation
    if batch is not None:
        global_sync_status['current_batch'] = batch
    
    # Atualizar outros campos se fornecidos
    for key, value in kwargs.items():
        if key in global_sync_status:
            global_sync_status[key] = value

@sync_bp.route('/accounts', methods=['GET'])
def get_accounts():
    """Lista todas as contas Kommo cadastradas"""
    try:
        accounts = KommoAccount.query.all()
        accounts_data = []
        
        for account in accounts:
            # Obter informações do grupo se aplicável
            group_info = None
            if account.sync_group_id:
                group = SyncGroup.query.get(account.sync_group_id)
                if group:
                    group_info = {
                        'id': group.id,
                        'name': group.name
                    }
            
            accounts_data.append({
                'id': account.id,
                'subdomain': account.subdomain,
                'is_master': account.is_master,
                'account_role': account.account_role,
                'sync_group_id': account.sync_group_id,
                'group': group_info,
                'created_at': account.created_at.isoformat(),
                'updated_at': account.updated_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'accounts': accounts_data,
            'total': len(accounts_data)
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar contas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_bp.route('/accounts', methods=['POST'])
def add_account():
    """Adiciona uma nova conta Kommo usando apenas subdomain e refresh_token"""
    try:
        data = request.get_json()
        
        if data is None:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        required_fields = ['subdomain', 'refresh_token']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Campo obrigatório: {field}'}), 400
        
        subdomain = data['subdomain']
        refresh_token = data['refresh_token']
        group_id = data.get('group_id')  # ID do grupo (opcional)
        
        # Verificar se a conta já existe
        existing_account = KommoAccount.query.filter_by(subdomain=subdomain).first()
        if existing_account:
            return jsonify({'success': False, 'error': 'Conta já existe'}), 400
        
        # Se group_id foi fornecido, validar se o grupo existe
        if group_id:
            group = SyncGroup.query.get(group_id)
            if not group:
                return jsonify({'success': False, 'error': 'Grupo não encontrado'}), 400
        
        # Criar nova conta (apenas subdomain e refresh_token)
        new_account = KommoAccount(
            subdomain=subdomain,
            access_token='',  # Não usado mais
            refresh_token=refresh_token,
            token_expires_at=datetime.utcnow(),  # Não usado mais
            is_master=data.get('is_master', False),
            account_role='master' if data.get('is_master', False) else 'slave',
            sync_group_id=group_id  # Associar ao grupo se fornecido
        )
        
        # Se esta conta for marcada como mestre, desmarcar outras contas mestres
        if new_account.is_master:
            KommoAccount.query.filter_by(is_master=True).update({'is_master': False})
        
        db.session.add(new_account)
        db.session.commit()
        
        # Preparar resposta com informações do grupo
        response_data = {
            'success': True,
            'message': 'Conta adicionada com sucesso',
            'account_id': new_account.id,
            'note': 'Sistema ultra-simplificado: usa apenas subdomain + refresh_token'
        }
        
        # Adicionar informações do grupo se aplicável
        if group_id:
            group = SyncGroup.query.get(group_id)
            if group:
                response_data['group'] = {
                    'id': group.id,
                    'name': group.name
                }
                response_data['message'] = f'Conta adicionada com sucesso ao grupo "{group.name}"'
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Erro ao adicionar conta: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

def trigger_group_sync(group_id, sync_type='full', batch_config=None):
    """Função para sincronizar um grupo específico"""
    try:
        if batch_config is None:
            batch_config = {}
        
        # Obter o grupo
        group = SyncGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupo não encontrado'}), 404
        
        if not group.is_active:
            return jsonify({'success': False, 'error': 'Grupo está inativo'}), 400
        
        # Obter conta mestre do grupo
        master_account = group.master_account
        if not master_account:
            return jsonify({'success': False, 'error': 'Grupo não possui conta mestre configurada'}), 400
        
        # Obter contas escravas do grupo
        slave_accounts = KommoAccount.query.filter_by(sync_group_id=group_id, account_role='slave').all()
        if not slave_accounts:
            return jsonify({'success': False, 'error': 'Grupo não possui contas escravas'}), 400
        
        # Configurações de lote
        batch_size = batch_config.get('batch_size', 10)
        batch_delay = batch_config.get('batch_delay', 2.0)
        max_concurrent = batch_config.get('max_concurrent', 3)
        
        logger.info(f"🚀 Iniciando sincronização do grupo '{group.name}' - {sync_type} com lotes de {batch_size} itens")
        
        # Atualizar status global
        update_global_status(
            status='starting',
            progress=0,
            operation=f'Iniciando sincronização do grupo {group.name}',
            batch='-',
            sync_type=sync_type,
            is_running=True,
            start_time=datetime.utcnow().isoformat()
        )
        
        # Criar log de sincronização
        sync_log = SyncLog(
            sync_group_id=group_id,
            sync_type=sync_type,
            status='started',
            message=f'Iniciando sincronização {sync_type} do grupo {group.name} para {len(slave_accounts)} contas'
        )
        db.session.add(sync_log)
        db.session.commit()
        
        try:
            # Inicializar serviço da conta mestre
            master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
            sync_service = KommoSyncService(master_api, batch_size=batch_size, delay_between_batches=batch_delay)
            
            # Testar conexão da conta mestre
            if not master_api.test_connection():
                raise Exception('Falha na conexão com a conta mestre')
            
            # Atualizar status
            update_global_status(
                status='preparing',
                operation='Extraindo configurações da conta mestre',
                total_accounts=len(slave_accounts)
            )
            
            # Extrair configurações da conta mestre
            master_config = sync_service.extract_master_configuration()
            
            # Callback para progresso
            def progress_callback(progress):
                logger.info(f"📦 Progresso grupo {group.name}: {progress['operation']} - {progress['percentage']:.1f}%")
            
            # Resultados da sincronização
            sync_results = {
                'group_id': group_id,
                'group_name': group.name,
                'accounts_processed': 0,
                'accounts_failed': 0,
                'batch_config': {
                    'batch_size': batch_size,
                    'batch_delay': batch_delay,
                    'max_concurrent': max_concurrent
                },
                'details': []
            }
            
            # Sincronizar cada conta escrava do grupo
            for i, slave_account in enumerate(slave_accounts):
                try:
                    # Atualizar progresso
                    account_progress = ((i + 1) / len(slave_accounts)) * 100
                    update_global_status(
                        status='processing',
                        progress=account_progress,
                        operation=f'Processando conta {slave_account.subdomain}',
                        accounts_processed=i,
                        total_accounts=len(slave_accounts)
                    )
                    
                    logger.info(f"📊 Processando conta {i + 1}/{len(slave_accounts)}: {slave_account.subdomain}")
                    
                    # Inicializar API da conta escrava
                    slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
                    
                    # Testar conexão
                    if not slave_api.test_connection():
                        raise Exception(f"Falha na conexão com a conta {slave_account.subdomain}")
                    
                    mappings = {'pipelines': {}, 'stages': {}, 'custom_fields': {}, 'roles': {}}
                    account_results = {'subdomain': slave_account.subdomain}
                    
                    # Sincronizar baseado no tipo solicitado
                    if sync_type == 'full':
                        all_results = sync_service.sync_all_to_slave(
                            slave_api, master_config, progress_callback,
                            group.id, slave_account.id
                        )
                        account_results.update(all_results)
                    else:
                        # Sincronização específica
                        if sync_type in ['pipelines']:
                            pipeline_results = sync_service.sync_pipelines_to_slave(
                                slave_api, master_config, mappings, progress_callback, 
                                group.id, slave_account.id
                            )
                            account_results['pipelines'] = pipeline_results
                        
                        if sync_type in ['custom_fields', 'required_statuses', 'field_groups']:
                            custom_fields_results = sync_service.sync_custom_fields_to_slave(
                                slave_api, master_config, mappings, progress_callback,
                                group.id, slave_account.id
                            )
                            account_results['custom_fields'] = custom_fields_results
                        
                        if sync_type in ['roles']:
                            roles_results = sync_service.sync_roles_to_slave(
                                slave_api, master_config, mappings, progress_callback
                            )
                            account_results['roles'] = roles_results
                    
                    sync_results['accounts_processed'] += 1
                    sync_results['details'].append(account_results)
                    
                except Exception as e:
                    error_msg = f"Erro ao sincronizar conta {slave_account.subdomain}: {e}"
                    logger.error(error_msg)
                    sync_results['accounts_failed'] += 1
                    sync_results['details'].append({
                        'subdomain': slave_account.subdomain,
                        'error': str(e)
                    })
            
            # Atualizar log de sincronização
            sync_log.status = 'completed'
            sync_log.accounts_processed = sync_results['accounts_processed']
            sync_log.accounts_failed = sync_results['accounts_failed']
            sync_log.completed_at = datetime.utcnow()
            sync_log.message = f'Sincronização do grupo {group.name} concluída: {sync_results["accounts_processed"]} sucessos, {sync_results["accounts_failed"]} falhas'
            
            db.session.commit()
            
            # Atualizar status global - conclusão
            update_global_status(
                status='completed',
                progress=100,
                operation=f'Sincronização do grupo {group.name} concluída',
                is_running=False,
                results=sync_results
            )
            
            return jsonify({
                'success': True,
                'message': f'Sincronização do grupo {group.name} concluída',
                'sync_log_id': sync_log.id,
                'results': sync_results
            })
            
        except Exception as e:
            # Atualizar log com falha
            sync_log.status = 'failed'
            sync_log.message = f'Falha na sincronização do grupo {group.name}: {e}'
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            
            # Atualizar status global - erro
            update_global_status(
                status='failed',
                operation=f'Erro no grupo {group.name}: {str(e)}',
                is_running=False
            )
            
            raise
            
    except Exception as e:
        logger.error(f"Erro na sincronização do grupo {group_id}: {e}")
        
        # Atualizar status global - erro
        update_global_status(
            status='failed',
            operation=f'Erro: {str(e)}',
            is_running=False
        )
        
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_bp.route('/groups/<int:group_id>/trigger', methods=['POST'])
def trigger_group_sync_endpoint(group_id):
    """Endpoint para sincronizar um grupo específico"""
    try:
        data = request.get_json() or {}
        sync_type = data.get('sync_type', 'full')
        batch_config = data.get('batch_config', {})
        
        return trigger_group_sync(group_id, sync_type, batch_config)
        
    except Exception as e:
        logger.error(f"Erro no endpoint de sincronização do grupo {group_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_bp.route('/trigger', methods=['POST'])
def trigger_sync():
    """Aciona a sincronização manual das configurações - COM SUPORTE A LOTES"""
    try:
        data = request.get_json() or {}
        sync_type = data.get('sync_type', 'full')  # 'pipelines', 'custom_fields', 'required_statuses', 'roles', 'full'
        
        # Configurações de lote (com valores padrão)
        batch_config = data.get('batch_config', {})
        batch_size = batch_config.get('batch_size', 10)
        batch_delay = batch_config.get('batch_delay', 2.0)
        max_concurrent = batch_config.get('max_concurrent', 3)
        
        logger.info(f"🚀 Iniciando sincronização {sync_type} com lotes de {batch_size} itens, {batch_delay}s de delay")
        
        # Atualizar status global - início da sincronização
        update_global_status(
            status='starting',
            progress=0,
            operation=f'Iniciando sincronização {sync_type}',
            batch='-',
            sync_type=sync_type,
            is_running=True,
            start_time=datetime.utcnow().isoformat()
        )
        
        # Obter conta mestre
        master_account = KommoAccount.query.filter_by(is_master=True).first()
        if not master_account:
            return jsonify({'success': False, 'error': 'Nenhuma conta mestre configurada'}), 400
        
        # Obter contas escravas
        slave_accounts = KommoAccount.query.filter_by(is_master=False).all()
        if not slave_accounts:
            return jsonify({'success': False, 'error': 'Nenhuma conta escrava configurada'}), 400
        
        # Criar log de sincronização
        sync_message = f'Iniciando sincronização {sync_type} em lotes para {len(slave_accounts)} contas'
        if sync_type == 'required_statuses':
            sync_message = f'🎯 Iniciando sincronização de Required Statuses em lotes para {len(slave_accounts)} contas'
        
        sync_log = SyncLog(
            sync_type=sync_type,
            status='started',
            message=sync_message
        )
        db.session.add(sync_log)
        db.session.commit()
        
        try:
            # Inicializar serviço da conta mestre com configurações de lote
            master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
            sync_service = KommoSyncService(master_api, batch_size=batch_size, delay_between_batches=batch_delay)
            
            # Testar conexão da conta mestre
            if not master_api.test_connection():
                return jsonify({'success': False, 'error': 'Falha na conexão com a conta mestre'}), 400
            
            # Extrair configurações da conta mestre
            master_config = sync_service.extract_master_configuration()
            
            # Callback para monitorar progresso
            progress_data = {'current_account': 0, 'total_accounts': len(slave_accounts)}
            
            def progress_callback(progress):
                logger.info(f"📦 Progresso: {progress['operation']} - {progress['percentage']:.1f}% "
                           f"(lote {progress.get('current_batch', '?')}/{progress.get('total_batches', '?')})")
            
            # Atualizar status global para preparação
            update_global_status(
                status='preparing',
                operation='Preparando sincronização',
                total_accounts=len(slave_accounts)
            )
            
            # Resultados da sincronização
            sync_results = {
                'accounts_processed': 0,
                'accounts_failed': 0,
                'batch_config': {
                    'batch_size': batch_size,
                    'batch_delay': batch_delay,
                    'max_concurrent': max_concurrent
                },
                'details': []
            }
            
            # Sincronizar cada conta escrava
            for slave_account in slave_accounts:
                try:
                    # Atualizar progresso da conta atual
                    progress_data['current_account'] += 1
                    logger.info(f"📊 Processando conta {progress_data['current_account']}/{progress_data['total_accounts']}: {slave_account.subdomain}")
                    
                    # Atualizar status global - processando conta
                    account_progress = (progress_data['current_account'] / progress_data['total_accounts']) * 100
                    update_global_status(
                        status='processing',
                        progress=account_progress,
                        operation=f'Processando conta {slave_account.subdomain}',
                        accounts_processed=progress_data['current_account'] - 1,
                        total_accounts=progress_data['total_accounts']
                    )
                    
                    # Inicializar API da conta escrava
                    slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
                    
                    # Testar conexão
                    if not slave_api.test_connection():
                        raise Exception(f"Falha na conexão com a conta {slave_account.subdomain}")
                    
                    mappings = {'pipelines': {}, 'stages': {}, 'custom_fields': {}, 'roles': {}}
                    account_results = {'subdomain': slave_account.subdomain}
                    
                    # Sincronizar baseado no tipo solicitado
                    if sync_type == 'full':
                        # Sincronização completa usando o método otimizado
                        all_results = sync_service.sync_all_to_slave(
                            slave_api, master_config, progress_callback,
                            account.id, slave_account.id  # Assumindo que account é o grupo aqui
                        )
                        account_results.update(all_results)
                    else:
                        # Sincronização específica
                        if sync_type in ['pipelines']:
                            pipeline_results = sync_service.sync_pipelines_to_slave(slave_api, master_config, mappings, progress_callback)
                            account_results['pipelines'] = pipeline_results
                        
                        if sync_type in ['custom_fields', 'required_statuses', 'field_groups']:
                            custom_fields_results = sync_service.sync_custom_fields_to_slave(
                                slave_api, master_config, mappings, progress_callback,
                                account.id, slave_account.id  # Assumindo que account é o grupo aqui
                            )
                            account_results['custom_fields'] = custom_fields_results
                        
                        if sync_type in ['roles']:
                            roles_results = sync_service.sync_roles_to_slave(
                                slave_api, master_config, mappings, progress_callback
                            )
                            account_results['roles'] = roles_results
                    
                    # Note: required_statuses é sincronizado junto com custom_fields
                    # pois eles fazem parte da configuração dos campos personalizados
                    
                    sync_results['accounts_processed'] += 1
                    sync_results['details'].append(account_results)
                    
                except Exception as e:
                    error_msg = f"Erro ao sincronizar conta {slave_account.subdomain}: {e}"
                    logger.error(error_msg)
                    sync_results['accounts_failed'] += 1
                    sync_results['details'].append({
                        'subdomain': slave_account.subdomain,
                        'error': str(e)
                    })
            
            # Atualizar log de sincronização
            sync_log.status = 'completed'
            sync_log.accounts_processed = sync_results['accounts_processed']
            sync_log.accounts_failed = sync_results['accounts_failed']
            sync_log.completed_at = datetime.utcnow()
            
            completion_message = f'Sincronização concluída: {sync_results["accounts_processed"]} sucessos, {sync_results["accounts_failed"]} falhas'
            if sync_type == 'required_statuses':
                completion_message = f'🎯 Required Statuses sincronizados: {sync_results["accounts_processed"]} sucessos, {sync_results["accounts_failed"]} falhas'
            
            sync_log.message = completion_message
            
            db.session.commit()
            
            # Atualizar status global - conclusão
            update_global_status(
                status='completed',
                progress=100,
                operation='Sincronização concluída',
                is_running=False,
                results=sync_results
            )
            
            return jsonify({
                'success': True,
                'message': 'Sincronização concluída',
                'sync_log_id': sync_log.id,
                'results': sync_results
            })
            
        except Exception as e:
            # Atualizar log com falha
            sync_log.status = 'failed'
            sync_log.message = f'Falha na sincronização: {e}'
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            
            # Atualizar status global - erro
            update_global_status(
                status='failed',
                operation=f'Erro: {str(e)}',
                is_running=False
            )
            
            raise
            
    except Exception as e:
        logger.error(f"Erro na sincronização: {e}")
        
        # Atualizar status global - erro
        update_global_status(
            status='failed',
            operation=f'Erro: {str(e)}',
            is_running=False
        )
        
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_bp.route('/webhook', methods=['POST'])
def webhook_trigger():
    """Endpoint para receber webhooks do Salesbot e acionar sincronização"""
    try:
        data = request.get_json()
        logger.info(f"Webhook recebido: {data}")
        
        # Verificar se é um webhook válido do Salesbot
        if not data or 'leads' not in data:
            return jsonify({'success': False, 'error': 'Webhook inválido'}), 400
        
        # Extrair informações do webhook
        webhook_data = data.get('leads', {})
        
        # Verificar se é um evento de sincronização (pode ser baseado em um estágio específico ou tag)
        # Por exemplo, se o lead entrar em um estágio específico chamado "Sincronizar Configurações"
        
        # Acionar sincronização automática
        sync_response = trigger_sync()
        
        # Log do webhook
        logger.info(f"Sincronização acionada via webhook. Resposta: {sync_response}")
        
        return jsonify({
            'success': True,
            'message': 'Webhook processado e sincronização acionada',
            'webhook_data': webhook_data
        })
        
    except Exception as e:
        logger.error(f"Erro no processamento do webhook: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_bp.route('/logs', methods=['GET'])
def get_sync_logs():
    """Obtém o histórico de sincronizações"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        logs = SyncLog.query.order_by(SyncLog.started_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs_data = []
        for log in logs.items:
            logs_data.append({
                'id': log.id,
                'sync_type': log.sync_type,
                'status': log.status,
                'message': log.message,
                'accounts_processed': log.accounts_processed,
                'accounts_failed': log.accounts_failed,
                'started_at': log.started_at.isoformat(),
                'completed_at': log.completed_at.isoformat() if log.completed_at else None
            })
        
        return jsonify({
            'success': True,
            'logs': logs_data,
            'pagination': {
                'page': logs.page,
                'pages': logs.pages,
                'per_page': logs.per_page,
                'total': logs.total
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_bp.route('/status', methods=['GET'])
def get_sync_status():
    """Obtém o status atual do sistema de sincronização"""
    try:
        # Retornar status global em tempo real
        return jsonify({
            'success': True,
            'status': {
                'current_status': global_sync_status['current_status'],
                'progress': global_sync_status['progress'],
                'current_operation': global_sync_status['current_operation'],
                'current_batch': global_sync_status['current_batch'],
                'estimated_time': global_sync_status['estimated_time'],
                'sync_type': global_sync_status['sync_type'],
                'is_running': global_sync_status['is_running'],
                'accounts_processed': global_sync_status['accounts_processed'],
                'total_accounts': global_sync_status['total_accounts'],
                'processed_items': global_sync_status['processed_items'],
                'total_items': global_sync_status['total_items'],
                'results': global_sync_status['results']
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_bp.route('/accounts/clear', methods=['DELETE'])
def clear_all_accounts():
    """Remove todas as contas do banco de dados"""
    try:
        # Contar quantas contas serão removidas
        count = KommoAccount.query.count()
        
        # Remover todas as contas
        KommoAccount.query.delete()
        
        # Commit das mudanças
        db.session.commit()
        
        logger.info(f"Todas as {count} contas foram removidas do banco")
        
        return jsonify({
            'success': True,
            'message': f'{count} contas removidas com sucesso',
            'accounts_removed': count
        })
        
    except Exception as e:
        logger.error(f"Erro ao limpar contas: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_bp.route('/config/test', methods=['GET'])
def test_config():
    """Testa as configurações do sistema"""
    try:
        config_status = {
            'accounts_count': KommoAccount.query.count(),
            'master_accounts': KommoAccount.query.filter_by(is_master=True).count()
        }
        
        # Verificar se há contas configuradas
        if config_status['accounts_count'] > 0:
            sample_account = KommoAccount.query.first()
            config_status['sample_subdomain'] = sample_account.subdomain
            config_status['sample_has_refresh_token'] = bool(sample_account.refresh_token)
        
        recommendations = []
        if config_status['master_accounts'] == 0:
            recommendations.append("Adicione pelo menos uma conta master")
        if config_status['accounts_count'] == 0:
            recommendations.append("Adicione pelo menos uma conta para sincronizar")
        
        return jsonify({
            'success': True,
            'config': config_status,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar configurações: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@sync_bp.route('/test/accounts', methods=['GET'])
def test_all_accounts():
    """Testa conexão e endpoints de todas as contas cadastradas"""
    try:
        accounts = KommoAccount.query.all()
        
        if not accounts:
            return jsonify({'success': False, 'error': 'Nenhuma conta cadastrada'}), 400
        
        test_results = {
            'total_accounts': len(accounts),
            'successful_tests': 0,
            'failed_tests': 0,
            'details': []
        }
        
        for account in accounts:
            account_result = {
                'subdomain': account.subdomain,
                'is_master': account.is_master,
                'tests': {}
            }
            
            try:
                # Inicializar API para a conta
                api_service = KommoAPIService(account.subdomain, account.refresh_token)
                
                # Teste 1: Conexão básica
                try:
                    connection_test = api_service.test_connection()
                    account_result['tests']['connection'] = {'success': connection_test, 'error': None}
                except Exception as e:
                    account_result['tests']['connection'] = {'success': False, 'error': str(e)}
                
                # Teste 2: Buscar pipelines
                try:
                    pipelines = api_service.get_pipelines()
                    account_result['tests']['pipelines'] = {
                        'success': True, 
                        'count': len(pipelines),
                        'names': [p['name'] for p in pipelines[:3]],  # Primeiros 3 nomes
                        'error': None
                    }
                except Exception as e:
                    account_result['tests']['pipelines'] = {'success': False, 'error': str(e)}
                
                # Teste 3: Buscar campos personalizados de leads
                try:
                    custom_fields = api_service.get_custom_fields('leads')
                    account_result['tests']['custom_fields_leads'] = {
                        'success': True,
                        'count': len(custom_fields),
                        'names': [f['name'] for f in custom_fields[:3]],  # Primeiros 3 nomes
                        'error': None
                    }
                except Exception as e:
                    account_result['tests']['custom_fields_leads'] = {'success': False, 'error': str(e)}
                
                # Teste 4: Buscar campos personalizados de contacts
                try:
                    custom_fields = api_service.get_custom_fields('contacts')
                    account_result['tests']['custom_fields_contacts'] = {
                        'success': True,
                        'count': len(custom_fields),
                        'names': [f['name'] for f in custom_fields[:3]],  # Primeiros 3 nomes
                        'error': None
                    }
                except Exception as e:
                    account_result['tests']['custom_fields_contacts'] = {'success': False, 'error': str(e)}
                
                # Teste 5: Buscar campos personalizados de companies
                try:
                    custom_fields = api_service.get_custom_fields('companies')
                    account_result['tests']['custom_fields_companies'] = {
                        'success': True,
                        'count': len(custom_fields),
                        'names': [f['name'] for f in custom_fields[:3]],  # Primeiros 3 nomes
                        'error': None
                    }
                except Exception as e:
                    account_result['tests']['custom_fields_companies'] = {'success': False, 'error': str(e)}
                
                # Verificar se pelo menos um teste passou
                successful_tests = sum(1 for test in account_result['tests'].values() if test['success'])
                if successful_tests > 0:
                    test_results['successful_tests'] += 1
                    account_result['overall_status'] = 'success'
                else:
                    test_results['failed_tests'] += 1
                    account_result['overall_status'] = 'failed'
                
            except Exception as e:
                account_result['overall_status'] = 'failed'
                account_result['general_error'] = str(e)
                test_results['failed_tests'] += 1
            
            test_results['details'].append(account_result)
        
        return jsonify({
            'success': True,
            'message': f'Teste concluído: {test_results["successful_tests"]} sucessos, {test_results["failed_tests"]} falhas',
            'results': test_results
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar contas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sync_bp.route('/multi-account', methods=['POST'])
def trigger_multi_account_sync():
    """Sincronização avançada com múltiplas contas em lotes"""
    try:
        data = request.get_json() or {}
        sync_type = data.get('sync_type', 'multi_account')
        parallel = data.get('parallel', True)
        continue_on_error = data.get('continue_on_error', True)
        
        # Configurações de lote
        batch_config = data.get('batch_config', {})
        batch_size = batch_config.get('batch_size', 10)
        batch_delay = batch_config.get('batch_delay', 2.0)
        max_concurrent = batch_config.get('max_concurrent', 3)
        
        logger.info(f"🚀 Iniciando sincronização múltipla: paralelo={parallel}, lotes={batch_size}")
        
        # TODO: Implementar lógica de sincronização múltipla
        # Por agora, redirecionar para o endpoint padrão
        return trigger_sync()
        
    except Exception as e:
        logger.error(f"Erro na sincronização múltipla: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sync_bp.route('/stop', methods=['POST'])
def stop_sync():
    """Para a sincronização em andamento"""
    try:
        logger.info("🛑 Solicitação de parada de sincronização recebida")
        
        # Atualizar status global
        update_global_status(
            status='stopping',
            operation='Parando sincronização...',
            is_running=False
        )
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de parada enviada'
        })
        
    except Exception as e:
        logger.error(f"Erro ao parar sincronização: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sync_bp.route('/roles', methods=['POST'])
def sync_roles_only():
    """Sincroniza somente as roles (funções/permissões) entre as contas"""
    try:
        data = request.get_json() or {}
        master_account_id = data.get('master_account_id')
        slave_account_ids = data.get('slave_account_ids', [])
        
        # Se não especificar contas, buscar todas as contas ativas
        if not master_account_id:
            # Buscar conta master padrão (primeira conta ativa com role 'master')
            master_account = KommoAccount.query.filter_by(
                is_active=True, 
                account_role='master'
            ).first()
            if not master_account:
                return jsonify({
                    'success': False, 
                    'error': 'Nenhuma conta master encontrada'
                }), 400
            master_account_id = master_account.id
        else:
            master_account = KommoAccount.query.get(master_account_id)
            if not master_account:
                return jsonify({
                    'success': False, 
                    'error': f'Conta master {master_account_id} não encontrada'
                }), 404
        
        # Se não especificar contas slave, buscar todas as contas slave ativas
        if not slave_account_ids:
            slave_accounts = KommoAccount.query.filter_by(
                is_active=True, 
                account_role='slave'
            ).all()
            slave_account_ids = [acc.id for acc in slave_accounts]
        
        if not slave_account_ids:
            return jsonify({
                'success': False, 
                'error': 'Nenhuma conta slave encontrada para sincronização'
            }), 400
        
        logger.info(f"🔐 Iniciando sincronização de roles - Master: {master_account_id}, Slaves: {slave_account_ids}")
        
        # Verificar se já há sincronização em andamento
        if global_sync_status['is_running']:
            return jsonify({
                'success': False, 
                'error': 'Já existe uma sincronização em andamento'
            }), 409
        
        # Atualizar status global
        update_global_status(
            is_running=True,
            sync_type='roles_only',
            current_status='initializing',
            progress=0,
            current_operation='Iniciando sincronização de roles...',
            start_time=datetime.now(),
            total_accounts=len(slave_account_ids),
            accounts_processed=0,
            results={}
        )
        
        # Configurar API da conta master
        master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
        
        # Testar conexão da conta master
        if not master_api.test_connection():
            update_global_status(is_running=False, current_status='error')
            return jsonify({
                'success': False, 
                'error': 'Falha na conexão com a conta master'
            }), 500
        
        # Configurações de lote
        batch_config = data.get('batch_config', {})
        batch_size = batch_config.get('batch_size', 5)
        batch_delay = batch_config.get('batch_delay', 1.0)
        
        # Inicializar serviço de sincronização
        sync_service = KommoSyncService(master_api, batch_size=batch_size, delay_between_batches=batch_delay)
        
        # Extrair configuração de roles da master
        update_global_status(
            current_status='extracting_config',
            current_operation='Extraindo configuração de roles da conta master...',
            progress=5
        )
        
        master_config = {'roles': []}
        try:
            roles = master_api.get_roles()
            for role in roles:
                role_data = {
                    'id': role['id'],
                    'name': role['name'],
                    'rights': role.get('rights', {}),
                }
                master_config['roles'].append(role_data)
                logger.debug(f"Role extraída: {role['name']} (ID: {role['id']})")
            
            logger.info(f"✅ {len(master_config['roles'])} roles extraídas da conta master")
            
        except Exception as e:
            logger.error(f"Erro ao extrair roles da master: {e}")
            update_global_status(is_running=False, current_status='error')
            return jsonify({
                'success': False, 
                'error': f'Erro ao extrair roles da master: {str(e)}'
            }), 500
        
        # Verificar se há roles para sincronizar
        if not master_config['roles']:
            update_global_status(is_running=False, current_status='completed')
            return jsonify({
                'success': True, 
                'message': 'Nenhuma role encontrada na conta master para sincronizar',
                'results': {'total_accounts': 0, 'success_accounts': 0, 'failed_accounts': 0}
            })
        
        # Resultados consolidados
        consolidated_results = {
            'total_accounts': len(slave_account_ids),
            'success_accounts': 0,
            'failed_accounts': 0,
            'total_roles_created': 0,
            'total_roles_updated': 0,
            'total_roles_deleted': 0,
            'total_roles_skipped': 0,
            'account_details': []
        }
        
        # Função de callback para progresso
        def progress_callback(progress_data):
            current_progress = 10 + (global_sync_status['accounts_processed'] * 80 // len(slave_account_ids))
            if progress_data:
                batch_progress = (progress_data.get('percentage', 0) * 80) // (100 * len(slave_account_ids))
                current_progress += batch_progress
            
            update_global_status(
                progress=min(current_progress, 95),
                current_operation=f"Sincronizando roles - {progress_data.get('operation', 'processando')}",
                current_batch=f"Conta {global_sync_status['accounts_processed'] + 1}/{len(slave_account_ids)}"
            )
        
        # Sincronizar para cada conta slave
        for i, slave_account_id in enumerate(slave_account_ids):
            try:
                if sync_service._stop_sync:
                    logger.info("🛑 Sincronização interrompida pelo usuário")
                    break
                
                update_global_status(
                    accounts_processed=i,
                    current_operation=f'Sincronizando roles para conta {slave_account_id}...'
                )
                
                # Obter dados da conta slave
                slave_account = KommoAccount.query.get(slave_account_id)
                if not slave_account:
                    logger.error(f"Conta slave {slave_account_id} não encontrada")
                    consolidated_results['failed_accounts'] += 1
                    consolidated_results['account_details'].append({
                        'account_id': slave_account_id,
                        'status': 'failed',
                        'error': 'Conta não encontrada'
                    })
                    continue
                
                # Configurar API da conta slave
                slave_api = KommoAPIService(slave_account.subdomain, slave_account.refresh_token)
                
                # Testar conexão da conta slave
                if not slave_api.test_connection():
                    logger.error(f"Falha na conexão com a conta slave {slave_account_id}")
                    consolidated_results['failed_accounts'] += 1
                    consolidated_results['account_details'].append({
                        'account_id': slave_account_id,
                        'subdomain': slave_account.subdomain,
                        'status': 'failed',
                        'error': 'Falha na conexão'
                    })
                    continue
                
                # Sincronizar roles
                logger.info(f"🔐 Sincronizando roles para conta {slave_account.subdomain}...")
                mappings = {'roles': {}}
                
                roles_results = sync_service.sync_roles_to_slave(
                    slave_api=slave_api,
                    master_config=master_config,
                    mappings=mappings,
                    progress_callback=progress_callback,
                    sync_group_id=slave_account.sync_group_id,
                    slave_account_id=slave_account.id
                )
                
                # Registrar resultado
                if roles_results.get('errors'):
                    consolidated_results['failed_accounts'] += 1
                    consolidated_results['account_details'].append({
                        'account_id': slave_account_id,
                        'subdomain': slave_account.subdomain,
                        'status': 'failed',
                        'error': '; '.join(roles_results['errors']),
                        'partial_results': roles_results
                    })
                else:
                    consolidated_results['success_accounts'] += 1
                    consolidated_results['account_details'].append({
                        'account_id': slave_account_id,
                        'subdomain': slave_account.subdomain,
                        'status': 'success',
                        'results': roles_results
                    })
                
                # Acumular estatísticas
                consolidated_results['total_roles_created'] += roles_results.get('created', 0)
                consolidated_results['total_roles_updated'] += roles_results.get('updated', 0)
                consolidated_results['total_roles_deleted'] += roles_results.get('deleted', 0)
                consolidated_results['total_roles_skipped'] += roles_results.get('skipped', 0)
                
                # Registrar log de sincronização
                sync_log = SyncLog(
                    source_account_id=master_account_id,
                    target_account_id=slave_account_id,
                    sync_type='roles_only',
                    status='success' if not roles_results.get('errors') else 'failed',
                    details={
                        'roles_created': roles_results.get('created', 0),
                        'roles_updated': roles_results.get('updated', 0),
                        'roles_deleted': roles_results.get('deleted', 0),
                        'roles_skipped': roles_results.get('skipped', 0),
                        'errors': roles_results.get('errors', [])
                    }
                )
                db.session.add(sync_log)
                
            except Exception as e:
                logger.error(f"Erro ao sincronizar roles para conta {slave_account_id}: {e}")
                consolidated_results['failed_accounts'] += 1
                consolidated_results['account_details'].append({
                    'account_id': slave_account_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Salvar logs no banco
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar logs: {e}")
            db.session.rollback()
        
        # Finalizar status
        update_global_status(
            is_running=False,
            current_status='completed',
            progress=100,
            current_operation='Sincronização de roles concluída',
            accounts_processed=len(slave_account_ids),
            results=consolidated_results
        )
        
        logger.info(f"🔐 Sincronização de roles concluída: {consolidated_results}")
        
        return jsonify({
            'success': True,
            'message': f'Sincronização de roles concluída',
            'results': consolidated_results
        })
        
    except Exception as e:
        logger.error(f"Erro geral na sincronização de roles: {e}")
        update_global_status(
            is_running=False,
            current_status='error',
            current_operation=f'Erro: {str(e)}'
        )
        return jsonify({'success': False, 'error': str(e)}), 500


# Endpoint duplicado removido - já existe no início do arquivo


@sync_bp.route('/account/<account_id>', methods=['POST'])
def sync_single_account(account_id):
    """Sincroniza uma única conta específica"""
    try:
        data = request.get_json() or {}
        sync_type = data.get('sync_type', 'full')
        batch_config = data.get('batch_config', {})
        
        logger.info(f"🚀 Iniciando sincronização {sync_type} da conta {account_id}")
        
        # Buscar a conta
        account = KommoAccount.query.get(account_id)
        if not account:
            return jsonify({'success': False, 'error': 'Conta não encontrada'}), 404
        
        if account.is_master or account.account_role == 'master':
            return jsonify({'success': False, 'error': 'Não é possível sincronizar uma conta mestre'}), 400
        
        # Buscar a conta mestre do mesmo grupo
        if account.sync_group_id:
            group = SyncGroup.query.get(account.sync_group_id)
            if group and group.master_account_id:
                master_account = KommoAccount.query.get(group.master_account_id)
            else:
                return jsonify({'success': False, 'error': 'Grupo ou conta mestre não encontrado'}), 400
        else:
            # Fallback para sistema antigo - buscar qualquer conta mestre
            master_account = KommoAccount.query.filter_by(is_master=True).first()
            if not master_account:
                return jsonify({'success': False, 'error': 'Nenhuma conta mestre configurada'}), 400
        
        try:
            # Inicializar serviços de API
            master_api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
            slave_api = KommoAPIService(account.subdomain, account.refresh_token)
            
            # Testar conexões
            master_api.test_connection()
            slave_api.test_connection()
            
            # Criar serviço de sincronização
            sync_service = KommoSyncService(master_api, [slave_api])
            
            # Executar sincronização baseada no tipo
            if sync_type == 'full':
                result = sync_service.sync_all_configurations([account.subdomain])
            elif sync_type == 'pipelines':
                result = sync_service.sync_pipelines([account.subdomain])
            elif sync_type == 'custom_fields':
                result = sync_service.sync_custom_fields([account.subdomain])
            elif sync_type == 'required_statuses':
                result = sync_service.sync_required_statuses([account.subdomain])
            elif sync_type == 'roles':
                # Para sincronização de roles individual, usar o método moderno com parâmetros corretos
                master_config = sync_service.extract_master_configuration()
                mappings = {'pipelines': {}, 'stages': {}, 'custom_fields': {}, 'roles': {}}
                result = sync_service.sync_roles_to_slave(
                    slave_api, 
                    master_config, 
                    mappings,
                    sync_group_id=account.sync_group_id,
                    slave_account_id=account.id
                )
            else:
                return jsonify({'success': False, 'error': f'Tipo de sincronização inválido: {sync_type}'}), 400
            
            # Log de resultado
            sync_log = SyncLog(
                account_id=account.id,
                sync_type=sync_type,
                status='completed',
                message=f'Sincronização {sync_type} da conta {account.subdomain} concluída com sucesso',
                details=str(result)
            )
            db.session.add(sync_log)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Sincronização {sync_type} da conta {account.subdomain} concluída com sucesso',
                'result': result
            })
            
        except Exception as sync_error:
            logger.error(f"Erro na sincronização da conta {account_id}: {sync_error}")
            
            # Log de erro
            sync_log = SyncLog(
                account_id=account.id,
                sync_type=sync_type,
                status='failed',
                message=f'Erro na sincronização {sync_type} da conta {account.subdomain}',
                details=str(sync_error)
            )
            db.session.add(sync_log)
            db.session.commit()
            
            return jsonify({
                'success': False,
                'error': f'Erro na sincronização: {str(sync_error)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao sincronizar conta {account_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sync_bp.route('/accounts/slaves', methods=['GET'])
def get_slave_accounts():
    """Lista contas escravas para interface de múltiplas contas - com suporte a grupos"""
    try:
        group_id = request.args.get('group_id', type=int)
        
        if group_id:
            # Filtrar por grupo específico
            slave_accounts = KommoAccount.query.filter_by(sync_group_id=group_id, account_role='slave').all()
        else:
            # Todas as contas escravas (compatibilidade com sistema antigo)
            slave_accounts = KommoAccount.query.filter_by(is_master=False).all()
        
        accounts_data = []
        for account in slave_accounts:
            # Testar status da conta
            try:
                api = KommoAPIService(account.subdomain, account.refresh_token)
                status = 'online' if api.test_connection() else 'offline'
            except:
                status = 'error'
            
            # Obter informações do grupo se aplicável
            group_info = None
            if account.sync_group_id:
                group = SyncGroup.query.get(account.sync_group_id)
                if group:
                    group_info = {
                        'id': group.id,
                        'name': group.name
                    }
            
            accounts_data.append({
                'id': account.id,
                'name': account.subdomain,
                'subdomain': account.subdomain,
                'status': status,
                'account_role': account.account_role,
                'group': group_info,
                'last_sync': account.updated_at.isoformat() if account.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'accounts': accounts_data
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar contas escravas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sync_bp.route('/accounts/<account_id>/test', methods=['GET'])
def test_single_account(account_id):
    """Testa conexão com uma conta específica"""
    try:
        account = KommoAccount.query.get_or_404(account_id)
        
        api = KommoAPIService(account.subdomain, account.refresh_token)
        success = api.test_connection()
        
        return jsonify({
            'success': success,
            'account_id': account_id,
            'subdomain': account.subdomain,
            'error': None if success else 'Falha na conexão'
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar conta {account_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@sync_bp.route('/accounts/master', methods=['GET'])
def get_master_account():
    """Obter informações da conta mestre - com suporte a grupos"""
    try:
        group_id = request.args.get('group_id', type=int)
        
        if group_id:
            # Buscar conta mestre do grupo específico
            group = SyncGroup.query.get(group_id)
            if not group:
                return jsonify({'success': False, 'error': 'Grupo não encontrado'}), 404
            
            master_account = group.master_account
            if not master_account:
                return jsonify({'success': False, 'error': 'Conta mestre não encontrada para este grupo'}), 404
        else:
            # Buscar conta mestre padrão (compatibilidade)
            master_account = KommoAccount.query.filter_by(is_master=True).first()
            if not master_account:
                return jsonify({'success': False, 'error': 'Nenhuma conta mestre configurada'}), 404
        
        # Testar conexão
        try:
            api = KommoAPIService(master_account.subdomain, master_account.refresh_token)
            status = 'online' if api.test_connection() else 'offline'
        except:
            status = 'error'
        
        # Informações do grupo
        group_info = None
        if master_account.sync_group_id:
            group = SyncGroup.query.get(master_account.sync_group_id)
            if group:
                group_info = {
                    'id': group.id,
                    'name': group.name,
                    'description': group.description
                }
        
        return jsonify({
            'success': True,
            'account': {
                'id': master_account.id,
                'name': master_account.subdomain,
                'subdomain': master_account.subdomain,
                'status': status,
                'account_role': master_account.account_role,
                'group': group_info,
                'last_sync': master_account.updated_at.isoformat() if master_account.updated_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter conta mestre: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

