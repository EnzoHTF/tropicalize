"use client";

import { Capacitor } from "@capacitor/core";
import { api } from "./api";

export const ehNativo = () => Capacitor.isNativePlatform();

function base64ParaUint8(base64: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - (base64.length % 4)) % 4);
  const bruto = atob((base64 + padding).replace(/-/g, "+").replace(/_/g, "/"));
  const saida = new Uint8Array(new ArrayBuffer(bruto.length));
  for (let i = 0; i < bruto.length; i++) saida[i] = bruto.charCodeAt(i);
  return saida;
}

/** Pede permissão e registra o aparelho para receber alertas de prazo. */
export async function ativarNotificacoes(): Promise<"ativado" | "negado" | "indisponivel"> {
  if (ehNativo()) {
    const { PushNotifications } = await import("@capacitor/push-notifications");
    const perm = await PushNotifications.requestPermissions();
    if (perm.receive !== "granted") return "negado";
    const token = await new Promise<string>((resolve, reject) => {
      PushNotifications.addListener("registration", (t) => resolve(t.value));
      PushNotifications.addListener("registrationError", (e) => reject(new Error(e.error)));
      PushNotifications.register();
    });
    await api("/api/push/inscrever", {
      method: "POST",
      body: JSON.stringify({ plataforma: Capacitor.getPlatform(), endpoint: token }),
    });
    return "ativado";
  }

  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return "indisponivel";
  const permissao = await Notification.requestPermission();
  if (permissao !== "granted") return "negado";
  const { chave } = await api<{ chave: string }>("/api/push/chave-publica");
  if (!chave) return "indisponivel";
  const registro = await navigator.serviceWorker.ready;
  const inscricao =
    (await registro.pushManager.getSubscription()) ??
    (await registro.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: base64ParaUint8(chave) }));
  const json = inscricao.toJSON();
  await api("/api/push/inscrever", {
    method: "POST",
    body: JSON.stringify({ plataforma: "web", endpoint: json.endpoint, chaves: json.keys }),
  });
  return "ativado";
}

/** Abre a notificação tocada no app nativo na tela certa. */
export async function ouvirToquesNativos(navegar: (url: string) => void) {
  if (!ehNativo()) return;
  const { PushNotifications } = await import("@capacitor/push-notifications");
  PushNotifications.addListener("pushNotificationActionPerformed", (acao) => {
    const url = acao.notification.data?.url as string | undefined;
    if (url) navegar(new URL(url).pathname);
  });
}
