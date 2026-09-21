# Auditoria de cambios

La funcion `auditar_cambio_fila()` intenta leer el usuario autenticado desde la variable de sesion PostgreSQL `app.user_id`.

El backend debe establecerla dentro de la misma transaccion que modifica datos:

```sql
SET LOCAL app.user_id = 'uuid-del-usuario-autenticado';
```

`SET LOCAL` limita el valor a la transaccion actual y evita que el usuario de una peticion se reutilice en otra conexion del pool.

Si la peticion no tiene usuario autenticado, la auditoria conserva el cambio con `id_usuario = NULL`. La aplicacion debe establecer esta variable antes de actualizar solicitudes, ofertas, financiaciones, polizas, desembolsos o productos de aliados.

La columna `fecha_actualizacion` se excluye intencionalmente de `auditoria_cambio`, porque es un campo de infraestructura actualizado automaticamente por trigger.
