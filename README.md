# 🌊 Santander Inmo<span style="color: #0277BD; font-weight: bold;">Factur</span>

> **Facturación inmobiliaria precisa, rápida y con identidad santanderina**  
> Sistema profesional para la gestión integral de clientes, inmuebles y facturas en el sector inmobiliario.

---

## 📌 Características principales

- ✅ Gestión completa de **clientes** (DNI, nombre, apellidos, teléfono, dirección y email).
- 🏠 Administración de **inmuebles** vinculados a clientes.
- 📄 Creación de **facturas profesionales** con:
  - Cálculo automático del IVA (21%).
  - Totales expresados en euros (€).
  - Información detallada del cliente e inmueble.
- 📤 **Exportación** de facturas y listados de clientes en **CSV** y **Excel**.
- 📧 Envío automático de facturas como **PDF adjunto** por correo electrónico.
- 🔐 Autenticación con **control de acceso por roles**.
- 🎨 Interfaz limpia, coherente y alineada con la identidad visual de *Inmosantander*.
- 🖼️ Soporte para **logo corporativo** y **marca de agua** en documentos impresos y digitales.

---

## 🛠️ Tecnologías utilizadas

- **Backend**: Python + Django (API REST)
- **Base de datos**: PostgreSQL
- **Frontend**: Angular
- **Envío de emails**: SMTP vía `smtp-relay.brevo.com` (puerto 587, TLS)
- **Generación de PDFs**: Renderizado dinámico en Django
- **Entorno de desarrollo**: API local en `http://localhost:8000`

---

## 🚀 Configuración local

1. **Clonar el repositorio**
   ```bash
   git clone <tu-repositorio>
   cd facturacion-inmosantander