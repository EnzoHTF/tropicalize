# Tropicalize — como colocar no ar

```
backend/   API em Python (FastAPI) + rotinas agendadas → Modal
web/       Site, blog, PWA e apps iOS/Android (Next.js + Capacitor) → Vercel
```

Os arquivos antigos (`app.py`, `modal_app.py` e `requirements.txt` na raiz, `static/`, `chroma_db/`) são do protótipo em Gradio e não são usados pela nova versão. Podem ser arquivados depois que a nova estiver no ar.

## 1. Contas e chaves

| Serviço | Para quê | Variável |
|---|---|---|
| Supabase | Banco Postgres + login | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` |
| Anthropic | Claude (relatórios, notícias, pesquisa) | `ANTHROPIC_API_KEY` |
| Google AI Studio | Embeddings `gemini-embedding-2` | `GEMINI_API_KEY` |
| NUVC | Ferramentas de VC via MCP | `NUVC_API_KEY` |
| Apify | Coleta do F6S | `APIFY_TOKEN` |
| Firebase (opcional) | Push nos apps nativos | `FIREBASE_CREDENCIAIS_JSON` |
| Make/Zapier/n8n (opcional) | Publicar nas redes | `WEBHOOK_REDES_SOCIAIS` |

## 2. Banco

1. Crie o projeto no Supabase (região São Paulo).
2. No SQL Editor, rode `backend/sql/schema.sql`.
3. Em Authentication: ative o login por e-mail (link mágico) e, se quiser, o Google. Em URL Configuration, cadastre a URL do site e `https://SEU-SITE/app`.

## 3. Backend

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate      # no Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                               # preencha as chaves

# Carga inicial
python -m tropicalize.ingest sementes                # 60 fundos/aceleradoras/editais + 54 ferramentas
python -m tropicalize.ingest yc ../all.json          # 6.267 startups da YC
python -m tropicalize.ingest f6s                     # F6S via Apify (cobra por registro, ~US$ 1 a cada 1.000)
python -m tropicalize.ingest enriquecer 100          # pesquisa na web: tese, ticket, prazos, links
python -m tropicalize.ingest noticias                # primeira coleta do blog

# Rodar localmente
python rodar_local.py                                # http://localhost:8000
```

No Windows, as ferramentas do NUVC ficam desligadas ao rodar localmente, por uma limitação do Windows com subprocessos. No Modal (Linux) elas funcionam.

Deploy:

```bash
pip install modal && modal setup
modal secret create tropicalize --from-dotenv .env
modal deploy modal_app.py
```

O Modal publica a API e agenda as rotinas: notícias a cada 3 h, alertas de prazo às 9 h, newsletter na segunda e atualização dos diretórios (F6S + enriquecimento) no domingo.

## 4. Site e PWA

```bash
cd web
npm install
copy .env.example .env.local    # aponte NEXT_PUBLIC_API_URL para a URL do Modal
npm run dev                     # http://localhost:3000
```

Deploy na Vercel: importe a pasta `web/` e configure as mesmas variáveis `NEXT_PUBLIC_*`. Depois, inclua o domínio do site em `ORIGENS_PERMITIDAS` e `SITE_URL` no backend.

Para o push na PWA, gere as chaves com `npx web-push generate-vapid-keys` e preencha `VAPID_*` no backend. No iPhone e no iPad, o push da PWA só funciona depois de "Adicionar à Tela de Início".

## 5. Apps iOS, iPadOS e Android

Os apps abrem o site publicado (`CAP_SERVER_URL`), com push e compartilhamento nativos.

```bash
cd web
npx cap add android && npx cap sync android && npx cap open android   # Android Studio
npx cap add ios && npx cap sync ios && npx cap open ios               # Xcode, exige um Mac
```

- Push nativo: crie um projeto no Firebase, adicione os apps (`app.tropicalize`), coloque `google-services.json` em `android/app/` e configure a chave APNs no Firebase para o iOS.
- Ícones das lojas: `public/icones/icone-1024.png` (gere todos os tamanhos com `npx @capacitor/assets generate`).
- Apple: apps que são só um site embrulhado costumam ser recusados (diretriz 4.2). O app já tem push nativo de prazos e compartilhamento nativo. Destaque isso na revisão.
- O login com Google não funciona dentro de apps (o Google bloqueia webviews). Por isso, no app aparece só o link por e-mail.

## 6. Rotina de conteúdo

1. As notícias chegam como rascunho em `/admin` (acesso pelos e-mails de `ADMIN_EMAILS`).
2. Você revisa, edita os textos das redes e clica em Publicar: a notícia vai para o blog e os posts seguem para o webhook das redes.
3. Toda segunda sai um rascunho da newsletter em `/admin`, pronto para colar na ferramenta de e-mail.
