from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Entrada, Inventario, Salida


@receiver(pre_save, sender=Entrada)
def entrada_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            anterior = Entrada.objects.get(pk=instance.pk)
            instance._estado_anterior = anterior.estado
        except Entrada.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(pre_save, sender=Salida)
def salida_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            anterior = Salida.objects.get(pk=instance.pk)
            instance._estado_anterior = anterior.estado
        except Salida.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=Entrada)
def entrada_post_save(sender, instance, **kwargs):
    estado_anterior = getattr(instance, '_estado_anterior', None)
    if instance.estado == 'confirmada' and estado_anterior != 'confirmada':
        _aplicar_entrada(instance)
    elif estado_anterior == 'confirmada' and instance.estado != 'confirmada':
        _revertir_entrada(instance)


@receiver(post_save, sender=Salida)
def salida_post_save(sender, instance, **kwargs):
    estado_anterior = getattr(instance, '_estado_anterior', None)
    if instance.estado == 'confirmada' and estado_anterior != 'confirmada':
        _aplicar_salida(instance)
    elif estado_anterior == 'confirmada' and instance.estado != 'confirmada':
        _revertir_salida(instance)


def _aplicar_entrada(entrada):
    with transaction.atomic():
        for detalle in entrada.detalles.select_related('producto'):
            inventario, _ = Inventario.objects.get_or_create(
                producto=detalle.producto,
                almacen=entrada.almacen,
                defaults={'cantidad': 0},
            )
            inventario.cantidad += detalle.cantidad
            inventario.save(update_fields=['cantidad', 'actualizado_en'])


def _revertir_entrada(entrada):
    with transaction.atomic():
        for detalle in entrada.detalles.select_related('producto'):
            inventario = Inventario.objects.filter(
                producto=detalle.producto, almacen=entrada.almacen
            ).first()
            if inventario:
                inventario.cantidad = max(0, inventario.cantidad - detalle.cantidad)
                inventario.save(update_fields=['cantidad', 'actualizado_en'])


def _aplicar_salida(salida):
    with transaction.atomic():
        for detalle in salida.detalles.select_related('producto'):
            inventario = Inventario.objects.filter(
                producto=detalle.producto, almacen=salida.almacen
            ).first()
            stock = inventario.cantidad if inventario else 0
            if stock < detalle.cantidad:
                raise ValueError(
                    f'Stock insuficiente de {detalle.producto} en {salida.almacen} '
                    f'(disponible: {stock}, solicitado: {detalle.cantidad})'
                )
            inventario.cantidad -= detalle.cantidad
            inventario.save(update_fields=['cantidad', 'actualizado_en'])


def _revertir_salida(salida):
    with transaction.atomic():
        for detalle in salida.detalles.select_related('producto'):
            inventario, _ = Inventario.objects.get_or_create(
                producto=detalle.producto,
                almacen=salida.almacen,
                defaults={'cantidad': 0},
            )
            inventario.cantidad += detalle.cantidad
            inventario.save(update_fields=['cantidad', 'actualizado_en'])
