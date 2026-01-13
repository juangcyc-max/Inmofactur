# facturacion/models.py
from django.db import models

class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    dni = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)  # ← AÑADIDO

    class Meta:
        db_table = 'clientes'
        ordering = ['apellidos', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"


class Inmueble(models.Model):
    id_inmueble = models.AutoField(primary_key=True)
    direccion = models.TextField()
    metros_cuadrados = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    TIPO_OPERACION_CHOICES = [('alquiler', 'Alquiler'), ('venta', 'Venta')]
    tipo_operacion = models.CharField(max_length=10, choices=TIPO_OPERACION_CHOICES)
    ESTADO_CHOICES = [('disponible', 'Disponible'), ('ocupado', 'Ocupado'), ('vendido', 'Vendido')]
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='disponible')
    precio = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'inmuebles'

    def __str__(self):
        return self.direccion


class Contrato(models.Model):
    id_contrato = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column='id_cliente')
    inmueble = models.ForeignKey(Inmueble, on_delete=models.CASCADE, db_column='id_inmueble')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    TIPO_CONTRATO_CHOICES = [('alquiler', 'Alquiler'), ('venta', 'Venta')]
    tipo_contrato = models.CharField(max_length=10, choices=TIPO_CONTRATO_CHOICES)

    class Meta:
        db_table = 'contratos'

    def __str__(self):
        return f"Contrato {self.id_contrato}"


class Factura(models.Model):
    id_factura = models.AutoField(primary_key=True)
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, db_column='id_contrato')
    fecha_factura = models.DateField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'facturas'

    def __str__(self):
        return f"Factura {self.id_factura}"

    def get_iva_from_db(self):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT iva FROM facturas WHERE id_factura = %s", [self.id_factura])
            row = cursor.fetchone()
            return row[0] if row else None

    def get_total_from_db(self):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT total FROM facturas WHERE id_factura = %s", [self.id_factura])
            row = cursor.fetchone()
            return row[0] if row else None


class Pago(models.Model):
    id_pago = models.AutoField(primary_key=True)
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, db_column='id_factura')
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateField()
    ESTADO_CHOICES = [('pendiente', 'Pendiente'), ('pagado', 'Pagado')]
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES)

    class Meta:
        db_table = 'pagos'

    def __str__(self):
        return f"Pago {self.id_pago}"