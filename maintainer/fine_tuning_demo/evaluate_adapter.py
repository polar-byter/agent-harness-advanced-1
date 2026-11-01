"""Сравнить базу и адаптер на одном отложенном наборе без изменения весов."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from data_contract import CATEGORIES, load_records, make_messages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("data/dev.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    args = parser.parse_args()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA недоступна")
    if args.output.exists():
        raise FileExistsError("Отчет уже существует. Выберите новое имя")
    tokenizer = AutoTokenizer.from_pretrained(args.base, local_files_only=True, trust_remote_code=False)
    base_model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.float32,
        local_files_only=True, trust_remote_code=False).to(args.device)
    model = PeftModel.from_pretrained(base_model, args.adapter, is_trainable=False)
    model.eval()
    records = load_records(args.data)
    if any(record["split"] not in ("dev", "exam") for record in records):
        raise ValueError("Для этой проверки нужны dev или exam")
    report = {"device": args.device, "data_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
              "results": {}, "accepted_for_use": False}
    for variant in ("baseline", "candidate"):
        results = []
        for record in records:
            prompt = tokenizer.apply_chat_template(make_messages(record), tokenize=False,
                                                   add_generation_prompt=True, enable_thinking=False)
            inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to(args.device)
            started = time.perf_counter()
            # Одна и та же база сравнивается с выключенной и включенной поправкой
            from contextlib import nullcontext
            adapter_mode = model.disable_adapter() if variant == "baseline" else nullcontext()
            with adapter_mode, torch.inference_mode():
                output = model.generate(**inputs, max_new_tokens=48, do_sample=False,
                                        pad_token_id=tokenizer.eos_token_id)
            answer = tokenizer.decode(output[0, inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
            try:
                parsed = json.loads(answer)
                valid = isinstance(parsed, dict) and set(parsed) == {"category"} and parsed["category"] in CATEGORIES
            except (ValueError, TypeError):
                valid, parsed = False, {}
            results.append({"id": record["id"], "answer": answer, "valid": valid,
                            "correct": valid and parsed.get("category") == record["expected"],
                            "seconds": round(time.perf_counter() - started, 3)})
        report["results"][variant] = {"count": len(results), "correct": sum(row["correct"] for row in results),
                                        "valid": sum(row["valid"] for row in results), "cases": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value["correct"] for key, value in report["results"].items()}))


if __name__ == "__main__":
    main()
