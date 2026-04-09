from django.db import models


class Scan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    TOOL_CHOICES = [
        ('slither', 'Slither'),
        ('mythril', 'Mythril'),
        ('echidna', 'Echidna'),
    ]

    contract_name = models.CharField(max_length=255, default='Unnamed')
    source_code = models.TextField()
    tool = models.CharField(max_length=20, choices=TOOL_CHOICES, default='slither')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Scan #{self.pk} — {self.contract_name} [{self.tool}] ({self.status})'


class Finding(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('info', 'Info'),
    ]

    scan = models.ForeignKey(Scan, on_delete=models.CASCADE, related_name='findings')
    swc_id = models.CharField(max_length=50, blank=True, default='')
    title = models.CharField(max_length=512)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    line_number = models.IntegerField(null=True, blank=True)
    recommendation = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['severity', 'line_number']

    def __str__(self):
        return f'[{self.severity.upper()}] {self.title}'
