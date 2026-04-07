#!/bin/bash
# NISA Fine-tuning Launcher
# Usage: bash finetune/train.sh

echo "================================================"
echo "  NISA Fine-tuning Pipeline"
echo "  Model: Phi-4 14B | Method: LoRA"
echo "================================================"

# Step 1: Build dataset
echo "[1/3] Building dataset from knowledge library..."
python3.11 /Users/joshuadavis/NISA/finetune/build_dataset.py

# Step 2: Run LoRA fine-tuning
echo "[2/3] Starting LoRA fine-tuning..."
python3.11 -m mlx_lm lora \
  --config /Users/joshuadavis/NISA/finetune/configs/phi4_security_lora.yaml

# Step 3: Fuse adapter into model
echo "[3/3] Fusing adapter weights..."
python3.11 -m mlx_lm fuse \
  --model microsoft/phi-4 \
  --adapter-path /Users/joshuadavis/NISA/finetune/adapters/phi4_nisa_v1 \
  --save-path /Users/joshuadavis/NISA/models/phi4_nisa_finetuned

echo "Fine-tuning complete!"
echo "Model saved to: ~/NISA/models/phi4_nisa_finetuned"
