"""Проверить подготовку данных и маску ответа без скачивания модели."""

from collections import Counter
import unittest

from data_contract import make_training_tokens
from prepare_data import build_records, validate_records


class TokenizerStub:
    eos_token = "!"

    def apply_chat_template(self, messages, **kwargs):
        return "prefix"

    def encode(self, text, **kwargs):
        return list(range(len(text)))


class TrainingDataTests(unittest.TestCase):
    def test_splits_and_context_pairs(self):
        records = build_records()
        validate_records(records)
        self.assertEqual(Counter(row["split"] for row in records), {"train": 36, "dev": 9, "exam": 9})
        pairs = [row for row in records if row["utterance"] == "Еще на неделю"]
        self.assertEqual({row["expected"] for row in pairs}, {"renew", "clarify"})

    def test_repeated_template_cannot_cross_split(self):
        records = build_records()
        records[0]["split"] = "exam"
        with self.assertRaises(ValueError):
            validate_records(records)

    def test_loss_mask_preserves_answer(self):
        tokens, labels = make_training_tokens(TokenizerStub(), build_records()[0])
        self.assertEqual(len(tokens), len(labels))
        self.assertEqual(labels[:6], [-100] * 6)
        self.assertEqual(labels[6:], tokens[6:])

    def test_long_record_is_rejected(self):
        with self.assertRaises(ValueError):
            make_training_tokens(TokenizerStub(), build_records()[0], max_tokens=3)


if __name__ == "__main__":
    unittest.main()
