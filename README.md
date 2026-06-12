# VetSalud — Sistema de Gestión de Clínica Veterinaria

Trabajo Práctico Obligatorio de **Base de Datos II** (1er Cuatrimestre 2026).

Backoffice de la red de clínicas veterinarias **VetSalud S.A.** sobre una
arquitectura de **persistencia políglota** con dos motores NoSQL de paradigmas
distintos:

- **MongoDB** (documental) — **fuente de verdad** de todo el dominio: pacientes,
  propietarios, veterinarios, consultas, vacunaciones, cirugías y **stock
  farmacéutico** (durable, con contadores atómicos vía `$inc`).
- **Redis** (clave-valor en memoria) — **capa de caché** sobre las
  consultas de lectura de la API, con invalidación en cada escritura y TTL.

El sistema resuelve **15 consultas/servicios** (12 de lectura + 3 servicios que
mutan datos), expuestos como **API REST** (FastAPI) con separación de capas
*router → service → query*. 

---

## Requisitos

- [Docker](https://www.docker.com/) y Docker Compose.



---

## Cómo correr el proyecto


```bash
# 1) Primera vez: levantar infra + API y cargar los datos
docker compose up -d --build      # mongo + redis + app  →  http://localhost:8000
docker compose run --rm etl       # Carga de los datos de los CSVs y los extras que agregamos 

# 2) Veces siguientes: reusar el estado ya cargado 
docker compose up -d             

# 3) Resetear los datos al estado original
docker compose run --rm etl
```

- **Swagger UI:** http://localhost:8000/docs (rutas agrupadas por *tag*).
- **Health check:** http://localhost:8000/health

---

## Inspeccionar los datos: CLI de Mongo y Redis

Los contenedores ya traen sus shells (`mongosh` y `redis-cli`), así que **no hay que
instalar nada**: se entra con `docker compose exec`. En Codespaces funcionan los
mismos comandos.

### Mongo (`mongosh`)

```bash
# Abrir un shell interactivo sobre la base del proyecto
docker compose exec mongo mongosh vetsalud

# O ejecutar una sola consulta sin entrar al shell (--eval)
docker compose exec mongo mongosh vetsalud --eval 'db.pacientes.countDocuments()'
```

### Redis (`redis-cli`)

```bash
# Abrir un shell interactivo
docker compose exec redis redis-cli

# O ejecutar un solo comando
docker compose exec redis redis-cli KEYS '*'
```

Comandos útiles para ver la caché (las claves las escriben los servicios):

```bash
KEYS *              # listar todas las claves cacheadas
GET <clave>         # ver el valor (JSON) de una consulta cacheada
TTL <clave>         # segundos que le quedan de vida (TTL)
DBSIZE              # cantidad de claves
FLUSHALL            # vaciar la caché (forzar recálculo en la próxima lectura)
exit                # salir
```

> Tip: corré una lectura (ej. `curl localhost:8000/pacientes/activos`) y después
> `KEYS *` para ver cómo aparece la clave en Redis; una escritura sobre los
> endpoints que mutan la invalida (ver la tabla de *Caché e invalidación*).

---

## Detener la infraestructura

```bash
docker compose down            # detiene los contenedores
docker compose down -v         # además borra los volúmenes (datos persistidos)
```

**Persistencia del estado:** los datos viven en volúmenes nombrados (`mongo_data`,
`redis_data`). `docker compose down` **conserva** el estado; sólo
`docker compose down -v` borra los volúmenes.

## Correr el proyecto en GitHub Codespaces

El repo trae un *devcontainer* con **Docker adentro**, así que
en Codespaces se usan **exactamente los mismos comandos** que en local.

1. En GitHub: **Code → Codespaces → Create codespace on `main`**.
2. Esperá a que termine de crearse. **No hay que correr nada a mano:** el
   `postCreateCommand` ya buildea, levanta `mongo` + `redis` + `app` y **carga los
   datos**. Cuando termina, la API ya está corriendo **con datos**.
   *(Si parás y reabrís el Codespace, el `postStartCommand` vuelve a levantar los
   servicios; los datos persisten en los volúmenes, el ETL no se re-corre.)*
3. *(Opcional)* Los mismos comandos del README sirven para recargar, relevantar o
   borrar todo y empezar de cero:

   ```bash
   docker compose run --rm etl       # recargar datos: el ETL ya borra y re-siembra (drop + seed)
   docker compose up -d              # relevantar servicios si hizo falta

   # Borrón total (también elimina los volúmenes mongo_data / redis_data):
   docker compose down -v
   docker compose up -d --build
   docker compose run --rm etl
   ```

#### Acceder a la API (puerto 8000)

1. Abrí la pestaña **PORTS / PUERTOS** del Codespace.
2. Buscá el puerto **8000** (lo expone la API). Su *Forwarded Address* es algo como:
   `https://TU-CODESPACE-8000.app.github.dev`. Este link se puede encontrar en la solapa de puertos que abre VSCODE cuando empezamos el codespace. 
3. Abrila en el navegador → **Swagger** en `/docs`, *health check* en `/health`.
   Los endpoints cuelgan de la **raíz** (no hay prefijo `/api`): `/pacientes/activos`,
   `/consultas/seguimiento`, etc.
4. *(Opcional)* Si necesitás que algo **de afuera** del Codespace le pegue a la API
   (entregar una URL navegable, Postman desde otra máquina, un front separado):
   clic derecho en el puerto 8000 → **Port Visibility → Public**. Por defecto es
   **Private** y sólo vos (logueado) podés abrirlo.

Desde la terminal del Codespace, `curl localhost:8000/health` también funciona sin
tocar nada de esto.

---


## Endpoints de la API

| Método | Ruta | Consulta | Descripción |
|--------|------|----------|-------------|
| `GET`  | `/pacientes/activos`                  | q01 | Pacientes activos con datos del propietario |
| `GET`  | `/pacientes/{id}/historial`           | q03 | Historial (consultas + vacunaciones) |
| `GET`  | `/pacientes/{id}/historial-completo`  | —   | Extra (fuera del enunciado): historial + cirugías |
| `GET`  | `/pacientes/vacunas-vencidas`         | q06 | Pacientes con vacunas vencidas |
| `GET`  | `/pacientes/por-sucursal?sucursal=`   | q10 | Pacientes de una sucursal |
| `GET`  | `/propietarios/multi-paciente`        | q04 | Propietarios con más de un paciente |
| `GET`  | `/propietarios/sin-consultas`         | q12 | Propietarios sin consultas en el último año |
| `POST` | `/propietarios`                       | q13 | Alta de propietario |
| `PUT`  | `/propietarios/{id}`                  | q13 | Modificación de propietario |
| `DELETE`| `/propietarios/{id}`                 | q13 | Baja lógica de propietario |
| `GET`  | `/consultas/seguimiento`              | q02 | Consultas en 'Seguimiento' con vet y costo |
| `GET`  | `/consultas/vets-activos`             | q05 | Veterinarios activos y consultas de los últimos 60 días |
| `GET`  | `/consultas/top-diagnosticos?limite=` | q07 | Top N diagnósticos más frecuentes (`limite` por defecto 5) |
| `GET`  | `/consultas/control-bajo-costo?umbral=`| q09 | Consultas 'Control' con costo bajo |
| `GET`  | `/consultas/ingresos-por-vet`         | q11 | Ingresos por veterinario en el mes (lee la **vista** `vista_ingresos_por_vet`) |
| `POST` | `/consultas`                          | q14 | Registrar consulta (valida paciente y vet) |
| `GET`  | `/stock/bajo?umbral=`                 | q08 | Stock con menos de N unidades y proveedor |
| `POST` | `/stock/{id}/decrementar`             | q15 | Decrementar unidades (atómico) |

Errores de negocio: `404` si el paciente/veterinario no existe (`ValidacionError`),
`409` si el stock es insuficiente (`StockError`) o si se da de alta un propietario
con un `id_propietario` ya existente (`PropietarioDuplicadoError`).

**Fecha de referencia:** las consultas sensibles al tiempo (`/consultas/vets-activos`,
`/pacientes/vacunas-vencidas`, `/consultas/ingresos-por-vet`,
`/propietarios/sin-consultas`) usan `datetime.now()` — la API se mantiene limpia, sin
parámetros de fecha. El dataset está anclado a **2026-06-01**; los tests congelan el
reloj con `freezegun` para que esas consultas sean deterministas.

---

## Ejemplos de uso (curl)

> Suponen la API corriendo en `http://localhost:8000` con los datos ya cargados. Los
> IDs (`P001`, `V001`, `C001`, `PRD001`, sucursal `Palermo`) existen en el seed.
> También podés probar todo de forma interactiva en http://localhost:8000/docs.

### Lecturas (GET)

```bash
curl localhost:8000/health
curl localhost:8000/pacientes/activos
curl localhost:8000/pacientes/P001/historial
curl localhost:8000/pacientes/vacunas-vencidas
curl "localhost:8000/pacientes/por-sucursal?sucursal=Palermo"
curl localhost:8000/propietarios/multi-paciente
curl localhost:8000/propietarios/sin-consultas
curl localhost:8000/consultas/seguimiento
curl localhost:8000/consultas/vets-activos
curl "localhost:8000/consultas/top-diagnosticos?limite=5"
curl "localhost:8000/consultas/control-bajo-costo?umbral=5000"
curl localhost:8000/consultas/ingresos-por-vet
curl "localhost:8000/stock/bajo?umbral=50"
```

Ejemplo de salida (`top-diagnosticos?limite=3`):

```json
[{"frecuencia":12,"diagnostico":"Sano"},
 {"frecuencia":6,"diagnostico":"Dermatitis atópica"},
 {"frecuencia":5,"diagnostico":"Gastritis"}]
```

### Servicios (escrituras — invalidan la caché)

**ABM de propietarios (q13):**

```bash
# Alta → devuelve el propietario creado (objeto completo, con activo por defecto)
curl -X POST localhost:8000/propietarios \
  -H 'Content-Type: application/json' \
  -d '{"id_propietario":"C900","nombre":"Ada","apellido":"Lovelace","dni":"12345678",
       "email":"ada@vetsalud.com","telefono":"1144440000","ciudad":"CABA",
       "provincia":"Buenos Aires","activo":true}'
# → {"activo":true,"id_propietario":"C900","nombre":"Ada","apellido":"Lovelace", ... ,"provincia":"Buenos Aires"}

# Modificación → devuelve el propietario ya actualizado (objeto completo)
curl -X PUT localhost:8000/propietarios/C900 \
  -H 'Content-Type: application/json' \
  -d '{"email":"ada.new@vetsalud.com","telefono":"1122223333"}'
# → {"activo":true,"id_propietario":"C900", ... ,"email":"ada.new@vetsalud.com","telefono":"1122223333"}

# Baja lógica → marca activo=false (no borra) y devuelve el propietario ya actualizado
curl -X DELETE localhost:8000/propietarios/C900
# → {"activo":false,"id_propietario":"C900","nombre":"Ada", ... ,"provincia":"Buenos Aires"}
```

**Registrar consulta (q14)** — valida que el paciente y el veterinario existan:

```bash
curl -X POST localhost:8000/consultas \
  -H 'Content-Type: application/json' \
  -d '{"id_paciente":"P001","id_vet":"V001","motivo":"Control anual",
       "diagnostico":"Sano","costo":3500,"estado":"Cerrada"}'
# → {"id_consulta":"CON036","id_paciente":"P001","id_vet":"V001", ... ,"vet_sucursal":"Palermo","id_propietario":"C001"}
```

**Decrementar stock (q15)** — `$inc` atómico:

```bash
curl -X POST localhost:8000/stock/PRD001/decrementar \
  -H 'Content-Type: application/json' \
  -d '{"cantidad":5}'
# → {"id_producto":"PRD001","unidades_antes":120,"decremento":5,"unidades_despues":115}
```

**Casos de error:**

```bash
# Stock insuficiente → HTTP 409
curl -i -X POST localhost:8000/stock/PRD001/decrementar \
  -H 'Content-Type: application/json' -d '{"cantidad":999999}'

# Paciente o veterinario inexistente → HTTP 404
curl -i -X POST localhost:8000/consultas \
  -H 'Content-Type: application/json' \
  -d '{"id_paciente":"NOPE","id_vet":"V001","motivo":"x","diagnostico":"y","costo":1}'
```

> Tras correr las escrituras, podés resetear los datos con
> `docker compose run --rm etl`.

---

## Ejecutar los tests

```bash
docker compose run --rm tests
```

Corre la suite en una **base de datos aislada** (`MONGO_DB=vetsalud_test`): siembra
su propio dataset y ejecuta `pytest`, **sin tocar** tus datos de `vetsalud`. (Redis
es sólo caché y se limpia entre pruebas.)

---

## Estructura del proyecto

```
.
├── .devcontainer/devcontainer.json   # GitHub Codespaces
├── data/                             # CSV provistos por la cátedra
├── src/
│   ├── db/                           # conexiones (mongo.py, redis_client.py) + cache.py (cache-aside)
│   ├── loaders/                      # ETL: load_mongo, seed_extra, clean
│   ├── queries/                      # q01..q15 (una consulta pura por módulo)
│   ├── api/
│   │   ├── main.py                   # app FastAPI: routers + handlers de error
│   │   ├── routers/                  # capa HTTP fina (pacientes, propietarios, consultas, stock)
│   │   └── services/                 # caché + invalidación, llaman a las queries
│   └── main.py                       # punto de entrada del ETL
├── tests/                            # 
├── docker-compose.yml                # mongo + redis + app + etl/tests (profiles)
├── Dockerfile                        # imagen de la API (uvicorn)
├── .dockerignore
├── requirements.txt
└── .env.example
```

---

## Las 15 consultas/servicios

Todas operan sobre **MongoDB** (fuente de verdad); **Redis** actúa como caché de
lectura transversal a todas ellas.

| #  | Descripción                                                   | Tipo     |
|----|---------------------------------------------------------------|----------|
| 1  | Pacientes activos con todos sus datos de propietario          | lectura  |
| 2  | Consultas en 'Seguimiento' con veterinario y costo            | lectura  |
| 3  | Historial de un paciente (consultas + vacunaciones) ordenado por fecha | lectura |
| 4  | Propietarios con más de un paciente                           | lectura  |
| 5  | Veterinarios activos y consultas en los últimos 60 días       | lectura  |
| 6  | Pacientes con vacunas vencidas                                | lectura  |
| 7  | Top 5 diagnósticos más frecuentes (`limite` parametrizable)   | lectura  |
| 8  | Stock con menos de 50 unidades y su proveedor                 | lectura  |
| 9  | Consultas de tipo 'Control' con costo bajo                    | lectura  |
| 10 | Pacientes de una sucursal (vía veterinario)                   | lectura  |
| 11 | Ingresos totales por veterinario en el mes actual (vista de MongoDB) | lectura  |
| 12 | Propietarios sin consultas en el último año                   | lectura  |
| 13 | ABM completo de propietarios (alta, modificación, baja lógica)| servicio |
| 14 | Registro de consulta con validación de paciente y veterinario | servicio |
| 15 | Decrementar unidades de un producto tras una consulta         | servicio |

---

## Caché e invalidación

Redis funciona como caché en la **capa de servicios**: las `q01..q15`
quedan **puras** (sólo datos, sin acoplamiento a Redis) y los servicios envuelven
las lecturas con `get_or_set_cache` y disparan `invalidate` en las escrituras.

| Endpoint que muta | Consultas que invalida |
|---|---|
| `POST/PUT/DELETE /propietarios` | q01, q04, q12 |
| `POST /consultas`               | q02, q03, q05, q07, q09, q10, q11, q12 |
| `POST /stock/{id}/decrementar`  | q08 |

TTL por defecto: `1 h` (consultas normales) y `12 h` (agregados casi estáticos,
ej. q07). Ver `src/db/cache.py`.
