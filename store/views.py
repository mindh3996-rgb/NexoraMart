from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.db.models import Avg
from django.db.models import Sum
import json
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum, Count
from django.db.models.functions import ExtractMonth
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Cart, Order, OrderItem, Profile, Wishlist, Review, Coupon

def home(request):

    category_id = request.GET.get("category")
    search = request.GET.get("search")

    products = Product.objects.all()

    # Category Filter
    if category_id:
        products = products.filter(category_id=category_id)

    # Search Filter
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__name__icontains=search)
        )

    categories = Category.objects.all()

    context = {
        "products": products,
        "categories": categories,
    }

    return render(request, "store/index.html", context)
@login_required
def add_to_cart(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, "Product added to cart")

    return redirect("cart")
@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = 0

    for item in cart_items:
        item.subtotal = item.product.price * item.quantity
        total += item.subtotal

    context = {
        "cart_items": cart_items,
        "total": total,
    }

    return render(request, "store/cart.html", context)


@login_required
def remove_from_cart(request, cart_id):
    item = get_object_or_404(
        Cart,
        id=cart_id,
        user=request.user
    )
    item.delete()

    return redirect("cart")


@login_required
def increase_quantity(request, cart_id):
    item = get_object_or_404(
        Cart,
        id=cart_id,
        user=request.user
    )

    item.quantity += 1
    item.save()

    return redirect("cart")


@login_required
def decrease_quantity(request, cart_id):
    item = get_object_or_404(
        Cart,
        id=cart_id,
        user=request.user
    )

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()

    return redirect("cart")
@login_required
def checkout(request):

    cart_items = Cart.objects.filter(user=request.user)

    total = 0

    for item in cart_items:
        total += item.product.price * item.quantity

    discount = 0

    if request.method == "POST":

        code = request.POST.get("coupon")

        if code:

            try:
                coupon = Coupon.objects.get(
                    code=code,
                    active=True
                )

                discount = coupon.discount
                total = total - (total * discount / 100)

                messages.success(
                    request,
                    f"Coupon Applied! {discount}% Discount"
                )

            except Coupon.DoesNotExist:

                messages.error(
                    request,
                    "Invalid Coupon Code"
                )

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        city = request.POST.get("city")
        payment_method = request.POST.get("payment_method")

        # Default values
        transaction_id = ""
        payment_screenshot = None

        # Easypaisa
        if payment_method == "EASYPAISA":

            transaction_id = request.POST.get("easypaisa_transaction")
            payment_screenshot = request.FILES.get("easypaisa_screenshot")

            if not transaction_id:
                messages.error(request, "Please enter Easypaisa Transaction ID.")
                return redirect("checkout")

            if not payment_screenshot:
                messages.error(request, "Please upload Easypaisa screenshot.")
                return redirect("checkout")

        # JazzCash
        elif payment_method == "JAZZCASH":

            transaction_id = request.POST.get("jazzcash_transaction")
            payment_screenshot = request.FILES.get("jazzcash_screenshot")

            if not transaction_id:
                messages.error(request, "Please enter JazzCash Transaction ID.")
                return redirect("checkout")

            if not payment_screenshot:
                messages.error(request, "Please upload JazzCash screenshot.")
                return redirect("checkout")

        order = Order.objects.create(
            user=request.user,
            customer_name=name,
            phone=phone,
            address=address,
            city=city,
            payment_method=payment_method,
            transaction_id=transaction_id,
            payment_screenshot=payment_screenshot,
            total_amount=total
        )

        for item in cart_items:

            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                price=item.product.price
            )

        #        # ==========================
        # Email to Customer (HTML)
        # ==========================

        html_content = render_to_string(
            "store/order_confirmation_email.html",
            {
                "name": name,
                "address": address,
                "city": city,
                "payment_method": payment_method,
                "total": total,
            }
        )

        email = EmailMultiAlternatives(
            subject="Your Order Confirmation - Nexora Mart",
            body=f"""
Dear {name},

Thank you for shopping at Nexora Mart.

Your order has been placed successfully.
""",
            from_email=settings.EMAIL_HOST_USER,
            to=[request.user.email],
        )

        email.attach_alternative(html_content, "text/html")
        email.send()
        # ==========================
        # Email to Admin
        # ==========================

        admin_message = f"""
New Order Received

Customer: {name}

Phone: {phone}

Address: {address}

City: {city}

Payment Method: {payment_method}

Transaction ID: {transaction_id}

Total: Rs{total}
"""

        send_mail(
            subject="New Order Received - Nexora Mart",
            message=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["mind3996@gmail.com"],
            fail_silently=False,
        )

        Cart.objects.filter(user=request.user).delete()

        return redirect("order_success")

    context = {
        "cart_items": cart_items,
        "total": total,
    }

    return render(request, "store/checkout.html", context)


def order_success(request):
    return render(request, "store/order_success.html")
def signup(request):

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")   

        phone = request.POST.get("phone")
        address = request.POST.get("address")
        city = request.POST.get("city")
        if password != confirm_password:
           messages.error(request, "Passwords do not match")
           return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")


        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )


        Profile.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
            address=address,
            city=city
        )


        messages.success(
            request,
            "Account Created Successfully"
        )

        return redirect("login")


    return render(request, "store/signup.html")
def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            messages.success(
                request,
                "Login Successful"
            )

            return redirect("home")

        else:
            messages.error(
                request,
                "Invalid Username or Password"
            )

    return render(request, "store/login.html")

def logout_view(request):
    logout(request)

    messages.success(
        request,
        "Logout Successfully"
    )

    return redirect("login")
@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    return render(request, "store/profile.html", {
        "profile": profile
    })


@login_required
def edit_profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        profile.full_name = request.POST.get("full_name")
        profile.phone = request.POST.get("phone")
        profile.city = request.POST.get("city")
        profile.address = request.POST.get("address")

        profile.save()

        messages.success(request, "Profile Updated Successfully")

        return redirect("profile")

    return render(
        request,
        "store/edit_profile.html",
        {
            "profile": profile
        }
    )
@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "store/my_orders.html",
        {
            "orders": orders
        }
    )

def contact(request):

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        send_mail(
            subject=f"New Contact Message from {name}",
            message=f"""
Name: {name}

Email: {email}

Message:
{message}
""",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
        )

        messages.success(
            request,
            "Your message has been sent successfully."
        )

        return redirect("contact")

    return render(request, "store/contact.html")
def product_detail(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    reviews = Review.objects.filter(
        product=product
    ).order_by("-created_at")

    average = reviews.aggregate(
        Avg("rating")
    )["rating__avg"]

    related_products = Product.objects.filter(
        category=product.category
    ).exclude(
        id=product.id
    )[:4]

    variants = product.variants.all()

    colors = []

    for variant in variants:
        if variant.color not in colors:
            colors.append(variant.color)

    context = {
        "product": product,
        "reviews": reviews,
        "average": average,
        "related_products": related_products,
        "variants": variants,
        "colors": colors,
    }

    return render(
        request,
        "store/product_detail.html",
        context
    )
@login_required
def add_to_wishlist(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    messages.success(request, "Added to Wishlist ❤️")

    return redirect("product_detail", product_id=product.id)

@login_required
def wishlist(request):

    wishlist_items = Wishlist.objects.filter(user=request.user)

    return render(
        request,
        "store/wishlist.html",
        {
            "wishlist_items": wishlist_items
        }
    )
@login_required
def add_review(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":

        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        Review.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            comment=comment
        )

        messages.success(
            request,
            "Review Added Successfully ⭐"
        )

    return redirect("product_detail", product_id=product.id)
@login_required
def download_invoice(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{order.id}.pdf"'

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, 800, "Nexora Mart")

    p.setFont("Helvetica", 12)
    p.drawString(50, 760, f"Invoice #: {order.id}")
    p.drawString(50, 740, f"Customer: {order.customer_name}")
    p.drawString(50, 720, f"Phone: {order.phone}")
    p.drawString(50, 700, f"City: {order.city}")
    p.drawString(50, 680, f"Status: {order.status}")

    y = 640

    p.drawString(50, y, "Products")
    y -= 20

    for item in order.items.all():
        p.drawString(
            50,
            y,
            f"{item.product.name} x {item.quantity} = Rs {item.price}"
        )
        y -= 20

    y -= 20
    p.drawString(50, y, f"Total: Rs {order.total_amount}")

    p.save()

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
    total_orders,
    total_products,
    total_customers,
    total_reviews,
]
    best_products = Product.objects.annotate(
    total_sold=Count("orderitem")
).order_by("-total_sold")[:5]
    recent_orders = Order.objects.order_by("-created_at")[:5]
    recent_reviews = Review.objects.select_related(
    "product",
    "user"
).order_by("-created_at")[:5]
    
    top_customers = User.objects.annotate(
    total_orders=Count("order"),
    total_spent=Sum("order__total_amount")
).order_by("-total_spent")[:5]
    monthly_sales = (
    Order.objects
    .annotate(month=ExtractMonth("created_at"))
    .values("month")
    .annotate(total=Sum("total_amount"))
    .order_by("month")
)
    context = {
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
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]),

"monthly_data": json.dumps([
    next((float(item["total"]) for item in monthly_sales if item["month"] == i), 0)
    for i in range(1, 13)
]),
}

    return render(
        request,
        "store/dashboard.html",
        context
    )
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
def update_order_status(request, order_id):

    if not request.user.is_staff:
        return redirect("home")

    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        status = request.POST.get("status")
        order.status = status
        order.save()

        messages.success(request, "Order status updated successfully.")

    return redirect("dashboard")
@login_required
def product_list(request):

    if not request.user.is_staff:
        return redirect("home")

    products = Product.objects.all()

    return render(
        request,
        "store/product_list.html",
        {
            "products": products
        }
    )
@login_required
def add_product(request):

    if not request.user.is_staff:
        return redirect("home")

    categories = Category.objects.all()

    if request.method == "POST":

        category_id = request.POST.get("category")
        name = request.POST.get("name")
        price = request.POST.get("price")
        description = request.POST.get("description")
        image = request.FILES.get("image")

        category = Category.objects.get(id=category_id)

        Product.objects.create(
            category=category,
            name=name,
            price=price,
            description=description,
            image=image
        )

        messages.success(
            request,
            "Product Added Successfully"
        )

        return redirect("product_list")


    return render(
        request,
        "store/add_product.html",
        {
            "categories": categories
        }
    )
@login_required
def delete_product(request, product_id):

    if not request.user.is_staff:
        return redirect("home")

    product = get_object_or_404(
        Product,
        id=product_id
    )

    product.delete()

    messages.success(
        request,
        "Product Deleted Successfully"
    )

    return redirect("product_list")
@login_required
def edit_product(request, product_id):

    if not request.user.is_staff:
        return redirect("home")

    product = get_object_or_404(
        Product,
        id=product_id
    )

    categories = Category.objects.all()

    if request.method == "POST":

        product.category_id = request.POST.get("category")
        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        product.description = request.POST.get("description")

        if request.FILES.get("image"):
            product.image = request.FILES.get("image")

        product.save()

        messages.success(
            request,
            "Product Updated Successfully"
        )

        return redirect("product_list")


    return render(
        request,
        "store/edit_product.html",
        {
            "product": product,
            "categories": categories
        }
    )
@login_required
def product_view(request, product_id):

    if not request.user.is_staff:
        return redirect("home")

    product = get_object_or_404(
        Product,
        id=product_id
    )

    reviews = Review.objects.filter(
        product=product
    )

    wishlist_count = Wishlist.objects.filter(
        product=product
    ).count()


    return render(
        request,
        "store/product_view.html",
        {
            "product": product,
            "reviews": reviews,
            "wishlist_count": wishlist_count,
        }
    )
@login_required
def update_order_status(request, order_id):

    if not request.user.is_staff:
        return redirect("home")

    order = get_object_or_404(
        Order,
        id=order_id
    )

    if request.method == "POST":

        status = request.POST.get("status")

        order.status = status
        order.save()

        messages.success(
            request,
            "Order status updated successfully"
        )

    return redirect("dashboard")
