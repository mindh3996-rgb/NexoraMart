
from .models import MenuItem, NavbarSettings

def navbar_menu(request):
    menus = MenuItem.objects.filter(
        is_active=True, parent__isnull=True
    ).prefetch_related("children")

    return {
        "navbar_menus": menus,
        "navbar_settings": NavbarSettings.objects.filter(
            is_active=True
        ).first(),
    }

from .models import WebsiteTheme

def global_website_theme(request):
    return {
        "website_theme": WebsiteTheme.objects.filter(is_active=True).first()
    }
