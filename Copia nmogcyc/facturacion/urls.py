from django.urls import path
from . import views

urlpatterns = [
    # Tus rutas existentes
    path('admin/factura/<int:factura_id>/pdf/', views.admin_descargar_factura_pdf, name='admin_descargar_factura_pdf'),
    path('api/facturas/', views.api_factura_list, name='api_factura_list'),
    path('api/facturas/enviar/', views.api_factura_enviar, name='api_factura_enviar'),
    path('api/contratos/', views.api_contrato_list, name='api_contrato_list'),
    path('api/facturas/crear/', views.api_factura_crear, name='api_factura_crear'),
    path('api/facturas/<int:id>/eliminar/', views.api_factura_eliminar, name='api_factura_eliminar'),
    path('api/clientes/crear/', views.api_cliente_crear, name='api_cliente_crear'),
    path('api/clientes/listar/', views.api_cliente_listar, name='api_cliente_listar'),
    path('api/clientes/eliminar/<int:id>/', views.api_cliente_eliminar, name='api_cliente_eliminar'),
    path('api/facturas/exportar/csv/', views.api_facturas_exportar_csv, name='api_facturas_exportar_csv'),
    path('api/facturas/exportar/excel/', views.api_facturas_exportar_excel, name='api_facturas_exportar_excel'),
    # ... tus rutas existentes ...
    path('api/contratos/', views.api_contrato_list, name='api_contrato_list'),
    path('api/contratos/crear/', views.api_contrato_crear, name='api_contrato_crear'),
    path('api/contratos/eliminar/<int:id>/', views.api_contrato_eliminar, name='api_contrato_eliminar'),
    # ... resto de rutas ...
    # ... tus rutas existentes ...
    path('api/clientes/crear/', views.api_cliente_crear, name='api_cliente_crear'),
    path('api/clientes/listar/', views.api_cliente_listar, name='api_cliente_listar'),
    path('api/clientes/eliminar/<int:id>/', views.api_cliente_eliminar, name='api_cliente_eliminar'),
    # Nueva ruta para inmuebles
        path('api/inmuebles/listar/', views.api_inmueble_list, name='api_inmueble_list'),
    path('api/inmuebles/crear/', views.api_inmueble_crear, name='api_inmueble_crear'),
    path('api/inmuebles/eliminar/<int:id>/', views.api_inmueble_eliminar, name='api_inmueble_eliminar'),
    # ... resto de rutas ...
        path('api/pagos/listar/', views.api_pago_list, name='api_pago_list'),
    path('api/pagos/crear/', views.api_pago_crear, name='api_pago_crear'),
    path('api/pagos/eliminar/<int:id>/', views.api_pago_eliminar, name='api_pago_eliminar'),
    
]