from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name



class Product(models.Model):

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=200
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to="products/"
    )

    description = models.TextField()


    def __str__(self):
        return self.name



# Multiple product images
class ProductImage(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(
        upload_to="products/gallery/"
    )


    def __str__(self):
        return self.product.name



# Product Color / Size Variants
class ProductVariant(models.Model):

    SIZE_CHOICES = [
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
        ("XL", "Extra Large"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    color = models.CharField(
        max_length=50
    )

    size = models.CharField(
        max_length=5,
        choices=SIZE_CHOICES
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    extra_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    image = models.ImageField(
        upload_to="products/variants/",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.product.name} - {self.color} - {self.size}"
class Cart(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )


    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )


    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )


    quantity = models.PositiveIntegerField(
        default=1
    )


    def __str__(self):
     if self.variant:
        return f"{self.user.username} - {self.product.name} - {self.variant.color} - {self.variant.size}"
     return f"{self.user.username} - {self.product.name}"      
class Order(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Processing", "Processing"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]

    PAYMENT_CHOICES = [
        ("COD", "Cash on Delivery"),
        ("EASYPAISA", "Easypaisa"),
        ("JAZZCASH", "JazzCash"),
    ]

    customer_name = models.CharField(max_length=100)

    phone = models.CharField(max_length=20)

    address = models.TextField()

    city = models.CharField(max_length=100)

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="COD"
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    payment_screenshot = models.ImageField(
        upload_to="payments/",
        blank=True,
        null=True
    )

    payment_verified = models.BooleanField(
        default=False
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.customer_name

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.product.name    


class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(
        max_length=100
    )

    phone = models.CharField(
        max_length=15
    )

    city = models.CharField(
        max_length=100
    )

    address = models.TextField()


    def __str__(self):
        return self.user.username
    
class Wishlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
class Review(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    rating = models.IntegerField()

    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class Coupon(models.Model):

    code = models.CharField(max_length=20, unique=True)

    discount = models.IntegerField(
        help_text="Discount Percentage"
    )

    active = models.BooleanField(default=True)
 
    def __str__(self):
        return self.code
class MenuItem(models.Model):
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=255, blank=True)

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="menu_items"
    )

    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class HeroSection(models.Model):
    MEDIA_CHOICES = [("image", "Image"), ("video", "Video")]
    ALIGN_CHOICES = [("left", "Left"), ("center", "Center"), ("right", "Right")]
    ANIMATION_CHOICES = [("none", "None"), ("fade", "Fade In"), ("slide", "Slide Up"), ("zoom", "Zoom In")]
    FONT_CHOICES = [
        ("Arial, sans-serif", "Arial"),
        ("Georgia, serif", "Georgia"),
        ("Verdana, sans-serif", "Verdana"),
        ("Tahoma, sans-serif", "Tahoma"),
    ]
    LAYOUT_CHOICES = [
        ("background", "Full Section Background"),
        ("side", "Image/Video on Side"),
        ("color", "Solid Color Background"),
        ("gradient", "Gradient Background"),
    ]
    CONTENT_CHOICES = [("inside", "Text Inside Image/Video"), ("outside", "Text Outside Image/Video")]
    BUTTON_CHOICES = [("glass", "Glassmorphism"), ("clay", "Claymorphism"), ("solid", "Solid Button")]

    title = models.CharField(max_length=150, blank=True)
    heading = models.CharField(max_length=200, blank=True)
    subheading = models.CharField(max_length=200, blank=True)
    paragraph = models.TextField(blank=True)

    media_type = models.CharField(max_length=10, choices=MEDIA_CHOICES, default="image")
    image = models.ImageField(upload_to="hero/", blank=True, null=True)
    video = models.FileField(upload_to="hero/videos/", blank=True, null=True)

    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default="side")
    content_position = models.CharField(max_length=10, choices=CONTENT_CHOICES, default="outside")
    media_position = models.CharField(max_length=10, choices=[("left", "Left"), ("right", "Right")], default="right")

    background_color = models.CharField(max_length=20, default="#ffffff")
    gradient_start = models.CharField(max_length=20, default="#111827")
    gradient_end = models.CharField(max_length=20, default="#4f46e5")
    text_color = models.CharField(max_length=20, default="#ffffff")

    font_family = models.CharField(max_length=100, choices=FONT_CHOICES, default="Arial, sans-serif")
    heading_size = models.PositiveIntegerField(default=48)
    paragraph_size = models.PositiveIntegerField(default=18)
    alignment = models.CharField(max_length=10, choices=ALIGN_CHOICES, default="left")
    animation = models.CharField(max_length=10, choices=ANIMATION_CHOICES, default="fade")

    show_text_box = models.BooleanField(default=True)
    box_opacity = models.PositiveIntegerField(default=45)

    button_text = models.CharField(max_length=50, default="Shop Now")
    button_url = models.CharField(max_length=300, default="/")
    button_style = models.CharField(max_length=10, choices=BUTTON_CHOICES, default="glass")
    button_color = models.CharField(max_length=20, default="#6366f1")
    button_text_color = models.CharField(max_length=20, default="#ffffff")

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title or "Hero Section"

class NavbarSettings(models.Model):
    ANIMATION_CHOICES = [
        ("none", "None"), ("rotate", "Circular Rotation"),
        ("zoom", "Zoom"), ("pulse", "Pulse"),
        ("flip", "Flip"), ("bounce", "Bounce"),
        ("float", "Float"), ("shake", "Shake"),
    ]
    ALIGN_CHOICES = [
        ("left", "Left"), ("center", "Center"), ("right", "Right"),
    ]
    MENU_CHOICES = [
        ("text", "Simple Text"), ("underline", "Underline"),
        ("button", "Button"), ("glass", "Glassmorphism"),
        ("clay", "Claymorphism"), ("neumorphism", "Neumorphism"),
    ]
    MORPHISM_CHOICES = [
        ("none", "None"), ("glass", "Glassmorphism"),
        ("clay", "Claymorphism"), ("neumorphism", "Neumorphism"),
    ]
    ICON_CHOICES = [
        ("icon", "Icon Only"), ("text", "Text Only"),
        ("both", "Icon + Text"),
    ]

    logo = models.ImageField(upload_to="navbar/", blank=True, null=True)
    brand_name = models.CharField(max_length=100, default="Nexora Mart")
    show_brand_name = models.BooleanField(default=True)
    logo_width = models.PositiveIntegerField(default=43)
    logo_height = models.PositiveIntegerField(default=43)
    logo_alignment = models.CharField(max_length=10, choices=ALIGN_CHOICES, default="left")
    logo_animation = models.CharField(max_length=10, choices=ANIMATION_CHOICES, default="none")
    animation_speed = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)

    background_color = models.CharField(max_length=30, default="#0a0a10")
    background_opacity = models.PositiveIntegerField(default=94)
    background_morphism = models.CharField(max_length=15, choices=MORPHISM_CHOICES, default="glass")
    background_blur = models.PositiveIntegerField(default=18)
    background_gradient = models.BooleanField(default=False)
    gradient_start = models.CharField(max_length=30, default="#0a0a10")
    gradient_end = models.CharField(max_length=30, default="#30205a")
    border_color = models.CharField(max_length=30, default="#333344")
    shadow_enabled = models.BooleanField(default=True)
    sticky_header = models.BooleanField(default=True)

    menu_style = models.CharField(max_length=15, choices=MENU_CHOICES, default="underline")
    menu_text_color = models.CharField(max_length=30, default="#f4f4f7")
    menu_hover_color = models.CharField(max_length=30, default="#b9a0ff")
    menu_background_color = models.CharField(max_length=30, default="#252535")
    menu_font_size = models.PositiveIntegerField(default=15)
    menu_gap = models.PositiveIntegerField(default=8)
    menu_underline_color = models.CharField(max_length=30, default="#b9a0ff")
    menu_border_radius = models.PositiveIntegerField(default=12)

    icon_display = models.CharField(max_length=10, choices=ICON_CHOICES, default="icon")
    icon_color = models.CharField(max_length=30, default="#ffffff")
    icon_hover_color = models.CharField(max_length=30, default="#111111")
    icon_background = models.CharField(max_length=30, default="#252535")
    icon_hover_background = models.CharField(max_length=30, default="#b9a0ff")
    icon_style = models.CharField(max_length=15, choices=MORPHISM_CHOICES, default="glass")
    icon_size = models.PositiveIntegerField(default=41)
    show_search = models.BooleanField(default=True)
    show_wishlist = models.BooleanField(default=True)
    show_cart = models.BooleanField(default=True)
    show_contact = models.BooleanField(default=True)

    search_placeholder = models.CharField(max_length=100, default="Search products...")
    search_width = models.PositiveIntegerField(default=150)
    search_background = models.CharField(max_length=30, default="#252535")
    search_text_color = models.CharField(max_length=30, default="#ffffff")
    search_border_color = models.CharField(max_length=30, default="#555566")
    search_border_radius = models.PositiveIntegerField(default=14)

    mobile_menu_background = models.CharField(max_length=30, default="#101018")
    mobile_menu_text_color = models.CharField(max_length=30, default="#ffffff")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Navbar Settings"
        verbose_name_plural = "Navbar Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Nexora Mart Navbar Settings"

class WebsiteTheme(models.Model):
    THEME_CHOICES = [
        ("solid", "Solid Color"),
        ("gradient", "Gradient"),
        ("glass", "Glassmorphism"),
        ("clay", "Claymorphism"),
    ]

    name = models.CharField(max_length=100, default="Main Theme")
    theme_type = models.CharField(max_length=20, choices=THEME_CHOICES, default="solid")
    background_color = models.CharField(max_length=20, default="#ffffff")
    gradient_color_1 = models.CharField(max_length=20, default="#667eea")
    gradient_color_2 = models.CharField(max_length=20, default="#764ba2")
    gradient_direction = models.CharField(max_length=20, default="135deg")
    blur = models.PositiveIntegerField(default=15)
    transparency = models.PositiveIntegerField(default=20)
    border_radius = models.PositiveIntegerField(default=16)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

from django.contrib import admin
from .models import WebsiteTheme

@admin.register(WebsiteTheme)
class WebsiteThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "theme_type", "is_active")
    list_editable = ("is_active",)
   
class ProductGridSettings(models.Model):
    desktop_columns = models.PositiveSmallIntegerField(default=4)
    tablet_columns = models.PositiveSmallIntegerField(default=3)
    mobile_columns = models.PositiveSmallIntegerField(default=2)
    image_height = models.PositiveIntegerField(default=240)
    card_gap = models.PositiveIntegerField(default=20)
    card_padding = models.PositiveIntegerField(default=12)
    card_radius = models.PositiveIntegerField(default=12)
    title_font_size = models.PositiveIntegerField(default=16)
    price_font_size = models.PositiveIntegerField(default=16)

    def __str__(self):
        return "Product Grid Settings"