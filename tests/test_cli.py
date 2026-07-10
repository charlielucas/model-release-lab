import tempfile
import unittest
from pathlib import Path

from document_labeling_eval.cli import DOCUMENTS_PATH, evaluate, label


class CliTests(unittest.TestCase):
    def test_workflow_writes_outputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            labeled_path = tmp_path / "labeled.csv"
            report_path = tmp_path / "report.md"

            label(input_path=DOCUMENTS_PATH, output_path=labeled_path)
            output = evaluate(labeled_path=labeled_path, output_path=report_path)

            self.assertTrue(labeled_path.exists())
            self.assertTrue(report_path.exists())
            self.assertIn("Topic accuracy", output)


if __name__ == "__main__":
    unittest.main()
