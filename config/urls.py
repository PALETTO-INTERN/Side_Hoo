"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

urlpatterns = [
    # 관리자 페이지 URL
    path('admin/', admin.site.urls),
    
    # Django 기본 인증(로그인/로그아웃) 관련 URL 연결
    # accounts/login/, accounts/logout/ 등의 주소를 사용하게 됩니다.
    path('accounts/', include('django.contrib.auth.urls')),
    
    # core 앱의 모든 URL을 루트 경로('')에 연결
    path('', include('core.urls')),
]