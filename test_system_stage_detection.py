#!/usr/bin/env python3
"""
Script para testar a função _is_system_stage
"""

def test_is_system_stage():
    """
    Testa se a função _is_system_stage identifica corretamente estágios especiais
    """
    print("🧪 Testando função _is_system_stage...")
    
    def _is_system_stage(stage):
        """Função igual à do código principal"""
        stage_id = stage.get('id')
        stage_type = stage.get('type', 0)
        stage_name = stage.get('name', '').lower()
        
        # Verificar por ID direto (MAIS IMPORTANTE)
        if stage_id in [1, 142, 143]:
            print(f"    DEBUG: Estágio '{stage_name}' é especial por ID: {stage_id}")
            return True
            
        # Verificar por tipo especial
        if stage_type in [1, 2]:  # 1=ganho, 2=perda
            print(f"    DEBUG: Estágio '{stage_name}' é especial por tipo: {stage_type}")
            return True
            
        # Verificar por nome (padrões conhecidos)
        system_patterns = [
            'incoming leads', 'incoming', 'etapa de leads de entrada', 'leads de entrada', 'entrada',
            'won', 'ganho', 'ganha', 'venda ganha', 'fechado - ganho', 'closed - won', 'successful', 'sucesso',
            'lost', 'perdido', 'perdida', 'venda perdida', 'fechado - perdido', 'closed - lost', 'unsuccessful', 'fracasso'
        ]
        
        for pattern in system_patterns:
            if pattern in stage_name:
                print(f"    DEBUG: Estágio '{stage_name}' é especial por nome (padrão: '{pattern}')")
                return True
                
        return False
    
    # Casos de teste
    test_stages = [
        # Casos que DEVEM ser detectados como especiais
        {'id': 142, 'name': 'Venda ganha', 'type': 1},
        {'id': 143, 'name': 'Venda perdida', 'type': 2},
        {'id': 1, 'name': 'Incoming leads', 'type': 1},
        {'id': 142, 'name': 'Closed - won', 'type': 1},
        {'id': 143, 'name': 'Closed - lost', 'type': 2},
        {'id': 999, 'name': 'Fechado - ganho', 'type': 0},  # Por nome
        {'id': 888, 'name': 'Fechado - perdido', 'type': 0},  # Por nome
        {'id': 777, 'name': 'Qualquer coisa', 'type': 1},  # Por tipo
        {'id': 666, 'name': 'Qualquer coisa', 'type': 2},  # Por tipo
        
        # Casos que NÃO devem ser detectados como especiais
        {'id': 555, 'name': 'Prospecção', 'type': 0},
        {'id': 444, 'name': 'Proposta', 'type': 0},
        {'id': 333, 'name': 'blue', 'type': 0},
        {'id': 222, 'name': 'Negociação', 'type': 0},
    ]
    
    print("✅ ESTÁGIOS QUE DEVEM SER ESPECIAIS:")
    for stage in test_stages[:9]:  # Primeiros 9 são especiais
        result = _is_system_stage(stage)
        status = "✅" if result else "❌"
        print(f"  {status} ID={stage['id']}, Nome='{stage['name']}', Type={stage['type']} -> {result}")
    
    print("\n❌ ESTÁGIOS QUE NÃO DEVEM SER ESPECIAIS:")
    for stage in test_stages[9:]:  # Últimos 4 não são especiais
        result = _is_system_stage(stage)
        status = "✅" if not result else "❌"
        print(f"  {status} ID={stage['id']}, Nome='{stage['name']}', Type={stage['type']} -> {result}")
    
    print("\n🎯 CASO ESPECÍFICO DOS LOGS (que estava tentando excluir):")
    problem_stages = [
        {'id': 142, 'name': 'Venda ganha'},
        {'id': 143, 'name': 'Venda perdida'}
    ]
    
    for stage in problem_stages:
        result = _is_system_stage(stage)
        status = "✅ DEVE SER PULADO" if result else "❌ SERÁ TENTADO EXCLUIR"
        print(f"  {status}: ID={stage['id']}, Nome='{stage['name']}' -> {result}")

if __name__ == "__main__":
    test_is_system_stage()
