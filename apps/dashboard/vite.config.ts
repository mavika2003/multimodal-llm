import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const received: { at: string; type: string; preview: string }[] = [];

function demoReceiverPlugin(): Plugin {
  return {
    name: "demo-receiver",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.url === "/api/received" && req.method === "GET") {
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify({ count: received.length, items: received }));
          return;
        }
        if (req.url === "/api/submit" && req.method === "POST") {
          let body = "";
          req.on("data", (chunk) => {
            body += chunk;
          });
          req.on("end", () => {
            let preview = body.slice(0, 200);
            try {
              const j = JSON.parse(body);
              preview = JSON.stringify(j).slice(0, 200);
            } catch {
              /* raw body */
            }
            received.push({
              at: new Date().toISOString(),
              type: "submit",
              preview,
            });
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({ ok: true, received_count: received.length }));
          });
          return;
        }
        next();
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), demoReceiverPlugin()],
  server: { host: "127.0.0.1", port: 5173 },
});