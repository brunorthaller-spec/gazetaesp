# Gazeta Esportiva RSS — Railway Deploy

Feed RSS sempre atualizado da Gazeta Esportiva via WP REST API.

## Endpoints
- `/` ou `/rss` ou `/feed` → Feed RSS (50 posts mais recentes)
- `/health` → Status do servidor

## Deploy no Railway (grátis, sempre ativo)

1. Acesse https://railway.app e crie conta (Google ou GitHub)
2. Clique em "New Project" → "Deploy from GitHub repo"
3. Suba estes arquivos num repositório GitHub e conecte
4. O Railway detecta o Procfile automaticamente
5. Vá em Settings → Networking → Generate Domain
6. Copie a URL (ex: https://gazeta-rss.up.railway.app/rss)
7. Cole no seu app Android como fonte RSS ✅

## Vantagens vs Render
- Servidor NUNCA dorme
- Resposta instantânea
- 500 horas grátis/mês

## Uso local
pip install -r requirements.txt
python app.py
# Acesse: http://localhost:10000/rss
