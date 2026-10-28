"use client";

import { createClient, type Session } from "@supabase/supabase-js";
import { useEffect, useState } from "react";

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
  { auth: { flowType: "pkce", persistSession: true, detectSessionInUrl: true } },
);

/** Sessão atual; `undefined` enquanto carrega, `null` se não houver login. */
export function useSessao(): Session | null | undefined {
  const [sessao, setSessao] = useState<Session | null | undefined>(undefined);
  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSessao(data.session));
    const { data } = supabase.auth.onAuthStateChange((_evento, s) => setSessao(s));
    return () => data.subscription.unsubscribe();
  }, []);
  return sessao;
}
