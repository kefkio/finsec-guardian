# scanner/management/commands/init_solidity_versions.py
from django.core.management.base import BaseCommand
from scanner.models import SolidityVersion

class Command(BaseCommand):
    def handle(self, *args, **options):
        versions = ['0.8.21', '0.8.20', '0.8.19', '0.7.6']
        for version in versions:
            SolidityVersion.objects.get_or_create(
                version=version,
                defaults={'is_active': True}
            )
        self.stdout.write("Solidity versions initialized")

# Run: python manage.py init_solidity_versions