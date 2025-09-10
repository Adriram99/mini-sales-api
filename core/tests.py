from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from django.urls import reverse

class NoRoleBlockedTests(APITestCase):
    def test_user_without_group_or_perms_is_blocked(self):
        u = User.objects.create_user(username="norole", password="pass")
        self.client.login(username="norole", password="pass")
        resp = self.client.get(reverse("product-list"))
        self.assertIn(resp.status_code, (401, 403))
