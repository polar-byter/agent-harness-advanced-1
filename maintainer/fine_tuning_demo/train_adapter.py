"""Учебное обучение LoRA на локальной NVIDIA без облачных запросов."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random

from data_contract import MODEL_NAME, load_records, make_training_tokens


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("data/train.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.epochs < 1 or not args.base.is_dir():
        raise ValueError("Нужны локальная папка модели и положительное число эпох")

    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if not torch.cuda.is_available():
        raise RuntimeError("Этот учебный тренер требует NVIDIA CUDA. Подготовка данных работает на CPU")
    args.output.mkdir(parents=True, exist_ok=False)
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.base, local_files_only=True, trust_remote_code=False)
    records = load_records(args.data)
    if any(record["split"] != "train" for record in records):
        raise ValueError("Обучение принимает только часть train")
    encoded_records = [make_training_tokens(tokenizer, record) for record in records]
    # FP32 упрощает первый пример ценой большего расхода памяти
    base_model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.float32,
        local_files_only=True, trust_remote_code=False).to("cuda")
    adapter_config = LoraConfig(task_type="CAUSAL_LM", r=8, lora_alpha=16, lora_dropout=0.05,
                                target_modules=["q_proj", "v_proj"])
    model = get_peft_model(base_model, adapter_config)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model.config.use_cache = False
    trainable_parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(trainable_parameters, lr=0.00002)
    provenance = json.loads((args.base / "provenance.json").read_text(encoding="utf-8"))
    if provenance["model_name"] != MODEL_NAME:
        raise ValueError("Этот пример рассчитан на модель из get_model.py")
    report = {"model_name": MODEL_NAME, "model_revision": provenance["revision"], "seed": args.seed,
              "data_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(), "epochs": args.epochs,
              "rank": 8, "alpha": 16, "learning_rate": 0.00002, "status": "training",
              "versions": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft")},
              "trainable_parameters": sum(parameter.numel() for parameter in trainable_parameters),
              "losses": [], "accepted_for_use": False}
    report_path = args.output / "training-report.json"
    model.train()
    for epoch in range(args.epochs):
        random.shuffle(encoded_records)
        for input_tokens, labels in encoded_records:
            input_tensor = torch.tensor([input_tokens], device="cuda")
            label_tensor = torch.tensor([labels], device="cuda")
            optimizer.zero_grad(set_to_none=True)
            output = model(input_ids=input_tensor, attention_mask=torch.ones_like(input_tensor), labels=label_tensor)
            loss = output.loss
            if not torch.isfinite(loss):
                raise ValueError("Потеря не является конечным числом")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(trainable_parameters, 1.0)
            optimizer.step()
            report["losses"].append(float(loss.detach()))
        report["completed_epochs"] = epoch + 1
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    model.save_pretrained(args.output / "adapter")
    tokenizer.save_pretrained(args.output / "adapter")
    report["status"] = "trained_not_evaluated"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Адаптер сохранен. Улучшение еще нужно измерить")


if __name__ == "__main__":
    main()
