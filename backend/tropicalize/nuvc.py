"""Cliente do servidor MCP do NUVC (npm `nuvc-mcp`, transporte stdio).

O servidor roda como subprocesso do backend e fica aberto entre as requisições. As
ferramentas dele viram ferramentas do Claude: o modelo decide quando pontuar a ideia,
analisar mercado, fazer o "roast", calcular métricas ou cruzar com a base de 3.700+
investidores do NUVC.
"""
import asyncio
import logging
import os
import shlex

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from . import config

log = logging.getLogger(__name__)

# nuvc_set_mandate grava um "mandato" global no servidor, que vazaria de um usuário
# para outro num backend compartilhado. O nuvc_score já aceita o mandato por chamada.
BLOQUEADAS = set(filter(None, os.environ.get(
    "NUVC_FERRAMENTAS_BLOQUEADAS", "nuvc_set_mandate,nuvc_get_mandate").split(",")))
TIMEOUT_CHAMADA = 120
TIMEOUT_INICIO = 60


class ClienteNuvc:
    """Uma tarefa dona mantém o contexto stdio/sessão aberto (o anyio exige que o
    contexto seja aberto e fechado na mesma tarefa); as chamadas usam a sessão dela."""

    def __init__(self):
        self._tarefa: asyncio.Task | None = None
        self._sessao: ClientSession | None = None
        self._pronto: asyncio.Event | None = None
        self._parar: asyncio.Event | None = None
        self._erro: BaseException | None = None
        self._ferramentas: list[dict] = []
        self._trava = asyncio.Lock()

    @property
    def ativo(self) -> bool:
        return bool(config.NUVC_API_KEY)

    async def _dono(self):
        partes = shlex.split(config.NUVC_COMANDO)
        params = StdioServerParameters(
            command=partes[0], args=partes[1:],
            env={**os.environ, "NUVC_API_KEY": config.NUVC_API_KEY},
        )
        try:
            async with stdio_client(params) as (leitura, escrita):
                async with ClientSession(leitura, escrita) as sessao:
                    await sessao.initialize()
                    resultado = await sessao.list_tools()
                    self._ferramentas = [
                        {
                            "name": t.name,
                            "description": t.description or t.name,
                            "input_schema": t.input_schema or {"type": "object", "properties": {}},
                            "eager_input_streaming": True,
                        }
                        for t in resultado.tools if t.name not in BLOQUEADAS
                    ]
                    self._sessao = sessao
                    log.info("NUVC conectado: %s", [f["name"] for f in self._ferramentas])
                    self._pronto.set()
                    await self._parar.wait()
        except BaseException as e:  # noqa: BLE001 - repassado a quem espera o início
            self._erro = e
            log.exception("MCP do NUVC encerrou")
        finally:
            self._sessao = None
            self._pronto.set()

    async def _garantir(self):
        async with self._trava:
            if self._sessao is not None:
                return
            self._erro = None
            self._pronto, self._parar = asyncio.Event(), asyncio.Event()
            self._tarefa = asyncio.create_task(self._dono())
            await asyncio.wait_for(self._pronto.wait(), TIMEOUT_INICIO)
            if self._sessao is None:
                raise RuntimeError(f"MCP do NUVC não iniciou: {self._erro}")

    async def ferramentas(self) -> list[dict]:
        """Definições das ferramentas no formato do Claude ([] se o NUVC estiver desligado)."""
        if not self.ativo:
            return []
        try:
            await self._garantir()
        except Exception:
            log.exception("Não foi possível iniciar o MCP do NUVC")
            return []
        return self._ferramentas

    def esquema(self, nome: str) -> dict | None:
        return next((f["input_schema"] for f in self._ferramentas if f["name"] == nome), None)

    async def chamar(self, nome: str, argumentos: dict) -> tuple[str, bool]:
        """Executa a ferramenta e devolve (texto, deu_erro)."""
        try:
            await self._garantir()
            res = await asyncio.wait_for(self._sessao.call_tool(nome, argumentos), TIMEOUT_CHAMADA)
        except Exception as e:  # noqa: BLE001 - o erro volta para o modelo como tool_result
            await self.fechar()  # força reconexão na próxima chamada
            return f"Erro ao chamar {nome}: {e}", True
        textos = [c.text for c in res.content if getattr(c, "type", "") == "text"]
        return "\n".join(textos) or "(sem conteúdo)", bool(res.is_error)

    async def fechar(self):
        if self._tarefa is not None:
            self._parar.set()
            try:
                await asyncio.wait_for(self._tarefa, 10)
            except Exception:  # noqa: BLE001
                self._tarefa.cancel()
            self._tarefa = None


nuvc = ClienteNuvc()
