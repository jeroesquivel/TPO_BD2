# VetSalud — Sistema de Gestión de Clínica Veterinaria

Trabajo Práctico Obligatorio de **Base de Datos II** (1er Cuatrimestre 2026).

Backoffice de la red de clínicas veterinarias **VetSalud S.A.** sobre una
arquitectura de **persistencia políglota** con dos motores NoSQL de paradigmas
distintos:

- **MongoDB** (documental) — motor principal: pacientes, propietarios,
  veterinarios, consultas, vacunaciones y cirugías.
- **Redis** (clave-valor en memoria) — stock farmacéutico (contadores atómicos,
  lecturas rápidas y alertas de vencimiento).

El sistema resuelve **15 consultas/servicios** (12 de lectura + 3 servicios que
mutan datos). La justificación técnica de los motores y el modelo de datos están
en [`informe/informe.md`](informe/informe.md).

---

## Requisitos

- [Docker](https://www.docker.com/) y Docker Compose.
- Python **3.11+**.

---

## Cómo correr el proyecto

### 1. Levantar la infraestructura (MongoDB + Redis)

```bash
docker compose up -d
```

Esto inicia los contenedores `vetsalud_mongo` (puerto `27017`) y `vetsalud_redis`
(puerto `6379`). Ambos tienen *healthcheck*; podés verificar el estado con:

```bash
docker compose ps
```

### 2. Crear el entorno e instalar dependencias

```bash
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Copiá el archivo de ejemplo (los valores por defecto ya apuntan a `localhost`):

```bash
cp .env.example .env        # En Windows: copy .env.example .env
```

| Variable     | Valor por defecto             | Descripción                  |
|--------------|-------------------------------|------------------------------|
| `MONGO_URI`  | `mongodb://localhost:27017`   | URI de conexión a MongoDB    |
| `MONGO_DB`   | `vetsalud`                    | Nombre de la base de datos   |
| `REDIS_HOST` | `localhost`                   | Host de Redis                |
| `REDIS_PORT` | `6379`                        | Puerto de Redis              |

### 4. Cargar los datos (ETL + registros adicionales)

```bash
python -m src.main etl
```

Ejecuta, en orden: `load_mongo` (CSV → MongoDB con limpieza), `load_redis`
(CSV → Redis) y `seed_extra` (≥10 registros propios por colección, diseñados
para que cada consulta devuelva resultados significativos).

> **Nota sobre fechas:** la fecha de referencia del proyecto es **2026-06-01**.
> Los registros adicionales incluyen consultas y vacunaciones con fechas
> relativas a esa fecha para que las consultas 5, 6, 11 y 12 devuelvan resultados.

### 5. Ejecutar las consultas

```bash
# Todas las consultas y servicios (imprime un ejemplo de cada uno):
python -m src.main all

# Una consulta puntual (q01 .. q15):
python -m src.main q07
python -m src.main q15

# Menú interactivo:
python -m src.main
```

Cada consulta también puede ejecutarse de forma aislada como módulo:

```bash
python -m src.queries.q01_pacientes_activos
python -m src.queries.q08_stock_bajo
```

---

## Ejecutar los tests

Con los contenedores levantados (paso 1; el ETL se ejecuta automáticamente
dentro de la fixture de pruebas):

```bash
python -m pytest
```

La suite (31 pruebas) cubre:

- **Limpieza del ETL** (`test_clean.py`): fechas, booleanos, números, `strip()`,
  normalización de categorías.
- **Carga** (`test_loaders.py`): cantidades mínimas por colección, tipos
  correctos en MongoDB y estructuras (`hash`, `set`, `sorted set`) en Redis.
- **Las 12 consultas de lectura** (`test_queries.py`).
- **Los 3 servicios mutadores** (`test_services.py`): ABM de propietarios,
  registro de consulta con validación y decremento de stock (incluyendo los
  casos de error).

Si MongoDB/Redis no están disponibles, las pruebas que dependen de la base se
omiten automáticamente (las unitarias de limpieza siguen corriendo).

---

## Estructura del proyecto

```
.
├── .devcontainer/devcontainer.json   # GitHub Codespaces
├── data/                             # CSV provistos por la cátedra
├── src/
│   ├── db/                           # conexiones (mongo.py, redis_client.py)
│   ├── loaders/                      # ETL: load_mongo, load_redis, seed_extra, clean
│   ├── queries/                      # q01..q15 (una consulta por módulo)
│   └── main.py                       # punto de entrada / menú
├── tests/                            # suite pytest
├── informe/informe.md                # informe técnico (base para el PDF)
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Las 15 consultas/servicios

| #  | Descripción                                                   | Motor   |
|----|---------------------------------------------------------------|---------|
| 1  | Pacientes activos con todos sus datos de propietario          | MongoDB |
| 2  | Consultas en 'Seguimiento' con veterinario y costo            | MongoDB |
| 3  | Historial completo de un paciente (consultas + vacunaciones)  | MongoDB |
| 4  | Propietarios con más de un paciente                           | MongoDB |
| 5  | Veterinarios activos y consultas en los últimos 60 días       | MongoDB |
| 6  | Pacientes con vacunas vencidas                                | MongoDB |
| 7  | Top 5 diagnósticos más frecuentes                             | MongoDB |
| 8  | Stock con menos de 50 unidades y su proveedor                 | **Redis** |
| 9  | Consultas de tipo 'Control' con costo < $5.000                | MongoDB |
| 10 | Pacientes de una sucursal (vía veterinario)                   | MongoDB |
| 11 | Ingresos totales por veterinario en el mes actual             | MongoDB |
| 12 | Propietarios sin consultas en el último año                   | MongoDB |
| 13 | ABM completo de propietarios (alta, modificación, baja lógica)| MongoDB |
| 14 | Registro de consulta con validación de paciente y veterinario | MongoDB |
| 15 | Decrementar unidades de un producto tras una consulta         | **Redis** |

---

## Detener la infraestructura

```bash
docker compose down            # detiene los contenedores
docker compose down -v         # además borra los volúmenes (datos persistidos)
```
