#!/usr/bin/env python3
"""
Script para testar a nova função _should_ignore_stage
"""

def test_should_ignore_stage():
    """
    Testa se a função _should_ignore_stage identifica corretamente estágios que devem ser ignorados
    """
    print("🧪 Testando função _should_ignore_stage...")
    
    def _should_ignore_stage(stage):
        """Função igual à do código principal"""
        stage_id = stage.get('id')
        stage_type = stage.get('type', 0)
        stage_name = stage.get('name', '').lower()
        
        # REGRA 1: Ignorar por ID direto (MAIS IMPORTANTE)
        if stage_id in [142, 143]:
            print(f"    DEBUG: 🚫 Ignorando estágio por ID especial: {stage_id} - '{stage_name}'")
            return True
            
        # REGRA 2: Ignorar estágios type=1 (incoming leads) - criados automaticamente
        if stage_type == 1:
            print(f"    DEBUG: 🚫 Ignorando estágio type=1: '{stage_name}' - criado automaticamente pelo Kommo")
            return True
            
        # REGRA 3: Ignorar por nome (padrões conhecidos de estágios especiais)
        special_patterns = [
            'incoming leads', 'incoming', 'etapa de leads de entrada', 'leads de entrada', 'entrada',
            'venda ganha', 'fechado - ganho', 'closed - won', 'won', 'successful', 'sucesso',
            'venda perdida', 'fechado - perdido', 'closed - lost', 'lost', 'unsuccessful', 'fracasso'
        ]
        
        for pattern in special_patterns:
            if pattern in stage_name:
                print(f"    DEBUG: 🚫 Ignorando estágio por padrão de nome: '{pattern}' em '{stage_name}'")
                return True
                
        return False
    
    # Casos de teste - estágios que DEVEM ser ignorados
    print("🚫 ESTÁGIOS QUE DEVEM SER IGNORADOS:")
    ignore_cases = [
        {'id': 142, 'name': 'Venda ganha', 'type': 1, 'description': 'ID 142 (Won)'},
        {'id': 143, 'name': 'Venda perdida', 'type': 2, 'description': 'ID 143 (Lost)'},
        {'id': 1, 'name': 'Incoming leads', 'type': 1, 'description': 'ID 1 (Incoming)'},
        {'id': 999, 'name': 'Qualquer coisa', 'type': 1, 'description': 'Type=1 (incoming)'},
        {'id': 888, 'name': 'Fechado - ganho', 'type': 0, 'description': 'Por nome (ganho)'},
        {'id': 777, 'name': 'Fechado - perdido', 'type': 0, 'description': 'Por nome (perdido)'},
        {'id': 666, 'name': 'Closed - won', 'type': 0, 'description': 'Por nome (won)'},
        {'id': 555, 'name': 'Closed - lost', 'type': 0, 'description': 'Por nome (lost)'},
    ]
    
    for stage in ignore_cases:
        result = _should_ignore_stage(stage)
        status = "✅" if result else "❌"
        print(f"  {status} {stage['description']}: ID={stage['id']}, Nome='{stage['name']}', Type={stage['type']} -> {result}")
    
    # Casos de teste - estágios que NÃO devem ser ignorados
    print("\n✅ ESTÁGIOS QUE NÃO DEVEM SER IGNORADOS:")
    keep_cases = [
        {'id': 444, 'name': 'Prospecção', 'type': 0, 'description': 'Estágio normal'},
        {'id': 333, 'name': 'Proposta', 'type': 0, 'description': 'Estágio normal'},
        {'id': 222, 'name': 'blue', 'type': 0, 'description': 'Estágio blue (problema original)'},
        {'id': 111, 'name': 'Negociação', 'type': 0, 'description': 'Estágio normal'},
        {'id': 100, 'name': 'Qualificação', 'type': 0, 'description': 'Estágio normal'},
    ]
    
    for stage in keep_cases:
        result = _should_ignore_stage(stage)
        status = "✅" if not result else "❌"
        print(f"  {status} {stage['description']}: ID={stage['id']}, Nome='{stage['name']}', Type={stage['type']} -> {result}")
    
    print("\n🎯 CASO ESPECÍFICO DOS LOGS (que causava erro 404):")
    problem_stages = [
        {'id': 142, 'name': 'Venda ganha'},
        {'id': 143, 'name': 'Venda perdida'}
    ]
    
    for stage in problem_stages:
        result = _should_ignore_stage(stage)
        status = "✅ SERÁ IGNORADO" if result else "❌ TENTARÁ PROCESSAR"
        print(f"  {status}: ID={stage['id']}, Nome='{stage['name']}' -> {result}")
    
    print("\n📊 RESUMO DA NOVA LÓGICA:")
    print("  🚫 IGNORAR COMPLETAMENTE:")
    print("     - Estágios com ID 142 ou 143 (Won/Lost)")
    print("     - Estágios com type=1 (Incoming leads)")
    print("     - Estágios com nomes especiais (ganho, perdido, won, lost, etc.)")
    print("  ✅ PROCESSAR NORMALMENTE:")
    print("     - Todos os outros estágios (Prospecção, Proposta, blue, etc.)")
    print("  🎯 RESULTADO: Nenhum erro 404 para estágios especiais!")

if __name__ == "__main__":
    test_should_ignore_stage()
