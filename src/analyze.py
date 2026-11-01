"""Experiments on adult-trained cardiomegaly models applied to children.

1. Replication: false-positive rate (FPR) at each model's published operating point, by age.
2. Fixes, with patient-disjoint pediatric calibration and test sets, repeated over random splits:
   A. Baseline: published operating point (0.5).
   B. Pediatric threshold: re-pick the threshold so FPR on n pediatric calibration images matches
      the adult FPR. Needs only n pediatric images, no retraining.
   C. Retrained head: logistic regression on frozen DenseNet features, trained on adult images plus
      the same n pediatric images; threshold set on adults only (no pediatric threshold).
3. Age documentation: can a linear probe on the same features flag pediatric images, so datasets
   that don't report age can still be audited?
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
TAGS = {"chex": "CheXpert model", "pc": "PadChest model", "mimic_ch": "MIMIC-CXR model"}
BINS = [(0, 5), (6, 10), (11, 14), (15, 17), (18, 40), (41, 60), (61, 120)]
NS = [0, 25, 50, 100, 250, 10**6]
REPEATS = 10
rng0 = np.random.default_rng(0)


def fpr(p, t=0.5):
    return float((p >= t).mean()) if len(p) else np.nan


def cluster_boot_ci(df, col, t=0.5, B=500, rng=rng0):
    pats = df.patient_id.unique()
    g = {k: v[col].values for k, v in df.groupby("patient_id")}
    vals = []
    for _ in range(B):
        s = rng.choice(pats, len(pats))
        x = np.concatenate([g[k] for k in s])
        vals.append((x >= t).mean())
    return np.percentile(vals, [2.5, 97.5])


def main():
    meta = pd.read_csv(os.path.join(RES, "nih_meta.csv"))
    gz = pd.read_csv(os.path.join(ROOT, "data", "guangzhou_peds.csv"))
    meta["child"] = meta.age < 18
    preds = {t: np.load(os.path.join(RES, f"preds_{t}.npz")) for t in TAGS}
    lines = ["# Results\n",
             f"NIH ChestX-ray14 subset: {len(meta)} images, {int(meta.child.sum())} pediatric "
             f"({meta[meta.child].patient_id.nunique()} patients, {int(meta[meta.child].cardiomegaly.sum())} cardiomegaly). "
             f"Guangzhou pediatric set (ages 1-5): {int((gz.label == 0).sum())} normal, {int((gz.label == 1).sum())} pneumonia.\n"]

    # ---------- 1. Replication: FPR by age ----------
    rows = []
    for t in TAGS:
        meta[f"p_{t}"] = preds[t]["p_nih"]
        gz[f"p_{t}"] = preds[t]["p_gz"]
        clean = meta[(meta.no_finding == 1)]
        for a, b in BINS:
            d = clean[(clean.age >= a) & (clean.age <= b)]
            lo, hi = cluster_boot_ci(d, f"p_{t}")
            rows.append({"model": TAGS[t], "group": f"NIH {a}-{b}" if b < 120 else "NIH 61+", "n": len(d),
                         "fpr": fpr(d[f"p_{t}"]), "lo": lo, "hi": hi})
        g = gz[gz.label == 0][f"p_{t}"].values
        bs = [fpr(rng0.choice(g, len(g))) for _ in range(500)]
        rows.insert(len(rows) - len(BINS), {"model": TAGS[t], "group": "Guangzhou 1-5", "n": len(g), "fpr": fpr(g),
                                            "lo": np.percentile(bs, 2.5), "hi": np.percentile(bs, 97.5)})
    rep = pd.DataFrame(rows)
    rep.to_csv(os.path.join(RES, "fpr_by_age.csv"), index=False)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharey=True)
    for ax, t in zip(axes, TAGS):
        d = rep[rep.model == TAGS[t]]
        colors = ["#c0392b" if ("Guangzhou" in g or int(g.split()[1].split("-")[0].rstrip("+")) < 18) else "#7f8c8d"
                  for g in d.group]
        ax.bar(range(len(d)), d.fpr, yerr=[d.fpr - d.lo, d.hi - d.fpr], color=colors, capsize=3)
        ax.set_xticks(range(len(d)))
        ax.set_xticklabels([g.replace("NIH ", "") for g in d.group], rotation=45, ha="right")
        ax.set_title(TAGS[t])
        ax.set_xlabel("Age (years); first bar = Guangzhou ages 1-5")
    axes[0].set_ylabel("Cardiomegaly false-positive rate\n(images with no finding)")
    fig.suptitle("Adult-trained models flag healthy children for cardiomegaly far more often (red = children)")
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "fig1_fpr_by_age.png"), dpi=160)

    lines.append("\n## 1. False-positive rate on healthy images, by age (operating point 0.5)\n")
    lines.append(rep.assign(ci=rep.apply(lambda r: f"{r.fpr:.1%} ({r.lo:.1%}-{r.hi:.1%})", axis=1))
                 .pivot(index="group", columns="model", values="ci")
                 .reindex(rep.group.unique()).to_markdown())

    # Discrimination by age group
    disc = []
    for t in TAGS:
        for name, d in [("Children (<18)", meta[meta.child]), ("Adults (18+)", meta[~meta.child])]:
            y, p = d.cardiomegaly.values, d[f"p_{t}"].values
            disc.append({"model": TAGS[t], "group": name, "AUROC": roc_auc_score(y, p),
                         "sensitivity": float((p[y == 1] >= .5).mean()), "FPR (all negatives)": float((p[y == 0] >= .5).mean()),
                         "positives": int(y.sum()), "n": len(y)})
    disc = pd.DataFrame(disc)
    lines.append("\n\n## Discrimination (NIH, all non-cardiomegaly images as negatives)\n")
    lines.append(disc.to_markdown(index=False, floatfmt=".3f"))

    # ---------- 2. Fixes (young children, ages 0-10, where the bias is) ----------
    out = []
    YOUNG = 10
    young = (meta.age <= YOUNG).values
    adult = (~meta.child).values
    y = meta.cardiomegaly.values
    healthy = meta.no_finding.values == 1
    young_pats = meta[young].patient_id.unique()
    ad_pats = meta[adult].patient_id.unique()
    gz_norm = (gz.label == 0).values
    for t in TAGS:
        F = preds[t]["f_nih"].astype(np.float32)
        Fg = preds[t]["f_gz"].astype(np.float32)
        p = meta[f"p_{t}"].values
        pg = gz[f"p_{t}"].values
        for r in range(REPEATS):
            rng = np.random.default_rng(100 + r)
            kp = rng.permutation(young_pats)
            pool_p = set(kp[: len(kp) // 2])
            ap = rng.permutation(ad_pats)
            atr_p = set(ap[: len(ap) // 2])
            in_pool = meta.patient_id.isin(pool_p).values
            in_atr = meta.patient_id.isin(atr_p).values
            pool = np.where(young & in_pool)[0]
            test = np.where(young & ~in_pool & (healthy | (y == 1)))[0]
            atr = np.where(adult & in_atr)[0]
            aval = np.where(adult & ~in_atr)[0]
            target = fpr(p[aval][healthy[aval]])
            yt, pt = y[test], p[test]
            sc = StandardScaler().fit(F[atr])
            pca = PCA(128, random_state=0).fit(sc.transform(F[atr]))
            Z = pca.transform(sc.transform(F))
            Zg = pca.transform(sc.transform(Fg))
            for n in NS:
                cal = rng.permutation(pool)[: min(n, len(pool))]
                base = {"model": TAGS[t], "rep": r, "n": n, "n_eff": len(cal), "target": target}
                # A: published operating point
                out.append({**base, "method": "A. Published threshold", "fpr": fpr(pt[yt == 0]),
                            "sens": float((pt[yt == 1] >= .5).mean()), "auroc": roc_auc_score(yt, pt),
                            "fpr_gz": fpr(pg[gz_norm])})
                # B: threshold re-picked on n young-child images so their FPR matches adults
                neg = p[cal][healthy[cal]]
                thr = np.quantile(neg, 1 - target) if len(neg) else 0.5
                out.append({**base, "method": "B. Pediatric threshold", "fpr": fpr(pt[yt == 0], thr),
                            "sens": float((pt[yt == 1] >= thr).mean()), "auroc": roc_auc_score(yt, pt),
                            "fpr_gz": fpr(pg[gz_norm], thr)})
                # C: head retrained on adults + the same n young-child images; threshold set on adults
                tr = np.concatenate([atr, cal])
                clf = LogisticRegression(C=0.5, max_iter=3000).fit(Z[tr], y[tr])
                thr_c = np.quantile(clf.decision_function(Z[aval])[healthy[aval]], 1 - target)
                st = clf.decision_function(Z[test])
                out.append({**base, "method": "C. Retrained head (adults + kids)", "fpr": fpr(st[yt == 0], thr_c),
                            "sens": float((st[yt == 1] >= thr_c).mean()), "auroc": roc_auc_score(yt, st),
                            "fpr_gz": fpr(clf.decision_function(Zg)[gz_norm], thr_c)})
        print(t, "fixes done", flush=True)
    fx = pd.DataFrame(out)
    fx.to_csv(os.path.join(RES, "fixes_raw.csv"), index=False)
    pool_size = int(fx.n_eff.max())
    fx.loc[fx.n == 10**6, "n"] = pool_size
    agg = fx.groupby(["model", "method", "n"]).agg(
        fpr=("fpr", "mean"), fpr_sd=("fpr", "std"), sens=("sens", "mean"), sens_sd=("sens", "std"),
        auroc=("auroc", "mean"), fpr_gz=("fpr_gz", "mean"), fpr_gz_sd=("fpr_gz", "std"),
        target=("target", "mean")).reset_index()
    agg.to_csv(os.path.join(RES, "fixes_summary.csv"), index=False)

    fig, axes = plt.subplots(3, 3, figsize=(15, 11), sharex=True)
    mcol = {"A. Published threshold": "#7f8c8d", "B. Pediatric threshold": "#2980b9",
            "C. Retrained head (adults + kids)": "#27ae60"}
    for j, t in enumerate(TAGS):
        d = agg[agg.model == TAGS[t]]
        for m, c in mcol.items():
            e = d[d.method == m]
            x = np.maximum(e.n, 10)
            axes[0, j].errorbar(x, e.fpr, yerr=e.fpr_sd, label=m, color=c, marker="o", capsize=3)
            axes[1, j].errorbar(x, e.fpr_gz, yerr=e.fpr_gz_sd, label=m, color=c, marker="o", capsize=3)
            axes[2, j].errorbar(x, e.sens, yerr=e.sens_sd, label=m, color=c, marker="o", capsize=3)
        for i in (0, 1):
            axes[i, j].axhline(d.target.mean(), ls="--", color="k", lw=1, label="Adult FPR (target)")
        axes[0, j].set_title(TAGS[t])
        for i in range(3):
            axes[i, j].set_xscale("log")
        axes[2, j].set_xlabel("Young-child images used for the fix (log; 10 = none)")
    axes[0, 0].set_ylabel(f"NIH ages 0-{YOUNG}, held-out:\nfalse-positive rate")
    axes[1, 0].set_ylabel("Guangzhou ages 1-5 (other hospital):\nfalse-positive rate")
    axes[2, 0].set_ylabel(f"NIH ages 0-{YOUNG}, held-out:\nsensitivity (few positives)")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(f"Closing the young-child gap: how many pediatric images each fix needs (mean ± sd, {REPEATS} patient-disjoint splits)")
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "fig2_fixes.png"), dpi=160)

    n_pos = int(y[young].sum())
    lines.append(f"\n\n## 2. Fixes for young children (ages 0-{YOUNG}), mean ± sd over {REPEATS} patient-disjoint splits\n")
    lines.append(f"Young-child pool for fixes: up to {pool_size} images. Test = the other half of young patients "
                 f"(healthy images + cardiomegaly; only {n_pos} cardiomegaly images at ages 0-{YOUNG} in total, so sensitivity is noisy). "
                 f"Guangzhou = external hospital, never used to build any fix. Target = adult FPR on healthy adult images.\n\n")
    show = agg.copy()
    show["NIH 0-10 FPR"] = show.apply(lambda r: f"{r.fpr:.1%} ± {r.fpr_sd:.1%}", axis=1)
    show["Guangzhou FPR"] = show.apply(lambda r: f"{r.fpr_gz:.1%} ± {r.fpr_gz_sd:.1%}", axis=1)
    show["Sensitivity"] = show.apply(lambda r: f"{r.sens:.1%} ± {r.sens_sd:.1%}", axis=1)
    show["AUROC"] = show.auroc.map(lambda v: f"{v:.3f}")
    show["Adult FPR"] = show.target.map(lambda v: f"{v:.1%}")
    show = show[~((show.method == "A. Published threshold") & (show.n > 0))]
    lines.append(show[["model", "method", "n", "NIH 0-10 FPR", "Guangzhou FPR", "Sensitivity", "AUROC", "Adult FPR"]]
                 .to_markdown(index=False))

    # ---------- 3. Age documentation probe ----------
    t = "pc"
    F = preds[t]["f_nih"].astype(np.float32)
    rng = np.random.default_rng(7)
    pats = rng.permutation(meta.patient_id.unique())
    trp = set(pats[: int(.7 * len(pats))])
    tr = meta.patient_id.isin(trp).values
    sc = StandardScaler().fit(F[tr])
    clf = LogisticRegression(C=0.5, max_iter=3000, class_weight="balanced").fit(sc.transform(F[tr]), meta.child.values[tr])
    s_te = clf.predict_proba(sc.transform(F[~tr]))[:, 1]
    y_te = meta.child.values[~tr]
    au = roc_auc_score(y_te, s_te)
    age_te = meta.age.values[~tr]
    by = {f"{a}-{b}": float((s_te[(age_te >= a) & (age_te <= b)] >= .5).mean()) for a, b in BINS}
    g_pred = clf.predict_proba(sc.transform(preds[t]["f_gz"].astype(np.float32)))[:, 1]
    lines.append("\n\n## 3. Flagging pediatric images when age isn't documented\n")
    lines.append(f"Linear probe on PadChest-model features, patient-disjoint 70/30 split on NIH. "
                 f"Child-vs-adult AUROC: {au:.3f}. Share flagged as child by age bin: "
                 + ", ".join(f"{k}: {v:.0%}" for k, v in by.items())
                 + f". External check: {float((g_pred >= .5).mean()):.1%} of the Guangzhou images (all ages 1-5) are flagged as children.\n")

    with open(os.path.join(RES, "summary.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
