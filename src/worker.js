// Worker delante de los archivos estáticos. Solo atiende /api/* (ver
// `run_worker_first` en wrangler.jsonc); todo lo demás lo sirve `public/`.
//
// Registro público y anónimo de solicitudes de transparencia (solicitar.html):
// - Solo sujeto obligado (lista cerrada), folio de la PNT, fechas y estado.
//   Nada de nombre, correo ni texto libre.
// - No se guardan IP, cookies ni identificadores. La IP solo se usa, en
//   memoria, como llave del límite de peticiones (binding LIMITE de Workers
//   Rate Limiting), como en camiones-basura-gdl y la política común.
// Ver docs/decisiones.md («Registro de solicitudes»).

const SUJETOS = { setran: "SETRAN", siteur: "SITEUR" };
const ESTADOS = {
  "sin-respuesta": "Sin respuesta",
  entregada: "Entregada",
  parcial: "Entregada parcial",
  negada: "Negada",
  prorroga: "Prórroga",
};
const PENDIENTES = ["sin-respuesta", "prorroga"];   // cuentan como «días sin respuesta»
const FECHA_MIN = "2026-11-01";                      // las solicitudes se redactaron en nov. 2026
const TZ_OFFSET_MS = -6 * 3600000;                   // Guadalajara: UTC−6 todo el año
const DAY_MS = 86400000;

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const p = url.pathname;
    try {
      if (p === "/api/solicitudes") {
        if (req.method === "GET") return await resumen(env);
        if (req.method === "POST") return await alta(req, env, url);
        return json({ error: "usa GET o POST" }, 405);
      }
      if (p === "/api/solicitudes.csv") {
        if (req.method !== "GET") return json({ error: "usa GET" }, 405);
        return await csv(env);
      }
      const m = p.match(/^\/api\/solicitudes\/([^/]+)\/estado$/);
      if (m) {
        if (req.method !== "POST" && req.method !== "PATCH") return json({ error: "usa POST o PATCH" }, 405);
        return await estado(req, env, url, decodeURIComponent(m[1]));
      }
    } catch (e) {   // p. ej. D1 sin migrar: la página muestra «No se pudo cargar»
      console.error(e);
      return json({ error: "no disponible" }, 503);
    }
    if (p.startsWith("/api/")) return json({ error: "no existe" }, 404);
    return env.ASSETS.fetch(req);
  },
};

const json = (body, status = 200, headers = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8", ...headers } });
const hoy = () => new Date(Date.now() + TZ_OFFSET_MS).toISOString().slice(0, 10);
const esFolio = f => typeof f === "string" && /^\d{10,20}$/.test(f);
function esFecha(v) {
  if (typeof v !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(v)) return false;
  const d = new Date(v + "T00:00:00Z");
  return !isNaN(d) && d.toISOString().slice(0, 10) === v;   // descarta 2026-02-30
}
const dias = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / DAY_MS);

async function leerJson(req) {
  try { const b = JSON.parse(await req.text()); return b && typeof b === "object" ? b : null; } catch { return null; }
}

// Origen propio (o sin Origin, p. ej. curl) y límite por IP, solo en memoria.
async function permitido(req, env, url) {
  const origin = req.headers.get("origin");
  if (origin && new URL(origin).host !== url.host) return json({ error: "origen" }, 403);
  if (env.LIMITE) {
    const { success } = await env.LIMITE.limit({ key: req.headers.get("cf-connecting-ip") || "?" });
    if (!success) return json({ error: "demasiadas solicitudes; intenta más tarde" }, 429);
  }
  return null;
}

async function alta(req, env, url) {
  const b = await leerJson(req);
  if (!b) return json({ error: "json" }, 400);
  const folio = typeof b.folio === "string" ? b.folio.trim() : b.folio;
  if (!SUJETOS[b.sujeto]) return json({ error: "sujeto: setran o siteur" }, 400);
  if (!esFolio(folio)) return json({ error: "folio: solo números, de 10 a 20" }, 400);
  if (!esFecha(b.fecha) || b.fecha < FECHA_MIN || b.fecha > hoy())
    return json({ error: `fecha: AAAA-MM-DD, entre ${FECHA_MIN} y hoy` }, 400);
  const no = await permitido(req, env, url);
  if (no) return no;
  const ahora = Date.now();
  const r = await env.DB.prepare(
    "INSERT INTO solicitudes (folio, sujeto, fecha, creado, actualizado) VALUES (?1, ?2, ?3, ?4, ?4) ON CONFLICT (folio) DO NOTHING"
  ).bind(folio, b.sujeto, b.fecha, ahora).run();
  if (!r.meta.changes) return json({ error: "ese folio ya está registrado", folio }, 409);
  return json({ ok: true, folio }, 201);
}

async function estado(req, env, url, folio) {
  if (!esFolio(folio)) return json({ error: "folio: solo números, de 10 a 20" }, 400);
  const b = await leerJson(req);
  if (!b) return json({ error: "json" }, 400);
  if (!ESTADOS[b.estado]) return json({ error: "estado: " + Object.keys(ESTADOS).join(" | ") }, 400);
  const s = await env.DB.prepare("SELECT fecha FROM solicitudes WHERE folio = ?1").bind(folio).first();
  if (!s) return json({ error: "folio no registrado" }, 404);
  let fe = null;
  if (b.estado !== "sin-respuesta") {
    if (!esFecha(b.fecha) || b.fecha < s.fecha || b.fecha > hoy())
      return json({ error: "fecha: AAAA-MM-DD, entre el envío y hoy" }, 400);
    fe = b.fecha;
  }
  const no = await permitido(req, env, url);
  if (no) return no;
  await env.DB.prepare("UPDATE solicitudes SET estado = ?2, fecha_estado = ?3, actualizado = ?4 WHERE folio = ?1")
    .bind(folio, b.estado, fe, Date.now()).run();
  return json({ ok: true, folio, estado: b.estado });
}

const lista = async env =>
  (await env.DB.prepare("SELECT folio, sujeto, fecha, estado, fecha_estado FROM solicitudes ORDER BY fecha, folio").all()).results;

async function resumen(env) {
  const filas = await lista(env);
  const d = hoy();
  const totales = {};
  for (const k of Object.keys(SUJETOS)) totales[k] = Object.fromEntries(Object.keys(ESTADOS).map(e => [e, 0]));
  const espera = [];
  const solicitudes = filas.map(f => {
    totales[f.sujeto][f.estado]++;
    const pendiente = PENDIENTES.includes(f.estado);
    const dd = pendiente ? dias(f.fecha, d) : null;
    if (pendiente) espera.push(dd);
    return { ...f, dias_sin_respuesta: dd };
  });
  espera.sort((a, b) => a - b);
  const n = espera.length;
  const mediana = n ? (n % 2 ? espera[(n - 1) / 2] : (espera[n / 2 - 1] + espera[n / 2]) / 2) : null;
  return json({
    generado: new Date().toISOString(), hoy: d, total: filas.length,
    sujetos: SUJETOS, estados: ESTADOS, totales,
    sinRespuesta: { n, mediana, maximo: n ? espera[n - 1] : null },
    solicitudes,
  }, 200, { "cache-control": "public, max-age=60", "access-control-allow-origin": "*" });
}

const celda = v => v === null || v === undefined ? "" : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v);

async function csv(env) {
  const filas = await lista(env);
  const d = hoy();
  const cols = ["folio", "sujeto_obligado", "fecha_envio", "estado", "fecha_estado", "dias_sin_respuesta"];
  const lineas = filas.map(f => [f.folio, SUJETOS[f.sujeto], f.fecha, ESTADOS[f.estado], f.fecha_estado,
    PENDIENTES.includes(f.estado) ? dias(f.fecha, d) : null].map(celda).join(","));
  return new Response("﻿" + [cols.join(","), ...lineas].join("\n") + "\n", { headers: {
    "content-type": "text/csv; charset=utf-8",
    "content-disposition": 'inline; filename="solicitudes-transparencia-rutas-gdl.csv"',
    "cache-control": "public, max-age=60",
    "access-control-allow-origin": "*",
  } });
}
