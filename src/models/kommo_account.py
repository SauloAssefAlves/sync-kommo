from src.database import db
from datetime import datetime

class SyncGroup(db.Model):
    """Grupo de sincronização - uma conta mestre com suas escravas"""
    __tablename__ = 'sync_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Nome do grupo (ex: "Grupo Principal", "Filial SP")
    description = db.Column(db.Text)  # Descrição opcional
    master_account_id = db.Column(db.Integer, db.ForeignKey('kommo_accounts.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    master_account = db.relationship('KommoAccount', foreign_keys=[master_account_id], backref='master_groups')
    
    def __repr__(self):
        return f'<SyncGroup {self.name}>'

class KommoAccount(db.Model):
    __tablename__ = 'kommo_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    subdomain = db.Column(db.String(100), unique=True, nullable=False)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    token_expires_at = db.Column(db.DateTime, nullable=False)
    
    # Novo campo para associar à um grupo de sincronização
    sync_group_id = db.Column(db.Integer, db.ForeignKey('sync_groups.id'), nullable=True)
    account_role = db.Column(db.String(20), default='slave')  # 'master' ou 'slave'
    
    # Manter compatibilidade com sistema antigo
    is_master = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    sync_group = db.relationship('SyncGroup', foreign_keys=[sync_group_id], backref='slave_accounts')
    
    def __repr__(self):
        return f'<KommoAccount {self.subdomain} ({self.account_role})>'

class PipelineMapping(db.Model):
    __tablename__ = 'pipeline_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_group_id = db.Column(db.Integer, db.ForeignKey('sync_groups.id'), nullable=False)
    master_pipeline_id = db.Column(db.Integer, nullable=False)
    slave_account_id = db.Column(db.Integer, db.ForeignKey('kommo_accounts.id'), nullable=False)
    slave_pipeline_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    sync_group = db.relationship('SyncGroup', backref='pipeline_mappings')
    slave_account = db.relationship('KommoAccount', backref='pipeline_mappings')
    
    def __repr__(self):
        return f'<PipelineMapping group:{self.sync_group_id} master:{self.master_pipeline_id} -> slave:{self.slave_pipeline_id}>'

class StageMapping(db.Model):
    __tablename__ = 'stage_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_group_id = db.Column(db.Integer, db.ForeignKey('sync_groups.id'), nullable=False)
    master_stage_id = db.Column(db.Integer, nullable=False)
    slave_account_id = db.Column(db.Integer, db.ForeignKey('kommo_accounts.id'), nullable=False)
    slave_stage_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    sync_group = db.relationship('SyncGroup', backref='stage_mappings')
    slave_account = db.relationship('KommoAccount', backref='stage_mappings')
    
    def __repr__(self):
        return f'<StageMapping group:{self.sync_group_id} master:{self.master_stage_id} -> slave:{self.slave_stage_id}>'

class CustomFieldMapping(db.Model):
    __tablename__ = 'custom_field_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_group_id = db.Column(db.Integer, db.ForeignKey('sync_groups.id'), nullable=False)
    master_field_id = db.Column(db.Integer, nullable=False)
    slave_account_id = db.Column(db.Integer, db.ForeignKey('kommo_accounts.id'), nullable=False)
    slave_field_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    sync_group = db.relationship('SyncGroup', backref='custom_field_mappings')
    slave_account = db.relationship('KommoAccount', backref='custom_field_mappings')
    
    def __repr__(self):
        return f'<CustomFieldMapping group:{self.sync_group_id} master:{self.master_field_id} -> slave:{self.slave_field_id}>'

class SyncLog(db.Model):
    __tablename__ = 'sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_group_id = db.Column(db.Integer, db.ForeignKey('sync_groups.id'), nullable=True)  # Opcional para compatibilidade
    sync_type = db.Column(db.String(50), nullable=False)  # 'pipelines', 'custom_fields', 'full'
    status = db.Column(db.String(20), nullable=False)  # 'started', 'completed', 'failed'
    message = db.Column(db.Text)
    accounts_processed = db.Column(db.Integer, default=0)
    accounts_failed = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relacionamento
    sync_group = db.relationship('SyncGroup', backref='sync_logs')
    
    def __repr__(self):
        return f'<SyncLog group:{self.sync_group_id} {self.sync_type} - {self.status}>'

