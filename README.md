# Sistema de Inventario - Tienda de Ropa

Sistema básico de gestión de inventario para una tienda de ropa, construido con **Django**, **PostgreSQL**, **Docker** y el panel de administración mejorado con **django-jazzmin**.

## Características

- **Productos**: SKU, talla, color, marca, género, temporada, precios
- **Categorías**: Camisetas, pantalones, vestidos, etc.
- **Almacenes**: Múltiples ubicaciones de stock
- **Inventario**: Stock por producto y almacén (actualización automática)
- **Entradas**: Recepción de mercancía de proveedores
- **Salidas**: Ventas, devoluciones, transferencias y ajustes
- **Clientes**: Minoristas, mayoristas y distribuidores
- **Estadísticas**: Dashboard con métricas de inventario y ventas

## Requisitos

- [Docker](https://www.docker.com/) y Docker Compose

## Inicio rápido

```bash
# 1. Copiar variables de entorno (si no existe .env)
cp .env.example .env

# 2. Levantar los servicios (migra BD y ejecuta seed automáticamente)
docker compose up --build
```

Abre el panel de administración en: **http://localhost:8000/admin/**

Al levantar el sistema se ejecuta automáticamente el seeder con upsert. Credenciales:
- Usuario: `admin`
- Contraseña: `admin123`

## Estructura del proyecto

```
├── config/              # Configuración Django
├── inventario/          # App principal
│   ├── models.py        # Modelos de datos
│   ├── admin.py         # Panel de administración
│   ├── signals.py       # Actualización automática de stock
│   └── management/      # Comandos personalizados
├── templates/admin/     # Vista de estadísticas
├── docker-compose.yml   # Orquestación Docker
├── Dockerfile
└── requirements.txt
```

## Flujo de trabajo

### Registrar una entrada (compra a proveedor)

1. Ir a **Entradas** → **Agregar entrada**
2. Seleccionar almacén y proveedor
3. Agregar productos en la sección de detalles (inline)
4. Guardar en estado **Borrador**
5. Cambiar estado a **Confirmada** → el stock se actualiza automáticamente

### Registrar una salida (venta)

1. Ir a **Salidas** → **Agregar salida**
2. Tipo: Venta, seleccionar almacén y cliente
3. Agregar productos vendidos con cantidad y precio
4. Confirmar la salida → el stock se descuenta automáticamente

### Ver estadísticas

El **Panel de control** (`/admin/`) muestra el dashboard de estadísticas al iniciar sesión.

### Logo personalizado

Coloca tu imagen en:

```
static/img/logo.png
```

Se mostrará en el login y en la barra lateral del panel. Ver `static/img/LEEME.txt` para más detalles.

### Modo claro / oscuro

Usa el botón de sol/luna en la barra superior del panel para alternar entre temas.

## Comandos útiles

```bash
# Ver logs
docker compose logs -f web

# Ejecutar migraciones
docker compose exec web python manage.py migrate

# Crear migraciones
docker compose exec web python manage.py makemigrations

# Detener servicios
docker compose down

# Detener y eliminar volúmenes (borra la BD)
docker compose down -v
```

## Desarrollo local (sin Docker)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Configurar POSTGRES_HOST=localhost en .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Tecnologías

- Django 5.x
- PostgreSQL 16
- django-jazzmin 3.x
- Docker & Docker Compose
- WhiteNoise (archivos estáticos)
