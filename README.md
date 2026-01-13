# Santander InmoFactur

Sistema de gestión y facturación inmobiliaria diseñado para agilizar la creación, gestión y envío de facturas profesionales en el sector inmobiliario. Desarrollado con una arquitectura full-stack moderna, permite administrar clientes, propiedades, contratos y facturas, con integración de envío automático por correo electrónico y exportación de datos.

---

## 📌 Características principales

- ✅ Gestión completa de **clientes** (DNI, nombre, teléfono, dirección, email).
- 🏠 Administración de **inmuebles** vinculados a clientes.
- 📄 Creación y visualización de **facturas detalladas** con:
  - Cálculo automático del IVA (21%).
  - Totales en euros (€).
  - Información clara del cliente y del inmueble.
- 📤 **Exportación** de facturas y listados de clientes en formatos **CSV** y **Excel**.
- 📧 Envío automático de facturas en **PDF adjunto** vía correo electrónico.
- 🔐 Sistema de autenticación con **control de acceso por roles**.
- 🎨 Interfaz de usuario limpia, profesional y coherente con la identidad de marca *Inmosantander*.
- 🖼️ Soporte para logo corporativo y marca de agua en documentos.

---

## 🛠️ Tecnologías utilizadas

- **Backend**: Python + Django (REST API)
- **Base de datos**: PostgreSQL
- **Frontend**: Angular
- **Envío de emails**: SMTP vía `smtp-relay.brevo.com` (puerto 587, TLS)
- **Generación de PDFs**: Librerías de renderizado dinámico en Django
- **Entorno de desarrollo**: API local en `http://localhost:8000`

---

## 🚀 Configuración local

1. **Clonar el repositorio**
   ```bash
   git clone <tu-repositorio>
   cd facturacion-inmosantander
