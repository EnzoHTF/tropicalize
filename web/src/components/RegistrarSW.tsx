"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ehNativo, ouvirToquesNativos } from "@/lib/push";

/** Registra o service worker (PWA instalável e push) ou, no app nativo, os toques em notificações. */
export default function RegistrarSW() {
  const router = useRouter();
  useEffect(() => {
    if (ehNativo()) {
      ouvirToquesNativos((caminho) => router.push(caminho));
      return;
    }
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
  }, [router]);
  return null;
}
