from django.db import models


class Slot(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        BOOKED = "booked", "Booked"

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    coordinates = models.JSONField(
        help_text="4-corner bounding box: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OPEN
    )

    class Meta:
        db_table = "slots"

    def __str__(self):
        return f"{self.name} ({self.status})"
