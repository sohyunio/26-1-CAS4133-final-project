# Lightweight Hybrid Guardrail for LLM Web Agents Against Indirect Prompt Injection

CAS4133 Final Project

## Overview

LLM web agents that summarize external webpages are vulnerable to **Indirect Prompt Injection (IPI)** — malicious instructions hidden inside HTML content that redirect the agent's behavior. This project proposes a two-stage hybrid defense:

- **Stage 1 (Static Filter):** HTML-aware preprocessing using BeautifulSoup — removes comments, hidden elements, and regex-matched injection patterns before the text reaches the LLM.
- **Stage 2 (Dynamic Isolation):** Wraps filtered content in `<untrusted_source>` XML tags and instructs the LLM to treat the content as data, never as commands.

## Project Structure

```
project/
├── model.py            # Model loading & LLM inference
├── defense.py          # Baseline agents + hybrid defense + evaluation
├── generate_data.py    # Dataset generation (malicious / subtle / benign)
├── run_experiment.py   # Main experiment: multi-model comparison + plots
├── demo.py             # Gradio interactive demo
├── data/
│   ├── malicious/      # Explicit injection attacks (EN + KO)
│   ├── subtle/         # Filter-evasion attacks
│   └── benign/         # Normal pages (fidelity test)
├── results/            # JSON results + plots (generated at runtime)
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# 1. Generate the dataset
python generate_data.py

# 2. Run the experiment (Qwen-0.5B and Qwen-3B)
python run_experiment.py

# 3. Launch the Gradio demo
python demo.py
```

## Demo Video

https://youtu.be/HNTxHCYaSfk

## Results Summary

| Model     | Method     | ASR (↓) | Latency | Fidelity (↑) |
|-----------|-----------|---------|---------|-------------|
| Qwen-0.5B | Baseline 0 | 40.9%  | 0.97s   | 100%        |
| Qwen-0.5B | Baseline 1 | 40.9%  | 0.96s   | 100%        |
| Qwen-0.5B | **Ours**   | **0.0%** | **0.50s** | 100%   |
| Qwen-3B   | Baseline 0 | 40.9%  | 1.84s   | 100%        |
| Qwen-3B   | Baseline 1 | 27.3%  | 1.14s   | 100%        |
| Qwen-3B   | **Ours**   | **4.5%** | **0.98s** | 100%   |


**Key finding:** 0.5B Ours achieves 0.0% ASR while reducing latency by 48% 
(0.97s → 0.50s). Stage 1 static filter removes injection content before 
LLM inference, shortening input tokens and improving speed alongside security.
Qwen-3B Baseline 1 (prompt-only) shows limited effectiveness (27.3%), 
demonstrating that system prompt hardening alone is insufficient.
Evaluation uses Qwen-3B as LLM-as-judge for reliable ASR measurement.

## Dataset

- **Malicious (25):** Explicit injection attacks — HTML comments, hidden CSS, role-hijacking (EN + KO bilingual)
- **Subtle (7):** Filter-evasion attacks — natural language disguise, authority spoofing, split payloads
- **Benign (10):** Normal webpages for false-positive (fidelity) evaluation

## Evaluation

- **ASR (Attack Success Rate):** % of malicious pages that compromise the agent — measured via LLM-as-judge
- **Latency:** Average end-to-end response time
- **Task Fidelity:** % of benign pages correctly summarized (false-positive rate)
