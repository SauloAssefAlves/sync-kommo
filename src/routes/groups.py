from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from src.database import db
from src.models.kommo_account import SyncGroup, KommoAccount, SyncLog
from src.services.kommo_api import KommoAPIService

group_bp = Blueprint('groups', __name__)
logger = logging.getLogger(__name__)

@group_bp.route('/overview', methods=['GET'])
def get_accounts_overview():
    """Obtém visão geral detalhada de todas as contas master e escravas"""
    try:
        groups = SyncGroup.query.filter_by(is_active=True).all()
        overview_data = []
        
        for group in groups:
            # Buscar todas as contas escravas do grupo
            slave_accounts = KommoAccount.query.filter_by(
                sync_group_id=group.id, 
                account_role='slave'
            ).all()
            
            # Calcular estatísticas
            total_contacts = 0
            for slave in slave_accounts:
                # Simular contagem de contatos (em produção, buscar da API)
                total_contacts += getattr(slave, 'contact_count', 0)
            
            # Último log do grupo
            last_sync = SyncLog.query.filter_by(
                sync_group_id=group.id
            ).order_by(SyncLog.started_at.desc()).first()
            
            # Dados das contas escravas
            slave_accounts_data = []
            for slave in slave_accounts:
                # Último sync específico da conta
                slave_last_sync = SyncLog.query.filter(
                    SyncLog.sync_group_id == group.id,
                    SyncLog.started_at >= datetime.now() - timedelta(days=30)
                ).order_by(SyncLog.started_at.desc()).first()
                
                slave_accounts_data.append({
                    'id': slave.id,
                    'subdomain': slave.subdomain,
                    'contact_count': getattr(slave, 'contact_count', 0),
                    'last_sync': slave_last_sync.started_at.isoformat() if slave_last_sync else None,
                    'status': 'active',  # Por enquanto, considerar todas como ativas
                    'created_at': slave.created_at.isoformat()
                })
            
            overview_data.append({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'master_account': {
                    'id': group.master_account.id,
                    'subdomain': group.master_account.subdomain,
                    'status': 'active'  # Por enquanto, considerar todas como ativas
                } if group.master_account else None,
                'slave_accounts': slave_accounts_data,
                'slave_accounts_count': len(slave_accounts_data),
                'total_contacts': total_contacts,
                'last_sync': {
                    'status': last_sync.status,
                    'started_at': last_sync.started_at.isoformat(),
                    'completed_at': last_sync.completed_at.isoformat() if last_sync.completed_at else None,
                    'duration': (last_sync.completed_at - last_sync.started_at).total_seconds() if last_sync and last_sync.completed_at else None
                } if last_sync else None,
                'created_at': group.created_at.isoformat(),
                'is_active': group.is_active
            })
        
        return jsonify({
            'success': True,
            'groups': overview_data,
            'total_groups': len(overview_data),
            'total_master_accounts': len([g for g in overview_data if g['master_account']]),
            'total_slave_accounts': sum(g['slave_accounts_count'] for g in overview_data),
            'total_contacts': sum(g['total_contacts'] for g in overview_data)
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter visão geral: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@group_bp.route('/', methods=['GET'])
def get_sync_groups():
    """Lista todos os grupos de sincronização"""
    try:
        groups = SyncGroup.query.filter_by(is_active=True).all()
        groups_data = []
        
        for group in groups:
            # Contar contas escravas no grupo
            slave_count = KommoAccount.query.filter_by(sync_group_id=group.id, account_role='slave').count()
            
            # Último log do grupo
            last_sync = SyncLog.query.filter_by(sync_group_id=group.id).order_by(SyncLog.started_at.desc()).first()
            
            groups_data.append({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'master_account': {
                    'id': group.master_account.id,
                    'subdomain': group.master_account.subdomain,
                } if group.master_account else None,
                'slave_count': slave_count,
                'last_sync': {
                    'status': last_sync.status,
                    'started_at': last_sync.started_at.isoformat(),
                    'completed_at': last_sync.completed_at.isoformat() if last_sync.completed_at else None
                } if last_sync else None,
                'created_at': group.created_at.isoformat(),
                'is_active': group.is_active
            })
        
        return jsonify({
            'success': True,
            'groups': groups_data,
            'total': len(groups_data)
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar grupos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@group_bp.route('/', methods=['POST'])
def create_sync_group():
    """Cria um novo grupo de sincronização"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        master_account_id = data.get('master_account_id')
        
        if not name or not master_account_id:
            return jsonify({'success': False, 'error': 'Nome e conta mestre são obrigatórios'}), 400
        
        # Verificar se a conta mestre existe
        master_account = KommoAccount.query.get(master_account_id)
        if not master_account:
            return jsonify({'success': False, 'error': 'Conta mestre não encontrada'}), 404
        
        # Verificar se já existe um grupo com este nome
        existing_group = SyncGroup.query.filter_by(name=name, is_active=True).first()
        if existing_group:
            return jsonify({'success': False, 'error': 'Já existe um grupo com este nome'}), 400
        
        # Criar o grupo
        new_group = SyncGroup(
            name=name,
            description=description,
            master_account_id=master_account_id
        )
        
        db.session.add(new_group)
        
        # Atualizar a conta mestre
        master_account.account_role = 'master'
        master_account.sync_group_id = new_group.id
        master_account.is_master = True  # Manter compatibilidade
        
        db.session.commit()
        
        logger.info(f"Grupo de sincronização criado: {name} com mestre {master_account.subdomain}")
        
        return jsonify({
            'success': True,
            'message': 'Grupo criado com sucesso',
            'group': {
                'id': new_group.id,
                'name': new_group.name,
                'description': new_group.description,
                'master_account': {
                    'id': master_account.id,
                    'subdomain': master_account.subdomain
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar grupo: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@group_bp.route('/<int:group_id>', methods=['GET'])
def get_sync_group(group_id):
    """Obtém detalhes de um grupo específico"""
    try:
        group = SyncGroup.query.get_or_404(group_id)
        
        # Buscar contas escravas do grupo
        slave_accounts = KommoAccount.query.filter_by(sync_group_id=group_id, account_role='slave').all()
        
        slaves_data = []
        for slave in slave_accounts:
            # Testar conectividade
            try:
                api = KommoAPIService(slave.subdomain, slave.refresh_token)
                connection_status = 'online' if api.test_connection() else 'offline'
            except:
                connection_status = 'error'
            
            slaves_data.append({
                'id': slave.id,
                'subdomain': slave.subdomain,
                'connection_status': connection_status,
                'created_at': slave.created_at.isoformat()
            })
        
        # Últimos logs do grupo
        recent_logs = SyncLog.query.filter_by(sync_group_id=group_id).order_by(SyncLog.started_at.desc()).limit(10).all()
        logs_data = []
        for log in recent_logs:
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
            'group': {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'master_account': {
                    'id': group.master_account.id,
                    'subdomain': group.master_account.subdomain,
                } if group.master_account else None,
                'slave_accounts': slaves_data,
                'recent_logs': logs_data,
                'created_at': group.created_at.isoformat(),
                'is_active': group.is_active
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter grupo {group_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@group_bp.route('/<int:group_id>/slaves', methods=['POST'])
def add_slave_to_group(group_id):
    """Adiciona uma conta escrava ao grupo"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        
        if not account_id:
            return jsonify({'success': False, 'error': 'ID da conta é obrigatório'}), 400
        
        # Verificar se o grupo existe
        group = SyncGroup.query.get_or_404(group_id)
        
        # Verificar se a conta existe
        account = KommoAccount.query.get(account_id)
        if not account:
            return jsonify({'success': False, 'error': 'Conta não encontrada'}), 404
        
        # Verificar se a conta já pertence a outro grupo
        if account.sync_group_id and account.sync_group_id != group_id:
            return jsonify({'success': False, 'error': 'Conta já pertence a outro grupo'}), 400
        
        # Adicionar ao grupo
        account.sync_group_id = group_id
        account.account_role = 'slave'
        account.is_master = False  # Manter compatibilidade
        
        db.session.commit()
        
        logger.info(f"Conta {account.subdomain} adicionada ao grupo {group.name}")
        
        return jsonify({
            'success': True,
            'message': f'Conta {account.subdomain} adicionada ao grupo {group.name}'
        })
        
    except Exception as e:
        logger.error(f"Erro ao adicionar conta ao grupo {group_id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@group_bp.route('/<int:group_id>/slaves/<int:account_id>', methods=['DELETE'])
def remove_slave_from_group(group_id, account_id):
    """Remove uma conta escrava do grupo"""
    try:
        # Verificar se o grupo existe
        group = SyncGroup.query.get_or_404(group_id)
        
        # Verificar se a conta existe e pertence ao grupo
        account = KommoAccount.query.filter_by(id=account_id, sync_group_id=group_id).first()
        if not account:
            return jsonify({'success': False, 'error': 'Conta não encontrada neste grupo'}), 404
        
        # Remover do grupo
        account.sync_group_id = None
        account.account_role = 'slave'  # Manter como escrava mas sem grupo
        account.is_master = False
        
        db.session.commit()
        
        logger.info(f"Conta {account.subdomain} removida do grupo {group.name}")
        
        return jsonify({
            'success': True,
            'message': f'Conta {account.subdomain} removida do grupo {group.name}'
        })
        
    except Exception as e:
        logger.error(f"Erro ao remover conta do grupo {group_id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@group_bp.route('/<int:group_id>/sync', methods=['POST'])
def sync_group(group_id):
    """Sincroniza um grupo específico"""
    try:
        data = request.get_json() or {}
        sync_type = data.get('sync_type', 'full')
        
        # Verificar se o grupo existe
        group = SyncGroup.query.get_or_404(group_id)
        
        # Importar função de sincronização (vamos atualizar esta parte)
        from src.routes.sync import trigger_group_sync
        
        result = trigger_group_sync(group_id, sync_type, data.get('batch_config', {}))
        return result
        
    except Exception as e:
        logger.error(f"Erro ao sincronizar grupo {group_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@group_bp.route('/<int:group_id>', methods=['PUT'])
def update_sync_group(group_id):
    """Atualiza um grupo de sincronização"""
    try:
        data = request.get_json()
        group = SyncGroup.query.get_or_404(group_id)
        
        # Atualizar campos se fornecidos
        if 'name' in data:
            group.name = data['name']
        if 'description' in data:
            group.description = data['description']
        if 'is_active' in data:
            group.is_active = data['is_active']
        
        group.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Grupo atualizado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar grupo {group_id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@group_bp.route('/<int:group_id>', methods=['DELETE'])
def delete_sync_group(group_id):
    """Desativa um grupo de sincronização (soft delete)"""
    try:
        group = SyncGroup.query.get_or_404(group_id)
        
        # Soft delete - apenas marcar como inativo
        group.is_active = False
        group.updated_at = datetime.utcnow()
        
        # Limpar referências nas contas
        accounts = KommoAccount.query.filter_by(sync_group_id=group_id).all()
        for account in accounts:
            account.sync_group_id = None
            account.account_role = 'slave'
            account.is_master = False
        
        db.session.commit()
        
        logger.info(f"Grupo {group.name} desativado")
        
        return jsonify({
            'success': True,
            'message': f'Grupo {group.name} desativado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao desativar grupo {group_id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
