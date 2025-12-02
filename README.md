# BlueShopping - Ventas e intercambio de productos

BlueShopping es una plataforma web desarrollada en Django que permite a los usuarios vender, intercambiar y comprar productos entre ellos. El sistema incluye funcionalidades de carrito persistente, favoritos, reviews y permite el inicio de sesión a través de Google y Facebook.

## Características principales

- Registro e inicio de sesión de usuarios, incluyendo autenticación social (Google y Facebook).
- Gestión de productos:
  - Agregar, editar y eliminar productos propios.
  - Mostrar productos en oferta.
  - Soporte para categorías y subcategorías.
- Sistema de favoritos para guardar productos deseados.
- Carrito de compras persistente:
  - Subtotal calculado automáticamente con precios de oferta.
  - Cantidad de productos editable.
- Reviews y valoraciones de productos.
- Interfaz responsiva y amigable.
- Buscador y filtros avanzados por categoría, marca, precio y tipo de transacción (venta/intercambio).

## Tecnologías utilizadas

- Python 3.13
- Django 5.2
- SQLite (base de datos por defecto, se puede cambiar)
- HTML, CSS, Bootstrap 5
- JavaScript (fetch API para interacciones asincrónicas)
- django-allauth para autenticación social

## Instalación

En una términal ejecuta estos comando para ejecutar el proyecto localmente:

git clone https:github.com/blocklal/marketplace-programacioniv.git

cd marketplace-programacioniv

python -m venv venv

.\venv\Scripts\activate (Windows) //// source venv/bin/activate (Linux/macOS)

pip install -r requirements.txt

python manage.py migrate

python manage.py createsuperuser (Introducir dentro del grupo de Admin en http://127.0.0.1:8000/admin)

python manage.py runserver

Abre tu navegador en http://127.0.0.1:8000/ para ver la aplicación

Incluye una base de datos mínima para demostración de productos, se pueden eliminar desde http://127.0.0.1:8000/admin




