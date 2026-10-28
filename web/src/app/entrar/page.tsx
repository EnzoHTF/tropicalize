"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import Topo from "@/components/Topo";
import { ehNativo } from "@/lib/push";
import { supabase, useSessao } from "@/lib/supabase";

function Formulario() {
  const router = useRouter();
  const destino = useSearchParams().get("volta") || "/app";
  const sessao = useSessao();
  const [email, setEmail] = useState("");
  const [estado, setEstado] = useState<"inicio" | "enviando" | "enviado">("inicio");
  const [erro, setErro] = useState("");
  const [nativo, setNativo] = useState(false);

  useEffect(() => setNativo(ehNativo()), []);
  useEffect(() => {
    if (sessao) router.replace(destino);
  }, [sessao, destino, router]);

  const urlRetorno = () => `${window.location.origin}${destino}`;

  async function enviarLink(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setEstado("enviando");
    const { error } = await supabase.auth.signInWithOtp({ email, options: { emailRedirectTo: urlRetorno() } });
    if (error) {
      setErro(error.message);
      setEstado("inicio");
    } else setEstado("enviado");
  }

  async function entrarComGoogle() {
    const { error } = await supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: urlRetorno() } });
    if (error) setErro(error.message);
  }

  return (
    <main className="wrap-estreito" style={{ paddingTop: 32, paddingBottom: 64 }}>
      <div className="cartao">
        <h1 style={{ fontSize: "1.8rem", marginBottom: 8 }}>Entrar no Tropicalize</h1>
        <p className="suave" style={{ marginBottom: 24 }}>
          Sem senha: enviamos um link de acesso para o seu e-mail.
        </p>
        {estado === "enviado" ? (
          <p>
            Pronto! Abra o e-mail enviado para <b>{email}</b> e toque no link para entrar.
          </p>
        ) : (
          <form onSubmit={enviarLink}>
            <div className="campo">
              <label htmlFor="email">E-mail</label>
              <input id="email" type="email" required autoComplete="email" value={email}
                     onChange={(e) => setEmail(e.target.value)} />
            </div>
            <button className="btn" style={{ width: "100%" }} disabled={estado === "enviando"}>
              {estado === "enviando" ? "Enviando…" : "Receber link de acesso"}
            </button>
          </form>
        )}
        {/* O Google bloqueia login dentro de webviews; no app nativo fica só o link por e-mail */}
        {!nativo && estado !== "enviado" && (
          <button className="btn btn-claro" style={{ width: "100%", marginTop: 12 }} onClick={entrarComGoogle}>
            Entrar com Google
          </button>
        )}
        {erro && <p className="erro">{erro}</p>}
      </div>
    </main>
  );
}

export default function Entrar() {
  return (
    <>
      <div className="wrap"><Topo direita={<span />} /></div>
      <Suspense>
        <Formulario />
      </Suspense>
    </>
  );
}
