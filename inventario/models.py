from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, F
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    TALLAS = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
        ('28', '28'),
        ('30', '30'),
        ('32', '32'),
        ('34', '34'),
        ('36', '36'),
        ('38', '38'),
        ('40', '40'),
        ('UNICA', 'Única'),
    ]

    sku = models.CharField('SKU', max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='productos'
    )
    marca = models.CharField(max_length=100, blank=True)
    talla = models.CharField(max_length=10, choices=TALLAS, default='M')
    color = models.CharField(max_length=50)
    genero = models.CharField(
        max_length=20,
        choices=[
            ('hombre', 'Hombre'),
            ('mujer', 'Mujer'),
            ('unisex', 'Unisex'),
            ('nino', 'Niño/a'),
        ],
        default='unisex',
    )
    temporada = models.CharField(
        max_length=20,
        choices=[
            ('verano', 'Verano'),
            ('invierno', 'Invierno'),
            ('primavera', 'Primavera'),
            ('otono', 'Otoño'),
            ('todo', 'Todo el año'),
        ],
        default='todo',
    )
    precio_compra = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    precio_venta = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    stock_minimo = models.PositiveIntegerField(default=5)
    activo = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre', 'talla', 'color']

    def __str__(self):
        return f'{self.sku} - {self.nombre} ({self.talla}/{self.color})'

    @property
    def stock_total(self):
        return self.inventarios.aggregate(total=Sum('cantidad'))['total'] or 0

    @property
    def bajo_stock(self):
        return self.stock_total <= self.stock_minimo


class Almacen(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    responsable = models.CharField(max_length=150, blank=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Almacén'
        verbose_name_plural = 'Almacenes'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'

    @property
    def total_productos(self):
        return self.inventarios.aggregate(total=Sum('cantidad'))['total'] or 0


class Inventario(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name='inventarios'
    )
    almacen = models.ForeignKey(
        Almacen, on_delete=models.CASCADE, related_name='inventarios'
    )
    cantidad = models.PositiveIntegerField(default=0)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Inventario'
        verbose_name_plural = 'Inventarios'
        unique_together = ['producto', 'almacen']
        ordering = ['almacen', 'producto']

    def __str__(self):
        return f'{self.producto} en {self.almacen}: {self.cantidad} uds.'


class Cliente(models.Model):
    TIPOS = [
        ('minorista', 'Minorista'),
        ('mayorista', 'Mayorista'),
        ('distribuidor', 'Distribuidor'),
    ]

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='minorista')
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class Entrada(models.Model):
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]

    folio = models.CharField(max_length=30, unique=True, editable=False)
    almacen = models.ForeignKey(
        Almacen, on_delete=models.PROTECT, related_name='entradas'
    )
    proveedor = models.CharField(max_length=200, help_text='Nombre del proveedor')
    fecha = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entrada'
        verbose_name_plural = 'Entradas'
        ordering = ['-fecha', '-creado_en']

    def __str__(self):
        return f'{self.folio} - {self.almacen}'

    def save(self, *args, **kwargs):
        if not self.folio:
            numero = Entrada.objects.count() + 1
            self.folio = f'ENT-{timezone.now().year}-{numero:05d}'
        super().save(*args, **kwargs)

    @property
    def total_unidades(self):
        return self.detalles.aggregate(total=Sum('cantidad'))['total'] or 0

    @property
    def total_costo(self):
        return sum(d.subtotal for d in self.detalles.all())


class DetalleEntrada(models.Model):
    entrada = models.ForeignKey(
        Entrada, on_delete=models.CASCADE, related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='detalles_entrada'
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    costo_unitario = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        verbose_name = 'Detalle de entrada'
        verbose_name_plural = 'Detalles de entrada'

    def __str__(self):
        return f'{self.producto} x{self.cantidad}'

    @property
    def subtotal(self):
        return self.cantidad * self.costo_unitario


class Salida(models.Model):
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]
    TIPOS = [
        ('venta', 'Venta'),
        ('devolucion', 'Devolución a proveedor'),
        ('transferencia', 'Transferencia entre almacenes'),
        ('ajuste', 'Ajuste de inventario'),
    ]

    folio = models.CharField(max_length=30, unique=True, editable=False)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='venta')
    almacen = models.ForeignKey(
        Almacen, on_delete=models.PROTECT, related_name='salidas'
    )
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name='salidas',
        blank=True, null=True,
    )
    fecha = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Salida'
        verbose_name_plural = 'Salidas'
        ordering = ['-fecha', '-creado_en']

    def __str__(self):
        return f'{self.folio} - {self.get_tipo_display()}'

    def save(self, *args, **kwargs):
        if not self.folio:
            numero = Salida.objects.count() + 1
            self.folio = f'SAL-{timezone.now().year}-{numero:05d}'
        super().save(*args, **kwargs)

    @property
    def total_unidades(self):
        return self.detalles.aggregate(total=Sum('cantidad'))['total'] or 0

    @property
    def total_venta(self):
        return sum(d.subtotal for d in self.detalles.all())


class DetalleSalida(models.Model):
    salida = models.ForeignKey(
        Salida, on_delete=models.CASCADE, related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name='detalles_salida'
    )
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        verbose_name = 'Detalle de salida'
        verbose_name_plural = 'Detalles de salida'

    def __str__(self):
        return f'{self.producto} x{self.cantidad}'

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
