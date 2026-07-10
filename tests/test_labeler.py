import unittest

from document_labeling_eval.labeler import label_risk, label_topic


class LabelerTests(unittest.TestCase):
    def test_labels_security_topic(self):
        topic = label_topic("Security review found exposed auth token")

        self.assertEqual(topic, "Security")

    def test_labels_risk(self):
        self.assertEqual(label_risk("critical auth vulnerability"), "High")
        self.assertEqual(label_risk("wrong account owner"), "Medium")
        self.assertEqual(label_risk("saved filters request"), "Low")


if __name__ == "__main__":
    unittest.main()
