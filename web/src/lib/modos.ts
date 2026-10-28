import type { Modo } from "./api";

export type Campo = {
  nome: string;
  rotulo: string;
  tipo: "texto" | "area" | "numero" | "opcoes" | "lista" | "booleano";
  obrigatorio?: boolean;
  dica?: string;
  minimo?: number;
  opcoes?: { valor: string; rotulo: string }[];
  padrao?: string | number | boolean | string[];
};

export type DefinicaoModo = {
  modo: Modo;
  titulo: string;
  chamada: string;
  descricao: string;
  icone: string;
  campos: Campo[];
};

const FAIXAS = [
  { valor: "ate_5k", rotulo: "Até R$ 5 mil" },
  { valor: "5k_50k", rotulo: "De R$ 5 mil a R$ 50 mil" },
  { valor: "acima_50k", rotulo: "Acima de R$ 50 mil" },
];

const ESTAGIOS = [
  { valor: "ideia", rotulo: "Só a ideia" },
  { valor: "pre_seed", rotulo: "Pre-seed (MVP, primeiros clientes)" },
  { valor: "seed", rotulo: "Seed (tração inicial)" },
  { valor: "series_a", rotulo: "Série A" },
  { valor: "series_b", rotulo: "Série B" },
  { valor: "growth", rotulo: "Growth" },
];

// Os nomes dos campos seguem os modelos de entrada do backend (tropicalize/modos.py)
export const MODOS: DefinicaoModo[] = [
  {
    modo: "descobrir",
    titulo: "Descobrir ideia",
    chamada: "Quero empreender",
    descricao: "O que deu certo lá fora e ainda não existe no Brasil, adaptado ao seu perfil e orçamento.",
    icone: "🌱",
    campos: [
      { nome: "tema", rotulo: "Tema, setor ou problema", tipo: "texto", obrigatorio: true, minimo: 3,
        dica: "Ex.: gestão financeira para freelancers" },
      { nome: "perfil", rotulo: "Seu perfil", tipo: "area",
        dica: "Experiência, habilidades, contatos, tempo disponível" },
      { nome: "faixa_investimento", rotulo: "Quanto pode investir no começo", tipo: "opcoes", opcoes: FAIXAS, padrao: "ate_5k" },
      { nome: "cidade", rotulo: "Cidade", tipo: "texto" },
    ],
  },
  {
    modo: "diagnosticar",
    titulo: "Diagnosticar empresa",
    chamada: "Já tenho uma empresa",
    descricao: "Gargalos priorizados e melhorias que já funcionaram em empresas daqui e de fora.",
    icone: "🩺",
    campos: [
      { nome: "nome", rotulo: "Nome da empresa", tipo: "texto", obrigatorio: true, minimo: 1 },
      { nome: "descricao", rotulo: "O que a empresa faz", tipo: "area", obrigatorio: true, minimo: 10 },
      { nome: "setor", rotulo: "Setor", tipo: "texto" },
      { nome: "funcionarios", rotulo: "Funcionários", tipo: "numero" },
      { nome: "faturamento_anual_brl", rotulo: "Faturamento anual (R$)", tipo: "numero" },
      { nome: "cidade", rotulo: "Cidade", tipo: "texto" },
      { nome: "processos", rotulo: "Como opera hoje", tipo: "area",
        dica: "Vendas, atendimento, operação, ferramentas que usa" },
      { nome: "dores", rotulo: "Principais dores", tipo: "area", obrigatorio: true, minimo: 3,
        dica: "O que trava o crescimento ou consome tempo e dinheiro" },
      { nome: "objetivos", rotulo: "Objetivos para os próximos 12 meses", tipo: "area" },
    ],
  },
  {
    modo: "validar",
    titulo: "Validar e viabilizar",
    chamada: "Tenho uma ideia",
    descricao: "Potencial da ideia, concorrentes e o passo a passo para construir, com as ferramentas certas para o seu orçamento.",
    icone: "🧪",
    campos: [
      { nome: "ideia", rotulo: "Descreva a ideia", tipo: "area", obrigatorio: true, minimo: 10 },
      { nome: "publico_alvo", rotulo: "Para quem é", tipo: "texto" },
      { nome: "diferencial", rotulo: "Diferencial", tipo: "area" },
      { nome: "ja_tem", rotulo: "O que já tem pronto", tipo: "area", dica: "MVP, clientes, equipe, parceiros" },
      { nome: "faixa_investimento", rotulo: "Orçamento para construir", tipo: "opcoes", opcoes: FAIXAS, padrao: "ate_5k" },
      { nome: "cidade", rotulo: "Cidade", tipo: "texto" },
    ],
  },
  {
    modo: "captar",
    titulo: "Captar investimento",
    chamada: "Quero investimento",
    descricao: "Fundos de VC, aceleradoras e editais compatíveis com o seu negócio, com prazos e links de inscrição.",
    icone: "💰",
    campos: [
      { nome: "descricao", rotulo: "Descreva o negócio", tipo: "area", obrigatorio: true, minimo: 10 },
      { nome: "setor", rotulo: "Setor", tipo: "texto", dica: "Ex.: fintech, saúde, agro, SaaS B2B" },
      { nome: "estagio", rotulo: "Estágio", tipo: "opcoes", opcoes: ESTAGIOS, padrao: "pre_seed" },
      { nome: "captacao_alvo_brl", rotulo: "Quanto quer captar (R$)", tipo: "numero" },
      { nome: "tracao", rotulo: "Tração", tipo: "area", dica: "Receita, usuários, crescimento mês a mês" },
      { nome: "cidade", rotulo: "Cidade", tipo: "texto" },
      { nome: "paises_interesse", rotulo: "Onde buscar investidores", tipo: "lista", padrao: ["Brasil"],
        dica: "Separe por vírgula. Ex.: Brasil, EUA, Portugal, Global" },
      { nome: "aceita_nao_diluitivo", rotulo: "Incluir editais e subvenções (sem ceder participação)", tipo: "booleano", padrao: true },
    ],
  },
];

export const modoPorNome = (modo: string) => MODOS.find((m) => m.modo === modo);
