from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='scanner.Scan')
def log_scan_completed(sender, instance, created, **kwargs):
    if not created and instance.status in ('completed', 'failed'):
        from audit.models import AuditEvent
        severity = 'high' if instance.status == 'failed' else 'info'
        AuditEvent.objects.create(
            event_type='scan_completed',
            description=(
                f'Scan #{instance.pk} ({instance.contract_name}) [{instance.tool}] '
                f'{instance.status}. {instance.findings.count()} findings.'
            ),
            severity=severity,
            resource=f'scan:{instance.pk}',
        )


@receiver(post_save, sender='scanner.Scan')
def log_scan_created(sender, instance, created, **kwargs):
    if created:
        from audit.models import AuditEvent
        AuditEvent.objects.create(
            event_type='scan_submitted',
            description=(
                f'New scan submitted for contract "{instance.contract_name}" '
                f'using {instance.tool}.'
            ),
            severity='info',
            resource=f'scan:{instance.pk}',
        )
