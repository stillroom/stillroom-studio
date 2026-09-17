import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('studio_bridge',Path(__file__).parents[1]/'studio/hermes_bridge.py')
bridge=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

class StudioSkillsTests(unittest.TestCase):
    def test_only_dedicated_folder_is_discovered(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            studio=root/'stillroom-studio'
            (studio/'brand-review').mkdir(parents=True)
            (studio/'brand-review'/'SKILL.md').write_text('Review the brand voice.')
            (root/'unrelated').mkdir()
            (root/'unrelated'/'SKILL.md').write_text('Not a Studio skill.')
            (studio/'external-link').symlink_to(root/'unrelated',target_is_directory=True)
            (studio/'linked-file').mkdir()
            (studio/'linked-file'/'SKILL.md').symlink_to(root/'unrelated'/'SKILL.md')
            with patch.object(bridge,'STUDIO_SKILLS',studio):
                self.assertEqual(list(bridge.studio_skills()),['brand-review'])
    def test_empty_and_missing_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(bridge,'STUDIO_SKILLS',Path(directory)/'missing'):
                self.assertEqual(bridge.studio_skills(),{})
            with patch.object(bridge,'STUDIO_SKILLS',Path(directory)):
                self.assertEqual(bridge.studio_skills(),{})
