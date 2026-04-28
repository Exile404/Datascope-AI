"""
DataScope AI — Training Script
Fine-tunes Llama 3.1 8B with Unsloth + LoRA on local GPU.

Usage:
    python train.py
    python train.py --config ../configs/training_config.yaml
"""

import argparse
import yaml
from pathlib import Path
from datasets import Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def parse_toon(filepath: str) -> list[dict]:
    """Parse .toon format into list of training examples."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    examples = []
    blocks = content.split("<<<EOE>>>")

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        entry = {}
        current_key = None
        current_lines = []

        for line in block.split("\n"):
            if line.startswith("[") and line.endswith("]"):
                if current_key:
                    entry[current_key] = "\n".join(current_lines).strip()
                current_key = line[1:-1]  # e.g. "system", "input", "thinking", "answer"
                current_lines = []
            else:
                current_lines.append(line)

        if current_key:
            entry[current_key] = "\n".join(current_lines).strip()

        if "system" in entry and "input" in entry:
            examples.append({
                "instruction": entry.get("system", ""),
                "input": entry.get("input", ""),
                "output": entry.get("output", ""),
            })

    return examples


def format_prompt(examples: dict) -> list[str]:
    """Format training examples into Llama 3.1 chat template."""
    texts = []
    for instruction, input_text, output in zip(
        examples["instruction"], examples["input"], examples["output"]
    ):
        text = (
            "<|begin_of_text|>"
            "<|start_header_id|>system<|end_header_id|>\n\n"
            f"{instruction}<|eot_id|>"
            "<|start_header_id|>user<|end_header_id|>\n\n"
            f"{input_text}<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n\n"
            f"{output}<|eot_id|>"
        )
        texts.append(text)
    return texts


def main():
    parser = argparse.ArgumentParser(description="Train DataScope AI model")
    parser.add_argument("--model-config", type=str, default="../configs/model_config.yaml")
    parser.add_argument("--train-config", type=str, default="../configs/training_config.yaml")
    parser.add_argument("--data", type=str, default="../data/processed/datascope_train.toon")
    args = parser.parse_args()

    model_cfg = load_config(args.model_config)
    train_cfg = load_config(args.train_config)

    print("╔══════════════════════════════════════════╗")
    print("║  DataScope AI — Model Training           ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║  Model: {model_cfg['base_model']['name'].split('/')[-1]:<32}║")
    print(f"║  LoRA rank: {model_cfg['lora']['r']:<28}║")
    print(f"║  Epochs: {train_cfg['training']['num_train_epochs']:<31}║")
    print(f"║  LR: {train_cfg['training']['learning_rate']:<35}║")
    print(f"║  Data: {Path(args.data).name:<33}║")
    print("╚══════════════════════════════════════════╝\n")

    # ── Load model ──
    print("[1/5] Loading base model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_cfg["base_model"]["name"],
        max_seq_length=model_cfg["base_model"]["max_seq_length"],
        load_in_4bit=model_cfg["quantization"]["load_in_4bit"],
        dtype=None,
    )

    # ── Apply LoRA ──
    print("[2/5] Applying LoRA adapters...")
    lora_cfg = model_cfg["lora"]
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        target_modules=lora_cfg["target_modules"],
        bias=lora_cfg["bias"],
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # Print trainable params
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"  Trainable: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)\n")

    # ── Load dataset ──
    print("[3/5] Loading training data...")
    examples = parse_toon(args.data)
    dataset = Dataset.from_list(examples)

    val_split = train_cfg["dataset"]["validation_split"]
    ds = dataset.train_test_split(
        test_size=val_split,
        seed=train_cfg["dataset"]["seed"],
    )
    train_ds = ds["train"]
    eval_ds = ds["test"]
    print(f"  Train: {len(train_ds)} | Validation: {len(eval_ds)}\n")

    # ── Training args ──
    print("[4/5] Configuring trainer...")
    t = train_cfg["training"]
    mem = train_cfg["memory"]
    sched = train_cfg["scheduler"]
    log = train_cfg["logging"]
    ckpt = train_cfg["checkpointing"]
    ev = train_cfg["evaluation"]

    output_dir = "./outputs"

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=t["num_train_epochs"],
        per_device_train_batch_size=t["per_device_train_batch_size"],
        gradient_accumulation_steps=t["gradient_accumulation_steps"],
        learning_rate=t["learning_rate"],
        weight_decay=t["weight_decay"],
        max_grad_norm=t["max_grad_norm"],
        lr_scheduler_type=sched["type"],
        warmup_ratio=sched["warmup_ratio"],
        optim=train_cfg["optimizer"]["type"],
        fp16=mem["fp16"],
        bf16=mem["bf16"],
        logging_steps=log["logging_steps"],
        report_to=log["report_to"],
        save_strategy=ckpt["save_strategy"],
        save_total_limit=ckpt["save_total_limit"],
        load_best_model_at_end=ckpt["load_best_model_at_end"],
        eval_strategy=ev["eval_strategy"],
        metric_for_best_model=ev["metric_for_best_model"],
        seed=train_cfg["dataset"]["seed"],
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        formatting_func=format_prompt,
        args=training_args,
        max_seq_length=model_cfg["base_model"]["max_seq_length"],
        packing=False,  # Keep examples separate — packing breaks structured <thinking>/<answer> output
    )

    # ── Train ──
    print("[5/5] Training started!\n")
    stats = trainer.train()

    print(f"\n  Training complete!")
    print(f"  Total steps: {stats.global_step}")
    print(f"  Training loss: {stats.training_loss:.4f}")
    print(f"  Runtime: {stats.metrics['train_runtime']:.0f}s")

    # ── Save ──
    export_cfg = model_cfg["export"]
    export_dir = export_cfg["output_dir"]
    Path(export_dir).mkdir(parents=True, exist_ok=True)

    if export_cfg["merge_adapters"]:
        print(f"\n  Merging adapters and saving to {export_dir}...")

        for fmt in export_cfg["formats"]:
            if fmt == "safetensors":
                model.save_pretrained_merged(
                    export_dir,
                    tokenizer,
                    save_method="merged_16bit",
                )
                print(f"  ✓ Saved merged model (safetensors)")

            elif fmt.startswith("gguf"):
                quant_method = fmt.replace("gguf_", "")
                gguf_dir = f"{export_dir}-gguf"
                model.save_pretrained_gguf(
                    gguf_dir,
                    tokenizer,
                    quantization_method=quant_method,
                )
                print(f"  ✓ Saved GGUF ({quant_method})")
    else:
        model.save_pretrained(export_dir)
        tokenizer.save_pretrained(export_dir)
        print(f"  ✓ Saved LoRA adapter to {export_dir}")

    if export_cfg.get("hub_repo"):
        print(f"  Pushing to HuggingFace: {export_cfg['hub_repo']}...")
        model.push_to_hub(export_cfg["hub_repo"])
        tokenizer.push_to_hub(export_cfg["hub_repo"])
        print("  ✓ Pushed to Hub")

    print("\n  Done! Model ready for serving.\n")


if __name__ == "__main__":
    main()