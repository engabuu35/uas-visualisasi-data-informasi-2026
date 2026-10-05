"""Perhitungan analitis: PCA, klaster, pencilan, klasifikasi peta, Moran's I, hierarki."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, leaves_list, linkage
from scipy.stats import chi2
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from config import SECTOR_GROUP, SECTOR_SHORT

# --- Multivariat ---

# Nama klaster dari sektor dengan z-score rata-rata tertinggi; urutan daftar menentukan warna,
# sehingga warna mengikuti "jenis ekonomi", bukan nomor klaster Ward.
CLUSTER_NAMES = [
    "Basis Pertanian",
    "Basis Industri",
    "Basis Perdagangan & Jasa",
    "Basis Jasa Perusahaan",
    "Basis Pertambangan",
    "Basis Sektor Publik",
]
_NAME_RULES = {
    "A": "Basis Pertanian",
    "B": "Basis Pertambangan",
    "C": "Basis Industri",
    "D": "Basis Industri",
    "E": "Basis Industri",
    "F": "Basis Sektor Publik",
    "O": "Basis Sektor Publik",
    "M,N": "Basis Jasa Perusahaan",
}


@dataclass
class MultivariateResult:
    shares: pd.DataFrame          # wilayah x 17 sektor (%)
    z: pd.DataFrame               # z-score pangsa
    scores: pd.DataFrame          # PC1..PCk per wilayah
    explained: np.ndarray         # rasio varians tiap PC
    loadings: pd.DataFrame        # sektor x PC (vektor eigen)
    cluster: pd.Series            # nama klaster per wilayah
    cluster_profile: pd.DataFrame  # klaster x sektor (rata-rata z)
    mahalanobis: pd.Series
    outlier: pd.Series            # bool
    n_pc_outlier: int
    row_order: list               # urutan wilayah dari dendrogram Ward
    col_order: list               # urutan sektor dari dendrogram korelasi


def run_multivariate(shares: pd.DataFrame, k: int = 6, alpha: float = 0.01) -> MultivariateResult:
    """PCA, klaster Ward, dan pencilan Mahalanobis pada z-score pangsa sektor.
    Pencilan diukur pada PC yang menjelaskan >= 80% varians, ambang chi-kuadrat 1%."""
    z = pd.DataFrame(
        StandardScaler().fit_transform(shares), index=shares.index, columns=shares.columns,
    )

    pca = PCA().fit(z)
    raw_scores = pca.transform(z)
    pcs = [f"PC{i + 1}" for i in range(raw_scores.shape[1])]
    scores = pd.DataFrame(raw_scores, index=z.index, columns=pcs)
    loadings = pd.DataFrame(pca.components_.T, index=z.columns, columns=pcs)

    # Tanda PC tidak unik; tetapkan PC1+ = jasa keuangan (K), PC2+ = industri (C).
    for pc, anchor in (("PC1", "K"), ("PC2", "C")):
        if loadings.loc[anchor, pc] < 0:
            loadings[pc] *= -1
            scores[pc] *= -1

    # Klaster Ward
    link = linkage(z.to_numpy(), method="ward", optimal_ordering=True)
    labels = fcluster(link, k, criterion="maxclust")
    profile = z.groupby(labels).mean()
    names = _name_clusters(profile)
    cluster = pd.Series(labels, index=z.index).map(names)
    profile.index = profile.index.map(names)
    profile = profile.reindex([n for n in CLUSTER_NAMES if n in profile.index]
                              + [n for n in profile.index if n not in CLUSTER_NAMES])

    row_order = z.index[leaves_list(link)].tolist()
    corr_dist = 1 - z.corr().to_numpy()
    condensed = corr_dist[np.triu_indices(len(corr_dist), k=1)]
    col_link = linkage(condensed, method="average", optimal_ordering=True)
    col_order = z.columns[leaves_list(col_link)].tolist()

    # Pencilan
    cum = np.cumsum(pca.explained_variance_ratio_)
    n_pc = int(np.searchsorted(cum, 0.80) + 1)
    d2 = (raw_scores[:, :n_pc] ** 2 / pca.explained_variance_[:n_pc]).sum(axis=1)
    maha = pd.Series(d2, index=z.index)
    outlier = maha > chi2.ppf(1 - alpha, df=n_pc)

    return MultivariateResult(
        shares=shares, z=z, scores=scores, explained=pca.explained_variance_ratio_,
        loadings=loadings, cluster=cluster, cluster_profile=profile,
        mahalanobis=maha, outlier=outlier, n_pc_outlier=n_pc,
        row_order=row_order, col_order=col_order,
    )


def silhouette_by_k(z: pd.DataFrame, ks) -> dict:
    from sklearn.metrics import silhouette_score
    link = linkage(z.to_numpy(), method="ward")
    return {k: float(silhouette_score(z, fcluster(link, k, criterion="maxclust"))) for k in ks}


def _name_clusters(profile: pd.DataFrame) -> dict:
    names, used = {}, set()
    # Klaster dengan ciri paling tajam diberi nama lebih dulu.
    for label in profile.max(axis=1).sort_values(ascending=False).index:
        ranked = profile.loc[label].sort_values(ascending=False)
        name = _NAME_RULES.get(ranked.index[0], "Basis Perdagangan & Jasa")
        if name in used:
            name = f"{name} ({SECTOR_SHORT[ranked.index[1]].lower()})"
        used.add(name)
        names[label] = name
    return names


def cluster_colors(names, palette) -> dict:
    """Warna tetap per nama klaster (warna mengikuti entitas)."""
    out, extra = {}, 0
    for name in names:
        if name in CLUSTER_NAMES:
            out[name] = palette[CLUSTER_NAMES.index(name) % len(palette)]
        else:
            out[name] = palette[(len(CLUSTER_NAMES) + extra) % len(palette)]
            extra += 1
    return out


# --- Klasifikasi peta ---

def jenks_breaks(values, k: int) -> list[float]:
    """Natural breaks Fisher-Jenks (pemrograman dinamis, O(k n^2)); mengembalikan k+1 batas."""
    x = np.sort(np.asarray(values, dtype=float))
    x = x[~np.isnan(x)]
    n = len(x)
    if n <= k:
        return list(np.unique(x))

    s1 = np.concatenate([[0.0], np.cumsum(x)])
    s2 = np.concatenate([[0.0], np.cumsum(x ** 2)])

    def ssd(i, j):  # jumlah kuadrat simpangan untuk x[i:j]
        m = j - i
        return s2[j] - s2[i] - (s1[j] - s1[i]) ** 2 / m

    cost = np.full((k + 1, n + 1), np.inf)
    back = np.zeros((k + 1, n + 1), dtype=int)
    cost[0, 0] = 0.0
    for c in range(1, k + 1):
        for j in range(c, n + 1):
            i = np.arange(c - 1, j)
            cand = cost[c - 1, i] + np.array([ssd(a, j) for a in i])
            best = int(np.argmin(cand))
            cost[c, j] = cand[best]
            back[c, j] = i[best]

    cuts, j = [], n
    for c in range(k, 0, -1):
        i = back[c, j]
        cuts.append(i)
        j = i
    cuts = sorted(cuts)[1:]
    return [x[0]] + [x[c - 1] for c in cuts] + [x[-1]]


def quantile_breaks(values, k: int) -> list[float]:
    return list(np.unique(np.nanquantile(values, np.linspace(0, 1, k + 1))))


def classify(values: pd.Series, breaks: list[float], fmt: str = "{:.1f}") -> pd.Series:
    """Label kelas berurutan ('1,2 – 3,4'). Kelas paling bawah inklusif kiri."""
    edges = list(breaks)
    labels = [f"{_fmt(edges[i], fmt)} – {_fmt(edges[i + 1], fmt)}" for i in range(len(edges) - 1)]
    cat = pd.cut(values, bins=edges, labels=labels, include_lowest=True, duplicates="drop")
    return cat


def _fmt(v, fmt):
    return fmt.format(v).replace(".", ",") if np.isfinite(v) else "∞"


# --- Autokorelasi spasial ---

def knn_weights(lat, lon, k: int = 6) -> np.ndarray:
    """Bobot k-tetangga terdekat (haversine), distandardisasi baris.
    Dipilih alih-alih queen karena banyak kab/kota kepulauan tidak bersinggungan."""
    lat_r, lon_r = np.radians(lat), np.radians(lon)
    dlat = lat_r[:, None] - lat_r[None, :]
    dlon = lon_r[:, None] - lon_r[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat_r)[:, None] * np.cos(lat_r)[None, :] * np.sin(dlon / 2) ** 2
    dist = 2 * np.arcsin(np.sqrt(a))
    np.fill_diagonal(dist, np.inf)
    nn = np.argsort(dist, axis=1)[:, :k]
    w = np.zeros_like(dist)
    np.put_along_axis(w, nn, 1.0 / k, axis=1)
    return w


def moran(values: np.ndarray, w: np.ndarray, permutations: int = 999, seed: int = 7) -> dict:
    """Moran's I global + LISA dengan uji permutasi bersyarat (dengan pengembalian)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(values, dtype=float)
    z = (x - x.mean()) / x.std()
    n = len(z)
    lag = w @ z
    i_global = float(z @ lag / n)

    sims = np.empty(permutations)
    for p in range(permutations):
        zp = rng.permutation(z)
        sims[p] = zp @ (w @ zp) / n
    # Uji satu sisi, searah dengan I teramati (I negatif pun bisa signifikan).
    tail = sims >= i_global if i_global >= -1 / (len(z) - 1) else sims <= i_global
    p_global = (np.sum(tail) + 1) / (permutations + 1)

    # Tarik k_i tetangga per wilayah (bisa < k bila ada wilayah yang dikeluarkan).
    k_i = (w > 0).sum(axis=1)
    local = z * lag
    draw = rng.integers(0, n - 1, size=(n, permutations, max(int(k_i.max()), 1)))
    draw += draw >= np.arange(n)[:, None, None]  # lewati diri sendiri
    csum = np.cumsum(z[draw], axis=2)
    pick = np.maximum(k_i, 1) - 1
    lag_sim = np.take_along_axis(csum, pick[:, None, None], axis=2)[..., 0] / np.maximum(k_i, 1)[:, None]
    local_sim = z[:, None] * lag_sim
    larger = (local_sim >= local[:, None]).sum(axis=1)
    smaller = permutations - larger
    p_local = (np.minimum(larger, smaller) + 1) / (permutations + 1)
    p_local[k_i == 0] = 1.0  # tanpa tetangga: tidak bisa diuji

    quad = np.select(
        [(z > 0) & (lag > 0), (z < 0) & (lag < 0), (z > 0) & (lag < 0), (z < 0) & (lag > 0)],
        ["Tinggi-Tinggi", "Rendah-Rendah", "Tinggi-Rendah", "Rendah-Tinggi"],
        default="Tidak signifikan",
    )
    quad = np.where(p_local < 0.05, quad, "Tidak signifikan")
    return {
        "I": i_global, "p": float(p_global), "expected": -1 / (n - 1),
        "z": z, "lag": lag, "p_local": p_local, "quadrant": quad,
    }


# --- Hierarki ---

def build_hierarchy(long: pd.DataFrame, period: str, order: str = "wilayah") -> pd.DataFrame:
    """Simpul treemap/icicle: ukuran = PDRB ADHK `period`, warna = pertumbuhan TW II vs TW I
    dari jumlah nilai di bawah simpul. `order` = "wilayah" atau "sektor" (urutan tingkat)."""
    d = long[long["kode_sektor"] != "TOTAL"].copy()
    d["kelompok"] = d["kode_sektor"].map(SECTOR_GROUP)
    d["sektor_singkat"] = d["kode_sektor"].map(SECTOR_SHORT)
    wide = d.pivot_table(
        index=["pulau", "provinsi", "kabkota", "kelompok", "kode_sektor", "sektor_singkat"],
        columns="periode", values="nilai", aggfunc="sum",
    ).reset_index()

    if order == "wilayah":
        levels = ["pulau", "provinsi", "kabkota", "sektor_singkat"]
        level_names = ["Pulau", "Provinsi", "Kab/Kota", "Sektor"]
    else:
        levels = ["kelompok", "sektor_singkat", "pulau", "provinsi"]
        level_names = ["Kelompok", "Sektor", "Pulau", "Provinsi"]

    nodes = []
    root_q1, root_q2 = wide["Triwulan I"].sum(), wide["Triwulan II"].sum()
    nodes.append({"id": "Indonesia", "parent": "", "label": "Indonesia", "tingkat": "Nasional",
                  "q1": root_q1, "q2": root_q2})
    for depth in range(len(levels)):
        keys = levels[: depth + 1]
        g = wide.groupby(keys, as_index=False)[["Triwulan I", "Triwulan II"]].sum()
        for row in g.itertuples(index=False):
            path = [str(v) for v in row[: depth + 1]]
            nodes.append({
                "id": "Indonesia/" + "/".join(path),
                "parent": "Indonesia" + ("/" + "/".join(path[:-1]) if depth else ""),
                "label": path[-1],
                "tingkat": level_names[depth],
                "q1": row[-2],
                "q2": row[-1],
            })

    out = pd.DataFrame(nodes)
    out["nilai"] = out["q2"] if period == "Triwulan II" else out["q1"]
    out["tumbuh"] = np.where(out["q1"] > 0, (out["q2"] / out["q1"] - 1) * 100, np.nan)
    out["pangsa_induk"] = out["nilai"] / out["parent"].map(out.set_index("id")["nilai"]) * 100
    return out[out["nilai"] > 0].reset_index(drop=True)

