import type { CapacitorConfig } from "@capacitor/cli";

// Os apps de iOS (iPhone/iPad) e Android abrem o site publicado (server.url), então toda
// atualização do site chega aos apps sem passar pelas lojas. Os recursos nativos (push,
// compartilhar) vêm dos plugins do Capacitor. A pasta capacitor-www só aparece sem internet.
const config: CapacitorConfig = {
  appId: "app.tropicalize",
  appName: "Tropicalize",
  webDir: "capacitor-www",
  server: {
    url: process.env.CAP_SERVER_URL ?? "https://tropicalize.app",
    errorPath: "index.html",
  },
  ios: { contentInset: "automatic", backgroundColor: "#FBF7EF" },
  android: { backgroundColor: "#FBF7EF" },
  plugins: {
    PushNotifications: { presentationOptions: ["badge", "sound", "alert"] },
  },
};

export default config;
