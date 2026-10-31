"""Respaldo consistente de SQLite antes de ampliar el esquema existente."""
from pathlib import Path
from datetime import datetime, timezone
import os
import sqlite3
import tempfile


def respaldar_antes_de_actualizar(engine, permitir_base_nueva=False):
    if engine.url.get_backend_name() != 'sqlite':
        return None
    ruta = engine.url.database
    if ruta in (None, '', ':memory:'):
        return None
    origen = Path(ruta).resolve()
    if not origen.is_file():
        if permitir_base_nueva:
            return None
        raise RuntimeError('No se encontró la base SQLite existente. Se detuvo el inicio para no crear una base vacía. Revisa la ruta del disco persistente.')
    requeridas = {
        'bitacora_turno': {'observaciones_recepcion'},
        'control_vehiculo': {'nota', 'salida_sin_entrada'},
        'bitacora_servicio': {'version'},
        'bitacora_tarea': {'version'},
        'bitacora_anotacion': {'texto'},
        'bitacora_evento': {'detalle'},
    }
    # mode=ro evita crear o escribir en el original durante la inspección.
    conexion = sqlite3.connect(origen.as_uri() + '?mode=ro', uri=True, timeout=30)
    try:
        tablas = {fila[0] for fila in conexion.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not permitir_base_nueva and 'usuarios' not in tablas:
            raise RuntimeError('La base configurada no contiene la tabla de usuarios existente. Revisa el disco antes de actualizar.')
        pendiente = any(tabla not in tablas or not columnas.issubset(
            {fila[1] for fila in conexion.execute(f'PRAGMA table_info("{tabla}")')}
        ) for tabla, columnas in requeridas.items())
        if not pendiente:
            return None
        carpeta = origen.parent / 'backups'
        carpeta.mkdir(exist_ok=True)
        fecha = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        descriptor, nombre = tempfile.mkstemp(prefix=f'antes_actualizacion_{fecha}_', suffix='.db', dir=carpeta)
        os.close(descriptor)
        destino = sqlite3.connect(nombre)
        try:
            conexion.backup(destino, pages=256, sleep=0.1)
            if destino.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise RuntimeError('El respaldo no superó la verificación; no se modificará el esquema.')
        finally:
            destino.close()
        return nombre
    finally:
        conexion.close()
