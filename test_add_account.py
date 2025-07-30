import requests
import json

# Testar a API de adicionar conta
url = "http://localhost:5000/api/sync/accounts"
data = {
    "subdomain": "test123",
    "refresh_token": "token123",
    "is_master": True
}

print(f"Enviando POST para {url}")
print(f"Dados: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.headers.get('content-type') and 'application/json' in response.headers.get('content-type'):
        try:
            print(f"JSON Response: {response.json()}")
        except:
            print("Resposta não é JSON válido")
    
except Exception as e:
    print(f"Erro: {e}")
