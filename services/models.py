import uuid
from django.db import models

from authentication.models import User


# Create your models here.


class Category(models.Model):
    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    name = models.CharField(max_length=225, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self) -> str:
        return self.name


class Rating(models.Model):
    id = models.UUIDField(
        primary_key=True, editable=False, unique=True, default=uuid.uuid4
    )
    service_provider = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="rating"
    )
    rating = models.PositiveIntegerField()
    review = models.TextField()
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="customer_review"
    )
    rated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.rating)


class Schedule(models.Model):
    id = models.UUIDField(
        primary_key=True, editable=False, unique=True, default=uuid.uuid4
    )
    title = models.CharField(max_length=225)
    service_provider = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="schedule"
    )
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="customer_schedule"
    )
    date_and_time = models.DateTimeField()
    detail = models.TextField()

    def __str__(self) -> str:
        return self.title
