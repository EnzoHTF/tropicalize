"""Embeddings multilíngues com o Gemini (gemini-embedding-2).

O gemini-embedding-2 não usa task_type: a tarefa vai no próprio texto. Consultas e
documentos usam formatos diferentes, então mantenha estas funções como única porta
de entrada para gerar vetores (trocar o formato exige reprocessar a base inteira).
"""
import asyncio

from google import genai
from google.genai import errors, types

from . import config

_cliente: genai.Client | None = None
LOTE = 50


def _client() -> genai.Client:
    global _cliente
    if _cliente is None:
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY não configurada")
        _cliente = genai.Client(api_key=config.GEMINI_API_KEY)
    return _cliente


def texto_documento(titulo: str, texto: str) -> str:
    return f"title: {titulo or 'none'} | text: {texto}"


def texto_consulta(texto: str) -> str:
    return f"task: search result | query: {texto}"


async def _embed(textos: list[str]) -> list[list[float]]:
    conteudos = [types.Content(parts=[types.Part.from_text(text=t)]) for t in textos]
    for tentativa in range(5):
        try:
            res = await _client().aio.models.embed_content(
                model=config.MODELO_EMBEDDING,
                contents=conteudos,
                config=types.EmbedContentConfig(output_dimensionality=config.DIMENSOES_EMBEDDING),
            )
            return [e.values for e in res.embeddings]
        except errors.APIError as e:
            # 429/5xx: espera e tenta de novo; o resto é erro de verdade
            if e.code not in (429, 500, 502, 503, 504) or tentativa == 4:
                raise
            await asyncio.sleep(2 ** tentativa * 2)
    raise RuntimeError("inalcançável")


async def embed_consulta(texto: str) -> list[float]:
    return (await _embed([texto_consulta(texto)]))[0]


async def embed_documentos(pares: list[tuple[str, str]]) -> list[list[float]]:
    """Recebe (título, texto) e devolve um vetor por item, em lotes."""
    vetores: list[list[float]] = []
    for i in range(0, len(pares), LOTE):
        lote = [texto_documento(t, x) for t, x in pares[i:i + LOTE]]
        vetores.extend(await _embed(lote))
    return vetores
