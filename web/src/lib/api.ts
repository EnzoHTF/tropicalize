import { API_URL } from "./config";
import { supabase } from "./supabase";

export { API_URL };

export class ErroApi extends Error {
  constructor(public status: number, mensagem: string) {
    super(mensagem);
  }
}

async function cabecalhos(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function erroDaResposta(r: Response): Promise<ErroApi> {
  let mensagem = `Erro ${r.status}`;
  try {
    const corpo = await r.json();
    if (typeof corpo.detail === "string") mensagem = corpo.detail;
  } catch {
    /* corpo sem JSON */
  }
  return new ErroApi(r.status, mensagem);
}

export async function api<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  const r = await fetch(`${API_URL}${caminho}`, {
    ...init,
    headers: { ...(await cabecalhos()), ...(init.headers ?? {}) },
  });
  if (!r.ok) throw await erroDaResposta(r);
  return r.json() as Promise<T>;
}

export type EventoAnalise =
  | { tipo: "inicio"; relatorio_id: number }
  | { tipo: "status"; texto: string }
  | { tipo: "texto"; texto: string }
  | { tipo: "fonte"; titulo: string; url: string }
  | { tipo: "recomendacoes"; itens: Recomendacao[] }
  | { tipo: "fim"; relatorio_id: number }
  | { tipo: "erro"; texto: string };

export type Recomendacao = {
  investidor_id: number;
  nome: string;
  tipo: string;
  aderencia: number;
  motivo: string;
  url_inscricao: string | null;
  inscricao_fecha: string | null;
  ticket_texto: string | null;
};

/** Inicia uma análise e repassa cada evento do stream (SSE) para `aoReceber`. */
export async function analisar(
  modo: string,
  entrada: Record<string, unknown>,
  aoReceber: (ev: EventoAnalise) => void,
  sinal?: AbortSignal,
): Promise<void> {
  const r = await fetch(`${API_URL}/api/analises/${modo}`, {
    method: "POST",
    headers: await cabecalhos(),
    body: JSON.stringify(entrada),
    signal: sinal,
  });
  if (!r.ok || !r.body) throw await erroDaResposta(r);

  const leitor = r.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await leitor.read();
    if (done) break;
    buffer += value;
    const blocos = buffer.split("\n\n");
    buffer = blocos.pop() ?? "";
    for (const bloco of blocos) {
      const dados = bloco
        .split("\n")
        .filter((l) => l.startsWith("data:"))
        .map((l) => l.slice(5).trim())
        .join("");
      if (dados) aoReceber(JSON.parse(dados) as EventoAnalise);
    }
  }
}

export type Relatorio = {
  id: number;
  modo: Modo;
  titulo: string;
  entrada: Record<string, unknown>;
  conteudo: string;
  estruturado: Recomendacao[] | null;
  fontes: { titulo: string; url: string }[];
  status: "gerando" | "pronto" | "erro";
  modelo: string | null;
  criado_em: string;
};

export type Modo = "descobrir" | "diagnosticar" | "validar" | "captar";

export type Eu = {
  id: string;
  email: string;
  plano: string;
  admin: boolean;
  analises_restantes: number;
  cota_mensal: number;
};
