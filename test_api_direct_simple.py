#!/usr/bin/env python3
"""
Script simplificado para verificar APIs diretamente (sem Flask/banco)
"""

import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_api():
    """
    Testa APIs diretamente usando tokens
    """
    logger.info("🔍 TESTE DIRETO DAS APIs (sem banco)")
    logger.info("=" * 60)
    
    # VOCÊ PRECISA SUBSTITUIR ESTES VALORES:
    MASTER_SUBDOMAIN = "seudominio"  # <<<< SUBSTITUIR
    MASTER_TOKEN = "seu_token_refresh"  # <<<< SUBSTITUIR
    
    SLAVE_SUBDOMAIN = "testedev"  # <<<< CONFIRMAR
    SLAVE_TOKEN = "token_slave"  # <<<< SUBSTITUIR
    
    logger.info("⚠️ IMPORTANTE: Você precisa editar este script com os tokens reais!")
    logger.info("📝 Edite as variáveis MASTER_TOKEN e SLAVE_TOKEN no arquivo")
    
    def get_pipelines(subdomain, token):
        """Obter pipelines via API"""
        try:
            url = f"https://{subdomain}.kommo.com/api/v4/leads/pipelines"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json().get('_embedded', {}).get('pipelines', [])
            else:
                logger.error(f"Erro API {subdomain}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Erro ao conectar {subdomain}: {e}")
            return []
    
    # Testar master
    logger.info("📋 TESTANDO MASTER...")
    if MASTER_TOKEN == "seu_token_refresh":
        logger.warning("❌ Token master não configurado!")
    else:
        master_pipelines = get_pipelines(MASTER_SUBDOMAIN, MASTER_TOKEN)
        logger.info(f"   Pipelines encontrados: {len(master_pipelines)}")
        
        for pipeline in master_pipelines[:3]:  # Mostrar apenas os primeiros 3
            logger.info(f"   - {pipeline['id']}: {pipeline['name']}")
    
    # Testar slave
    logger.info("\n📋 TESTANDO SLAVE...")
    if SLAVE_TOKEN == "token_slave":
        logger.warning("❌ Token slave não configurado!")
    else:
        slave_pipelines = get_pipelines(SLAVE_SUBDOMAIN, SLAVE_TOKEN)
        logger.info(f"   Pipelines encontrados: {len(slave_pipelines)}")
        
        for pipeline in slave_pipelines[:3]:  # Mostrar apenas os primeiros 3
            logger.info(f"   - {pipeline['id']}: {pipeline['name']}")
            
            # Verificar se é o pipeline 'cor teste 2'
            if 'cor teste 2' in pipeline['name'].lower():
                logger.info(f"   🎯 ENCONTROU 'cor teste 2': ID = {pipeline['id']}")
                
                if pipeline['id'] == 11680487:
                    logger.info(f"      ✅ ID está correto!")
                else:
                    logger.info(f"      ❓ ID diferente do esperado (11680487)")
    
    logger.info("\n💡 PRÓXIMOS PASSOS:")
    logger.info("1. Configure os tokens reais no script")
    logger.info("2. Execute novamente para ver os IDs reais")
    logger.info("3. Compare com o que está no banco de dados")

if __name__ == "__main__":
    test_direct_api()
