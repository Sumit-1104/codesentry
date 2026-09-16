from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from reviewer.views import dashboard_view, review_report, signup_view, history_view, history_detail_view, download_pdf_view, api_history_list, api_history_detail, api_docs_view
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard_view),
    path("analyze/", review_report, name="analyze"),
    path("signup/", signup_view, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="reviewer/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("history/", history_view, name="history"),
    path("history/<int:history_id>/", history_detail_view, name="history_detail"),
    path("history/<int:history_id>/pdf/", download_pdf_view, name="download_pdf"),
    path("api/history/", api_history_list, name="api_history_list"),
    path("api/history/<int:history_id>/", api_history_detail, name="api_history_detail"),
    path("api/", api_docs_view, name="api_docs"),
    path("api/token/", obtain_auth_token, name="api_token"),
]