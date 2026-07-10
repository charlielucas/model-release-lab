import unittest

from document_labeling_eval.evaluator import accuracy, missed_rows


class EvaluatorTests(unittest.TestCase):
    def test_accuracy(self):
        rows = [{"topic_match": "True"}, {"topic_match": "False"}]

        self.assertEqual(accuracy(rows, "topic_match"), 0.5)

    def test_missed_rows(self):
        rows = [
            {"topic_match": "True", "risk_match": "True"},
            {"topic_match": "False", "risk_match": "True"},
        ]

        self.assertEqual(len(missed_rows(rows)), 1)


if __name__ == "__main__":
    unittest.main()
