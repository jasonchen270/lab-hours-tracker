from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from sessions_app import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("start/", views.start_session, name="start_session"),
    path("stop/", views.stop_session, name="stop_session"),
    path("export.csv", views.export_csv, name="export_csv"),
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
