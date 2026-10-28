-- Esquema do Tropicalize (Postgres + pgvector, ex.: Supabase).
-- Rode uma vez no SQL Editor do Supabase ou com: psql "$DATABASE_URL" -f sql/schema.sql
-- Os embeddings são gerados pelo gemini-embedding-2 com 768 dimensões (já normalizados).

create extension if not exists vector;

-- Startups usadas como benchmark (YC, F6S, fontes brasileiras...)
create table if not exists startups (
    id            bigserial primary key,
    fonte         text not null,                 -- 'yc', 'f6s', 'startupbase', ...
    fonte_id      text not null,
    nome          text not null,
    descricao     text not null,
    descricao_longa text,
    setores       text[] not null default '{}',
    tags          text[] not null default '{}',
    paises        text[] not null default '{}',
    estagio       text,
    status        text,
    lote          text,                          -- ex.: 'Winter 2012' na YC
    site          text,
    url_fonte     text,
    embedding     vector(768),
    atualizado_em timestamptz not null default now(),
    unique (fonte, fonte_id)
);
create index if not exists startups_embedding_idx on startups using hnsw (embedding vector_cosine_ops);
create index if not exists startups_setores_idx on startups using gin (setores);

-- Fundos de VC, aceleradoras, incubadoras, anjos, programas corporativos e de governo
create table if not exists investidores (
    id               bigserial primary key,
    fonte            text not null,              -- 'semente', 'f6s', 'nuvc', ...
    fonte_id         text not null,
    tipo             text not null check (tipo in
                       ('fundo_vc','aceleradora','incubadora','anjos','corporativo','governo','programa')),
    nome             text not null,
    tese             text,                       -- descrição da tese / foco
    setores          text[] not null default '{}',
    estagios         text[] not null default '{}',  -- pre_seed, seed, series_a, series_b, growth
    paises           text[] not null default '{}',  -- onde investe
    cidade           text,
    ticket_min_usd   numeric,
    ticket_max_usd   numeric,
    ticket_texto     text,                       -- valor original, ex.: '$100k' ou 'R$ 500 mil'
    equity_texto     text,
    nao_diluitivo    boolean not null default false,  -- subvenção/bolsa (FAPESP, Finep...)
    site             text,
    url_inscricao    text,
    inscricao_abre   date,
    inscricao_fecha  date,
    inscricao_texto  text,
    url_fonte        text,
    verificado       boolean not null default false,  -- dados confirmados (manual ou enriquecimento)
    embedding        vector(768),
    atualizado_em    timestamptz not null default now(),
    unique (fonte, fonte_id)
);
create index if not exists investidores_embedding_idx on investidores using hnsw (embedding vector_cosine_ops);
create index if not exists investidores_paises_idx on investidores using gin (paises);
create index if not exists investidores_estagios_idx on investidores using gin (estagios);
create index if not exists investidores_fecha_idx on investidores (inscricao_fecha);

-- Catálogo curado de ferramentas para o plano de construção (a IA escolhe só daqui)
create table if not exists ferramentas (
    id             bigserial primary key,
    nome           text not null unique,
    categoria      text not null,                -- 'site', 'pagamentos', 'crm', 'no-code', ...
    descricao      text not null,
    preco_texto    text,                         -- ex.: 'Grátis até 1k usuários; US$ 25/mês'
    faixa          text not null check (faixa in ('ate_5k','5k_50k','acima_50k')),
    site           text,
    link_afiliado  text,
    atualizado_em  timestamptz not null default now()
);

-- Usuários vêm do Supabase Auth (auth.users). Aqui só o que é nosso.
create table if not exists perfis (
    usuario_id    uuid primary key,
    email         text,
    plano         text not null default 'gratis' check (plano in ('gratis','pro','admin')),
    criado_em     timestamptz not null default now()
);

-- Empresa ou ideia do usuário (usada no diagnóstico, validação e captação)
create table if not exists empresas (
    id            bigserial primary key,
    usuario_id    uuid not null,
    nome          text not null,
    descricao     text not null,
    setor         text,
    estagio       text,
    cidade        text,
    pais          text not null default 'Brasil',
    faturamento_anual_brl numeric,
    funcionarios  integer,
    captacao_alvo_brl numeric,
    dados         jsonb not null default '{}',   -- respostas extras do questionário
    criado_em     timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);
create index if not exists empresas_usuario_idx on empresas (usuario_id);

-- Relatórios gerados pelos 4 modos
create table if not exists relatorios (
    id            bigserial primary key,
    usuario_id    uuid not null,
    empresa_id    bigint references empresas(id) on delete set null,
    modo          text not null check (modo in ('descobrir','diagnosticar','validar','captar')),
    titulo        text not null,
    entrada       jsonb not null,
    conteudo      text not null default '',     -- markdown
    estruturado   jsonb,                         -- ex.: matches do modo captar
    fontes        jsonb not null default '[]',   -- links citados pela busca na web
    modelo        text,
    tokens_entrada integer,
    tokens_saida  integer,
    status        text not null default 'gerando' check (status in ('gerando','pronto','erro')),
    criado_em     timestamptz not null default now()
);
create index if not exists relatorios_usuario_idx on relatorios (usuario_id, criado_em desc);

-- Fundos/aceleradoras recomendados num relatório de captação (para alertas de prazo)
create table if not exists recomendacoes (
    relatorio_id   bigint not null references relatorios(id) on delete cascade,
    investidor_id  bigint not null references investidores(id) on delete cascade,
    usuario_id     uuid not null,
    aderencia      integer not null,             -- 0-100
    motivo         text not null,
    salvo          boolean not null default false,
    primary key (relatorio_id, investidor_id)
);
create index if not exists recomendacoes_usuario_idx on recomendacoes (usuario_id);

-- Inscrições de push (web push da PWA ou token FCM do app nativo)
create table if not exists push_inscricoes (
    id            bigserial primary key,
    usuario_id    uuid not null,
    plataforma    text not null check (plataforma in ('web','android','ios')),
    endpoint      text not null unique,          -- endpoint do web push ou token FCM
    chaves        jsonb,                         -- p256dh/auth do web push
    criado_em     timestamptz not null default now()
);

create table if not exists alertas_enviados (
    usuario_id    uuid not null,
    investidor_id bigint not null,
    tipo          text not null,                 -- 'prazo_7d', 'prazo_1d'
    enviado_em    timestamptz not null default now(),
    primary key (usuario_id, investidor_id, tipo)
);

-- Notícias do blog: coletadas por RSS, resumidas pela IA, aprovadas por um admin
create table if not exists noticias (
    id            bigserial primary key,
    slug          text not null unique,
    titulo        text not null,
    resumo        text not null,                 -- texto próprio (markdown), nunca a matéria copiada
    por_que_importa text,
    categoria     text not null check (categoria in ('brasil','mundo')),
    tags          text[] not null default '{}',
    fonte_nome    text not null,
    fonte_url     text not null unique,
    imagem_url    text,
    publicado_fonte_em timestamptz,
    status        text not null default 'rascunho' check (status in ('rascunho','publicado','descartado')),
    publicado_em  timestamptz,
    criado_em     timestamptz not null default now()
);
create index if not exists noticias_status_idx on noticias (status, publicado_em desc);

-- Textos prontos para cada rede social, gerados junto com a notícia
create table if not exists posts_sociais (
    id            bigserial primary key,
    noticia_id    bigint references noticias(id) on delete cascade,
    newsletter_semana date,                      -- preenchido quando o post é a newsletter semanal
    rede          text not null check (rede in ('instagram','linkedin','x','threads','newsletter')),
    texto         text not null,
    status        text not null default 'pendente' check (status in ('pendente','enviado','erro')),
    enviado_em    timestamptz,
    unique (noticia_id, rede),
    unique (newsletter_semana, rede)
);

-- Cota mensal de análises por usuário
create table if not exists uso_mensal (
    usuario_id    uuid not null,
    mes           date not null,                 -- primeiro dia do mês
    analises      integer not null default 0,
    primary key (usuario_id, mes)
);

-- O backend acessa o banco com a connection string de serviço; o app nunca lê as
-- tabelas direto pelo PostgREST, então RLS ligado sem políticas bloqueia o acesso anônimo.
alter table startups          enable row level security;
alter table investidores      enable row level security;
alter table ferramentas       enable row level security;
alter table perfis            enable row level security;
alter table empresas          enable row level security;
alter table relatorios        enable row level security;
alter table recomendacoes     enable row level security;
alter table push_inscricoes   enable row level security;
alter table alertas_enviados  enable row level security;
alter table noticias          enable row level security;
alter table posts_sociais     enable row level security;
alter table uso_mensal        enable row level security;
