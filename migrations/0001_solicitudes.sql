-- Registro público y anónimo de solicitudes de transparencia (solicitar.html).
-- Sin nombre, correo, IP ni texto libre: solo sujeto obligado, folio, fechas y
-- estado. Los folios ya son públicos en la PNT. Ver src/worker.js.
CREATE TABLE solicitudes (
  folio        TEXT PRIMARY KEY,           -- folio de la PNT: solo números, 10 a 20
  sujeto       TEXT NOT NULL,              -- 'setran' | 'siteur'
  fecha        TEXT NOT NULL,              -- AAAA-MM-DD en que se envió
  estado       TEXT NOT NULL DEFAULT 'sin-respuesta', -- sin-respuesta | entregada | parcial | negada | prorroga
  fecha_estado TEXT,                       -- AAAA-MM-DD de la respuesta (null si sin respuesta)
  creado       INTEGER NOT NULL,           -- ms desde 1970 (UTC)
  actualizado  INTEGER NOT NULL
);
CREATE INDEX solicitudes_sujeto ON solicitudes (sujeto, estado);

-- Límite de peticiones: llave = SHA-256(sal + día + IP); la IP no se guarda
-- y las llaves de días anteriores se borran.
CREATE TABLE limites (
  h   TEXT NOT NULL,
  dia TEXT NOT NULL,
  n   INTEGER NOT NULL,
  PRIMARY KEY (h, dia)
);
