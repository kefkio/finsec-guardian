from django.db import models


class TamperProofRecord(models.Model):
    title = models.CharField(max_length=512)
    content = models.TextField()
    content_hash = models.CharField(max_length=64)
    previous_hash = models.CharField(max_length=64, default='0' * 64)
    chain_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Record #{self.pk} — {self.title}'
