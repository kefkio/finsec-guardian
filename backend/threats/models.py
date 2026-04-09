from django.db import models


class Threat(models.Model):
    CATEGORY_CHOICES = [
        ('spoofing', 'Spoofing'),
        ('tampering', 'Tampering'),
        ('repudiation', 'Repudiation'),
        ('information_disclosure', 'Information Disclosure'),
        ('denial_of_service', 'Denial of Service'),
        ('elevation_of_privilege', 'Elevation of Privilege'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('mitigated', 'Mitigated'),
        ('accepted', 'Accepted'),
        ('closed', 'Closed'),
    ]

    title = models.CharField(max_length=512)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='tampering')
    likelihood = models.IntegerField(default=5)
    impact = models.IntegerField(default=5)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    mitigation = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def risk_score(self):
        return self.likelihood * self.impact

    def __str__(self):
        return self.title
