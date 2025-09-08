# Mini Sales API (Django + DRF + Celery + PostgreSQL)

Prueba técnica: API de gestión de ventas con **Django + DRF + Celery + Redis + PostgreSQL**.

Incluye:
- CRUD de **Products** con etiquetas.
- CRUD de **Customers**.
- CRUD de **Orders** con items, validación de stock y precios congelados.
- Grupos de usuario (`manager`, `seller`, `viewer`).
- Generación diaria de un reporte CSV de ventas con **Celery Beat**.

---

## Requisitos

- Docker y Docker compose instalados.

--

## Instalación y configuración

1. Clonar el repositorio:
    ```bash
    git clone https://github.com/Adriram99/mini-sales-api.git
    cd mini-sales-api
    ```
2. Copiar el archivo de entorno:
    ```bash
    cp .env.example .env
    ```
3. Levantar los servicios:
    ```bash
    docker compose up --build
    ```
4. Aplicar migraciones:
    ```bash
    docker compose run --rm web python manage.py migrate
    ```
5. Crear superusuario:
    ```
    docker compose run --rm web python manage.py createsuperuser
    ```
6. Acceder:
    - API Docs: http://localhost:8000/api/docs/
    - Django Admin: http://localhost:8000/admin/

-- 

## Roles de usuario

- **manager** -> CRUD completo de toda la API.
- **seller** -> puede crear/actualizar ordenes y ejecutar pay/cancel. Solo lectura del catálogo.
- **viewer** -> solo lectura de toda la API.

--

## Endpoints principales

#### Products
- `GET /api/products/`
- `POST /api/products/`
- `PATCH /api/products/{id}/`
- `DELETE /api/products/{id}/`
- `POST /api/products/{id}/labels` -> Para asignar etiquetas.
- `DELETE /api/products/{id}/labels/{label_id}/` -> Quitar etiquetas.

#### Customers
- `GET /api/customers/`
- `POST /api/customers/`

#### Orders
- `GET /api/orders/`
```json
{
    "id": 2,
    "customer": 2,
    "status": "PENDING",
    "created_at": "2025-09-08T10:41:36.212711Z",
    "items": [
      {
        "id": 3,
        "product": 27,
        "product_name": "Audience",
        "quantity": "1.00",
        "unit_price": "59184.00",
        "subtotal": 59184
      },
      {
        "id": 4,
        "product": 24,
        "product_name": "They",
        "quantity": "2.00",
        "unit_price": "15221.00",
        "subtotal": 30442
      },
      {
        "id": 5,
        "product": 26,
        "product_name": "Key",
        "quantity": "2.00",
        "unit_price": "2736.00",
        "subtotal": 5472
      },
      {
        "id": 6,
        "product": 28,
        "product_name": "Statement",
        "quantity": "3.00",
        "unit_price": "2255.00",
        "subtotal": 6765
      },
      {
        "id": 7,
        "product": 28,
        "product_name": "Statement",
        "quantity": "2.00",
        "unit_price": "2255.00",
        "subtotal": 4510
      }
    ],
    "total_amount": 106373
  } 
```
- `POST /api/orders/{id}/pay/` -> Para pagar una orden.
- `POST /api/orders/{id}/cancel/` -> Para cancelar una orden.

--

## Ejemplos con cURL

- Crear un producto:
```bash
curl -X post http://localhost:8000/api/products/ \
    -H "Content-Type: application/json" \
    -u admin:password \
    -d '{"name": "Mouse", "sku": "MOU-001", "price": "150000", "stock": 7}'
```
- Etiquetar un producto:
```bash
curl -X post http://localhost:8000/api/products/1/labels/ \
    -H "Content-Type: application/json" \
    -u admin:password \
    -d '{"label_id": 3}'