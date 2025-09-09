from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Product
from customers.models import Customer
from orders.models import Order


# ==== Helpers para manejar respuestas con/ sin paginación ====
def is_paginated(data):
    return isinstance(data, dict) and "results" in data and "count" in data

def get_results(data):
    """Devuelve la lista de objetos (results si paginado, o la propia lista)."""
    if is_paginated(data):
        return data.get("results", [])
    if isinstance(data, list):
        return data
    # Si no es ni dict paginado ni lista, intenta normalizar a lista
    return list(data) if data else []

def first_item(data):
    results = get_results(data)
    return results[0] if results else None

def total_returned(data):
    results = get_results(data)
    return len(results)


def token_for(user):
    return str(RefreshToken.for_user(user).access_token)


class BaseAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Grupos
        from django.contrib.auth.models import Group, User
        cls.grp_manager, _ = Group.objects.get_or_create(name="Manager")
        cls.grp_seller, _ = Group.objects.get_or_create(name="Seller")
        cls.grp_viewer, _ = Group.objects.get_or_create(name="Viewer")

        # Usuarios
        cls.user_manager = User.objects.create_user(username="manager", password="pass")
        cls.user_seller = User.objects.create_user(username="seller", password="pass")
        cls.user_viewer = User.objects.create_user(username="viewer", password="pass")

        cls.user_manager.groups.add(cls.grp_manager)
        cls.user_seller.groups.add(cls.grp_seller)
        cls.user_viewer.groups.add(cls.grp_viewer)

        # Tokens
        cls.tok_manager = token_for(cls.user_manager)
        cls.tok_seller = token_for(cls.user_seller)
        cls.tok_viewer = token_for(cls.user_viewer)

        # Datos base
        cls.prod = Product.objects.create(name="Mouse", sku="MOU-001", price=100, stock=10)
        cls.prod2 = Product.objects.create(name="Teclado", sku="KB-001", price=50, stock=5)

        cls.cust = Customer.objects.create(full_name="Alice Doe", email="alice@example.com")

    def auth_client(self, token: str) -> APIClient:
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c


class OrderFlowTests(BaseAPITestCase):
    def test_total_frozen_price_with_multiple_items(self):
        """
        Crea una orden con 2 ítems; luego cambia el precio del producto.
        El total debe quedarse igual (precio congelado).
        """
        client = self.auth_client(self.tok_manager)

        payload = {
            "customer": self.cust.id,
            "items": [
                {"product": self.prod.id, "quantity": 2},
                {"product": self.prod2.id, "quantity": 1},
            ]
        }
        resp = client.post(reverse("order-list"), payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        order_id = resp.data["id"]
        total_initial = resp.data["total_amount"]

        # Cambiar el precio de los productos: el total NO debe cambiar
        self.prod.price = 999
        self.prod.save()
        self.prod2.price = 999
        self.prod2.save()

        resp2 = client.get(reverse("order-detail", args=[order_id]))
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertEqual(resp2.data["total_amount"], total_initial)

    def test_stock_decrement_on_create_and_restock_on_cancel(self):
        """
        Crear orden descuenta stock; action cancel repone stock.
        """
        client = self.auth_client(self.tok_manager)

        start_stock = self.prod.stock  # 10
        resp = client.post(
            reverse("order-list"),
            {"customer": self.cust.id, "items": [{"product": self.prod.id, "quantity": 3}]},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        order_id = resp.data["id"]

        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, start_stock - 3)

        # Cancelar debe reponer stock
        resp_cancel = client.post(reverse("order-cancel", args=[order_id]))
        self.assertEqual(resp_cancel.status_code, 200, resp_cancel.data)

        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, start_stock)


class PermissionsTests(BaseAPITestCase):
    def test_seller_cannot_create_products(self):
        """
        El grupo Seller no debe poder crear productos (solo catálogo lectura + órdenes).
        """
        client = self.auth_client(self.tok_seller)
        resp = client.post(
            reverse("product-list"),
            {"name": "Monitor", "sku": "MON-1", "price": 250, "stock": 3},
            format="json",
        )
        # Esperamos 403 por permisos insuficientes (o 401 si no quedó autenticado)
        self.assertIn(resp.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED), resp.data)

    def test_viewer_cannot_pay_or_cancel_and_cannot_see_stock(self):
        """
        El grupo Viewer:
          - No puede ejecutar pay/cancel
          - No ve el campo 'stock' en las respuestas de productos (paginadas o no)
        """
        client = self.auth_client(self.tok_viewer)

        # (1) No ve 'stock' en list/GET products — compatible con paginación
        resp_list = client.get(reverse("product-list"))
        self.assertEqual(resp_list.status_code, 200)

        # Si hay paginación, opcionalmente afirma su estructura:
        if is_paginated(resp_list.data):
            self.assertIn("count", resp_list.data)
            self.assertIn("results", resp_list.data)

        item = first_item(resp_list.data)
        # Puede que aún no haya productos si la BD está vacía en este test,
        # pero como creamos productos en setUpTestData, debería haber al menos 1
        self.assertIsNotNone(item, "La lista de productos está vacía y no se puede verificar 'stock'.")
        self.assertNotIn("stock", item)

        # (2) No puede pay/cancel
        # Creamos una orden como manager
        manager_client = self.auth_client(self.tok_manager)
        resp_order = manager_client.post(
            reverse("order-list"),
            {"customer": self.cust.id, "items": [{"product": self.prod.id, "quantity": 1}]},
            format="json",
        )
        self.assertEqual(resp_order.status_code, 201, resp_order.data)
        order_id = resp_order.data["id"]

        # Viewer intenta pay
        resp_pay = client.post(reverse("order-pay", args=[order_id]))
        self.assertIn(resp_pay.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED), resp_pay.data)

        # Viewer intenta cancel
        resp_cancel = client.post(reverse("order-cancel", args=[order_id]))
        self.assertIn(resp_cancel.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED), resp_cancel.data)
