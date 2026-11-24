# Taller-ORM-Programaci-n-2
Taller evaluado, perteneciente al estudiante Simón Pedro Millanguir Zambrano y Benjamín Varela.

## Reportes de arriendos

Instala las dependencias con `python -m pip install -r requirements.txt` y abre la aplicación con `python main.py`. En la pestaña **Reportes**, el botón **Actualizar gráficos** vuelve a consultar `arriendos.db` en la raíz del proyecto.

- **Arriendos por categoría** muestra todas las categorías registradas, incluidas las que tienen cero operaciones. Usa la categoría actual del equipo asociado al arriendo.
- **Equipos con más arriendos** muestra hasta diez equipos con operaciones, ordenados de mayor a menor. Cada equipo se identifica por su nombre e ID.

Ambos gráficos incluyen arriendos activos y devueltos. Cada fila de `arriendos` cuenta como una operación, independientemente de las unidades de `cantidad`. Los gráficos muestran los datos guardados en SQLite y tienen un mensaje para los casos sin datos.

## Factory Method para equipamiento

En la pestaña **Equipos**, selecciona el **Tipo de equipamiento** al crear un equipo. La tabla muestra el tipo guardado y el formulario lo presenta como solo lectura al editar un equipo existente.

`CRUD.equipo.crear_equipo` acepta el argumento opcional `tipo` con los valores `general` (predeterminado), `proteccion` y `entrenamiento`. Por ejemplo, `crear_equipo(sesion, "Casco", categoria_id, 3500, 10, tipo="proteccion")` devuelve un `EquipoProteccion` persistido.

`CreadorEquipo` centraliza la validación del nombre, el precio y el stock. Su método `_crear_producto` permite que cada creador concreto construya la clase ORM de su tipo. Para agregar uno se puede definir un nuevo producto y su creador con las mismas validaciones y el mismo flujo de guardado.

SQLAlchemy guarda los tipos en la tabla `equipos` y reconstruye la clase correspondiente cuando los vuelve a leer. `categoria_id` sigue identificando la categoría que se usa en los reportes. Al abrir una base anterior, se agrega la columna `tipo` con el valor inicial `general` para sus equipos existentes.
