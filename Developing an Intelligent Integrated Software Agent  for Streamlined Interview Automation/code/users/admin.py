from django.contrib import admin

from .models import Candidate, InterviewResponse, RegisteredUser


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "created_at")
    search_fields = ("name", "email")


@admin.register(InterviewResponse)
class InterviewResponseAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate", "score", "created_at")
    list_filter = ("score",)


@admin.register(RegisteredUser)
class RegisteredUserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "email")
