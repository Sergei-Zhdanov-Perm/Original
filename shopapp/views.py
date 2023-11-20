"""
В этом модуле лежат различные наборы представлений.

Разные view интернет-магазина: по товарам, заказам и тд.
"""
import logging
from timeit import default_timer
from csv import DictWriter

from django.contrib.auth.models import Group, User
from django.contrib.syndication.views import Feed
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404, reverse
from django.core.cache import cache
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .common import save_csv_products
from .forms import ProductForm, OrderForm, GroupForm
from .models import Product, Order, ProductImage
from .serializers import ProductSerializer, OrderSerializer

log = logging.getLogger(__name__)


@extend_schema(description="Product views CRUD")
class ProductViewSet(ModelViewSet):
    """
    Набор представлений для действий над Product
    Полный CRUD для сущностей товара
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter
    ]
    search_fields = ["name", "description"]
    filterset_fields = [
        "name",
        "description",
        "price",
        "discount",
        "archived",
    ]
    ordering_fields = [
        "pk",
        "name",
        "description",
        "price",
        "discount",
        "archived",
    ]

    @method_decorator(cache_page(60 * 2))
    def list(self, *args, **kwargs):
        # print("hello products list")
        return super().list(*args, **kwargs)

    @extend_schema(
        summary="Get one product by ID",
        description="Retrieves **product**, returns 404 if not found",
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Empty response, product by id not found")
        }
    )
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @action(methods=["get"], detail=False)
    def dowload_csv(self, request: Request):
        response = HttpResponse(content_type="text/csv")
        filename = "products-export.csv"
        response["Content-Disposition"] = f"attachment; filename={filename}-export.csv"
        queryset = self.filter_queryset(self.get_queryset())
        fields = [
            "name",
            "description",
            "price",
            "discount",
        ]
        queryset = queryset.only(*fields)
        writer = DictWriter(response, fieldnames=fields)
        writer.writeheader()

        for product in queryset:
            writer.writerow({
                field: getattr(product, field)
                for field in fields
            })

        return response

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser],
    )
    def upload_csv(self, request: Request):
        products = save_csv_products(
            request.FILES["file"].file,
            encoding=request.encoding,
        )
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter
    ]

    filterset_fields = [
        "user",
        "delivery_address"

    ]
    ordering_fields = [
        "pk",
        "created_at",
    ]


class ShopIndexView(View):
    # @method_decorator(cache_page(60 * 2))
    def get(self, request: HttpRequest) -> HttpResponse:
        products = [
            ('Laptop', 1999),
            ('Desktop', 2999),
            ('Smartphone', 999),
        ]
        numbers = [
            ('First', 1),
            ('Second', 2),
            ('Third', 3),
        ]
        text = [
            ('One', 'word'),
            ('TWo', 'word'),
            ('ThrEE', 'word'),
        ]
        context = {
            "time_running": default_timer(),
            "products": products,
            "list_order": numbers,
            "text": text,
            "items": 2,
        }
        print("shop index context", context)
        log.debug("Products for shop index: %s", products)
        log.info("Rendering shop index")
        return render(request, 'shopapp/shop-index.html')


class GroupsListView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        context = {
            "form": GroupForm(),
            "groups": Group.objects.prefetch_related('permissions').all(),
        }
        return render(request, 'shopapp/groups-list.html', context=context)

    def post(self, request: HttpRequest):
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect(request.path)


class ProductDetailsView(DetailView):
    template_name = "shopapp/products-details.html"
    # model = Product
    queryset = Product.objects.prefetch_related("images")
    context_object_name = "product"


class ProductsListView(ListView):
    template_name = "shopapp/products-list.html"
    # model = Product """Если сделать вместо queryset, то в случае удаления - всё равно будет показывать продукт в списке"""
    context_object_name = "products"
    queryset = (Product.objects
                .filter(archived=False)
                )


# def create_product(request: HttpRequest) -> HttpResponse:
#     if request.method == "POST":
#         form = ProductForm(request.POST)
#         if form.is_valid():
#             # name = form.cleaned_data["name"]
#             # price = form.cleaned_data["price"]
#             # Product.objects.create(**form.cleaned_data)
#             form.save()
#             url = reverse("shopapp:products_list")
#             return redirect(url)
#     else:
#         form = ProductForm()
#     context = {
#         "form": form,
#     }
#     return render(request, 'shopapp/create-product.html', context=context)


# def create_order(request: HttpRequest) -> HttpResponse:
#     if request.method == "POST":
#         form = OrderForm(request.POST)
#         if form.is_valid():
#             form.save()
#             url = reverse("shopapp:orders_list")
#             return redirect(url)
#     else:
#         form = OrderForm()
#     context = {
#         "form": form,
#     }
#     return render(request, 'shopapp/create-order.html', context=context)


class ProductCreateView(UserPassesTestMixin, CreateView):
    def test_func(self):
        # return self.request.user.groups.filter(name="secret-group").exists()
        return self.request.user.has_perm("shopapp.add_product")

    model = Product
    fields = "name", "price", "description", "discount", "preview"
    success_url = reverse_lazy("shopapp:products_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProductUpdateView(UserPassesTestMixin, UpdateView):
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        if self.request.user.has_perm("shopapp.change_product") and self.get_object().created_by == self.request.user:
            return True
        else:
            return False

    model = Product
    # fields = "name", "price", "description", "discount", "preview"
    template_name_suffix = "_update_form"
    form_class = ProductForm

    def get_success_url(self):
        return reverse(
            "shopapp:products_details",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        for image in form.files.getlist("images"):
            ProductImage.objects.create(
                product=self.objects,
                image=image,
            )

        return response


class ProductDeleteView(DeleteView):
    model = Product
    success_url = reverse_lazy("shopapp:products_list")

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.archived = True
        self.object.save()
        return HttpResponseRedirect(success_url)


class OrdersListView(LoginRequiredMixin, ListView):
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
        .all()
    )


class OrderDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "shopapp.view_order"
    queryset = (
        Order.objects
        .select_related("user")
        .prefetch_related("products")
    )


class OrderCreateView(CreateView):
    model = Order
    fields = "delivery_address", "promocode", "user", "products"
    success_url = reverse_lazy("shopapp:orders_list")


class OrderUpdateView(UpdateView):
    model = Order
    fields = "delivery_address", "promocode", "user", "products"
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse(
            "shopapp:order_details",
            kwargs={"pk": self.object.pk},
        )


class OrderDeleteView(DeleteView):
    model = Order
    success_url = reverse_lazy("shopapp:orders_list")


class ProductsDataExportView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        cache_key = "products_data_export"
        products_data = cache.get(cache_key)
        if products_data is None:
            products = Product.objects.order_by("pk").all()
            products_data = [
                {
                    "pk": product.pk,
                    "name": product.name,
                    "price": product.price,
                    "archived": product.archived,
                }
                for product in products
            ]
            elem = products_data[0]
            name = elem["name"]
            print("name:", name)
            cache.set(cache_key, products_data, 300)
        return JsonResponse({"products": products_data})


class OrderExportView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request: HttpRequest):
        orders = Order.objects.order_by("pk").all()
        response = {"orders": [
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

        return JsonResponse(response)


class LatestProductsFeed(Feed):
    title = "Latest Products"
    description = "Updates on changes and addition products"
    link = reverse_lazy("shopapp:products_list")

    def items(self):
        return (
            Product.objects
            .filter(created_at__isnull=False)
            .order_by("-created_at")[:5]
        )

    def item_title(self, item: Product):
        return item.name

    def item_description(self, item: Product):
        return item.description[:100]


class UserOrdersListView(ListView):
    model = Order
    template_name = 'shopapp/user-orders.html'
    context_object_name = 'user_orders'

    # def get_queryset(self, user_id=None, **kwargs):
    #     get_object_or_404(User, pk=self.kwargs['user_id'])
    #     self.owner = self.kwargs["user_id"], ["username"]
    #     print(self.owner)
    #     return Order.objects.select_related("user").prefetch_related("products").order_by('pk').filter(
    #         user=self.owner).all()
    #
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     return context #некорректный код, потому что не отображается имя пользователя в шаблоне который создал заказы.
    # Потому что вы его не поместили в контекст. Вам нужно получить пользователя в методе get_queryset, записав его в
    # атрибут self.owner, а затем в методе get_context_data добавить в контекст.
    def get_queryset(self, user_id=None, **kwargs):
        self.owner = get_object_or_404(User, pk=self.kwargs['user_id'])
        return Order.objects.select_related("user").prefetch_related("products").order_by('pk').filter(
            user=self.owner).all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["owner"] = self.owner
        return context


class UserOrdersExportView(View):
    @method_decorator(cache_page(60 * 3))
    def get(self, request: HttpRequest, user_id) -> JsonResponse:
        owner: User = get_object_or_404(User, pk=user_id)
        cache_key = f'user_id:{user_id}_data_export'
        orders_data = cache.get(cache_key)
        if orders_data is None:
            orders = Order.objects.select_related("user").prefetch_related("products").order_by('pk').filter(
                user=owner).all()
            orders_data = [
                {
                    "delivery_address": order.delivery_address,
                    "promocode": order.promocode,
                    "user": order.user.pk,
                }
                for order in orders
            ]
            cache.set("user_orders_data_export", orders_data, 300)
        return JsonResponse({"orders": orders_data})
