#!/usr/bin/env python3
"""
Script para testar a identificação de estágios especiais do sistema
"""

def test_system_stage_detection():
    """Testa a identificação de estágios especiais do sistema"""
    
    def _get_default_stage_id(stage_name: str, stage_type: int) -> int:
        """Retorna o ID padrão do Kommo para estágios especiais (Incoming=1, Won=142, Lost=143)"""
        stage_name_lower = stage_name.lower()
        
        # Estágio inicial (Incoming leads) - ID 1
        incoming_patterns = ['incoming leads', 'incoming', 'etapa de leads de entrada', 'leads de entrada', 'entrada']
        for pattern in incoming_patterns:
            if pattern in stage_name_lower:
                return 1
        
        # Estágios de vitória (Won) - ID 142
        won_patterns = ['won', 'ganho', 'ganha', 'venda ganha', 'fechado - ganho', 'closed - won', 'successful', 'sucesso']
        for pattern in won_patterns:
            if pattern in stage_name_lower:
                return 142
                
        # Estágios de perda (Lost) - ID 143  
        lost_patterns = ['lost', 'perdido', 'perdida', 'venda perdida', 'fechado - perdido', 'closed - lost', 'unsuccessful', 'fracasso']
        for pattern in lost_patterns:
            if pattern in stage_name_lower:
                return 143
                
        # Verificar por tipo também (1 = ganho, 2 = perda)
        if stage_type == 1:
            return 142
        elif stage_type == 2:
            return 143
            
        return None
    
    # Estágios de teste
    test_stages = [
        {'name': 'Incoming leads', 'type': 0},
        {'name': 'Contato inicial', 'type': 0},
        {'name': 'Proposta enviada', 'type': 0},
        {'name': 'Venda ganha', 'type': 0},
        {'name': 'Fechado - ganho', 'type': 0},
        {'name': 'Closed - won', 'type': 0},
        {'name': 'Venda perdida', 'type': 0},
        {'name': 'Fechado - perdido', 'type': 0},
        {'name': 'Closed - lost', 'type': 0},
        {'name': 'Negociação', 'type': 0},
        {'name': 'Won', 'type': 0},
        {'name': 'Lost', 'type': 0},
    ]
    
    print("🔍 TESTE DE IDENTIFICAÇÃO DE ESTÁGIOS ESPECIAIS")
    print("=" * 60)
    
    for stage in test_stages:
        stage_name = stage['name']
        stage_type = stage['type']
        default_id = _get_default_stage_id(stage_name, stage_type)
        is_system_stage = default_id in [142, 143] if default_id else False
        
        if default_id == 1:
            status = "� INCOMING"
            sync_action = "❌ PULAR (type=1)"
        elif is_system_stage:
            status = "🔴 ESPECIAL"
            sync_action = "❌ PULAR COMPLETAMENTE"
        else:
            status = "🟢 NORMAL"
            sync_action = "✅ SINCRONIZAR TUDO"
        
        id_info = f"ID: {default_id}" if default_id else "ID: None"
        
        print(f"{status} '{stage_name}' - {id_info} - {sync_action}")
    
    print("\n📋 RESUMO:")
    print("� INCOMING (1): Criado automaticamente, não sincronizar")
    print("�🔴 ESPECIAIS (142, 143): Gerenciados completamente pelo sistema")
    print("🟢 NORMAIS: Sincronizar nome e cor da master para slave")

if __name__ == "__main__":
    test_system_stage_detection()
