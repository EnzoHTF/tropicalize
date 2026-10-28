"""Os 4 modos do Tropicalize: entrada (formulário), contexto recuperado e instruções.

Cada modo monta um prompt com dados da nossa base (startups, investidores, ferramentas)
e o modelo só pode citar o que veio da base ou da busca na web, com link.
"""
import json
import os
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from . import busca

TAXA_USD_BRL = float(os.environ.get("TAXA_USD_BRL", "5.5"))

Faixa = Literal["ate_5k", "5k_50k", "acima_50k"]
Estagio = Literal["ideia", "pre_seed", "seed", "series_a", "series_b", "growth"]

NOMES_FAIXA = {"ate_5k": "até R$ 5 mil", "5k_50k": "de R$ 5 mil a R$ 50 mil", "acima_50k": "acima de R$ 50 mil"}

# Países como estão gravados na base (nomes em inglês, como no F6S)
PAISES = {"brasil": "Brazil", "brazil": "Brazil", "eua": "United States", "estados unidos": "United States",
          "portugal": "Portugal", "mexico": "Mexico", "méxico": "Mexico", "argentina": "Argentina",
          "chile": "Chile", "colombia": "Colombia", "colômbia": "Colombia", "reino unido": "United Kingdom",
          "alemanha": "Germany", "espanha": "Spain", "franca": "France", "frança": "France", "canada": "Canada",
          "canadá": "Canada", "israel": "Israel", "singapura": "Singapore", "global": "Global"}
REGIAO_LATAM = "Latin America"


class EntradaDescobrir(BaseModel):
    tema: str = Field(min_length=3, max_length=500)
    perfil: str = Field("", max_length=1000, description="Experiência, habilidades e interesses")
    faixa_investimento: Faixa = "ate_5k"
    cidade: str = Field("", max_length=100)


class EntradaDiagnosticar(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    descricao: str = Field(min_length=10, max_length=2000)
    setor: str = Field("", max_length=100)
    funcionarios: int | None = Field(None, ge=0)
    faturamento_anual_brl: float | None = Field(None, ge=0)
    cidade: str = Field("", max_length=100)
    processos: str = Field("", max_length=2000, description="Como a empresa opera hoje")
    dores: str = Field(min_length=3, max_length=2000)
    objetivos: str = Field("", max_length=1000)


class EntradaValidar(BaseModel):
    ideia: str = Field(min_length=10, max_length=3000)
    publico_alvo: str = Field("", max_length=500)
    diferencial: str = Field("", max_length=1000)
    ja_tem: str = Field("", max_length=1000, description="O que já está pronto: MVP, clientes, equipe...")
    faixa_investimento: Faixa = "ate_5k"
    cidade: str = Field("", max_length=100)


class EntradaCaptar(BaseModel):
    descricao: str = Field(min_length=10, max_length=3000)
    setor: str = Field("", max_length=100)
    estagio: Estagio = "pre_seed"
    captacao_alvo_brl: float | None = Field(None, ge=0)
    cidade: str = Field("", max_length=100)
    paises_interesse: list[str] = Field(default_factory=lambda: ["Brasil"], max_length=10)
    tracao: str = Field("", max_length=1500, description="Receita, usuários, crescimento")
    aceita_nao_diluitivo: bool = True
    relatorio_origem_id: int | None = None


ENTRADAS = {"descobrir": EntradaDescobrir, "diagnosticar": EntradaDiagnosticar,
            "validar": EntradaValidar, "captar": EntradaCaptar}


SISTEMA_BASE = """Você é o Tropicalize, um analista de negócios brasileiro especializado em \
importar e adaptar ao Brasil modelos que já deram certo lá fora, validar ideias e conectar \
empreendedores a capital.

Regras que valem sempre:
- Escreva em português do Brasil, direto e prático, sem floreio. Use markdown com títulos ##.
- Só cite startups, fundos, aceleradoras e ferramentas que estejam nos dados fornecidos ou que \
você encontrou na busca na web. Nunca invente nomes, números ou links.
- Ao trazer um dado de mercado, concorrente ou notícia da web, cite a fonte com link markdown.
- Se os dados não bastarem para uma conclusão, diga isso e explique o que falta.
- Valores em reais (R$). Considere a realidade brasileira: regulação, impostos, Pix, canais de \
venda, poder de compra e diferenças regionais.
- Quando houver ferramentas do NUVC disponíveis, use-as onde agregam: nuvc_score e nuvc_roast \
para avaliar a ideia com olhar de investidor, nuvc_analyze para mercado/concorrência, \
nuvc_venture_math para métricas e nuvc_match_investors para investidores. Os textos enviados \
ao NUVC devem estar em inglês. Traduza e resuma em português o que voltar.
- Data de hoje: {hoje}."""

INSTRUCOES = {
    "descobrir": """Modo DESCOBRIR IDEIA. O usuário quer empreender e procura uma oportunidade.
Estrutura do relatório:
## O que funciona lá fora
## O que já existe no Brasil (pesquise na web os concorrentes brasileiros atuais)
## Oportunidades para o Brasil (2 a 4 ideias concretas, cada uma com público, proposta de valor \
e por que agora)
## Como começar com {faixa} (primeiros 30/60/90 dias)
## Hipóteses para validar antes de investir
## Riscos e diferenças culturais/regulatórias""",

    "diagnosticar": """Modo DIAGNOSTICAR EMPRESA. O usuário já tem uma empresa e quer achar \
gargalos e melhorias.
Estrutura do relatório:
## Diagnóstico (principais gargalos, do mais ao menos crítico, ligados às dores relatadas)
## Benchmarks: o que empresas de fora e do Brasil fizeram em situações parecidas (use as \
startups fornecidas e a busca na web; cite casos reais)
## Melhorias e inovações priorizadas (tabela: ação, impacto, esforço, custo estimado, prazo)
## Indicadores para acompanhar
## Próximos passos nas próximas 4 semanas""",

    "validar": """Modo VALIDAR E VIABILIZAR. O usuário tem uma ideia e quer saber o potencial \
e como construí-la na prática com o orçamento de {faixa}.
Estrutura do relatório:
## Veredito (nota de 0 a 10 e resumo em 3 linhas)
## Mercado no Brasil (tamanho estimado com fontes, tendências, público)
## Concorrentes e referências (Brasil e exterior)
## Pontos fortes e pontos fracos
## Como construir na prática (etapas do MVP ao lançamento)
## Ferramentas necessárias (tabela: etapa, ferramenta, para quê, custo). Use SOMENTE ferramentas \
do catálogo fornecido; se faltar uma categoria, diga que o catálogo não cobre.
## Orçamento estimado dentro de {faixa}
## Como validar antes de gastar (experimentos baratos e métricas de sucesso)""",

    "captar": """Modo CAPTAR INVESTIMENTO. Recomende fundos de venture capital, aceleradoras e \
programas para o usuário se inscrever.
Estrutura do relatório:
## Prontidão para captar (o que um investidor vai perguntar e o que falta)
## Melhores opções (as 5 a 10 mais aderentes da lista de candidatos, da mais à menos aderente). \
Para cada uma: nome em negrito seguido do código [#id] exato da lista, tipo, por que combina, \
ticket/condições, prazo de inscrição e link de inscrição ou site.
## Outras opções sugeridas pelo NUVC (se usar nuvc_match_investors; deixe claro que não estão \
na nossa base verificada)
## Capital não diluitivo (subvenções e editais), se fizer sentido
## Como se preparar para a inscrição (pitch, métricas, documentos)
Só recomende da lista de candidatos o que realmente tiver aderência. Se nenhum servir, diga.""",
}


def _bloco(titulo: str, dados) -> str:
    return f"<{titulo}>\n{json.dumps(dados, ensure_ascii=False, default=str, indent=1)}\n</{titulo}>"


def _resumo_startup(s: dict) -> dict:
    return {k: s[k] for k in ("nome", "descricao", "setores", "paises", "lote", "status", "site") if s.get(k)}


def _resumo_investidor(i: dict) -> dict:
    campos = ("id", "tipo", "nome", "tese", "setores", "estagios", "paises", "cidade", "ticket_texto",
              "equity_texto", "nao_diluitivo", "site", "url_inscricao", "inscricao_fecha",
              "inscricao_texto", "verificado")
    return {k: i[k] for k in campos if i.get(k) not in (None, "", [])}


def sistema(modo: str, entrada: BaseModel) -> str:
    faixa = NOMES_FAIXA.get(getattr(entrada, "faixa_investimento", ""), "")
    return (SISTEMA_BASE.format(hoje=date.today().isoformat()) + "\n\n"
            + INSTRUCOES[modo].format(faixa=faixa or "o orçamento informado"))


def paises_busca(nomes: list[str]) -> list[str]:
    paises = {PAISES.get(n.strip().lower(), n.strip()) for n in nomes if n.strip()}
    if paises & {"Brazil", "Mexico", "Argentina", "Chile", "Colombia"}:
        paises.add(REGIAO_LATAM)
    return sorted(paises)


async def montar_mensagem(modo: str, entrada: BaseModel, relatorio_origem: str | None = None
                          ) -> tuple[str, dict]:
    """Devolve a mensagem do usuário com o contexto recuperado e um extra por modo
    (no modo captar, os candidatos usados para validar as recomendações)."""
    extra: dict = {}
    partes = [_bloco("pedido_do_usuario", entrada.model_dump(exclude_none=True))]

    if modo == "descobrir":
        startups = await busca.startups_parecidas(f"{entrada.tema}. {entrada.perfil}", 12, fora_do_brasil=True)
        partes.append(_bloco("startups_de_fora_parecidas", [_resumo_startup(s) for s in startups]))

    elif modo == "diagnosticar":
        consulta = f"{entrada.descricao}. Problemas: {entrada.dores}. {entrada.objetivos}"
        startups = await busca.startups_parecidas(consulta, 12)
        partes.append(_bloco("startups_que_resolvem_problemas_parecidos", [_resumo_startup(s) for s in startups]))

    elif modo == "validar":
        consulta = f"{entrada.ideia}. {entrada.publico_alvo}. {entrada.diferencial}"
        startups = await busca.startups_parecidas(consulta, 10)
        ferramentas = await busca.ferramentas_ate(entrada.faixa_investimento)
        partes.append(_bloco("startups_parecidas", [_resumo_startup(s) for s in startups]))
        partes.append(_bloco("catalogo_de_ferramentas", ferramentas))

    elif modo == "captar":
        consulta = f"{entrada.setor}. {entrada.descricao}. {entrada.tracao}"
        if relatorio_origem:
            consulta += f" {relatorio_origem[:1500]}"
        tipos = None if entrada.aceita_nao_diluitivo else [
            "fundo_vc", "aceleradora", "incubadora", "anjos", "corporativo", "programa"]
        captacao_usd = entrada.captacao_alvo_brl / TAXA_USD_BRL if entrada.captacao_alvo_brl else None
        candidatos = await busca.investidores_compativeis(
            consulta,
            paises=paises_busca(entrada.paises_interesse),
            estagio=None if entrada.estagio == "ideia" else entrada.estagio,
            captacao_usd=captacao_usd,
            tipos=tipos,
            limite=40,
        )
        extra["candidatos"] = {c["id"]: c for c in candidatos}
        partes.append(_bloco("candidatos_da_base", [_resumo_investidor(c) for c in candidatos]))
        if captacao_usd:
            partes.append(f"Captação desejada: R$ {entrada.captacao_alvo_brl:,.0f} (~US$ {captacao_usd:,.0f}).")

    if relatorio_origem:
        partes.append(_bloco("relatorio_anterior_do_usuario", relatorio_origem[:6000]))

    partes.append("Escreva o relatório agora, seguindo a estrutura pedida.")
    return "\n\n".join(partes), extra


def titulo(modo: str, entrada: BaseModel) -> str:
    base = {"descobrir": entrada.__dict__.get("tema"), "diagnosticar": entrada.__dict__.get("nome"),
            "validar": entrada.__dict__.get("ideia"), "captar": entrada.__dict__.get("descricao")}[modo]
    rotulo = {"descobrir": "Ideias", "diagnosticar": "Diagnóstico", "validar": "Validação", "captar": "Captação"}[modo]
    base = " ".join((base or "").split())
    return f"{rotulo}: {base[:80]}{'…' if len(base) > 80 else ''}"


class Recomendacao(BaseModel):
    investidor_id: int
    aderencia: int = Field(description="0 a 100")
    motivo: str = Field(description="Uma frase em português explicando a aderência")


class Recomendacoes(BaseModel):
    recomendacoes: list[Recomendacao]


INSTRUCAO_EXTRAIR = """Liste cada fundo/aceleradora/programa recomendado no relatório abaixo que \
tenha um código [#id]. Use o número do código como investidor_id, a aderência de 0 a 100 \
coerente com a ordem do relatório e o motivo em uma frase. Ignore opções sem código [#id]."""
