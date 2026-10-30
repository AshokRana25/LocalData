import contextlib
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import download_model as model


class ModelDownloadTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.destination = Path(directory.name) / "hand_landmarker.task"
        self.payload = b"test-model-data"
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(model, "MODEL_SHA256", hashlib.sha256(self.payload).hexdigest()))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    @patch.object(model.urllib.request, "urlopen")
    def test_valid_existing_model_needs_no_network(self, request):
        self.destination.write_bytes(self.payload)
        model.download_model(self.destination)
        request.assert_not_called()

    @patch.object(model.urllib.request, "urlopen")
    def test_different_existing_model_is_preserved(self, request):
        self.destination.write_bytes(b"custom-model")
        with self.assertRaisesRegex(ValueError, "different checksum"):
            model.download_model(self.destination)
        self.assertEqual(self.destination.read_bytes(), b"custom-model")
        request.assert_not_called()

    @patch.object(model.urllib.request, "urlopen")
    def test_valid_download_is_installed(self, request):
        request.return_value = io.BytesIO(self.payload)
        model.download_model(self.destination)
        self.assertEqual(self.destination.read_bytes(), self.payload)
        self.assertEqual(list(self.destination.parent.glob("*.download")), [])

    @patch.object(model.urllib.request, "urlopen")
    def test_corrupt_download_is_not_installed(self, request):
        request.return_value = io.BytesIO(b"corrupt")
        with self.assertRaisesRegex(ValueError, "checksum does not match"):
            model.download_model(self.destination)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.destination.parent.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
