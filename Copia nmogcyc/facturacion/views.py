# -*- coding: utf-8 -*-
import os
import json
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage
from django.db import IntegrityError
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from .models import Factura, Cliente, Contrato, Inmueble, Pago


def formatear_euros(valor):
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return "0,00 €"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def _generar_pdf(factura_id):
    factura = get_object_or_404(Factura, id_factura=factura_id)
    cliente = factura.contrato.cliente
    inmueble = factura.contrato.inmueble

    iva = factura.get_iva_from_db()
    total = factura.get_total_from_db()
    if iva is None or total is None:
        iva = float(factura.subtotal) * 0.21
        total = float(factura.subtotal) * 1.21

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{factura.id_factura}.pdf"'
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Marca de agua
    logo_path = os.path.join(settings.BASE_DIR, 'facturacion', 'static', 'imagenes', 'logoinmogcyc.png')
    if os.path.exists(logo_path):
        try:
            p.saveState()
            p.setFillAlpha(0.07)
            margin = 30
            logo_width = width - 2 * margin
            logo_height = height - 2 * margin
            x = margin
            y = margin
            p.drawImage(
                logo_path,
                x, y,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                anchor='c',
                mask='auto'
            )
            p.restoreState()
        except Exception as e:
            print("Error al cargar logo:", e)

    # Contenido principal
    left_margin = 50
    right_margin = width - 50
    top_margin = height - 50
    p.setFont("Helvetica-Bold", 16)
    p.drawString(left_margin, top_margin, "INMOBILIARIA SOLUCIONES")
    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    company_lines = [
        "CIF: B-12345678",
        "Calle Gran Vía, 123 • 28001 Madrid",
        "Tel: 910 000 000 • Email: info@inmobiliariasoluciones.es"
    ]
    y = top_margin - 20
    for line in company_lines:
        p.drawString(left_margin, y, line)
        y -= 14
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    p.drawRightString(right_margin, top_margin, "FACTURA")
    p.setFont("Helvetica", 11)
    p.drawRightString(right_margin, top_margin - 20, f"Nº: FAC-{factura.fecha_factura.year}-{factura.id_factura:04d}")
    p.drawRightString(right_margin, top_margin - 35, f"Fecha: {factura.fecha_factura.strftime('%d/%m/%Y')}")
    p.line(left_margin, y - 10, right_margin, y - 10)
    y = y - 30
    p.setFont("Helvetica-Bold", 11)
    p.drawString(left_margin, y, "Cliente")
    p.setFont("Helvetica", 10)
    y -= 20
    p.drawString(left_margin, y, f"{cliente.nombre} {cliente.apellidos}")
    y -= 16
    p.drawString(left_margin, y, f"DNI: {cliente.dni}")
    y -= 16
    p.drawString(left_margin, y, f"Dirección: {cliente.direccion}")
    y -= 16
    p.drawString(left_margin, y, f"Teléfono: {cliente.telefono or '—'}")
    y -= 25
    p.setFont("Helvetica-Bold", 11)
    p.drawString(left_margin, y, "Inmueble alquilado")
    p.setFont("Helvetica", 10)
    y -= 20
    p.drawString(left_margin, y, inmueble.direccion)
    y -= 40
    p.setFont("Helvetica-Bold", 11)
    p.drawString(left_margin, y, "Concepto")
    p.drawRightString(right_margin - 100, y, "Base imponible")
    p.drawRightString(right_margin, y, "Importe")
    y -= 20
    p.line(left_margin, y, right_margin, y)
    y -= 25
    p.setFont("Helvetica", 10)
    concepto = f"Alquiler mensual - {factura.fecha_factura.strftime('%B %Y').capitalize()}"
    p.drawString(left_margin, y, concepto)
    p.drawRightString(right_margin - 100, y, formatear_euros(factura.subtotal))
    p.drawRightString(right_margin, y, formatear_euros(factura.subtotal))
    y -= 30
    p.drawString(left_margin, y, "IVA (21%)")
    p.drawRightString(right_margin, y, formatear_euros(iva))
    y -= 25
    p.setFont("Helvetica-Bold", 12)
    p.drawString(left_margin, y, "TOTAL FACTURA")
    p.drawRightString(right_margin, y, formatear_euros(total))
    y -= 40
    p.setFont("Helvetica", 8)
    p.setFillColor(colors.grey)
    p.drawString(left_margin, 80, "• Esta factura se emite conforme al contrato de alquiler.")
    p.drawString(left_margin, 65, "• El pago se considerará efectivo al recibir justificante bancario.")
    p.drawString(left_margin, 50, "• Documento válido sin firma física.")
    p.drawRightString(right_margin, 50, "Gracias por confiar en nosotros.")
    p.setFillColor(colors.black)
    p.showPage()
    p.save()
    return response


def admin_descargar_factura_pdf(request, factura_id):
    return _generar_pdf(factura_id)


# === API FACTURAS ===
@csrf_exempt
@require_http_methods(["GET"])
def api_factura_list(request):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                f.id_factura,
                CONCAT(c.nombre, ' ', c.apellidos),
                f.fecha_factura,
                f.subtotal,
                COALESCE(f.iva, f.subtotal * 0.21),
                COALESCE(f.total, f.subtotal * 1.21),
                CASE WHEN c.email IS NOT NULL AND c.email != '' THEN TRUE ELSE FALSE END
            FROM facturas f
            JOIN contratos co ON f.id_contrato = co.id_contrato
            JOIN clientes c ON co.id_cliente = c.id_cliente
            ORDER BY f.fecha_factura DESC
        """)
        rows = cursor.fetchall()
    facturas = [
        {
            "id": r[0],
            "cliente": r[1],
            "fecha": r[2].isoformat(),
            "subtotal": float(r[3]),
            "iva": float(r[4]),
            "total": float(r[5]),
            "email_enviado": False,
            "tiene_email": r[6]
        }
        for r in rows
    ]
    return JsonResponse(facturas, safe=False)


# === API INMUEBLES ===
@csrf_exempt
@require_http_methods(["GET"])
def api_inmueble_list(request):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_inmueble, direccion, tipo_operacion, estado, precio
            FROM inmuebles
            ORDER BY direccion
        """)
        rows = cursor.fetchall()
    
    inmuebles = [
        {
            "id": r[0],
            "direccion": r[1],
            "tipo_operacion": r[2],
            "estado": r[3],
            "precio": float(r[4])
        }
        for r in rows
    ]
    return JsonResponse(inmuebles, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def api_inmueble_crear(request):
    try:
        data = json.loads(request.body)
        direccion = data.get('direccion', '').strip()
        metros = data.get('metros_cuadrados')
        tipo = data.get('tipo_operacion', 'alquiler')
        estado = data.get('estado', 'disponible')
        precio = data.get('precio')

        if not direccion or not metros or not precio:
            return JsonResponse({"error": "Dirección, metros y precio son obligatorios"}, status=400)

        inmueble = Inmueble.objects.create(
            direccion=direccion,
            metros_cuadrados=float(metros),
            tipo_operacion=tipo,
            estado=estado,
            precio=float(precio)
        )
        return JsonResponse({"msg": "Inmueble creado", "id": inmueble.id_inmueble}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_inmueble_eliminar(request, id):
    try:
        inmueble = Inmueble.objects.get(id_inmueble=id)
        inmueble.delete()
        return JsonResponse({"message": "Inmueble eliminado correctamente."})
    except Inmueble.DoesNotExist:
        return JsonResponse({"error": "Inmueble no encontrado."}, status=404)
    except Exception:
        return JsonResponse({"error": "No se puede eliminar: está asociado a un contrato."}, status=400)


# === API CLIENTES ===
@csrf_exempt
@require_http_methods(["GET"])
def api_cliente_listar(request):
    clientes = Cliente.objects.all().values(
        'id_cliente',
        'dni',
        'nombre',
        'apellidos',
        'telefono',
        'direccion',
        'email'
    )
    return JsonResponse(list(clientes), safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def api_cliente_crear(request):
    try:
        data = json.loads(request.body)
        dni = data.get('dni', '').strip()
        nombre = data.get('nombre', '').strip()
        apellidos = data.get('apellidos', '').strip()
        telefono = (data.get('telefono') or '').strip() or None
        direccion = (data.get('direccion') or '').strip() or None
        email = (data.get('email') or '').strip() or None

        if not dni or not nombre or not apellidos:
            return JsonResponse({"error": "DNI, nombre y apellidos son obligatorios"}, status=400)

        if email and ('@' not in email or '.' not in email):
            return JsonResponse({"error": "Email inválido"}, status=400)

        try:
            cliente = Cliente.objects.create(
                dni=dni,
                nombre=nombre,
                apellidos=apellidos,
                telefono=telefono,
                direccion=direccion,
                email=email
            )
            return JsonResponse({"msg": "Cliente creado", "id": cliente.id_cliente}, status=201)
        except IntegrityError:
            return JsonResponse({"error": "El DNI ya está registrado"}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        return JsonResponse({"error": "Error interno: " + str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_cliente_eliminar(request, id):
    try:
        cliente = Cliente.objects.get(id_cliente=id)
        cliente.delete()
        return JsonResponse({"message": "Cliente eliminado correctamente."})
    except Cliente.DoesNotExist:
        return JsonResponse({"error": "Cliente no encontrado."}, status=404)


# === API CONTRATOS ===
@csrf_exempt
@require_http_methods(["GET"])
def api_contrato_list(request):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                co.id_contrato,
                c.nombre || ' ' || c.apellidos AS cliente,
                i.direccion AS inmueble,
                co.fecha_inicio
            FROM contratos co
            JOIN clientes c ON co.id_cliente = c.id_cliente
            JOIN inmuebles i ON co.id_inmueble = i.id_inmueble
            ORDER BY co.fecha_inicio DESC
        """)
        rows = cursor.fetchall()
    
    contratos = [
        {
            "id": r[0],
            "cliente": r[1],
            "inmueble": r[2],
            "fecha_inicio": r[3].isoformat() if r[3] else None
        }
        for r in rows
    ]
    return JsonResponse(contratos, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def api_contrato_crear(request):
    try:
        data = json.loads(request.body)
        id_cliente = data.get('id_cliente')
        id_inmueble = data.get('id_inmueble')
        fecha_inicio = data.get('fecha_inicio')
        tipo_contrato = data.get('tipo_contrato', 'alquiler')

        if not all([id_cliente, id_inmueble, fecha_inicio]):
            return JsonResponse({"error": "Faltan campos: id_cliente, id_inmueble, fecha_inicio"}, status=400)

        cliente = Cliente.objects.get(id_cliente=id_cliente)
        inmueble = Inmueble.objects.get(id_inmueble=id_inmueble)

        contrato = Contrato.objects.create(
            cliente=cliente,
            inmueble=inmueble,
            fecha_inicio=fecha_inicio,
            tipo_contrato=tipo_contrato
        )
        return JsonResponse({"msg": "Contrato creado", "id": contrato.id_contrato}, status=201)
    except Cliente.DoesNotExist:
        return JsonResponse({"error": "Cliente no encontrado"}, status=404)
    except Inmueble.DoesNotExist:
        return JsonResponse({"error": "Inmueble no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_contrato_eliminar(request, id):
    try:
        contrato = Contrato.objects.get(id_contrato=id)
        contrato.delete()
        return JsonResponse({"message": "Contrato eliminado correctamente."})
    except Contrato.DoesNotExist:
        return JsonResponse({"error": "Contrato no encontrado."}, status=404)
    except Exception:
        return JsonResponse({"error": "No se puede eliminar: existen facturas asociadas."}, status=400)


# === API FACTURAS (continuación) ===
@csrf_exempt
@require_http_methods(["POST"])
def api_factura_crear(request):
    try:
        data = json.loads(request.body)
        id_contrato = data.get('id_contrato')
        fecha = data.get('fecha')
        subtotal = data.get('subtotal')

        if not all([id_contrato, fecha, subtotal]):
            return JsonResponse({"error": "Faltan campos: id_contrato, fecha, subtotal"}, status=400)

        contrato = Contrato.objects.get(id_contrato=id_contrato)
        factura = Factura.objects.create(
            contrato=contrato,
            fecha_factura=fecha,
            subtotal=subtotal
        )
        return JsonResponse({"msg": "Factura creada", "id": factura.id_factura}, status=201)
    except Contrato.DoesNotExist:
        return JsonResponse({"error": "Contrato no encontrado"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_factura_eliminar(request, id):
    try:
        factura = Factura.objects.get(id_factura=id)
        factura.delete()
        return JsonResponse({"message": "Factura eliminada correctamente."})
    except Factura.DoesNotExist:
        return JsonResponse({"error": "Factura no encontrada."}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def api_factura_enviar(request):
    try:
        body = json.loads(request.body)
        factura_id = body.get("factura_id")
        if not factura_id:
            return JsonResponse({"error": "factura_id requerido"}, status=400)

        factura = Factura.objects.select_related('contrato__cliente').get(id_factura=factura_id)
        cliente = factura.contrato.cliente

        if not cliente.email:
            return JsonResponse({"msg": "El cliente no tiene email registrado."}, status=400)

        from io import BytesIO
        pdf_buffer = BytesIO()
        cliente = factura.contrato.cliente
        inmueble = factura.contrato.inmueble
        iva = factura.get_iva_from_db() or float(factura.subtotal) * 0.21
        total = factura.get_total_from_db() or float(factura.subtotal) * 1.21

        p = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4

        logo_path = os.path.join(settings.BASE_DIR, 'facturacion', 'static', 'imagenes', 'logoinmogcyc.png')
        if os.path.exists(logo_path):
            try:
                p.saveState()
                p.setFillAlpha(0.07)
                margin = 30
                logo_width = width - 2 * margin
                logo_height = height - 2 * margin
                x = margin
                y = margin
                p.drawImage(
                    logo_path,
                    x, y,
                    width=logo_width,
                    height=logo_height,
                    preserveAspectRatio=True,
                    anchor='c',
                    mask='auto'
                )
                p.restoreState()
            except:
                pass

        # Mismo contenido que en _generar_pdf
        left_margin = 50
        right_margin = width - 50
        top_margin = height - 50
        p.setFont("Helvetica-Bold", 16)
        p.drawString(left_margin, top_margin, "INMOBILIARIA SOLUCIONES")
        p.setFont("Helvetica", 10)
        p.setFillColor(colors.grey)
        company_lines = [
            "CIF: B-12345678",
            "Calle Gran Vía, 123 • 28001 Madrid",
            "Tel: 910 000 000 • Email: info@inmobiliariasoluciones.es"
        ]
        y = top_margin - 20
        for line in company_lines:
            p.drawString(left_margin, y, line)
            y -= 14
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 14)
        p.drawRightString(right_margin, top_margin, "FACTURA")
        p.setFont("Helvetica", 11)
        p.drawRightString(right_margin, top_margin - 20, f"Nº: FAC-{factura.fecha_factura.year}-{factura.id_factura:04d}")
        p.drawRightString(right_margin, top_margin - 35, f"Fecha: {factura.fecha_factura.strftime('%d/%m/%Y')}")
        p.line(left_margin, y - 10, right_margin, y - 10)
        y = y - 30
        p.setFont("Helvetica-Bold", 11)
        p.drawString(left_margin, y, "Cliente")
        p.setFont("Helvetica", 10)
        y -= 20
        p.drawString(left_margin, y, f"{cliente.nombre} {cliente.apellidos}")
        y -= 16
        p.drawString(left_margin, y, f"DNI: {cliente.dni}")
        y -= 16
        p.drawString(left_margin, y, f"Dirección: {cliente.direccion}")
        y -= 16
        p.drawString(left_margin, y, f"Teléfono: {cliente.telefono or '—'}")
        y -= 25
        p.setFont("Helvetica-Bold", 11)
        p.drawString(left_margin, y, "Inmueble alquilado")
        p.setFont("Helvetica", 10)
        y -= 20
        p.drawString(left_margin, y, inmueble.direccion)
        y -= 40
        p.setFont("Helvetica-Bold", 11)
        p.drawString(left_margin, y, "Concepto")
        p.drawRightString(right_margin - 100, y, "Base imponible")
        p.drawRightString(right_margin, y, "Importe")
        y -= 20
        p.line(left_margin, y, right_margin, y)
        y -= 25
        p.setFont("Helvetica", 10)
        concepto = f"Alquiler mensual - {factura.fecha_factura.strftime('%B %Y').capitalize()}"
        p.drawString(left_margin, y, concepto)
        p.drawRightString(right_margin - 100, y, formatear_euros(factura.subtotal))
        p.drawRightString(right_margin, y, formatear_euros(factura.subtotal))
        y -= 30
        p.drawString(left_margin, y, "IVA (21%)")
        p.drawRightString(right_margin, y, formatear_euros(iva))
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(left_margin, y, "TOTAL FACTURA")
        p.drawRightString(right_margin, y, formatear_euros(total))
        y -= 40
        p.setFont("Helvetica", 8)
        p.setFillColor(colors.grey)
        p.drawString(left_margin, 80, "• Esta factura se emite conforme al contrato de alquiler.")
        p.drawString(left_margin, 65, "• El pago se considerará efectivo al recibir justificante bancario.")
        p.drawString(left_margin, 50, "• Documento válido sin firma física.")
        p.drawRightString(right_margin, 50, "Gracias por confiar en nosotros.")
        p.setFillColor(colors.black)
        p.showPage()
        p.save()

        pdf_buffer.seek(0)

        email = EmailMessage(
            subject=f"Factura {factura.id_factura} - {factura.fecha_factura.strftime('%d/%m/%Y')}",
            body=f"Estimado/a {cliente.nombre},\n\nAdjuntamos su factura.\n\nSaludos cordiales.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[cliente.email]
        )
        email.attach(f"factura_{factura.id_factura}.pdf", pdf_buffer.read(), "application/pdf")
        email.send()

        return JsonResponse({"msg": "Factura enviada correctamente."})

    except Factura.DoesNotExist:
        return JsonResponse({"msg": "Factura no encontrada."}, status=404)
    except Exception as e:
        return JsonResponse({"msg": str(e)}, status=500)


# === API PAGOS ===
@csrf_exempt
@require_http_methods(["GET"])
def api_pago_list(request):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                p.id_pago,
                f.id_factura,
                CONCAT(c.nombre, ' ', c.apellidos) AS cliente,
                f.fecha_factura,
                p.monto_pagado,
                p.fecha_pago,
                p.estado
            FROM pagos p
            JOIN facturas f ON p.id_factura = f.id_factura
            JOIN contratos co ON f.id_contrato = co.id_contrato
            JOIN clientes c ON co.id_cliente = c.id_cliente
            ORDER BY p.fecha_pago DESC
        """)
        rows = cursor.fetchall()
    
    pagos = [
        {
            "id": r[0],
            "factura_id": r[1],
            "cliente": r[2],
            "fecha_factura": r[3].isoformat() if r[3] else None,
            "monto_pagado": float(r[4]),
            "fecha_pago": r[5].isoformat() if r[5] else None,
            "estado": r[6]
        }
        for r in rows
    ]
    return JsonResponse(pagos, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def api_pago_crear(request):
    try:
        data = json.loads(request.body)
        id_factura = data.get('id_factura')
        monto_pagado = data.get('monto_pagado')
        fecha_pago = data.get('fecha_pago')
        estado = data.get('estado', 'pagado')

        if not all([id_factura, monto_pagado, fecha_pago]):
            return JsonResponse({"error": "Faltan campos: id_factura, monto_pagado, fecha_pago"}, status=400)

        factura = Factura.objects.get(id_factura=id_factura)
        pago = Pago.objects.create(
            factura=factura,
            monto_pagado=monto_pagado,
            fecha_pago=fecha_pago,
            estado=estado
        )
        return JsonResponse({"msg": "Pago registrado", "id": pago.id_pago}, status=201)
    except Factura.DoesNotExist:
        return JsonResponse({"error": "Factura no encontrada"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_pago_eliminar(request, id):
    try:
        pago = Pago.objects.get(id_pago=id)
        pago.delete()
        return JsonResponse({"message": "Pago eliminado correctamente."})
    except Pago.DoesNotExist:
        return JsonResponse({"error": "Pago no encontrado."}, status=404)


# === EXPORTACIONES ===
@csrf_exempt
@require_http_methods(["GET"])
def api_facturas_exportar_csv(request):
    from django.db import connection
    import csv
    from io import StringIO

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                f.id_factura,
                CONCAT(c.nombre, ' ', c.apellidos) AS cliente,
                i.direccion AS inmueble,
                f.fecha_factura,
                f.subtotal,
                COALESCE(f.iva, f.subtotal * 0.21) AS iva,
                COALESCE(f.total, f.subtotal * 1.21) AS total
            FROM facturas f
            JOIN contratos co ON f.id_contrato = co.id_contrato
            JOIN clientes c ON co.id_cliente = c.id_cliente
            JOIN inmuebles i ON co.id_inmueble = i.id_inmueble
            ORDER BY f.fecha_factura DESC
        """)
        rows = cursor.fetchall()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Cliente', 'Inmueble', 'Fecha', 'Subtotal', 'IVA', 'Total'])
    for row in rows:
        writer.writerow([
            row[0],
            row[1],
            row[2],
            row[3].strftime('%Y-%m-%d') if row[3] else '',
            float(row[4]),
            float(row[5]),
            float(row[6])
        ])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="facturas.csv"'
    return response


@csrf_exempt
@require_http_methods(["GET"])
def api_facturas_exportar_excel(request):
    from django.db import connection
    from openpyxl import Workbook
    from io import BytesIO

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                f.id_factura,
                CONCAT(c.nombre, ' ', c.apellidos) AS cliente,
                i.direccion AS inmueble,
                f.fecha_factura,
                f.subtotal,
                COALESCE(f.iva, f.subtotal * 0.21) AS iva,
                COALESCE(f.total, f.subtotal * 1.21) AS total
            FROM facturas f
            JOIN contratos co ON f.id_contrato = co.id_contrato
            JOIN clientes c ON co.id_cliente = c.id_cliente
            JOIN inmuebles i ON co.id_inmueble = i.id_inmueble
            ORDER BY f.fecha_factura DESC
        """)
        rows = cursor.fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Facturas"
    ws.append(['ID', 'Cliente', 'Inmueble', 'Fecha', 'Subtotal', 'IVA', 'Total'])

    for row in rows:
        ws.append([
            row[0],
            row[1],
            row[2],
            row[3].strftime('%Y-%m-%d') if row[3] else '',
            float(row[4]),
            float(row[5]),
            float(row[6])
        ])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=facturas.xlsx'
    return response