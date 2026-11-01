"""Run adult-trained TorchXRayVision models on the NIH subset and the Guangzhou pediatric set.

Saves, per model: calibrated cardiomegaly probability (0.5 = the model's published operating
point) and the 1024-d pooled DenseNet features (used later for head retraining).

Models are chosen so none was trained on NIH ChestX-ray14 (the evaluation set):
  chex     = CheXpert (Stanford, adults)
  pc       = PadChest (Spain, mostly adults)
  mimic_ch = MIMIC-CXR (Boston, adults)
"""
import glob
import os

import numpy as np
import pandas as pd
import torch
import torchxrayvision as xrv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = ["densenet121-res224-chex", "densenet121-res224-pc", "densenet121-res224-mimic_ch"]
DEV = "mps" if torch.backends.mps.is_available() else "cpu"


def load_nih():
    csvs = sorted(glob.glob(os.path.join(ROOT, "data", "nih_subset", "*.csv")))
    metas, arrs = [], []
    for c in csvs:
        m = pd.read_csv(c)
        if len(m):
            metas.append(m)
            arrs.append(np.load(c.replace(".csv", ".npy")))
    return pd.concat(metas, ignore_index=True), np.concatenate(arrs)


@torch.no_grad()
def run(model, imgs, bs=64):
    idx = model.pathologies.index("Cardiomegaly")
    probs, feats = [], []
    for i in range(0, len(imgs), bs):
        x = xrv.datasets.normalize(imgs[i:i + bs].astype(np.float32), 255)[:, None]
        x = torch.from_numpy(x).to(DEV)
        f = model.features2(x)
        # Same as DenseNet.forward: sigmoid, then op_norm so 0.5 = published operating point
        out = xrv.models.op_norm(torch.sigmoid(model.classifier(f)), model.op_threshs.to(DEV))
        probs.append(out[:, idx].float().cpu().numpy())
        feats.append(f.float().cpu().numpy())
    return np.concatenate(probs), np.concatenate(feats)


def main():
    nih_meta, nih = load_nih()
    gz_meta = pd.read_csv(os.path.join(ROOT, "data", "guangzhou_peds.csv"))
    gz = np.load(os.path.join(ROOT, "data", "guangzhou_peds.npy"))
    nih_meta.to_csv(os.path.join(ROOT, "results", "nih_meta.csv"), index=False)
    print("NIH", len(nih_meta), "kids", int((nih_meta.age < 18).sum()), "| Guangzhou", len(gz_meta), flush=True)
    for w in MODELS:
        m = xrv.models.DenseNet(weights=w).to(DEV).eval()
        p_nih, f_nih = run(m, nih)
        p_gz, f_gz = run(m, gz)
        tag = w.split("-")[-1]
        np.savez_compressed(os.path.join(ROOT, "results", f"preds_{tag}.npz"),
                            p_nih=p_nih, f_nih=f_nih.astype(np.float16), p_gz=p_gz, f_gz=f_gz.astype(np.float16))
        print(tag, "done", flush=True)


if __name__ == "__main__":
    main()
