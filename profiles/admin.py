from django.contrib import admin
from .models import CustomUser, Addresses

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Addresses)

