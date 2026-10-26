
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.db.models import Q, Avg, Sum, Count
from django.db.models.functions import ExtractMonth
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib import messages
import json
from reportlab.pdfgen import canvas

from .models import (
    Product, Category, Cart, Order, OrderItem, Profile,
    Wishlist, Review, Coupon, ProductVariant,
    HeroSection, WebsiteTheme, ProductGridSettings,
)


def home(request):
    category_id = request.GET.get("category")
    search = request.GET.get("search")

    products = Product.objects.all()

    if category_id:
        products = products.filter(category_id=category_id)

    if search:
        products = products.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(category__name__icontains=search)
        )

    categories = Category.objects.all()
    hero = HeroSection.objects.filter(is_active=True).first()

    return render(request, "store/index.html", {
        "products": products,
        "categories": categories,
        "hero": hero,
    })


def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    grid_settings = ProductGridSettings.objects.first()

    return render(request, "store/category_products.html", {
        "category": category,
        "products": products,
        "grid_settings": grid_settings,
    })


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        variant_id = request.POST.get("variant")

        try:
            quantity = max(1, int(request.POST.get("quantity", 1)))
        except (ValueError, TypeError):
            quantity = 1

        variant = None
        if variant_id:
            variant = get_object_or_404(
                ProductVariant, id=variant_id, product=product
            )

        if request.POST.get("buy_now") == "1":
            request.session["direct_buy"] = {
                "product_id": product.id,
                "variant_id": variant.id if variant else None,
                "quantity": quantity,
            }
            return redirect("/?show_checkout=1")

        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            variant=variant,
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        messages.success(request, "Product added to cart.")
        return redirect("cart")

    return redirect("cart")


@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user).select_related(
        "product", "variant"
    )
    total = 0

    for item in cart_items:
        variant_extra = item.variant.extra_price if item.variant else 0
        item.subtotal = (item.product.price + variant_extra) * item.quantity
        total += item.subtotal

    return render(request, "store/cart.html", {
        "cart_items": cart_items,
        "total": total,
    })


@login_required
def remove_from_cart(request, cart_id):
    item = get_object_or_404(Cart, id=cart_id, user=request.user)
    item.delete()
    return redirect("cart")


@login_required
def increase_quantity(request, cart_id):
    item = get_object_or_404(Cart, id=cart_id, user=request.user)
    item.quantity += 1
    item.save()
    return redirect("cart")


@login_required
def decrease_quantity(request, cart_id):
    item = get_object_or_404(Cart, id=cart_id, user=request.user)

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()

    return redirect("cart")


@login_required
def checkout(request):
    direct_buy = request.session.get("direct_buy")

    if direct_buy:
        product = get_object_or_404(Product, id=direct_buy["product_id"])
        variant = None

        if direct_buy.get("variant_id"):
            variant = get_object_or_404(
                ProductVariant,
                id=direct_buy["variant_id"],
                product=product,
            )

        quantity = max(1, int(direct_buy.get("quantity", 1)))
        cart_items = [{
            "product": product,
            "variant": variant,
            "quantity": quantity,
            "price": product.price + (
                variant.extra_price if variant else 0
            ),
        }]
    else:
        cart_items = list(
            Cart.objects.filter(user=request.user).select_related(
                "product", "variant"
            )
        )

        for item in cart_items:
            item.price = item.product.price + (
                item.variant.extra_price if item.variant else 0
            )

    total = sum(
        (item["price"] * item["quantity"])
        if isinstance(item, dict)
        else (item.price * item.quantity)
        for item in cart_items
    )

    if request.method == "POST":
        code = request.POST.get("coupon", "").strip()

        if code:
            try:
                coupon = Coupon.objects.get(code=code, active=True)
                total -= total * coupon.discount / 100
                messages.success(
                    request, f"Coupon applied: {coupon.discount}% discount."
                )
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")

        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        payment_method = request.POST.get("payment_method")

        transaction_id = ""
        payment_screenshot = None

        if payment_method == "EASYPAISA":
            transaction_id = request.POST.get(
                "easypaisa_transaction", ""
            ).strip()
            payment_screenshot = request.FILES.get(
                "easypaisa_screenshot"
            )
        elif payment_method == "JAZZCASH":
            transaction_id = request.POST.get(
                "jazzcash_transaction", ""
            ).strip()
            payment_screenshot = request.FILES.get(
                "jazzcash_screenshot"
            )

        if payment_method in ["EASYPAISA", "JAZZCASH"]:
            if not transaction_id or not payment_screenshot:
                messages.error(
                    request,
                    "Transaction ID aur payment screenshot dono required hain.",
                )
                return redirect("checkout")

        if not cart_items:
            messages.error(request, "Your cart is empty.")
            return redirect("cart")

        order = Order.objects.create(
            user=request.user,
            customer_name=name,
            phone=phone,
            address=address,
            city=city,
            payment_method=payment_method,
            transaction_id=transaction_id,
            payment_screenshot=payment_screenshot,
            total_amount=total,
        )

        for item in cart_items:
            if isinstance(item, dict):
                product = item["product"]
                variant = item["variant"]
                quantity = item["quantity"]
                price = item["price"]
            else:
                product = item.product
                variant = item.variant
                quantity = item.quantity
                price = item.price

            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                quantity=quantity,
                price=price,
            )

        try:
            html_content = render_to_string(
                "store/order_confirmation_email.html",
                {
                    "name": name,
                    "address": address,
                    "city": city,
                    "payment_method": payment_method,
                    "total": total,
                },
            )

            email = EmailMultiAlternatives(
                subject="Your Order Confirmation - Nexora Mart",
                body=f"Dear {name},\n\nThank you for shopping at Nexora Mart.",
                from_email=settings.EMAIL_HOST_USER,
                to=[request.user.email],
            )
            email.attach_alternative(html_content, "text/html")

            if request.user.email:
                email.send()

            send_mail(
                subject="New Order Received - Nexora Mart",
                message=(
                    f"Customer: {name}\nPhone: {phone}\nAddress: {address}"
                    f"\nCity: {city}\nPayment: {payment_method}"
                    f"\nTransaction ID: {transaction_id}\nTotal: Rs {total}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["mind3996@gmail.com"],
                fail_silently=True,
            )
        except Exception:
            # Email failure should not undo an order that was created.
            pass

        if direct_buy:
            request.session.pop("direct_buy", None)
        else:
            Cart.objects.filter(user=request.user).delete()

        return redirect("order_success")

    return render(request, "store/checkout.html", {
        "cart_items": cart_items,
        "total": total,
        "direct_buy": bool(direct_buy),
    })


def order_success(request):
    return render(request, "store/order_success.html")


def signup(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        Profile.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
            address=address,
            city=city,
        )

        messages.success(request, "Account created successfully.")
        return redirect("login")

    return render(request, "store/signup.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request, username=username, password=password
        )

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(request, "store/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Logout successful.")
    return redirect("login")


@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, "store/profile.html", {
        "profile": profile_obj,
    })


@login_required
def edit_profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile_obj.full_name = request.POST.get("full_name", "")
        profile_obj.phone = request.POST.get("phone", "")
        profile_obj.city = request.POST.get("city", "")
        profile_obj.address = request.POST.get("address", "")
        profile_obj.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "store/edit_profile.html", {
        "profile": profile_obj,
    })


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "store/my_orders.html", {"orders": orders})


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        email = request.POST.get("email", "")
        message = request.POST.get("message", "")

        send_mail(
            subject=f"New Contact Message from {name}",
            message=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=True,
        )

        messages.success(request, "Your message has been sent successfully.")
        return redirect("contact")

    return render(request, "store/contact.html")


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product).order_by("-created_at")
    average = reviews.aggregate(Avg("rating"))["rating__avg"]
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    variants = product.variants.all()

    colors = []
    for variant in variants:
        if variant.color not in colors:
            colors.append(variant.color)

    return render(request, "store/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "average": average,
        "related_products": related_products,
        "variants": variants,
        "colors": colors,
    })


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    messages.success(request, "Added to wishlist.")
    return redirect("product_detail", product_id=product.id)


@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, "store/wishlist.html", {
        "wishlist_items": wishlist_items,
    })


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        Review.objects.create(
            user=request.user,
            product=product,
            rating=request.POST.get("rating"),
            comment=request.POST.get("comment"),
        )
        messages.success(request, "Review added successfully.")

    return redirect("product_detail", product_id=product.id)


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(
        Order, id=order_id, user=request.user
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="invoice_{order.id}.pdf"'
    )

    pdf = canvas.Canvas(response)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(200, 800, "Nexora Mart")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 760, f"Invoice #: {order.id}")
    pdf.drawString(50, 740, f"Customer: {order.customer_name}")
    pdf.drawString(50, 720, f"Phone: {order.phone}")
    pdf.drawString(50, 700, f"City: {order.city}")
    pdf.drawString(50, 680, f"Status: {order.status}")

    y = 640
    pdf.drawString(50, y, "Products")
    y -= 20

    for item in order.items.all():
        pdf.drawString(
            50, y,
            f"{item.product.name} x {item.quantity} = Rs {item.price}",
        )
        y -= 20

        if y < 60:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = 800

    pdf.drawString(50, y - 20, f"Total: Rs {order.total_amount}")
    pdf.save()
    return response


@login_required
def dashboard(request):
    if not request.user.is_staff:
        return redirect("home")

    total_orders = Order.objects.count()
    total_sales = Order.objects.aggregate(
        Sum("total_amount")
    )["total_amount__sum"] or 0
    total_customers = User.objects.count()
    total_products = Product.objects.count()
    total_reviews = Review.objects.count()
    total_wishlist = Wishlist.objects.count()

    sales_labels = ["Orders", "Products", "Customers", "Reviews"]
    sales_data = [
        total_orders, total_products, total_customers, total_reviews
    ]

    best_products = Product.objects.annotate(
        total_sold=Count("orderitem")
    ).order_by("-total_sold")[:5]

    recent_orders = Order.objects.order_by("-created_at")[:5]
    recent_reviews = Review.objects.select_related(
        "product", "user"
    ).order_by("-created_at")[:5]

    top_customers = User.objects.annotate(
        total_orders=Count("order"),
        total_spent=Sum("order__total_amount"),
    ).order_by("-total_spent")[:5]

    monthly_sales = (
        Order.objects.annotate(month=ExtractMonth("created_at"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )

    return render(request, "store/dashboard.html", {
        "total_orders": total_orders,
        "total_sales": total_sales,
        "total_customers": total_customers,
        "total_products": total_products,
        "total_reviews": total_reviews,
        "total_wishlist": total_wishlist,
        "sales_labels": json.dumps(sales_labels),
        "sales_data": json.dumps(sales_data),
        "best_products": best_products,
        "recent_orders": recent_orders,
        "recent_reviews": recent_reviews,
        "top_customers": top_customers,
        "monthly_labels": json.dumps([
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]),
        "monthly_data": json.dumps([
            next(
                (
                    float(item["total"])
                    for item in monthly_sales
                    if item["month"] == month
                ),
                0,
            )
            for month in range(1, 13)
        ]),
    })


@login_required
def update_order_status(request, order_id):
    if not request.user.is_staff:
        return redirect("home")

    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        order.status = request.POST.get("status")
        order.save()
        messages.success(request, "Order status updated successfully.")

    return redirect("dashboard")


@login_required
def product_list(request):
    if not request.user.is_staff:
        return redirect("home")

    return render(request, "store/product_list.html", {
        "products": Product.objects.all(),
    })


@login_required
def add_product(request):
    if not request.user.is_staff:
        return redirect("home")

    categories = Category.objects.all()

    if request.method == "POST":
        category = get_object_or_404(
            Category, id=request.POST.get("category")
        )

        Product.objects.create(
            category=category,
            name=request.POST.get("name"),
            price=request.POST.get("price"),
            description=request.POST.get("description"),
            image=request.FILES.get("image"),
        )

        messages.success(request, "Product added successfully.")
        return redirect("product_list")

    return render(request, "store/add_product.html", {
        "categories": categories,
    })


@login_required
def delete_product(request, product_id):
    if not request.user.is_staff:
        return redirect("home")

    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect("product_list")


@login_required
def edit_product(request, product_id):
    if not request.user.is_staff:
        return redirect("home")

    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    if request.method == "POST":
        product.category_id = request.POST.get("category")
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.description = request.POST.get("description")

        if request.FILES.get("image"):
            product.image = request.FILES["image"]

        product.save()
        messages.success(request, "Product updated successfully.")
        return redirect("product_list")

    return render(request, "store/edit_product.html", {
        "product": product,
        "categories": categories,
    })


@login_required
def product_view(request, product_id):
    if not request.user.is_staff:
        return redirect("home")

    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)
    wishlist_count = Wishlist.objects.filter(product=product).count()

    return render(request, "store/product_view.html", {
        "product": product,
        "reviews": reviews,
        "wishlist_count": wishlist_count,
    })


def order_confirmation_preview(request):
    context = {
        "name": "Customer",
        "total": 2500,
        "payment_method": "Cash on Delivery",
        "city": "Pirmahal",
        "address": "Example delivery address",
    }
    return render(request, "store/order_success.html", context)


@login_required
def variant_list(request):
    if not request.user.is_staff:
        return redirect("home")

    variants = ProductVariant.objects.select_related("product").all()
    return render(request, "store/variant_list.html", {
        "variants": variants,
    })


@login_required
def add_variant(request):
    if not request.user.is_staff:
        return redirect("home")

    products = Product.objects.all()

    if request.method == "POST":
        try:
            ProductVariant.objects.create(
                product=get_object_or_404(
                    Product, id=request.POST.get("product")
                ),
                color=request.POST.get("color", "").strip(),
                size=request.POST.get("size"),
                stock=int(request.POST.get("stock", 0)),
                extra_price=request.POST.get("extra_price", 0),
                image=request.FILES.get("image"),
            )
            messages.success(request, "Variant added successfully.")
            return redirect("variant_list")
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid stock and price.")

    return render(request, "store/variant_form.html", {
        "products": products,
        "sizes": ProductVariant.SIZE_CHOICES,
    })


@login_required
def edit_variant(request, variant_id):
    if not request.user.is_staff:
        return redirect("home")

    variant = get_object_or_404(ProductVariant, id=variant_id)
    products = Product.objects.all()

    if request.method == "POST":
        try:
            variant.product = get_object_or_404(
                Product, id=request.POST.get("product")
            )
            variant.color = request.POST.get("color", "").strip()
            variant.size = request.POST.get("size")
            variant.stock = int(request.POST.get("stock", 0))
            variant.extra_price = request.POST.get("extra_price", 0)

            if request.FILES.get("image"):
                variant.image = request.FILES["image"]

            variant.save()
            messages.success(request, "Variant updated successfully.")
            return redirect("variant_list")
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid stock and price.")

    return render(request, "store/variant_form.html", {
        "variant": variant,
        "products": products,
        "sizes": ProductVariant.SIZE_CHOICES,
    })


@login_required
def delete_variant(request, variant_id):
    if not request.user.is_staff:
        return redirect("home")

    variant = get_object_or_404(ProductVariant, id=variant_id)

    if request.method == "POST":
        variant.delete()
        messages.success(request, "Variant deleted successfully.")

    return redirect("variant_list")


@login_required
def theme_settings(request):
    if not request.user.is_staff:
        return redirect("home")

    theme = WebsiteTheme.objects.filter(is_active=True).first()

    if not theme:
        theme = WebsiteTheme.objects.create(name="Main Theme")

    if request.method == "POST":
        try:
            theme.theme_type = request.POST.get("theme_type", "solid")
            theme.background_color = request.POST.get(
                "background_color", "#ffffff"
            )
            theme.gradient_color_1 = request.POST.get(
                "gradient_color_1", "#667eea"
            )
            theme.gradient_color_2 = request.POST.get(
                "gradient_color_2", "#764ba2"
            )
            theme.gradient_direction = request.POST.get(
                "gradient_direction", "135deg"
            )
            theme.blur = int(request.POST.get("blur", 15))
            theme.transparency = int(request.POST.get("transparency", 20))
            theme.border_radius = int(request.POST.get("border_radius", 16))
            theme.save()
            messages.success(request, "Theme settings saved!")
            return redirect("theme_settings")
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid theme settings.")

    return render(request, "store/theme_settings.html", {
        "theme": theme,
    })
