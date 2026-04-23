from django.db import models


class TamperRecord(models.Model):
    content = models.TextField()
    content_hash = models.CharField(max_length=64)
    previous_hash = models.CharField(max_length=64, default='0' * 64)
    chain_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Record {self.id} — {self.content_hash[:16]}..."
