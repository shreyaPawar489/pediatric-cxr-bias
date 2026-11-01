"""Convert the Guangzhou pediatric chest X-ray set (Kermany et al. 2018, CC BY 4.0, ages 1-5;
hf-vision/chest-xray-pneumonia parquet files in data/) to 224x224 grayscale uint8 arrays.

label 0 = NORMAL, 1 = PNEUMONIA. No image here is labeled cardiomegaly, so any cardiomegaly
call on a NORMAL image counts as a false positive.
"""
import glob
import io
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def to_224(b: bytes) -> np.ndarray:
    im = Image.open(io.BytesIO(b)).convert("L")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    return np.asarray(im.resize((224, 224), Image.BILINEAR), dtype=np.uint8)


imgs, rows = [], []
for f in sorted(glob.glob(os.path.join(ROOT, "data", "peds_*.parquet"))):
    split = os.path.basename(f).split("_")[1].split("-")[0]
    for batch in pq.ParquetFile(f).iter_batches(batch_size=256):
        for r in batch.to_pylist():
            imgs.append(to_224(r["image"]["bytes"]))
            rows.append({"split": split, "label": r["label"]})
np.save(os.path.join(ROOT, "data", "guangzhou_peds.npy"), np.stack(imgs))
pd.DataFrame(rows).to_csv(os.path.join(ROOT, "data", "guangzhou_peds.csv"), index=False)
print(len(rows), pd.DataFrame(rows).label.value_counts().to_dict())
