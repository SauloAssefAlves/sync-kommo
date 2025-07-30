# Sistema de Sincronização Kommo

Sistema completo para sincronizar configurações de funis e campos personalizados entre múltiplas contas Kommo.

## 🎯 Objetivo

Manter a consistência das configurações de funis de vendas (pipelines) e campos personalizados (custom fields) entre 120 contas Kommo, garantindo que qualquer alteração na conta mestre seja automaticamente replicada para todas as contas escravas.

## ✨ Funcionalidades

- 🔄 **Sincronização Automática**: Funis, estágios e campos personalizados
- 🎛️ **Interface Web**: Dashboard intuitivo para gerenciamento
- 🔗 **Webhook Integration**: Acionamento via Salesbot
- 📊 **Monitoramento**: Logs detalhados e status em tempo real
- 🔐 **OAuth 2.0**: Autenticação segura com a API do Kommo
- ⚡ **Rate Limiting**: Tratamento inteligente de limites da API

## 🚀 Início Rápido

### Pré-requisitos
- Python 3.11+
- Tokens OAuth 2.0 das contas Kommo

### Instalação

1. **Ativar ambiente virtual**
   ```bash
   source venv/bin/activate
   ```

2. **Instalar dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Iniciar servidor**
   ```bash
   python src/main.py
   ```

4. **Acessar interface**
   ```
   http://localhost:5000
   ```

## 📋 Configuração

### 1. Adicionar Conta Mestre
- Acesse a interface web
- Clique em "Adicionar Conta"
- Marque como "Conta Mestre"
- Insira credenciais OAuth 2.0

### 2. Adicionar Contas Escravas
- Repita o processo para as 119 contas restantes
- Marque como "Conta Escrava"

### 3. Configurar Webhook (Opcional)
- URL do webhook: `http://seu-servidor:5000/api/sync/webhook`
- Configure no Salesbot para acionamento automático

## 🔧 Uso

### Interface Web
- **Dashboard**: Status do sistema e métricas
- **Sincronização**: Botões para acionamento manual
- **Logs**: Histórico de operações
- **Contas**: Gerenciamento de contas Kommo

### API REST

#### Acionar Sincronização
```bash
curl -X POST http://localhost:5000/api/sync/trigger \
  -H "Content-Type: application/json" \
  -d '{"sync_type": "full"}'
```

#### Verificar Status
```bash
curl http://localhost:5000/api/sync/status
```

### Tipos de Sincronização
- `full`: Funis + Campos Personalizados
- `pipelines`: Apenas funis e estágios
- `custom_fields`: Apenas campos personalizados

## 📁 Estrutura do Projeto

```
kommo-sync-system/
├── src/
│   ├── models/          # Modelos de dados
│   ├── routes/          # Rotas da API
│   ├── services/        # Lógica de negócio
│   ├── static/          # Interface web
│   └── main.py          # Aplicação principal
├── venv/                # Ambiente virtual
├── requirements.txt     # Dependências
└── exemplo_uso.py       # Script de exemplo
```

## 🔄 Fluxo de Sincronização

1. **Extração**: Configurações da conta mestre
2. **Processamento**: Normalização e validação
3. **Replicação**: Aplicação nas contas escravas
4. **Mapeamento**: IDs entre contas
5. **Log**: Registro de resultados

## 🛡️ Segurança

- Tokens OAuth 2.0 armazenados localmente
- Comunicação HTTPS com API do Kommo
- Validação de dados de entrada
- Logs sem informações sensíveis

## 📊 Monitoramento

### Métricas Disponíveis
- Total de contas cadastradas
- Status da última sincronização
- Taxa de sucesso por conta
- Histórico de operações

### Logs
- Sincronizações bem-sucedidas
- Falhas e erros detalhados
- Timestamps de operações
- Contas processadas/falhadas

## ⚠️ Limitações

- Máximo 50 funis por conta (Kommo)
- Máximo 100 estágios por funil (Kommo)
- Renovação manual de tokens OAuth 2.0
- Rate limiting da API do Kommo

## 🔧 Troubleshooting

### Problemas Comuns

**Token Expirado**
- Renovar tokens OAuth 2.0 nas contas
- Verificar data de expiração

**Rate Limit Atingido**
- Sistema implementa backoff automático
- Aguardar e tentar novamente

**Falha de Conexão**
- Verificar conectividade com internet
- Validar credenciais da conta

## 🚀 Próximos Passos

- [ ] Renovação automática de tokens
- [ ] Sincronização bidirecional
- [ ] Notificações por email/Slack
- [ ] Interface de administração avançada
- [ ] Processamento paralelo otimizado

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar logs na interface web
2. Consultar documentação completa
3. Executar script de exemplo

## 📄 Licença

Este projeto foi desenvolvido para uso interno e gerenciamento de contas Kommo.

---

**Desenvolvido por:** Manus AI  
**Versão:** 1.0  
**Data:** Julho 2025

