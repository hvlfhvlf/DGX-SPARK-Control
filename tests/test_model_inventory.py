import tempfile
import unittest
from pathlib import Path
from spark_control.config import Config
from spark_control.models import Models


class InventoryTests(unittest.TestCase):
    def test_explicit_roots_candidates_and_registration_never_change_weights(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);weights=root/'weights';weights.mkdir()
            file=weights/'example.gguf';file.write_bytes(b'fixture-only')
            (weights/'model-00001-of-00002.safetensors').write_bytes(b'fixture-shard')
            (weights/'model.safetensors.index.json').write_text('{}')
            config=Config(root/'settings');models=Models(config)
            models.set_roots([str(weights)])
            matches=models.discover()['matches'];self.assertEqual(len(matches),2)
            chosen=next(m for m in matches if m['format']=='GGUF')
            result=models.register(chosen['id'],'Example')
            self.assertTrue(result['inventory'][0]['exists'])
            self.assertEqual(file.read_bytes(),b'fixture-only')
            self.assertEqual(len(models.register(chosen['id'],'Example')['inventory']),1)
            file.unlink()
            self.assertFalse(models.roots()['inventory'][0]['exists'])
            with self.assertRaises(ValueError):models.register(chosen['id'],'Example')
            for path in ('/','/proc','/sys','/dev','/etc'):
                with self.assertRaises(ValueError):models.set_roots([path])
