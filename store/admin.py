from django.utils.html import format_html
from django.contrib import admin
from django.http import HttpResponse
import openpyxl
from .models import ProductVariant
from .models import Coupon
from reportlab.pdfgen import canvas
from .models import Product, ProductImage, Category, Cart, Order, OrderItem, Profile, Wishlist, Review
from .models import ProductGridSettings


# =========================
# Export to Excel
# =========================
def export_to_excel(modeladmin, request, queryset):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Products"

    sheet.append(["ID", "Name", "Price", "Description"])

    for product in queryset:
        sheet.append([
            product.id,
            product.name,
            product.price,
            product.description,
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = 'attachment; filename="products.xlsx"'

    workbook.save(response)

    return response


export_to_excel.short_description = "Export Selected Products to Excel"


# =========================
# Export to PDF
# =========================
def export_to_pdf(modeladmin, request, queryset):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="products.pdf"'

    pdf = canvas.Canvas(response)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 800, "Nexora Mart Product List")

    y = 770

    pdf.setFont("Helvetica", 11)

    for product in queryset:
        pdf.drawString(
            50,
            y,
            f"ID: {product.id} | {product.name} | ${product.price}"
        )

        y -= 20

        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y = 800

    pdf.save()

    return response


export_to_pdf.short_description = "Export Selected Products to PDF"


# =========================
# Admin
# =========================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = ("id", "name", "category", "price", "edit_button")

    actions = [export_to_excel, export_to_pdf]

    def edit_button(self, obj):
        return format_html(
            '<a style="background:#0d6efd; color:white; padding:5px 10px; border-radius:5px; text-decoration:none;" href="/admin/store/product/{}/change/">Edit</a>',
            obj.id
        )

    edit_button.short_description = "Edit"


# 👇 Ye line class ke bahar hogi
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)

admin.site.register(Cart)
admin.site.register(Profile)
admin.site.register(ProductImage)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer_name",
        "phone",
        "city",
        "payment_method",
        "payment_verified",
        "status",
        "total_amount",
        "payment_image",
        "created_at",
    )

    list_filter = (
        "payment_method",
        "payment_verified",
        "status",
        "city",
        "created_at",
    )

    search_fields = (
        "customer_name",
        "phone",
        "city",
        "transaction_id",
    )

    readonly_fields = (
        "payment_image",
    )

    def payment_image(self, obj):

        if obj.payment_screenshot:

            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" width="100" style="border-radius:8px;border:1px solid #ddd;">'
                '</a>',
                obj.payment_screenshot.url,
                obj.payment_screenshot.url
            )

        return "No Screenshot"

    payment_image.short_description = "Screenshot"
admin.site.register(Wishlist)
admin.site.register(Review)
admin.site.register(Coupon)
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "color",
        "size",
        "stock",
        "extra_price",
    )

    list_filter = (
        "color",
        "size",
    )

    search_fields = (
        "product__name",
        "color",
        "size",
    )
from .models import MenuItem
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "url", "parent", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("title",)
    autocomplete_fields = ("category", "parent")
from .models import HeroSection


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "layout", "media_type", "button_style", "is_active")
    list_editable = ("is_active",)
    list_filter = ("layout", "media_type", "animation", "button_style", "is_active")
    search_fields = ("title", "heading", "subheading")

    fieldsets = (
        ("Text Content", {"fields": ("title", "heading", "subheading", "paragraph", "font_family", "heading_size", "paragraph_size", "alignment", "text_color")}),
        ("Image / Video", {"fields": ("media_type", "image", "video", "layout", "media_position", "content_position")}),
        ("Background Design", {"fields": ("background_color", "gradient_start", "gradient_end", "show_text_box", "box_opacity")}),
        ("Button Settings", {"fields": ("button_text", "button_url", "button_style", "button_color", "button_text_color")}),
        ("Effects & Status", {"fields": ("animation", "is_active")}),
    )

from .models import NavbarSettings


@admin.register(NavbarSettings)
class NavbarSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Logo & Branding", {
            "fields": (
                "logo", "brand_name", "show_brand_name",
                "logo_width", "logo_height", "logo_alignment",
                "logo_animation", "animation_speed",
            )
        }),
        ("Background & Morphism", {
            "fields": (
                "background_color", "background_opacity",
                "background_morphism", "background_blur",
                "background_gradient", "gradient_start",
                "gradient_end", "border_color",
                "shadow_enabled", "sticky_header",
            )
        }),
        ("Menu Design", {
            "fields": (
                "menu_style", "menu_text_color", "menu_hover_color",
                "menu_background_color", "menu_font_size", "menu_gap",
                "menu_underline_color", "menu_border_radius",
            )
        }),
        ("Icons & Visibility", {
            "fields": (
                "icon_display", "icon_color", "icon_hover_color",
                "icon_background", "icon_hover_background",
                "icon_style", "icon_size", "show_search",
                "show_wishlist", "show_cart", "show_contact",
            )
        }),
        ("Search Bar", {
            "fields": (
                "search_placeholder", "search_width",
                "search_background", "search_text_color",
                "search_border_color", "search_border_radius",
            )
        }),
        ("Mobile & Status", {
            "fields": (
                "mobile_menu_background",
                "mobile_menu_text_color", "is_active",
            )
        }),
    )

    def has_add_permission(self, request):
        return not NavbarSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(ProductGridSettings)
class ProductGridSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "desktop_columns",
        "tablet_columns",
        "mobile_columns",
        "image_height",
        "card_gap",
        "card_padding",
        "card_radius",
        "title_font_size",
        "price_font_size",
    )

    def has_add_permission(self, request):
        return not ProductGridSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
