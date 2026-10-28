// Service worker do Tropicalize: tela offline, cache leve e notificações push.
const CACHE = "tropicalize-v1";
const OFFLINE = "/offline.html";

self.addEventListener("install", (evento) => {
  evento.waitUntil(caches.open(CACHE).then((c) => c.addAll([OFFLINE, "/logo.svg"])));
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((chaves) => Promise.all(chaves.filter((k) => k !== CACHE).map((k) => caches.delete(k)))),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (evento) => {
  const req = evento.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  // Páginas: rede primeiro, tela offline se falhar
  if (req.mode === "navigate") {
    evento.respondWith(fetch(req).catch(() => caches.match(OFFLINE)));
    return;
  }
  // Arquivos estáticos do Next têm hash no nome: cache primeiro
  if (req.url.includes("/_next/static/") || req.url.includes("/icones/")) {
    evento.respondWith(
      caches.match(req).then((r) => r || fetch(req).then((resp) => {
        const copia = resp.clone();
        caches.open(CACHE).then((c) => c.put(req, copia));
        return resp;
      })),
    );
  }
});

self.addEventListener("push", (evento) => {
  let dados = { titulo: "Tropicalize", corpo: "", url: "/app" };
  try {
    dados = { ...dados, ...evento.data.json() };
  } catch {
    /* payload sem JSON */
  }
  evento.waitUntil(
    self.registration.showNotification(dados.titulo, {
      body: dados.corpo,
      icon: "/icones/icone-192.png",
      badge: "/icones/icone-192.png",
      data: { url: dados.url },
    }),
  );
});

self.addEventListener("notificationclick", (evento) => {
  evento.notification.close();
  const url = evento.notification.data?.url || "/app";
  evento.waitUntil(
    self.clients.matchAll({ type: "window" }).then((janelas) => {
      for (const j of janelas) {
        if ("focus" in j) {
          j.navigate(url);
          return j.focus();
        }
      }
      return self.clients.openWindow(url);
    }),
  );
});
