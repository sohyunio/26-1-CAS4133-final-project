"""
Run the full experiment and save metrics.

Usage:
    python run_experiment.py
"""
import json
import os
import time

import numpy as np
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

from model import load_model
from defense import baseline0, baseline1, hybrid_defense, is_attacked

# Configuration
MODEL_SIZES   = ["0.5B", "3B"]
PROJECT_DATA_ROOT = os.environ.get("PROJECT_DATA_ROOT", "/opt/vessl/shared/project-data")
DATA_DIR = os.environ.get("PROJECT_DATA_DIR", os.path.join(PROJECT_DATA_ROOT, "data"))
DATA_FOLDERS  = {
    "malicious": os.path.join(DATA_DIR, "malicious"),
    "subtle":    os.path.join(DATA_DIR, "subtle"),
    "benign":    os.path.join(DATA_DIR, "benign"),
}
MAX_FILES = {"malicious": 15, "subtle": 7, "benign": 10}
RESULTS_DIR = os.environ.get("PROJECT_RESULTS_DIR", os.path.join(PROJECT_DATA_ROOT, "results"))
os.makedirs(RESULTS_DIR, exist_ok=True)


# Experiment

def read_page(filepath):
    with open(filepath, encoding="utf-8") as f:
        html = f.read()
    text = BeautifulSoup(html, "html.parser").get_text(separator="\n")
    return text, html


def run_experiment(bundle, folder, label, max_files=None, judge_bundle=None):
    results = []
    files = sorted(f for f in os.listdir(folder) if f.endswith(".html"))
    if max_files:
        files = files[:max_files]

    for fname in files:
        text, html = read_page(os.path.join(folder, fname))

        t0 = time.time(); r0 = baseline0(bundle, text);      l0 = time.time() - t0
        t1 = time.time(); r1 = baseline1(bundle, text);      l1 = time.time() - t1
        t2 = time.time(); r2 = hybrid_defense(bundle, html); l2 = time.time() - t2

        entry = {
            "file":  fname,
            "label": label,
            "baseline0": {"response": r0, "attacked": is_attacked(r0, judge_bundle), "latency": l0},
            "baseline1": {"response": r1, "attacked": is_attacked(r1, judge_bundle), "latency": l1},
            "ours":      {"response": r2, "attacked": is_attacked(r2, judge_bundle), "latency": l2},
        }
        results.append(entry)
        print(f"  {fname:<30} B0:{entry['baseline0']['attacked']} "
              f"B1:{entry['baseline1']['attacked']} Ours:{entry['ours']['attacked']}")
    return results


# Metric calculation

def calc_metrics(results, attack_labels=("malicious", "subtle")):
    attack = [r for r in results if r["label"] in attack_labels]
    benign = [r for r in results if r["label"] == "benign"]

    def asr(data, key):
        return sum(r[key]["attacked"] for r in data) / len(data) * 100 if data else 0

    def avg_lat(data, key):
        return float(np.mean([r[key]["latency"] for r in data])) if data else 0

    def fidelity(data, key):
        return sum(not r[key]["attacked"] for r in data) / len(data) * 100 if data else 0

    return {
        "baseline0": {
            "asr": asr(attack, "baseline0"),
            "latency": avg_lat(attack, "baseline0"),
            "fidelity": fidelity(benign, "baseline0"),
        },
        "baseline1": {
            "asr": asr(attack, "baseline1"),
            "latency": avg_lat(attack, "baseline1"),
            "fidelity": fidelity(benign, "baseline1"),
        },
        "ours": {
            "asr": asr(attack, "ours"),
            "latency": avg_lat(attack, "ours"),
            "fidelity": fidelity(benign, "ours"),
        },
    }


# Visualization

def plot_results(all_metrics: dict, save_path="results/results.png"):
    """
    all_metrics: {model_size: {method: {asr, latency, fidelity}}}
    """
    model_sizes = list(all_metrics.keys())
    methods     = ["baseline0", "baseline1", "ours"]
    labels      = ["Baseline 0\n(No Guard)", "Baseline 1\n(Prompt Only)", "Ours\n(Hybrid)"]
    colors      = ["#FF6B6B", "#FFB347", "#4ECDC4"]

    fig, axes = plt.subplots(len(model_sizes), 3,
                             figsize=(15, 5 * len(model_sizes)))
    if len(model_sizes) == 1:
        axes = [axes]

    for row, size in enumerate(model_sizes):
        metrics = all_metrics[size]
        asr_vals = [metrics[m]["asr"]      for m in methods]
        lat_vals = [metrics[m]["latency"]  for m in methods]
        fid_vals = [metrics[m]["fidelity"] for m in methods]

        for col, (vals, title, ylabel, ylim) in enumerate([
            (asr_vals, f"[{size}] ASR (↓)",      "ASR (%)",      (0, 110)),
            (lat_vals, f"[{size}] Latency (↓)",  "Seconds",      None),
            (fid_vals, f"[{size}] Fidelity (↑)", "Fidelity (%)", (0, 110)),
        ]):
            ax = axes[row][col]
            bars = ax.bar(labels, vals, color=colors, edgecolor="white")
            ax.set_title(title, fontsize=11, fontweight="bold")
            ax.set_ylabel(ylabel)
            if ylim:
                ax.set_ylim(*ylim)
            for bar, v in zip(bars, vals):
                unit = "s" if col == 1 else "%"
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + (0.02 if col == 1 else 1),
                        f"{v:.1f}{unit}",
                        ha="center", fontsize=9, fontweight="bold")

    fig.suptitle("Hybrid Guardrail for LLM Web Agents Against IPI\n"
                 "Model Size Comparison: Qwen-0.5B vs Qwen-3B",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"[OK] Saved {save_path}")


# Main entry point

if __name__ == "__main__":
    judge_bundle = load_model("3B")
    all_metrics = {}

    for size in MODEL_SIZES:
        print(f"\n{'='*55}")
        print(f"  Model: Qwen-{size}")
        print(f"{'='*55}")
        bundle = load_model(size)
        all_results = []

        for label, folder in DATA_FOLDERS.items():
            print(f"\n-- {label} --")
            res = run_experiment(
                bundle, folder, label,
                max_files=MAX_FILES[label],
                judge_bundle=judge_bundle
            )
            all_results.extend(res)

        # Save per-model raw results.
        out_path = os.path.join(RESULTS_DIR, f"results_{size}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Saved {out_path}")

        all_metrics[size] = calc_metrics(all_results)

        # Print a compact console summary.
        print(f"\n  {'Method':<20} {'ASR':>8} {'Latency':>10} {'Fidelity':>10}")
        print(f"  {'-'*50}")
        for m, lbl in zip(["baseline0","baseline1","ours"],
                          ["Baseline0","Baseline1","Ours"]):
            d = all_metrics[size][m]
            print(f"  {lbl:<20} {d['asr']:>7.1f}% {d['latency']:>9.2f}s {d['fidelity']:>9.1f}%")

    # Save aggregate metrics and plot the final comparison.
    with open(os.path.join(RESULTS_DIR, "all_metrics.json"), "w") as f:
        json.dump(all_metrics, f, indent=2)

    plot_results(all_metrics)
    print("\nExperiment complete.")
