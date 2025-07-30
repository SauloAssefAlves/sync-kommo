#!/usr/bin/env python3
"""
Sistema para configurar required_statuses manualmente
"""

import requests
import json

# Configuração para definir campos obrigatórios por estágio
REQUIRED_FIELDS_CONFIG = {
    'leads': [
        {
            'field_name': 'Nome da Empresa',  # Nome do campo
            'field_code': 'COMPANY_NAME',     # Código do campo (opcional)
            'required_in_stages': [
                {'pipeline_name': 'Vendas', 'stage_name': 'Qualificação'},
                {'pipeline_name': 'Vendas', 'stage_name': 'Proposta'},
            ]
        },
        {
            'field_name': 'Telefone',
            'field_code': 'PHONE',
            'required_in_stages': [
                {'pipeline_name': 'Vendas', 'stage_name': 'Contato Inicial'},
                {'pipeline_name': 'Vendas', 'stage_name': 'Qualificação'},
            ]
        }
        # Adicione mais campos conforme necessário
    ],
    'contacts': [
        # Configurações para contatos
    ],
    'companies': [
        # Configurações para empresas
    ]
}

def configure_required_statuses():
    """Configura required_statuses baseado na configuração manual"""
    
    API_BASE = "http://localhost:5000/api/sync"
    
    print("🎯 Configurando required_statuses manualmente...")
    
    # Esta seria a lógica para aplicar as configurações
    # Por enquanto, apenas mostra o que seria feito
    
    for entity_type, field_configs in REQUIRED_FIELDS_CONFIG.items():
        print(f"\n📋 Configurando {entity_type}:")
        
        for field_config in field_configs:
            field_name = field_config['field_name']
            required_stages = field_config['required_in_stages']
            
            print(f"  🔸 Campo: {field_name}")
            print(f"    Será obrigatório em {len(required_stages)} estágios:")
            
            for stage in required_stages:
                print(f"      - {stage['pipeline_name']} → {stage['stage_name']}")
    
    print(f"\n✅ Configuração manual de required_statuses concluída!")
    print(f"💡 Para implementar, será necessário:")
    print(f"   1. Buscar IDs dos pipelines e estágios pelos nomes")
    print(f"   2. Buscar IDs dos campos pelos nomes/códigos")  
    print(f"   3. Aplicar required_statuses via API do Kommo")

if __name__ == "__main__":
    configure_required_statuses()
