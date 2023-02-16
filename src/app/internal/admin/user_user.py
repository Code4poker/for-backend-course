from django.contrib import admin
from app.internal.models.user_user import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass
