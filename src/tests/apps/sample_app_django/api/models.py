from decimal import Decimal
from django.db import models


class User(models.Model):
    id: str = models.AutoField(primary_key=True)
    username: str = models.CharField(
        null=False,
        blank=False,
        db_index=True,
        unique=True,
        max_length=100,
    )


class Order(models.Model):
    id: str = models.BigAutoField(primary_key=True)
    user: "User" = models.ForeignKey("api.User", null=False, on_delete=models.CASCADE)
    name: str = models.CharField(null=True, blank=True, max_length=30)
    price: Decimal = models.DecimalField(null=False, decimal_places=2, max_digits=10)
