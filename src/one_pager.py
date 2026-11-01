"""One-page visual summary (PDF + PNG) for sharing. Reads numbers from results/*.csv."""
import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
rep = pd.read_csv(os.path.join(RES, "fpr_by_age.csv"))
fx = pd.read_csv(os.path.join(RES, "fixes_summary.csv"))
N_FIX = 100

INK, MUTED = "#1f2933", "#616e7c"
COL = {"CheXpert model": "#2563eb", "PadChest model": "#d97706", "MIMIC-CXR model": "#dc2626"}

fig = plt.figure(figsize=(11, 8.5))
fig.text(0.05, 0.94, "Adult-trained chest X-ray AI over-flags young children. Can a cheap fix help?",
         fontsize=16, weight="bold", color=INK)
fig.text(0.05, 0.905, "Follow-up to Hua et al., \"Lack of children in public medical imaging data\" (2025)  ·  "
         "Shreya Pawar, UC Berkeley  ·  public data and models",
         fontsize=10, color=MUTED)

# Panel 1: FPR by age
ax1 = fig.add_axes([0.06, 0.42, 0.40, 0.42])
bins = ["NIH 0-5", "NIH 6-10", "NIH 11-14", "NIH 15-17", "NIH 18-40", "NIH 41-60", "NIH 61+"]
labels = ["0-5", "6-10", "11-14", "15-17", "18-40", "41-60", "61+"]
ax1.axvspan(-0.4, 3.5, color="#fde8e8", zorder=0)
ax1.text(1.55, 0.98, "children", ha="center", fontsize=9, color="#b91c1c", transform=ax1.get_xaxis_transform())
for m, c in COL.items():
    d = rep[rep.model == m].set_index("group").loc[bins]
    ax1.errorbar(range(7), d.fpr * 100, yerr=[(d.fpr - d.lo) * 100, (d.hi - d.fpr) * 100], color=c, marker="o",
                 capsize=2, lw=2, label=m.replace(" model", ""))
ax1.set_xticks(range(7))
ax1.set_xticklabels(labels)
ax1.set_xlabel("Patient age (years), NIH ChestX-ray14", color=INK)
ax1.set_ylabel("False alarms on healthy X-rays (%)", color=INK)
ax1.set_title("1. False alarms for 'enlarged heart' peak in the youngest kids", loc="left", fontsize=11, weight="bold", color=INK)
ax1.legend(frameon=False, fontsize=9, title="Model trained on", title_fontsize=9)
ax1.spines[["top", "right"]].set_visible(False)
ax1.set_ylim(0, 100)

# Panel 2: the fix, MIMIC-CXR model (largest gap)
ax2 = fig.add_axes([0.56, 0.42, 0.40, 0.42])
m = "MIMIC-CXR model"
a = fx[(fx.model == m) & (fx.method == "A. Published threshold") & (fx.n == 0)].iloc[0]
b = fx[(fx.model == m) & (fx.method == "B. Pediatric threshold") & (fx.n == N_FIX)].iloc[0]
groups = ["Young kids (0-10)\nNIH, held out", "Toddlers (1-5)\nother hospital", "Real cases caught\n(sensitivity, 0-10)"]
before = [a.fpr * 100, a.fpr_gz * 100, a.sens * 100]
after = [b.fpr * 100, b.fpr_gz * 100, b.sens * 100]
err = [b.fpr_sd * 100, b.fpr_gz_sd * 100, b.sens_sd * 100]
x = range(3)
ax2.bar([i - 0.19 for i in x], before, 0.36, color="#cbd2d9", label="Before (published threshold)")
ax2.bar([i + 0.19 for i in x], after, 0.36, yerr=err, capsize=3, color=COL[m], label=f"After: threshold re-picked with {N_FIX} kids' X-rays")
for i in x:
    ax2.text(i - 0.19, before[i] + 1.5, f"{before[i]:.0f}%", ha="center", fontsize=9, color=MUTED)
    ax2.text(i + 0.19, after[i] + err[i] + 1.5, f"{after[i]:.0f}%", ha="center", fontsize=9, weight="bold", color=INK)
ax2.axhline(a.target * 100, xmax=0.66, ls="--", color=INK, lw=1)
ax2.text(-0.4, a.target * 100 + 1.5, f"adult false-alarm rate {a.target * 100:.0f}%", fontsize=8, color=INK, ha="left")
ax2.set_xticks(list(x))
ax2.set_xticklabels(groups, fontsize=9)
ax2.set_ylim(0, 128)
ax2.set_ylabel("%", color=INK)
ax2.set_title(f"2. Fix: re-pick the threshold with {N_FIX} kids' X-rays", loc="left", fontsize=11, weight="bold", color=INK)
ax2.legend(frameon=False, fontsize=8.5, loc="upper left")
ax2.set_xlabel("Shown for the MIMIC-CXR model (largest gap)", color=MUTED, fontsize=9)
ax2.spines[["top", "right"]].set_visible(False)


def get(model, method, n, col):
    return fx[(fx.model == model) & (fx.method == method) & (fx.n == n)].iloc[0][col] * 100


young = {mm: (rep[(rep.model == mm) & (rep.group == "NIH 0-5")].fpr.iloc[0] * 100,
              rep[(rep.model == mm) & (rep.group == "NIH 18-40")].fpr.iloc[0] * 100) for mm in COL}
take = [
    ("What I found",
     "Ages 0-5 get the most false 'enlarged heart' calls on healthy X-rays: "
     + "; ".join(f"{k.replace(' model', '')} {v[0]:.0f}% vs {v[1]:.0f}% for ages 18-40" for k, v in young.items())
     + ". This reproduces the paper's age-bias finding using only public data."),
    ("What helps",
     f"Re-picking the decision threshold with ~{N_FIX} healthy young-child X-rays (no retraining) brings the MIMIC model's "
     f"young-child false alarms from {a.fpr * 100:.0f}% to {b.fpr * 100:.0f}% (adults: {a.target * 100:.0f}%), and the same threshold "
     f"carries over to toddlers from a hospital it never saw ({a.fpr_gz * 100:.0f}% to {b.fpr_gz * 100:.0f}%). Gains are smaller for "
     f"CheXpert ({get('CheXpert model', 'A. Published threshold', 0, 'fpr'):.0f}% to {get('CheXpert model', 'B. Pediatric threshold', N_FIX, 'fpr'):.0f}%) "
     f"and PadChest ({get('PadChest model', 'A. Published threshold', 0, 'fpr'):.0f}% to {get('PadChest model', 'B. Pediatric threshold', N_FIX, 'fpr'):.0f}%)."),
    ("The catch",
     f"Fewer false alarms cost sensitivity ({a.sens * 100:.0f}% to {b.sens * 100:.0f}% for MIMIC; only 53 young-child cardiomegaly cases, so this "
     "is noisy). Retraining the model's last layer on NIH children did not carry over to the other hospital. Fixing the gap without missing "
     "real cases likely needs real pediatric training data, which supports the paper's call to release it."),
    ("Next",
     "Repeat on VinDr-PCXR (the paper's pediatric set) with age-specific thresholds and full fine-tuning; measure how many pediatric images "
     "it takes to recover sensitivity."),
]
y = 0.33
for head, body in take:
    fig.text(0.06, y, head, fontsize=10.5, weight="bold", color=INK, va="top")
    fig.text(0.17, y, "\n".join(textwrap.wrap(body, 125)), fontsize=9.5, color=INK, va="top")
    y -= 0.075 if len(body) < 260 else 0.085
fig.text(0.06, 0.02, "Data: NIH ChestX-ray14 (16,291 images incl. all 5,402 pediatric), Guangzhou pediatric CXR (Kermany 2018, ages 1-5). "
         "\nModels: TorchXRayVision DenseNet-121 (none trained on NIH). 10 patient-disjoint splits. Code: see repo link.",
         fontsize=8, color=MUTED)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(RES, f"one_pager.{ext}"), dpi=200)
print("saved")
