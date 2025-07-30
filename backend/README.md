# Backend - Kommo Sync System

Backend Flask da aplicação Kommo Sync System.

## Configuração

1. Instalar dependências:

```bash
pip install -r requirements.txt
```

2. Configurar variáveis de ambiente:

```bash
# Opcional: configurar porta do Flask
export FLASK_PORT=5000
```

3. Executar o backend:

```bash
python src/main.py
```

## Estrutura

- `src/` - Código principal do Flask
- `src/models/` - Modelos do banco de dados
- `src/routes/` - Rotas da API
- `src/services/` - Serviços de sincronização
- `tests/` - Testes unitários

## API Endpoints

- `GET /api/sync/accounts` - Listar contas
- `POST /api/sync/account` - Adicionar conta
- `POST /api/sync/start` - Iniciar sincronização
- `GET /api/sync/logs` - Ver logs

## Para deploy na VPS

Este backend pode ser executado independentemente. Configure o reverse proxy (Nginx) para redirecionar as chamadas da API para esta aplicação.
