from datetime import datetime

# Fecha fija para reproducibilidad del CLI (python -m src.main all).
# La API usa datetime.now() en tiempo real pasando None a las funciones.
FECHA_REFERENCIA = datetime(2026, 6, 1)
