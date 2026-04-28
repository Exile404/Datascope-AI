"""
DataScope AI — Model Export Script
Re-export a trained model without retraining.

Usage:
    python export.py                                    # defaults from config
    python export.py --format gguf_q5_k_m               # different quantization
    python export.py --format safetensors --push-hub     # push to HuggingFace
"""

import argparse
import yaml
from pathlib import Path
from unsloth import FastLanguageModel


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Export DataScope AI model")
    parser.add_argument("--model-config", type=str, default="../configs/model_config.yaml")
    parser.add_argument("--checkpoint", type=str, default=None,
                        help="Path to training checkpoint (default: uses base model + adapter)")
    parser.add_argument("--adapter", type=str, default="./outputs",
                        help="Path to LoRA adapter from training")
    parser.add_argument("--format", type=str, nargs="+",
                        default=None, help="Export formats: safetensors, gguf_q4_k_m, gguf_q5_k_m, gguf_q8_0")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--push-hub", action="store_true", help="Push to HuggingFace Hub")
    parser.add_argument("--hub-repo", type=str, default=None)
    args = parser.parse_args()

    model_cfg = load_config(args.model_config)
    export_cfg = model_cfg["export"]

    formats = args.format or export_cfg["formats"]
    output_dir = args.output_dir or export_cfg["output_dir"]
    hub_repo = args.hub_repo or export_cfg.get("hub_repo")

    print("╔══════════════════════════════════════════╗")
    print("║  DataScope AI — Model Export             ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║  Formats: {', '.join(formats):<30}║")
    print(f"║  Output:  {output_dir:<30}║")
    print("╚══════════════════════════════════════════╝\n")

    # Load model
    print("[1/3] Loading model + adapter...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.adapter,
        max_seq_length=model_cfg["base_model"]["max_seq_length"],
        load_in_4bit=True,
        dtype=None,
    )
    FastLanguageModel.for_inference(model)

    # Export
    print("[2/3] Exporting...\n")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for fmt in formats:
        if fmt == "safetensors":
            print(f"  Exporting merged safetensors → {output_dir}")
            model.save_pretrained_merged(
                output_dir, tokenizer, save_method="merged_16bit"
            )
            print("  ✓ safetensors done\n")

        elif fmt.startswith("gguf"):
            quant = fmt.replace("gguf_", "")
            gguf_dir = f"{output_dir}-gguf"
            print(f"  Exporting GGUF ({quant}) → {gguf_dir}")
            model.save_pretrained_gguf(
                gguf_dir, tokenizer, quantization_method=quant
            )
            print(f"  ✓ GGUF ({quant}) done\n")

        else:
            print(f"  ⚠ Unknown format: {fmt}, skipping\n")

    # Push to hub
    if args.push_hub and hub_repo:
        print(f"[3/3] Pushing to HuggingFace: {hub_repo}")
        model.push_to_hub(hub_repo)
        tokenizer.push_to_hub(hub_repo)
        print("  ✓ Pushed to Hub\n")
    else:
        print("[3/3] Skipping hub push\n")

    print("Done!")


if __name__ == "__main__":
    main()