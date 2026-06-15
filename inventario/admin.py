from django.contrib import admin
from django.db.models import Count, Sum, F
from django.template.response import TemplateResponse
from django.utils import timezone

from .models import (
    Almacen, Categoria, Cliente, DetalleEntrada, DetalleSalida,
    Entrada, Inventario, Producto, Salida,
)


class EstadisticasMixin:
    index_title = 'Panel de control'

    def index(self, request, extra_context=None):
        return self.estadisticas_view(request)

    def estadisticas_view(self, request):
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)

        total_productos = Producto.objects.filter(activo=True).count()
        total_clientes = Cliente.objects.filter(activo=True).count()
        total_almacenes = Almacen.objects.filter(activo=True).count()

        stock_total = Inventario.objects.aggregate(total=Sum('cantidad'))['total'] or 0

        valor_inventario = Inventario.objects.select_related('producto').aggregate(
            total=Sum(F('cantidad') * F('producto__precio_compra'))
        )['total'] or 0

        productos_bajo_stock = Producto.objects.filter(activo=True).annotate(
            stock=Sum('inventarios__cantidad')
        ).filter(stock__lte=F('stock_minimo')).count()

        entradas_mes = Entrada.objects.filter(
            fecha__gte=inicio_mes, estado='confirmada'
        ).count()
        salidas_mes = Salida.objects.filter(
            fecha__gte=inicio_mes, estado='confirmada'
        ).count()

        ventas_mes = Salida.objects.filter(
            fecha__gte=inicio_mes, estado='confirmada', tipo='venta'
        ).prefetch_related('detalles')

        total_ventas_mes = sum(s.total_venta for s in ventas_mes)

        top_productos = (
            DetalleSalida.objects
            .filter(salida__estado='confirmada', salida__tipo='venta')
            .values('producto__nombre', 'producto__sku')
            .annotate(unidades=Sum('cantidad'))
            .order_by('-unidades')[:10]
        )

        stock_por_almacen = (
            Almacen.objects.filter(activo=True)
            .annotate(unidades=Sum('inventarios__cantidad'))
            .values('nombre', 'codigo', 'unidades')
            .order_by('-unidades')
        )

        stock_por_categoria = (
            Categoria.objects.filter(activa=True)
            .annotate(
                unidades=Sum('productos__inventarios__cantidad'),
                num_productos=Count('productos', distinct=True),
            )
            .values('nombre', 'unidades', 'num_productos')
            .order_by('-unidades')
        )

        ultimas_entradas = Entrada.objects.filter(estado='confirmada').order_by('-fecha')[:5]
        ultimas_salidas = Salida.objects.filter(estado='confirmada').order_by('-fecha')[:5]

        context = {
            **self.each_context(request),
            'title': 'Panel de control',
            'total_productos': total_productos,
            'total_clientes': total_clientes,
            'total_almacenes': total_almacenes,
            'stock_total': stock_total,
            'valor_inventario': valor_inventario,
            'productos_bajo_stock': productos_bajo_stock,
            'entradas_mes': entradas_mes,
            'salidas_mes': salidas_mes,
            'total_ventas_mes': total_ventas_mes,
            'top_productos': top_productos,
            'stock_por_almacen': stock_por_almacen,
            'stock_por_categoria': stock_por_categoria,
            'ultimas_entradas': ultimas_entradas,
            'ultimas_salidas': ultimas_salidas,
        }
        return TemplateResponse(request, 'admin/estadisticas.html', context)


admin.site.__class__ = type(
    'JazzminAdminSite',
    (EstadisticasMixin, admin.site.__class__),
    {},
)


class DetalleEntradaInline(admin.TabularInline):
    model = DetalleEntrada
    extra = 1
    autocomplete_fields = ['producto']


class DetalleSalidaInline(admin.TabularInline):
    model = DetalleSalida
    extra = 1
    autocomplete_fields = ['producto']


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa', 'creado_en']
    list_filter = ['activa']
    search_fields = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        'sku', 'nombre', 'categoria', 'marca', 'talla', 'color',
        'precio_venta', 'stock_display', 'bajo_stock_display', 'activo',
    ]
    list_filter = ['categoria', 'genero', 'temporada', 'talla', 'activo']
    search_fields = ['sku', 'nombre', 'marca', 'color']
    autocomplete_fields = ['categoria']
    readonly_fields = ['creado_en', 'actualizado_en', 'stock_total']
    fieldsets = (
        ('Identificación', {
            'fields': ('sku', 'nombre', 'descripcion', 'categoria', 'imagen'),
        }),
        ('Características de ropa', {
            'fields': ('marca', 'talla', 'color', 'genero', 'temporada'),
        }),
        ('Precios y stock', {
            'fields': ('precio_compra', 'precio_venta', 'stock_minimo', 'stock_total'),
        }),
        ('Estado', {
            'fields': ('activo', 'creado_en', 'actualizado_en'),
        }),
    )

    @admin.display(description='Stock')
    def stock_display(self, obj):
        return obj.stock_total

    @admin.display(description='Bajo stock', boolean=True)
    def bajo_stock_display(self, obj):
        return obj.bajo_stock


@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'ciudad', 'responsable', 'total_productos_display', 'activo']
    list_filter = ['activo', 'ciudad']
    search_fields = ['codigo', 'nombre', 'ciudad']

    @admin.display(description='Unidades')
    def total_productos_display(self, obj):
        return obj.total_productos


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ['producto', 'almacen', 'cantidad', 'actualizado_en']
    list_filter = ['almacen', 'producto__categoria']
    search_fields = ['producto__sku', 'producto__nombre', 'almacen__nombre']
    autocomplete_fields = ['producto', 'almacen']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo', 'telefono', 'ciudad', 'activo']
    list_filter = ['tipo', 'activo', 'ciudad']
    search_fields = ['codigo', 'nombre', 'email', 'telefono']


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = [
        'folio', 'almacen', 'proveedor', 'fecha', 'estado',
        'total_unidades_display', 'total_costo_display',
    ]
    list_filter = ['estado', 'almacen', 'fecha']
    search_fields = ['folio', 'proveedor']
    readonly_fields = ['folio', 'creado_en', 'actualizado_en']
    autocomplete_fields = ['almacen']
    inlines = [DetalleEntradaInline]
    date_hierarchy = 'fecha'

    @admin.display(description='Unidades')
    def total_unidades_display(self, obj):
        return obj.total_unidades

    @admin.display(description='Costo total')
    def total_costo_display(self, obj):
        return f'${obj.total_costo:,.2f}'


@admin.register(Salida)
class SalidaAdmin(admin.ModelAdmin):
    list_display = [
        'folio', 'tipo', 'almacen', 'cliente', 'fecha', 'estado',
        'total_unidades_display', 'total_venta_display',
    ]
    list_filter = ['tipo', 'estado', 'almacen', 'fecha']
    search_fields = ['folio', 'cliente__nombre']
    readonly_fields = ['folio', 'creado_en', 'actualizado_en']
    autocomplete_fields = ['almacen', 'cliente']
    inlines = [DetalleSalidaInline]
    date_hierarchy = 'fecha'

    @admin.display(description='Unidades')
    def total_unidades_display(self, obj):
        return obj.total_unidades

    @admin.display(description='Total')
    def total_venta_display(self, obj):
        return f'${obj.total_venta:,.2f}'
