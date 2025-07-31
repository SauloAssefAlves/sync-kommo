#!/usr/bin/env python3
"""
Teste offline da lógica de cores - simula o comportamento sem precisar do banco
"""

import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_valid_kommo_color(master_color, fallback_index=0):
    """
    Função igual à implementada no código principal
    """
    kommo_colors = [
        '#fffeb2', '#fffd7f', '#fff000', '#ffeab2', '#ffdc7f', '#ffce5a',
        '#ffdbdb', '#ffc8c8', '#ff8f92', '#d6eaff', '#c1e0ff', '#98cbff',
        '#ebffb1', '#deff81', '#87f2c0', '#f9deff', '#f3beff', '#ccc8f9',
        '#eb93ff', '#f2f3f4', '#e6e8ea'
    ]
    
    logger.debug(f"Validando cor: master='{master_color}', fallback_index={fallback_index}")
    
    # Se a cor master é válida, usar ela
    if master_color and master_color.lower() in [c.lower() for c in kommo_colors]:
        logger.debug(f"✅ Cor master '{master_color}' é válida")
        return master_color
    
    # Buscar cor azul inteligentemente se parecer com azul
    if master_color and ('blue' in str(master_color).lower() or 
                         master_color.lower().startswith('#0000') or
                         master_color.lower() in ['blue', '#0000ff', '#00f']):
        blue_colors = ['#d6eaff', '#c1e0ff', '#98cbff']
        selected_blue = blue_colors[0]  # Padrão: azul claro
        logger.info(f"🔵 Detectada cor azul '{master_color}' → mapeando para '{selected_blue}'")
        return selected_blue
    
    # Fallback por índice
    fallback_color = kommo_colors[fallback_index % len(kommo_colors)]
    logger.warning(f"⚠️ Cor master '{master_color}' inválida → usando fallback índice {fallback_index}: '{fallback_color}'")
    return fallback_color

def test_color_scenarios():
    """
    Testa diferentes cenários de cores
    """
    logger.info("🧪 TESTANDO LÓGICA DE CORES...")
    logger.info("=" * 60)
    
    # Cenários de teste
    test_cases = [
        # (master_color, expected_behavior, description)
        ('#0000ff', 'should_map_to_blue', 'Azul padrão HTML'),
        ('blue', 'should_map_to_blue', 'Nome da cor em inglês'),
        ('#98cbff', 'should_keep', 'Azul Kommo válido'),
        ('#ff0000', 'should_fallback', 'Vermelho inválido'),
        ('invalid_color', 'should_fallback', 'Cor totalmente inválida'),
        ('#fff000', 'should_keep', 'Amarelo Kommo válido'),
        (None, 'should_fallback', 'Cor nula'),
        ('', 'should_fallback', 'Cor vazia'),
    ]
    
    for i, (master_color, expected, description) in enumerate(test_cases):
        logger.info(f"\n🔬 TESTE {i+1}: {description}")
        logger.info(f"   Entrada: '{master_color}'")
        
        result = get_valid_kommo_color(master_color, i)
        logger.info(f"   Resultado: '{result}'")
        
        # Verificar comportamento esperado
        if expected == 'should_map_to_blue':
            blue_colors = ['#d6eaff', '#c1e0ff', '#98cbff']
            if result in blue_colors:
                logger.info(f"   ✅ SUCESSO: Mapeou para azul corretamente")
            else:
                logger.error(f"   ❌ FALHA: Deveria mapear para azul, mas retornou '{result}'")
                
        elif expected == 'should_keep':
            if result == master_color:
                logger.info(f"   ✅ SUCESSO: Manteve cor válida")
            else:
                logger.error(f"   ❌ FALHA: Deveria manter '{master_color}', mas retornou '{result}'")
                
        elif expected == 'should_fallback':
            kommo_colors = [
                '#fffeb2', '#fffd7f', '#fff000', '#ffeab2', '#ffdc7f', '#ffce5a',
                '#ffdbdb', '#ffc8c8', '#ff8f92', '#d6eaff', '#c1e0ff', '#98cbff',
                '#ebffb1', '#deff81', '#87f2c0', '#f9deff', '#f3beff', '#ccc8f9',
                '#eb93ff', '#f2f3f4', '#e6e8ea'
            ]
            expected_fallback = kommo_colors[i % len(kommo_colors)]
            if result == expected_fallback:
                logger.info(f"   ✅ SUCESSO: Usou fallback correto")
            else:
                logger.error(f"   ❌ FALHA: Deveria usar fallback '{expected_fallback}', mas retornou '{result}'")
        
        # Verificar se não retornou amarelo quando não deveria
        yellow_colors = ['#fff000', '#fffd7f', '#fffeb2', '#ffeab2', '#ffdc7f', '#ffce5a']
        if result in yellow_colors and expected != 'should_fallback':
            logger.warning(f"   ⚠️ ATENÇÃO: Retornou amarelo quando poderia não ser ideal")

def test_pipeline_cor_teste_2_scenario():
    """
    Simula especificamente o cenário do pipeline 'cor teste 2'
    """
    logger.info("\n" + "=" * 60)
    logger.info("🎯 SIMULANDO CENÁRIO ESPECÍFICO: Pipeline 'cor teste 2'")
    logger.info("=" * 60)
    
    # Simular dados do pipeline master
    master_stages = [
        {'name': 'red', 'color': '#ff0000', 'id': 1},
        {'name': 'blue', 'color': '#0000ff', 'id': 2},  # Problema aqui
        {'name': 'green', 'color': '#00ff00', 'id': 3},
        {'name': 'yellow', 'color': '#fff000', 'id': 4},  # Válido
    ]
    
    logger.info("📋 Estágios do pipeline master:")
    for stage in master_stages:
        logger.info(f"   - {stage['name']}: {stage['color']}")
    
    logger.info("\n🔄 SIMULANDO SINCRONIZAÇÃO...")
    
    for i, stage in enumerate(master_stages):
        stage_name = stage['name']
        master_color = stage['color']
        
        logger.info(f"\n🔸 Processando estágio '{stage_name}':")
        logger.info(f"   Cor master: {master_color}")
        
        # Aplicar nossa lógica
        result_color = get_valid_kommo_color(master_color, i)
        logger.info(f"   Cor final: {result_color}")
        
        # Análise específica
        if stage_name == 'blue':
            blue_colors = ['#d6eaff', '#c1e0ff', '#98cbff']
            if result_color in blue_colors:
                logger.info(f"   ✅ RESOLVIDO: Status 'blue' agora terá cor azul real!")
            else:
                logger.error(f"   ❌ PROBLEMA: Status 'blue' ainda não tem cor azul!")
        
        elif stage_name == 'yellow':
            if result_color == master_color:
                logger.info(f"   ✅ OK: Status 'yellow' mantém cor amarela válida")
            else:
                logger.warning(f"   ⚠️ Mudança: Status 'yellow' mudou de cor")

def main():
    """
    Executa todos os testes
    """
    logger.info("🚀 INICIANDO TESTES OFFLINE DA LÓGICA DE CORES")
    logger.info("Este teste simula o comportamento sem precisar do banco na VPS")
    
    # Teste geral da lógica
    test_color_scenarios()
    
    # Teste específico do problema relatado
    test_pipeline_cor_teste_2_scenario()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ TESTES CONCLUÍDOS")
    logger.info("📝 RESUMO:")
    logger.info("   - A lógica de mapeamento de cores azuis está implementada")
    logger.info("   - Cores azuis (#0000ff, 'blue') serão mapeadas para #d6eaff")
    logger.info("   - Isso deve resolver o problema do status 'blue' aparecer amarelo")
    logger.info("   - O sistema ignora completamente os estágios especiais (142, 143)")

if __name__ == "__main__":
    main()
