from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

from inventario.models import (
    Almacen, Categoria, Cliente, DetalleEntrada,
    Entrada, Producto,
)

ENTRADA_SEED_FOLIO = 'ENT-SEED-00001'


class Command(BaseCommand):
    help = 'Carga o actualiza datos de ejemplo para una tienda de ropa (upsert)'

    def _upsert_superusuario(self):
        User = get_user_model()
        user, created = User.objects.update_or_create(
            username='admin',
            defaults={
                'email': 'admin@tienda.com',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        user.set_password('admin123')
        user.save(update_fields=['password'])

        accion = 'creado' if created else 'actualizado'
        self.stdout.write(self.style.SUCCESS(f'Superusuario {accion}: admin / admin123'))

    def _upsert_categorias(self):
        categorias_data = [
            ('Camisetas', 'Camisetas y tops'),
            ('Pantalones', 'Jeans, pantalones y shorts'),
            ('Vestidos', 'Vestidos y faldas'),
            ('Chaquetas', 'Chaquetas y abrigos'),
            ('Accesorios', 'Cinturones, bufandas y más'),
        ]
        for nombre, desc in categorias_data:
            Categoria.objects.update_or_create(
                nombre=nombre,
                defaults={'descripcion': desc, 'activa': True},
            )

    def _upsert_almacenes(self):
        almacenes_data = [
            ('ALM-01', 'Almacén Central', 'Av. Principal 100', 'Ciudad de México'),
            ('ALM-02', 'Tienda Centro', 'Calle Reforma 50', 'Ciudad de México'),
            ('ALM-03', 'Tienda Norte', 'Blvd. Norte 200', 'Monterrey'),
        ]
        for codigo, nombre, direccion, ciudad in almacenes_data:
            Almacen.objects.update_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'direccion': direccion,
                    'ciudad': ciudad,
                    'activo': True,
                },
            )

    def _upsert_clientes(self):
        clientes_data = [
            ('CLI-001', 'María García', 'minorista'),
            ('CLI-002', 'Boutique Elegance', 'mayorista'),
            ('CLI-003', 'Tienda Moda Express', 'distribuidor'),
        ]
        for codigo, nombre, tipo in clientes_data:
            Cliente.objects.update_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'tipo': tipo,
                    'email': f'{codigo.lower()}@email.com',
                    'activo': True,
                },
            )

    def _upsert_productos(self):
        cat_camisetas = Categoria.objects.get(nombre='Camisetas')
        cat_pantalones = Categoria.objects.get(nombre='Pantalones')
        cat_vestidos = Categoria.objects.get(nombre='Vestidos')

        productos_data = [
            ('CAM-001-M-BL', 'Camiseta Básica Algodón', cat_camisetas, 'BasicWear', 'M', 'Blanco', 'unisex', Decimal('80'), Decimal('199')),
            ('CAM-002-L-NG', 'Camiseta Estampada', cat_camisetas, 'UrbanStyle', 'L', 'Negro', 'hombre', Decimal('120'), Decimal('299')),
            ('PAN-001-32-AZ', 'Jeans Slim Fit', cat_pantalones, 'DenimCo', '32', 'Azul', 'hombre', Decimal('250'), Decimal('599')),
            ('PAN-002-M-GR', 'Pantalón Chino', cat_pantalones, 'ClassicFit', 'M', 'Gris', 'mujer', Decimal('200'), Decimal('449')),
            ('VES-001-M-RJ', 'Vestido Floral Verano', cat_vestidos, 'FloraModa', 'M', 'Rosa', 'mujer', Decimal('300'), Decimal('699')),
            ('VES-002-S-AZ', 'Vestido Casual', cat_vestidos, 'FloraModa', 'S', 'Azul', 'mujer', Decimal('280'), Decimal('649')),
        ]
        for sku, nombre, cat, marca, talla, color, genero, pc, pv in productos_data:
            Producto.objects.update_or_create(
                sku=sku,
                defaults={
                    'nombre': nombre,
                    'categoria': cat,
                    'marca': marca,
                    'talla': talla,
                    'color': color,
                    'genero': genero,
                    'precio_compra': pc,
                    'precio_venta': pv,
                    'activo': True,
                },
            )

    def _upsert_entrada_ejemplo(self):
        almacen_central = Almacen.objects.get(codigo='ALM-01')
        productos = list(Producto.objects.filter(
            sku__in=['CAM-001-M-BL', 'CAM-002-L-NG', 'PAN-001-32-AZ', 'PAN-002-M-GR']
        ))

        entrada, created = Entrada.objects.get_or_create(
            folio=ENTRADA_SEED_FOLIO,
            defaults={
                'almacen': almacen_central,
                'proveedor': 'Distribuidora Textil MX',
                'estado': 'borrador',
            },
        )

        if not created:
            Entrada.objects.filter(pk=entrada.pk).update(
                almacen=almacen_central,
                proveedor='Distribuidora Textil MX',
            )
            entrada.refresh_from_db()

        for producto in productos:
            DetalleEntrada.objects.update_or_create(
                entrada=entrada,
                producto=producto,
                defaults={
                    'cantidad': 50,
                    'costo_unitario': producto.precio_compra,
                },
            )

        if entrada.estado == 'borrador':
            entrada.estado = 'confirmada'
            entrada.save(update_fields=['estado', 'actualizado_en'])

        accion = 'creada' if created else 'actualizada'
        self.stdout.write(self.style.SUCCESS(f'Entrada de ejemplo {accion}: {entrada.folio}'))

    def handle(self, *args, **options):
        self._upsert_superusuario()
        self._upsert_categorias()
        self._upsert_almacenes()
        self._upsert_clientes()
        self._upsert_productos()
        self._upsert_entrada_ejemplo()

        self.stdout.write(self.style.SUCCESS('Seed completado (upsert).'))
