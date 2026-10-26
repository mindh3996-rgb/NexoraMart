from django.contrib import admin
from django.urls import path
from store import views

from django.conf import settings
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    # signup url
    path("signup/", views.signup, name="signup"),
    #login url
    path("login/", views.login_view, name="login"),
    #logout url
    path("logout/", views.logout_view, name="logout"),
    # My profile url
    path("profile/", views.profile, name="profile"),
    #Edit Profile
    path("edit-profile/", views.edit_profile, name="edit_profile"),

    # Add to Cart
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),

    # Cart Page
    path('cart/', views.cart, name='cart'),

    # Remove from Cart
    path('remove/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Increase Quantity
    path('increase/<int:cart_id>/', views.increase_quantity, name='increase_quantity'),

    # Decrease Quantity
    path('decrease/<int:cart_id>/', views.decrease_quantity, name='decrease_quantity'),
    # checkout
    path("checkout/", views.checkout, name="checkout"),
    # Order success
    path("order-success/", views.order_success, name="order_success"),
    # My orders
    path(
    "my-orders/",
    views.my_orders,
    name="my_orders"
),
path(
    "update-order/<int:order_id>/",
    views.update_order_status,
    name="update_order_status",
),
path("contact/", views.contact, name="contact"),

path(
    "product/<int:product_id>/",
    views.product_detail,
    name="product_detail"
),
path(
    "wishlist/add/<int:product_id>/",
    views.add_to_wishlist,
    name="add_to_wishlist",
),

path(
    "wishlist/",
    views.wishlist,
    name="wishlist",
),
path(
    "review/<int:product_id>/",
    views.add_review,
    name="add_review"
),
path(
    "invoice/<int:order_id>/",
    views.download_invoice,
    name="download_invoice",
),
path("dashboard/", views.dashboard, name="dashboard"),
path(
    "products/",
    views.product_list,
    name="product_list"
),

path(
    "add-product/",
    views.add_product,
    name="add_product"
),

path(
    "delete-product/<int:product_id>/",
    views.delete_product,
    name="delete_product"
),
path(
    "edit-product/<int:product_id>/",
    views.edit_product,
    name="edit_product"
),
path(
    "product-view/<int:product_id>/",
    views.product_view,
    name="product_view"
),
# path(
#     "update-order/<int:order_id>/",
#     views.update_order_status,
#     name="update_order_status",
# ),
path(
    "order-confirmation-preview/",
    views.order_confirmation_preview,
    name="order_confirmation_preview"
),
path("variants/", views.variant_list, name="variant_list"),
path("variants/add/", views.add_variant, name="add_variant"),
path("variants/edit/<int:variant_id>/", views.edit_variant, name="edit_variant"),
path("variants/delete/<int:variant_id>/", views.delete_variant, name="delete_variant"),
path("dashboard/theme/", views.theme_settings, name="theme_settings"),
]

