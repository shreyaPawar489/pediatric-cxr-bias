"""Stream NIH ChestX-ray14 shards (timm/nih-chest-xray-14 on Hugging Face) and keep a small subset.

Kept: every pediatric image (age < 18), every adult Cardiomegaly image, and a seeded ~8% sample of
other adult images. Each image is center-cropped, resized to 224x224 grayscale uint8, and saved
per shard. The raw shard is deleted afterwards.

Usage: python -I src/prepare_nih.py <shard_index_start> <shard_index_end>
"""
import hashlib
import io
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "nih_subset")
REPO = "timm/nih-chest-xray-14"
LABELS = ["Atelectasis", "Cardiomegaly", "Consolidation", "Edema", "Effusion", "Emphysema",
          "Fibrosis", "Hernia", "Infiltration", "Mass", "Nodule", "Pleural_Thickening",
          "Pneumonia", "Pneumothorax"]
ADULT_SAMPLE = 0.08


def keep_adult(image_id: str) -> bool:
    h = int(hashlib.md5(image_id.encode()).hexdigest()[:8], 16)
    return (h % 10000) / 10000 < ADULT_SAMPLE


def to_224(img_bytes: bytes) -> np.ndarray:
    im = Image.open(io.BytesIO(img_bytes)).convert("L")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    return np.asarray(im.resize((224, 224), Image.BILINEAR), dtype=np.uint8)


def main(a: int, b: int) -> None:
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    files = sorted(f.path for f in HfApi().list_repo_tree(REPO, repo_type="dataset", path_in_repo="data"))
    for path in files[a:b]:
        name = os.path.basename(path).replace(".parquet", "")
        if os.path.exists(os.path.join(OUT, name + ".csv")):
            continue
        local = hf_hub_download(REPO, path, repo_type="dataset", local_dir=RAW)
        pf = pq.ParquetFile(local)
        imgs, rows = [], []
        for batch in pf.iter_batches(batch_size=256):
            for r in batch.to_pylist():
                age = r["patient_age"]
                labs = [LABELS[i] for i in (r["labels"] or [])]
                cardio = "Cardiomegaly" in labs
                if age < 18 or cardio or keep_adult(r["image_id"]):
                    imgs.append(to_224(r["image"]["bytes"]))
                    rows.append({"image_id": r["image_id"], "patient_id": r["patient_id"], "age": age,
                                 "sex": r["patient_sex"], "view": r["view_position"],
                                 "cardiomegaly": int(cardio), "no_finding": int(len(labs) == 0),
                                 "labels": "|".join(labs), "shard": name})
        np.save(os.path.join(OUT, name + ".npy"), np.stack(imgs) if imgs else np.zeros((0, 224, 224), np.uint8))
        pd.DataFrame(rows).to_csv(os.path.join(OUT, name + ".csv"), index=False)
        os.remove(local)
        print(name, len(rows), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
