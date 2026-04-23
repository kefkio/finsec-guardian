from django.db import models


class ThreatRecord(models.Model):
    CATEGORY_CHOICES = [
        ('spoofing', 'Spoofing'),
        ('tampering', 'Tampering'),
        ('repudiation', 'Repudiation'),
        ('info_disclosure', 'Information Disclosure'),
        ('dos', 'Denial of Service'),
        ('elevation', 'Elevation of Privilege'),
    ]

    LIKELIHOOD_CHOICES = [(i, str(i)) for i in range(1, 6)]
    IMPACT_CHOICES = [(i, str(i)) for i in range(1, 6)]

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.TextField()
    likelihood = models.IntegerField(choices=LIKELIHOOD_CHOICES, default=3)
    impact = models.IntegerField(choices=IMPACT_CHOICES, default=3)
    mitigation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-impact', '-likelihood']

    @property
    def risk_score(self):
        return self.likelihood * self.impact

    def __str__(self):
        return self.title
