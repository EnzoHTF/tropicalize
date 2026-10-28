"""Configuração lida das variáveis de ambiente (veja .env.example)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _lista(nome: str) -> list[str]:
    return [v.strip().lower() for v in os.environ.get(nome, "").split(",") if v.strip()]


DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Claude: o modelo mais capaz faz os relatórios; um modelo rápido cuida das tarefas leves
# (resumir notícias, extrair campos, textos para redes sociais).
MODELO_PROFUNDO = os.environ.get("MODELO_PROFUNDO", "claude-fable-5-1")
MODELO_RAPIDO = os.environ.get("MODELO_RAPIDO", "claude-haiku-5-5")
# Pesquisa em lote na web (enriquecer fundos/aceleradoras): precisa da busca na web nova
MODELO_PESQUISA = os.environ.get("MODELO_PESQUISA", "claude-sonnet-5-5")
ESFORCO_RELATORIO = os.environ.get("ESFORCO_RELATORIO", "high")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODELO_EMBEDDING = os.environ.get("MODELO_EMBEDDING", "gemini-embedding-2")
DIMENSOES_EMBEDDING = 768

NUVC_API_KEY = os.environ.get("NUVC_API_KEY", "")
# Comando que sobe o servidor MCP do NUVC via stdio. Na imagem do Modal o pacote já vem
# instalado globalmente; localmente "npx -y nuvc-mcp" também funciona.
NUVC_COMANDO = os.environ.get("NUVC_COMANDO", "nuvc-mcp")

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
APIFY_ATOR_F6S = os.environ.get("APIFY_ATOR_F6S", "jungle_synthesizer/f6s-accelerator-scraper")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

ADMIN_EMAILS = _lista("ADMIN_EMAILS")
ORIGENS_PERMITIDAS = [o.strip() for o in os.environ.get(
    "ORIGENS_PERMITIDAS", "http://localhost:3000,capacitor://localhost,https://localhost"
).split(",") if o.strip()]

# Análises por mês em cada plano
COTA_MENSAL = {"gratis": int(os.environ.get("COTA_GRATIS", "5")),
               "pro": int(os.environ.get("COTA_PRO", "100")),
               "admin": 10_000}

# Push: web push (PWA) com VAPID e FCM para os apps nativos (Capacitor)
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_CONTATO = os.environ.get("VAPID_CONTATO", "mailto:contato@tropicalize.app")
FIREBASE_CREDENCIAIS_JSON = os.environ.get("FIREBASE_CREDENCIAIS_JSON", "")

# Publicação nas redes: um webhook (Make, Zapier, n8n, Buffer...) recebe cada post aprovado
WEBHOOK_REDES_SOCIAIS = os.environ.get("WEBHOOK_REDES_SOCIAIS", "")
SITE_URL = os.environ.get("SITE_URL", "http://localhost:3000").rstrip("/")
