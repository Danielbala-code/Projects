import hashlib
import io
import tempfile
import unittest
from pathlib import Path

from scripts.download_model import download_verified


class DownloadTests(unittest.TestCase):
    def test_verified_download_and_existing_file_skip(self):
        data = b'a verified model fixture'
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'model.gguf'
            opener = lambda url, timeout: io.BytesIO(data)
            download_verified('https://example.test/model', path, hashlib.sha256(data).hexdigest(), len(data), opener=opener)
            self.assertEqual(path.read_bytes(), data)
            def forbidden(*args, **kwargs):
                raise AssertionError('Existing verified file should not be downloaded')
            download_verified('https://example.test/model', path, hashlib.sha256(data).hexdigest(), len(data), opener=forbidden)

    def test_invalid_and_interrupted_downloads_preserve_existing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'model.gguf'; path.write_bytes(b'previous-file')
            with self.assertRaises(ValueError):
                download_verified('https://example.test/model', path, '0'*64, 4, opener=lambda url, timeout: io.BytesIO(b'bad!'))
            self.assertEqual(path.read_bytes(), b'previous-file')
            self.assertFalse(path.with_suffix('.gguf.part').exists())
            class Broken(io.BytesIO):
                def read(self, *args):
                    raise OSError('download interrupted')
            with self.assertRaises(OSError):
                download_verified('https://example.test/model', path, '0'*64, 4, opener=lambda url, timeout: Broken(b'bad!'))
            self.assertEqual(path.read_bytes(), b'previous-file')
            self.assertFalse(path.with_suffix('.gguf.part').exists())

if __name__ == '__main__':
    unittest.main()
