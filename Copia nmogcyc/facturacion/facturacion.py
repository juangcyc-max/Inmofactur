# facturacion/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('admin/factura/<int:factura_id>/pdf/', views.admin_descargar_factura_pdf, name='admin_descargar_factura_pdf'),
    path('api/facturas/', views.api_factura_list, name='api_factura_list'),
    path('api/facturas/enviar/', views.api_factura_enviar, name='api_factura_enviar'),
]