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

| Model     | Method          | ASR (↓) | Latency | Fidelity (↑) |
|-----------|----------------|---------|---------|--------------|
| Qwen-0.5B | Baseline 0     | 46.7%   | 1.83s   | 100%         |
| Qwen-0.5B | Baseline 1     | 20.0%   | 2.34s   | 100%         |
| Qwen-0.5B | **Ours**       | **0.0%**| 1.03s   | 100%         |
| Qwen-3B   | Baseline 0     | 66.7%   | 2.58s   | 100%         |
| Qwen-3B   | Baseline 1     | —       | —       | —            |
| Qwen-3B   | **Ours**       | **0.0%**| 1.33s   | 100%         |

**Key finding:** Larger models (3B) are *more* vulnerable at baseline (66.7% vs 46.7%) because stronger instruction-following ability makes them more susceptible to injected commands. The hybrid defense reduces ASR to 0% regardless of model size.

## Dataset

- **Malicious (25):** Explicit injection attacks — HTML comments, hidden CSS, role-hijacking (EN + KO bilingual)
- **Subtle (7):** Filter-evasion attacks — natural language disguise, authority spoofing, split payloads
- **Benign (10):** Normal webpages for false-positive (fidelity) evaluation

## Evaluation

- **ASR (Attack Success Rate):** % of malicious pages that compromise the agent — measured via LLM-as-judge
- **Latency:** Average end-to-end response time
- **Task Fidelity:** % of benign pages correctly summarized (false-positive rate)
