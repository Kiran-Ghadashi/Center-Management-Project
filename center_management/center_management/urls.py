"""
URL configuration for center_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [

    # ─────────────────────────────────────────
    # ADMIN PANEL
    # ─────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ─────────────────────────────────────────
    # CORE APP — all pages go through core/urls.py
    # ─────────────────────────────────────────
    path('', include('core.urls', namespace='core')),

    # ─────────────────────────────────────────
    # ROOT REDIRECT — visiting "/" goes to dashboard
    # (handled inside core/urls.py but kept here as fallback)
    # ─────────────────────────────────────────

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ── Custom error pages (optional but professional) ──
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'
