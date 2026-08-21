from django.utils.html import format_html
from django.contrib import admin
from django.http import HttpResponse
import openpyxl
from .models import ProductVariant
from .models import Coupon
from reportlab.pdfgen import canvas
from .models import Product, ProductImage, Category, Cart, Order, OrderItem, Profile, Wishlist, Review

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
admin.site.register(Category)
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