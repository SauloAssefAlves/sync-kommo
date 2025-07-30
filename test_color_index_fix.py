#!/usr/bin/env python3
"""
Script para testar o comportamento das cores com o novo sistema de índices
"""

def test_color_fallback():
    """
    Testa como as cores são aplicadas com o novo sistema de contagem de índices
    """
    print("🎨 Testando comportamento de cores com novo índice...")
    
    # Cores oficiais do Kommo
    kommo_colors = [
        '#fffeb2',  # 0 - Amarelo claro
        '#fffd7f',  # 1 - Amarelo médio  
        '#fff000',  # 2 - Amarelo forte
        '#ffeab2',  # 3 - Laranja claro
        '#ffdc7f',  # 4 - Laranja médio
        '#ffce5a',  # 5 - Laranja forte
        '#ffdbdb',  # 6 - Rosa claro
        '#ffc8c8',  # 7 - Rosa médio
        '#ff8f92',  # 8 - Rosa forte
        '#d6eaff',  # 9 - Azul claro
        '#c1e0ff',  # 10 - Azul médio
        '#98cbff',  # 11 - Azul forte
        '#ebffb1',  # 12 - Verde claro
        '#deff81',  # 13 - Verde médio
        '#87f2c0',  # 14 - Verde forte
        '#f9deff',  # 15 - Roxo claro
        '#f3beff',  # 16 - Roxo médio
        '#ccc8f9',  # 17 - Roxo forte
        '#eb93ff',  # 18 - Magenta
        '#f2f3f4',  # 19 - Cinza claro
        '#e6e8ea'   # 20 - Cinza escuro
    ]
    
    def get_valid_kommo_color(master_color, fallback_index):
        """Função igual à do código principal"""
        if master_color and master_color.lower() in [c.lower() for c in kommo_colors]:
            return master_color
        else:
            return kommo_colors[fallback_index % len(kommo_colors)]
    
    # Simular um pipeline com estágios, alguns sendo pulados
    master_stages = [
        {'name': 'Entrada', 'type': 1, 'color': '#ffffff'},  # Será pulado (type=1)
        {'name': 'Prospecção', 'type': 0, 'color': '#ff0000'},  # Inválida -> fallback índice 0
        {'name': 'Proposta', 'type': 0, 'color': '#00ff00'},  # Inválida -> fallback índice 1  
        {'name': 'blue', 'type': 0, 'color': '#0000ff'},  # Inválida -> fallback índice 2
        {'name': 'Negociação', 'type': 0, 'color': '#98cbff'},  # Válida (azul forte)
        {'name': 'Fechado - ganho', 'type': 1, 'color': '#00ff00'},  # Será pulado (ID=142)
        {'name': 'Fechado - perdido', 'type': 2, 'color': '#ff0000'}  # Será pulado (ID=143)
    ]
    
    def _get_default_stage_id(stage_name, stage_type):
        """Simular função de detecção de estágios especiais"""
        stage_name_lower = stage_name.lower()
        if 'ganho' in stage_name_lower or stage_type == 1:
            return 142
        elif 'perdido' in stage_name_lower or stage_type == 2:
            return 143
        elif stage_type == 1:
            return 1
        return None
    
    print("📋 Estágios da master:")
    for i, stage in enumerate(master_stages):
        stage_type = stage.get('type', 0)
        stage_name = stage['name']
        master_color = stage.get('color')
        
        # Verificar se deve ser pulado
        if stage_type == 1 and stage_name == 'Entrada':
            print(f"  {i}: {stage_name} - 🚫 PULADO (type=1)")
            continue
            
        default_stage_id = _get_default_stage_id(stage_name, stage_type)
        if default_stage_id in [142, 143]:
            print(f"  {i}: {stage_name} - 🚫 PULADO (sistema ID={default_stage_id})")
            continue
        
        print(f"  {i}: {stage_name} - type={stage_type}, master_color={master_color}")
    
    print("\n🎯 COMPORTAMENTO ANTIGO (usando índice i):")
    for i, stage in enumerate(master_stages):
        stage_type = stage.get('type', 0)
        stage_name = stage['name']
        master_color = stage.get('color')
        
        # Verificar se deve ser pulado
        if stage_type == 1 and stage_name == 'Entrada':
            continue
            
        default_stage_id = _get_default_stage_id(stage_name, stage_type)
        if default_stage_id in [142, 143]:
            continue
        
        # PROBLEMA: usar i mesmo com estágios pulados
        result_color = get_valid_kommo_color(master_color, i)
        color_name = get_color_name(result_color)
        print(f"  {stage_name}: índice {i} -> {result_color} ({color_name})")
    
    print("\n✅ COMPORTAMENTO NOVO (usando processed_stage_index):")
    processed_stage_index = 0
    for i, stage in enumerate(master_stages):
        stage_type = stage.get('type', 0)
        stage_name = stage['name']
        master_color = stage.get('color')
        
        # Verificar se deve ser pulado
        if stage_type == 1 and stage_name == 'Entrada':
            continue
            
        default_stage_id = _get_default_stage_id(stage_name, stage_type)
        if default_stage_id in [142, 143]:
            continue
        
        # CORREÇÃO: usar processed_stage_index
        result_color = get_valid_kommo_color(master_color, processed_stage_index)
        color_name = get_color_name(result_color)
        print(f"  {stage_name}: índice processado {processed_stage_index} -> {result_color} ({color_name})")
        processed_stage_index += 1

def get_color_name(color_code):
    """Retorna o nome da cor baseado no código"""
    color_map = {
        '#fffeb2': 'Amarelo claro', '#fffd7f': 'Amarelo médio', '#fff000': 'Amarelo forte',
        '#ffeab2': 'Laranja claro', '#ffdc7f': 'Laranja médio', '#ffce5a': 'Laranja forte',
        '#ffdbdb': 'Rosa claro', '#ffc8c8': 'Rosa médio', '#ff8f92': 'Rosa forte',
        '#d6eaff': 'Azul claro', '#c1e0ff': 'Azul médio', '#98cbff': 'Azul forte',
        '#ebffb1': 'Verde claro', '#deff81': 'Verde médio', '#87f2c0': 'Verde forte',
        '#f9deff': 'Roxo claro', '#f3beff': 'Roxo médio', '#ccc8f9': 'Roxo forte',
        '#eb93ff': 'Magenta', '#f2f3f4': 'Cinza claro', '#e6e8ea': 'Cinza escuro'
    }
    return color_map.get(color_code.lower(), 'Desconhecida')

if __name__ == "__main__":
    test_color_fallback()
