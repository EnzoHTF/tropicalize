"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type Eu } from "@/lib/api";
import { ativarNotificacoes } from "@/lib/push";
import { supabase } from "@/lib/supabase";

const MENSAGENS = {
  ativado: "Notificações ativadas neste aparelho.",
  negado: "Permissão negada. Libere as notificações nas configurações do aparelho.",
  indisponivel: "Este navegador não aceita notificações. No iPhone/iPad, adicione o Tropicalize à tela de início primeiro.",
};

export default function Conta() {
  const router = useRouter();
  const [eu, setEu] = useState<Eu | null>(null);
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    api<Eu>("/api/eu").then(setEu).catch(() => {});
  }, []);

  async function notificacoes() {
    try {
      setAviso(MENSAGENS[await ativarNotificacoes()]);
    } catch {
      setAviso("Não foi possível ativar as notificações agora.");
    }
  }

  async function sair() {
    await supabase.auth.signOut();
    router.replace("/");
  }

  return (
    <div className="wrap-estreito" style={{ padding: 0 }}>
      <h1 style={{ fontSize: "1.9rem", margin: "8px 0 20px" }}>Sua conta</h1>
      {eu && (
        <div className="cartao" style={{ marginBottom: 16 }}>
          <p><b>{eu.email}</b></p>
          <p className="suave">
            Plano {eu.plano} · {eu.analises_restantes} de {eu.cota_mensal} análises restantes neste mês
          </p>
        </div>
      )}
      <div className="cartao" style={{ marginBottom: 16 }}>
        <h2 style={{ fontSize: "1.15rem", marginBottom: 6 }}>Alertas de prazo</h2>
        <p className="suave" style={{ marginBottom: 12 }}>Receba um aviso antes de fechar a inscrição de um fundo ou aceleradora recomendado.</p>
        <button className="btn" onClick={notificacoes}>Ativar notificações</button>
        {aviso && <p style={{ marginTop: 10 }}>{aviso}</p>}
      </div>
      {eu?.admin && (
        <Link href="/admin" className="btn btn-claro" style={{ marginBottom: 16 }}>Curadoria de notícias</Link>
      )}
      <div>
        <button className="btn btn-claro" onClick={sair}>Sair</button>
      </div>
    </div>
  );
}
