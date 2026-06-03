from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from users import views

urlpatterns = [
    path("", views.index, name="index"),
    path("home/", views.home, name="home"),
    path("user/home/", views.user_homepage, name="UserHome"),
    path("user/login/", views.user_login, name="UserLogin"),
    path("interview/", views.interview_page, name="interview_page"),
    path("admin/login/", views.admin_login, name="AdminLogin"),
    path("admin/home/", views.admin_home, name="admin_home"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("register/", views.register_view, name="register_view"),
    path("register/form/", views.register_view, name="UserRegisterForm"),
    path("verify/", views.verify_otp, name="verify_view"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/", views.reset_password, name="reset_password"),
    path("logout/", views.user_logout, name="user_logout"),
    path("api/start-interview/", views.start_interview, name="start_interview"),
    path("api/answer-question/", views.answer_question, name="answer_question"),
    path("api/interview-results/", views.interview_results, name="interview_results"),
    path("api/all-results/", views.all_results, name="all_results"),
    path("admin/users/<int:user_id>/activate/", views.activate_user, name="activate_user"),
    path("admin/users/<int:user_id>/deactivate/", views.deactivate_user, name="deactivate_user"),
    path("admin/users/<int:user_id>/delete/", views.delete_user, name="delete_user"),
    path("admin/", admin.site.urls),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
