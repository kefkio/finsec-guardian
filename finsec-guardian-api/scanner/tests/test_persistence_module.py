from django.test import SimpleTestCase

from scanner.infrastructure.persistence.models import ScanJob as PersistenceScanJob
from scanner.models import ScanJob as AppScanJob


class PersistenceImportTests(SimpleTestCase):
    def test_models_are_reexported_from_persistence_module(self):
        self.assertIs(AppScanJob, PersistenceScanJob)
