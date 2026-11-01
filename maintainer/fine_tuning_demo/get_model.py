"""Скачать закрепленную ревизию учебной модели отдельно от кода."""

import argparse
import json
from pathlib import Path

from data_contract import MODEL_NAME


MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("models/qwen3-0.6b"))
    args = parser.parse_args()
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=MODEL_NAME, revision=MODEL_REVISION, local_dir=args.output,
                      allow_patterns=["*.json", "*.safetensors", "*.txt", "LICENSE", "*.jinja"])
    provenance = {"model_name": MODEL_NAME, "revision": MODEL_REVISION}
    (args.output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print("Модель загружена в", args.output)


if __name__ == "__main__":
    main()
