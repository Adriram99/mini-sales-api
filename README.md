# Mini Sales API (Django + DRF + Celery + PostgreSQL)

Prueba técnica: API de gestión de ventas con **Django + DRF + Celery + Redis + PostgreSQL**.

Incluye:
- Autenticación con JWT.
- CRUD de **Products** con etiquetas.
- CRUD de **Customers**.
- CRUD de **Orders** con items, validación de stock y precios congelados.
- Grupos de usuario (`manager`, `seller`, `viewer`).
- Generación diaria de un reporte CSV de ventas con **Celery Beat**.
- Tests.

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
    cp env-example.txt .env
    ```
3. Levantar los servicios:
    ```bash
    docker compose up -d --build
    ```
4. Aplicar migraciones:
    ```bash
    docker compose run --rm web python manage.py migrate
    ```
5. Crear superusuario:
    ```bash
    docker compose run --rm web python manage.py createsuperuser
    ```
7. Ejecutar seed:
    ```bash
    docker compose run --rm web python manage.py seed
    ```
6. Acceder:
    - API Docs: http://localhost:8000/api/docs/
    - Django Admin: http://localhost:8000/admin/

-- 

## Roles de usuario y credenciales

- **manager** -> CRUD completo de toda la API.
    - manager1:managerpass
- **seller** -> puede crear/actualizar ordenes y ejecutar pay/cancel. Solo lectura del catálogo.
    - seller1:sellerpass
- **viewer** -> solo lectura de toda la API.
    - viewer1:viewerpass
- Se creo un usuario sin grupo/rol.
    - norole:norolepass

--

## Configuración y uso de Celery y Beat
- Worker:
    ```bash
    docker compose logs -f celery
    ```
- Beat (scheduler):
    ```bash
    docker compose logs -f celery-beat
    ```
#### Tarea para generar .csv de ventas diarias
Se ejecuta todos los días a las 22:00 y genera un CSV en `/tmp/` dentro del contenedor:
- Archivo: `/tmp/daily_sales_YYYY-MM-DD.csv
- Contenido: `Order ID, Customer Email, Items Count, Total Amount, Status, Created At`

#### Para ejecutar manualmente
```bash
docker compose run --rm web python manage.py shell
```

```python
from orders.tasks import export_daily_orders_to_csv
export_daily_orders_to_csv.delay()
```
#### Ver archivo generado
Este archivo se ve reflejado en /reports donde se levanto el docker, para facilitar el acceso al reporte.

--

## Endpoints principales
Obs: se implemento paginación de API REST.

#### Auth
- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`

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
- `POST /api/orders/{id}/pay/` -> Para pagar una orden pendiente.
- `POST /api/orders/{id}/cancel/` -> Para cancelar una orden pendiente o pagada.

--

## Ejemplos con cURL

- Iniciar sesión:
```bash
TOKEN=$(curl -s http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"manager","password":"pass"}' | jq -r .access)
```
- Crear un producto:
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Mouse Gamer","sku":"MOU-001","price":"25.00","stock":50}'
```
- Crear una etiqueta:
```bash
curl -X POST http://localhost:8000/api/labels/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Electrónica"}'
```
- Etiquetar un producto:
```bash
curl -X POST http://localhost:8000/api/products/1/labels/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"label_name":"Electrónica"}'
```
- Crear orden con items:
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "customer": 1,
        "items": [
          {"product": 1, "quantity": 2},
          {"product": 2, "quantity": 1}
        ]
      }'
```
- Pagar una orden:
```bash
curl -X POST http://localhost:8000/api/orders/1/pay/ \
  -H "Authorization: Bearer $TOKEN"
```
```bash
- Cancelar una orden:
curl -X POST http://localhost:8000/api/orders/1/cancel/ \
  -H "Authorization: Bearer $TOKEN"
```

--

## Tests
Los siguientes tests estan disponibles, los usuarios de prueba se generan en el script de ejecución en orders/tests.py:
- Total de orden con múltiples ítems y precio “fijo”.
- Crear orden descuenta stock.
- Cancelar orden repone stock.
- Seller no puede crear productos.
- Viewer no puede utilizar pay/cancel y no ve stock.
- Usuario sin rol/grupo/permiso no puede interactuar con EP.

Para ejecutar los tests (el servicio debe estar activo): 
```bash
docker compose exec web python manage.py test
```
