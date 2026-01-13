from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.core.mail import EmailMessage
from django.contrib import messages
import csv
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from .models import Cliente, Inmueble, Contrato, Factura, Pago


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id_cliente', 'dni', 'nombre', 'apellidos', 'telefono', 'direccion')
    search_fields = ('dni', 'nombre', 'apellidos')
    list_per_page = 20


@admin.register(Inmueble)
class InmuebleAdmin(admin.ModelAdmin):
    list_display = ('id_inmueble', 'direccion', 'metros_cuadrados', 'tipo_operacion', 'precio', 'estado')
    list_filter = ('tipo_operacion', 'estado')
    search_fields = ('direccion', 'descripcion')
    list_per_page = 20


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ('id_contrato', 'cliente', 'inmueble', 'fecha_inicio', 'fecha_fin', 'tipo_contrato')
    list_filter = ('tipo_contrato', 'fecha_inicio')
    search_fields = (
        'cliente__nombre',
        'cliente__apellidos',
        'cliente__dni',
        'inmueble__direccion'
    )
    raw_id_fields = ('cliente', 'inmueble')
    list_per_page = 20


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('id_factura', 'contrato', 'fecha_factura', 'subtotal', 'iva_display', 'total_display', 'descargar_pdf')
    search_fields = (
        'contrato__cliente__nombre',
        'contrato__cliente__apellidos',
        'contrato__inmueble__direccion'
    )
    list_filter = ('fecha_factura',)
    raw_id_fields = ('contrato',)
    list_per_page = 20

    fields = ('contrato', 'fecha_factura', 'subtotal')
    readonly_fields = ('id_factura', 'iva_display', 'total_display', 'descargar_pdf')

    # ✅ ACCIONES: ¡aquí está el botón!
    actions = ['enviar_factura_email', 'exportar_facturas_csv', 'exportar_facturas_excel']

    def iva_display(self, obj):
        if obj.pk:
            iva = obj.get_iva_from_db()
            if iva is not None:
                from .views import formatear_euros
                return formatear_euros(iva)
        return "—"
    iva_display.short_description = "IVA"

    def total_display(self, obj):
        if obj.pk:
            total = obj.get_total_from_db()
            if total is not None:
                from .views import formatear_euros
                return formatear_euros(total)
        return "—"
    total_display.short_description = "Total"

    def descargar_pdf(self, obj):
        if obj.pk:
            url = reverse('admin_descargar_factura_pdf', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" target="_blank" '
                'style="padding:5px 10px; background:#447e9b; color:white; text-decoration:none; border-radius:3px;">📄 PDF</a>',
                url
            )
        return mark_safe('<span style="color:gray;">Sin guardar</span>')
    descargar_pdf.short_description = "Descargar PDF"

    # === BOTÓN: Enviar por email ===
    def enviar_factura_email(self, request, queryset):
        from django.test import RequestFactory
        from .views import admin_descargar_factura_pdf

        for factura in queryset:
            if not factura.pk:
                messages.error(request, "No se puede enviar una factura no guardada.")
                continue

            cliente = factura.contrato.cliente
            # Si el cliente tiene email, se usa; si no, va a tu correo
            destinatario = getattr(cliente, 'email', None) or 'juangcyc@gmail.com'

            # Generar PDF en memoria
            factory = RequestFactory()
            fake_request = factory.get('/')
            fake_request.user = request.user
            pdf_response = admin_descargar_factura_pdf(fake_request, factura.id_factura)

            # Crear el correo
            subject = f"Factura FAC-{factura.fecha_factura.year}-{factura.id_factura:04d}"
            body = f"""
Estimado/a {cliente.nombre} {cliente.apellidos},

Adjuntamos su factura de alquiler correspondiente al mes de {factura.fecha_factura.strftime('%B %Y')}.

Gracias por su confianza en Inmobiliaria Soluciones.
            """.strip()

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email='Inmobiliaria Soluciones <juangcyc@gmail.com>',
                to=[destinatario],
            )
            email.attach(f"factura_{factura.id_factura}.pdf", pdf_response.content, 'application/pdf')

            try:
                email.send()
                messages.success(request, f"✅ Factura {factura.id_factura} enviada a {destinatario}.")
            except Exception as e:
                messages.error(request, f"❌ Error: {str(e)}")

    enviar_factura_email.short_description = "📧 Enviar factura por correo electrónico"

    # === Exportar a CSV ===
    def exportar_facturas_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="facturas.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Cliente', 'Inmueble', 'Fecha', 'Subtotal', 'IVA', 'Total'])
        for f in queryset:
            iva = f.get_iva_from_db() or (f.subtotal * 0.21)
            total = f.get_total_from_db() or (f.subtotal * 1.21)
            writer.writerow([
                f.id_factura,
                str(f.contrato.cliente),
                f.contrato.inmueble.direccion,
                f.fecha_factura.strftime('%Y-%m-%d'),
                f.subtotal,
                iva,
                total
            ])
        return response

    exportar_facturas_csv.short_description = "📤 Exportar a CSV"

    # === Exportar a Excel ===
    def exportar_facturas_excel(self, request, queryset):
        wb = Workbook()
        ws = wb.active
        ws.title = "Facturas"
        headers = ['ID', 'Cliente', 'Inmueble', 'Fecha', 'Subtotal', 'IVA', 'Total']
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for f in queryset:
            iva = f.get_iva_from_db() or (f.subtotal * 0.21)
            total = f.get_total_from_db() or (f.subtotal * 1.21)
            ws.append([
                f.id_factura,
                str(f.contrato.cliente),
                f.contrato.inmueble.direccion,
                f.fecha_factura.strftime('%Y-%m-%d'),
                float(f.subtotal),
                float(iva),
                float(total)
            ])
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=facturas.xlsx'
        wb.save(response)
        return response

    exportar_facturas_excel.short_description = "📊 Exportar a Excel"


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id_pago', 'factura', 'monto_pagado', 'fecha_pago', 'estado')
    list_filter = ('estado', 'fecha_pago')
    search_fields = (
        'factura__id_factura',
        'factura__contrato__cliente__nombre',
        'factura__contrato__cliente__apellidos'
    )
    raw_id_fields = ('factura',)
    list_per_page = 20