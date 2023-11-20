from string import ascii_letters
from random import choices

from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.urls import reverse

from shopapp.models import Product
from shopapp.utils import add_two_numbers

from .models import Order


class AddTwoNumbersTestCase(TestCase):
    def test_add_two_numbers(self):
        result = add_two_numbers(2, 3)
        self.assertEquals(result, 5)


class ProductsListViewTestCase(TestCase):
    fixtures = [
        'products-fixture.json',
        'users-fixture.json',
        'groups-fixture.json',
    ]

    def test_products(self):
        response = self.client.get(reverse("shopapp:products_list"))
        self.assertQuerySetEqual(
            qs=Product.objects.filter(archived=False).all(),
            values=(p.pk for p in response.context["products"]),
            transform=lambda p: p.pk,
        )
        self.assertTemplateUsed(response, 'shopapp/products-list.html')


class OrdersListViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="bob_test", password="qwerty")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.user.delete()

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_orders_view(self):
        response = self.client.get(reverse("shopapp:orders_list"))
        self.assertContains(response, "Orders")

    def test_orders_view_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse("shopapp:orders_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(settings.LOGIN_URL), response.url)


class ProductsExportViewTestCase(TestCase):
    fixtures = [
        'products-fixture.json',
        'users-fixture.json',
        'groups-fixture.json',
    ]

    def test_get_products_view(self):
        response = self.client.get(
            reverse("shopapp:products-export")
        )
        self.assertEqual(response.status_code, 200)
        products = Product.objects.order_by("pk").all()
        expected_data = [
            {
                "pk": product.pk,
                "name": product.name,
                "price": str(product.price),
                "archived": product.archived,
            }
            for product in products
        ]
        products_data = response.json()
        self.assertEqual(
            products_data["products"],
            expected_data,
        )


class OrderDetailViewTestCase(TestCase):
    fixtures = [
        'products-fixture.json',
        'users-fixture.json',
        'groups-fixture.json',
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.credentials = dict(username="bob", password="pass")
        cls.user = User.objects.create_user(**cls.credentials)
        cls.user.user_permissions.add(Permission.objects.get(codename='view_order'))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.user.delete()

    def setUp(self):
        self.client.force_login(self.user)
        self.order = Order.objects.create(
            delivery_address="Ul. Pushkina d.7",
            promocode="Sales123",
            user=self.user
        )

    def tearDown(self):
        self.order.delete()

    def test_order_details(self):
        response = self.client.get(
            reverse("shopapp:order_details", kwargs={"pk": self.order.pk})
        )
        self.assertContains(response, self.order.delivery_address)
        self.assertContains(response, self.order.promocode)
        self.assertEqual(response.context['order'].pk, self.order.pk)


class OrderExportTestCases(TestCase):
    fixtures = [
        'orders-fixture.json',
        'products-fixture.json',
        'users-fixture.json',
        'groups-fixture.json',
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="bob", password="pass")
        cls.user.is_staff = True
        cls.user.save()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.user.delete()

    def setUp(self):
        self.client.force_login(self.user)

    def test_order_export(self):
        response = self.client.get(reverse("shopapp:orders-export"))
        self.assertEqual(response.status_code, 200)

        orders = Order.objects.order_by("pk").all()
        expected = {"orders": [
            {
                "pk": order.pk,
                "delivery_address": order.delivery_address,
                "promocode": order.promocode,
                "user": order.user.pk,
                "products": [product.pk for product in order.products.all()]
            }
            for order in orders
        ]
        }
        self.assertEqual(response.json(), expected)