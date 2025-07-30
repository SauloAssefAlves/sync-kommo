#!/usr/bin/env python3
"""
Script para executar sincronização via API da VPS
"""

import requests
import logging
import sys
import json
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

VPS_BASE_URL = "http://89.116.186.230:5000"

def trigger_sync_via_api():
    """
    Disparar sincronização via API REST da VPS
    """
    logger.info("🚀 DISPARANDO SINCRONIZAÇÃO VIA API DA VPS...")
    
    try:
        # Endpoint correto baseado no JavaScript
        sync_url = f"{VPS_BASE_URL}/api/sync/trigger"
        
        # Dados para a sincronização baseado no código JS
        sync_data = {
            "sync_type": "pipelines",  # ou "full", "field_groups", "custom_fields"
            "batch_config": {
                "batch_size": 10,
                "delay_between_batches": 2.0,
                "max_concurrent": 3
            }
        }
        
        logger.info(f"📡 Fazendo requisição para: {sync_url}")
        logger.info(f"📦 Dados: {sync_data}")
        
        # Fazer requisição POST
        response = requests.post(
            sync_url,
            json=sync_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=300  # 5 minutos
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Sincronização disparada com sucesso!")
            logger.info(f"📤 Resultado: {json.dumps(result, indent=2)}")
            
            # Monitorar o progresso
            monitor_sync_progress()
            
        elif response.status_code == 202:
            logger.info("✅ Sincronização aceita e processando...")
            logger.info(f"📤 Resposta: {response.text}")
            
            # Monitorar o progresso
            monitor_sync_progress()
            
        else:
            logger.error(f"❌ Erro na API: {response.status_code}")
            logger.error(f"📤 Resposta: {response.text}")
            
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout na requisição à API")
    except requests.exceptions.ConnectionError:
        logger.error("❌ Erro de conexão com a VPS")
    except Exception as e:
        logger.error(f"❌ Erro na requisição: {e}")

def monitor_sync_progress():
    """
    Monitorar o progresso da sincronização
    """
    logger.info("🔍 Monitorando progresso da sincronização...")
    
    max_attempts = 60  # 5 minutos com checks a cada 5s
    attempt = 0
    
    while attempt < max_attempts:
        try:
            status_url = f"{VPS_BASE_URL}/api/sync/status"
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success') and result.get('status'):
                    status = result['status']
                    current_status = status.get('current_status', 'unknown')
                    progress = status.get('progress', 0)
                    operation = status.get('current_operation', '-')
                    
                    logger.info(f"📊 Status: {current_status} | Progresso: {progress}% | Operação: {operation}")
                    
                    # Verificar se terminou
                    if current_status in ['completed', 'failed']:
                        if current_status == 'completed':
                            logger.info("✅ Sincronização concluída com sucesso!")
                            if 'results' in status:
                                logger.info(f"🎯 Resultados: {json.dumps(status['results'], indent=2)}")
                        else:
                            logger.error("❌ Sincronização falhou!")
                        break
                        
                    elif current_status == 'idle':
                        logger.info("ℹ️ Sistema em estado idle")
                        
                else:
                    logger.warning("⚠️ Resposta de status inválida")
                    
            else:
                logger.warning(f"⚠️ Erro ao verificar status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao monitorar progresso: {e}")
            
        time.sleep(5)  # Aguardar 5 segundos antes da próxima verificação
        attempt += 1
    
    if attempt >= max_attempts:
        logger.warning("⚠️ Timeout no monitoramento - processo pode ainda estar rodando")

def check_api_status():
    """
    Verificar se a API da VPS está respondendo
    """
    logger.info("🔍 Verificando status da API...")
    
    try:
        # Endpoint de status baseado no JavaScript
        status_url = f"{VPS_BASE_URL}/api/sync/status"
        
        response = requests.get(status_url, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ API está online!")
            result = response.json()
            logger.info(f"📤 Status: {json.dumps(result, indent=2)}")
        else:
            logger.warning(f"⚠️ API retornou status {response.status_code}")
            logger.warning(f"Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Não foi possível conectar à API da VPS")
    except Exception as e:
        logger.error(f"❌ Erro ao verificar API: {e}")

def list_sync_groups():
    """
    Listar grupos de sincronização disponíveis
    """
    logger.info("📋 Listando grupos de sincronização...")
    
    try:
        # Endpoint baseado no JavaScript
        groups_url = f"{VPS_BASE_URL}/api/groups"
        
        response = requests.get(groups_url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            groups = result.get('groups', [])
            logger.info("✅ Grupos encontrados:")
            for group in groups:
                logger.info(f"  📁 {group['name']} (ID: {group['id']})")
                if 'master_account' in group and group['master_account']:
                    logger.info(f"     Master: {group['master_account'].get('subdomain', 'N/A')}")
                else:
                    logger.info(f"     Master: N/A")
                slave_count = len(group.get('slave_accounts', []))
                logger.info(f"     Slaves: {slave_count}")
        else:
            logger.error(f"❌ Erro ao listar grupos: {response.status_code}")
            logger.error(f"Resposta: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Erro ao listar grupos: {e}")

def trigger_group_sync(group_id=None):
    """
    Disparar sincronização de um grupo específico
    """
    if not group_id:
        # Primeiro listar os grupos para o usuário escolher
        list_sync_groups()
        return
    
    logger.info(f"🚀 DISPARANDO SINCRONIZAÇÃO DO GRUPO {group_id}...")
    
    try:
        # Endpoint para sincronização de grupo baseado no JavaScript
        sync_url = f"{VPS_BASE_URL}/api/groups/{group_id}/sync"
        
        # Dados para a sincronização
        sync_data = {
            "sync_type": "full",
            "batch_config": {
                "batch_size": 10,
                "batch_delay": 2.0,
                "max_concurrent": 3
            }
        }
        
        logger.info(f"📡 Fazendo requisição para: {sync_url}")
        logger.info(f"📦 Dados: {sync_data}")
        
        # Fazer requisição POST
        response = requests.post(
            sync_url,
            json=sync_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=300  # 5 minutos
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Sincronização do grupo disparada com sucesso!")
            logger.info(f"📤 Resultado: {json.dumps(result, indent=2)}")
            
            # Monitorar o progresso
            monitor_sync_progress()
            
        else:
            logger.error(f"❌ Erro na API: {response.status_code}")
            logger.error(f"📤 Resposta: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Interagir com API da VPS")
    parser.add_argument("--status", action="store_true", help="Verificar status da API")
    parser.add_argument("--sync", action="store_true", help="Executar sincronização geral")
    parser.add_argument("--groups", action="store_true", help="Listar grupos")
    parser.add_argument("--group-sync", type=int, help="Sincronizar grupo específico (informar ID)")
    
    args = parser.parse_args()
    
    if args.status:
        check_api_status()
    elif args.groups:
        list_sync_groups()
    elif args.group_sync:
        trigger_group_sync(args.group_sync)
    elif args.sync:
        trigger_sync_via_api()
    else:
        # Por padrão, verificar status e listar grupos
        check_api_status()
        time.sleep(2)
        list_sync_groups()
        time.sleep(1)
        print("\n" + "="*50)
        print("💡 Para sincronizar um grupo específico, use:")
        print("   python sync_api_client.py --group-sync <ID_DO_GRUPO>")
        print("💡 Para sincronização geral, use:")
        print("   python sync_api_client.py --sync")
        print("="*50)
