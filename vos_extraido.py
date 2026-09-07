# Código extraído verbatim do prompt Prompt_ANALISE_Bibliometrica_VOSviewer.md
# Trechos na ordem em que aparecem no documento; requer adaptacao ao seu corpus.

def norm_doi(x):
    return (x or '').strip().lower().replace('https://doi.org/', '').rstrip('.')


# ---- bloco seguinte ----

SYN = {
    r'^(ai|artificial intelligence) agents?$': 'AI agents',
    r'^(large language models?|llms?)$': 'large language models',
    r'^(principal[- ]agent( theory)?|agency theory)$': 'agency theory',
    r'^dynamic capabilit(y|ies)$': 'dynamic capabilities',
    r'^organi[sz]ational (change|transformation)$': 'organizational transformation',
    r'^(human[- ]in[- ]the[- ]loop|human oversight)$': 'human oversight',
    # ... adapte ao seu campo
}

def norm(k):
    k = re.sub(r'\s+', ' ', k.strip().lower()).strip(' .,;')
    for padrao, canonico in SYN.items():
        if re.match(padrao, k):
            return canonico
    return k

docs = {}
for c in corpus:
    ks = {norm(x) for x in re.split(r'[;|]', c['keywords'] or '') if x.strip()}
    if ks:
        docs[c['id']] = ks


# ---- bloco seguinte ----

import numpy as np, igraph as ig, leidenalg as la

def build_network(docs, df, minocc, dedup=False, rel_keep=None, label=''):
    cand = [t for t, n in df.items() if n >= minocc]

    if dedup:   # SO para redes de termos; NAO usar em palavras-chave de autor
        srt = sorted(cand, key=lambda t: -len(t.split())); drop = set()
        for longo in srt:
            lw = longo.split()
            if len(lw) < 2: continue
            for curto in srt:
                if curto in drop or curto == longo: continue
                sw = curto.split()
                if len(sw) >= len(lw): continue
                if any(lw[k:k+len(sw)] == sw for k in range(len(lw)-len(sw)+1)) \
                   and df[longo]/df[curto] >= 0.80:
                    drop.add(curto)
        cand = [t for t in cand if t not in drop]

    idx = {t: i for i, t in enumerate(cand)}; n = len(cand)
    M = np.zeros((len(docs), n), dtype=np.int8)
    for r, ts in enumerate(docs.values()):
        for t in ts:
            if t in idx: M[r, idx[t]] = 1
    Co = (M.T @ M).astype(float)
    occ = np.diag(Co).copy()
    np.fill_diagonal(Co, 0)

    if rel_keep and rel_keep < 1.0:   # SO para redes de termos
        tot = Co.sum(axis=1); glob = tot / max(tot.sum(), 1)
        rel = np.zeros(n)
        for i in range(n):
            if tot[i] <= 0: continue
            p = Co[i] / tot[i]; m = (p > 0) & (glob > 0)
            rel[i] = float(np.sum(p[m] * np.log(p[m] / glob[m])))
        z = lambda a: (a - a.mean()) / (a.std() + 1e-9)
        score = z(rel) + 0.55 * z(np.log1p(occ))
        keep = sorted(np.argsort(-score)[:int(round(rel_keep * n))])
    else:
        keep = list(range(n))

    terms = [cand[i] for i in keep]
    Co = Co[np.ix_(keep, keep)]; occ = occ[keep]
    print(f"[{label}] candidatos {n} -> rede {len(terms)} nos")
    return terms, Co, occ


def association_strength(Co, occ):
    """s_ij = c_ij / (w_i * w_j / 2m). Normalizacao do VOSviewer."""
    w = Co.sum(axis=1); m2 = w.sum()
    E = np.outer(w, w) / max(m2, 1e-9)
    S = np.divide(Co, E, out=np.zeros_like(Co), where=E > 0)
    np.fill_diagonal(S, 0)
    return S


def cluster_cpm(S, resolution=1.0, seed=42):
    """Constant Potts Model via Leiden.
    CRITICO: o RNG do igraph e GLOBAL. Passar seed a find_partition NAO basta."""
    import random as _random
    _random.seed(seed)
    ig.set_random_number_generator(_random)
    n = S.shape[0]; edges = []; ws = []
    for i in range(n):
        for j in range(i+1, n):
            if S[i, j] > 0:
                edges.append((i, j)); ws.append(float(S[i, j]))
    g = ig.Graph(n=n, edges=edges); g.es['weight'] = ws
    part = la.find_partition(g, la.CPMVertexPartition, weights='weight',
                             resolution_parameter=resolution, seed=seed,
                             n_iterations=-1)
    return np.array(part.membership), g


def vos_layout(S, iters=600, seed=42):
    """Minimiza V(x) = sum s_ij |xi-xj|^2 sob restricao de distancia media 1."""
    rng = np.random.default_rng(seed); n = S.shape[0]
    X = rng.normal(scale=1.0, size=(n, 2))
    W = S.copy(); np.fill_diagonal(W, 0)
    deg = W.sum(axis=1)
    for _ in range(iters):
        D = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2) + 1e-9
        R = 1.0 / D; np.fill_diagonal(R, 0)
        Xn = (W @ X + 0.30 * (R @ X)) / ((deg + 0.30 * R.sum(axis=1))[:, None] + 1e-9)
        Xn -= Xn.mean(axis=0)
        if np.linalg.norm(Xn - X) < 1e-7:
            X = Xn; break
        X = Xn
    D = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2)
    return X / max(D[np.triu_indices(n, 1)].mean(), 1e-9)


# ---- bloco seguinte ----

from collections import Counter

def canon(m):
    """Canoniza rotulos. SEM ISSO, particoes identicas com rotulos trocados
    sao contadas como distintas e a moda sai errada."""
    ren, out = {}, []
    for x in m:
        if x not in ren: ren[x] = len(ren)
        out.append(ren[x])
    return tuple(out)

N_EXEC = 200
freq = Counter()
for semente in range(N_EXEC):
    memb, _ = cluster_cpm(S, resolution=RES, seed=semente)
    freq[canon(memb)] += 1
modal, vezes = freq.most_common(1)[0]
memb = np.array(modal)
print(f"particao modal obtida em {vezes} de {N_EXEC}; {len(freq)} particoes distintas")


# ---- bloco seguinte ----

from sklearn.metrics import adjusted_rand_score as ari

for RES in (0.8, 1.0, 1.2):
    parts = [cluster_cpm(S, resolution=RES, seed=s)[0] for s in range(10)]
    sc = [ari(parts[i], parts[j]) for i in range(10) for j in range(i+1, 10)]
    nk = sorted({len(set(p)) for p in parts})
    print(f"res {RES}: ARI medio {np.mean(sc):.3f} min {np.min(sc):.3f} clusters {nk}")


# ---- bloco seguinte ----

D = np.hypot(X[:, None] - X[None, :], Y[:, None] - Y[None, :])
h = float(np.median(np.sort(D, axis=1)[:, 3])) * 0.70   # regra do 4o vizinho
TERMOS_BUSCA = {...}   # os termos da propria consulta
wd = np.array([0.0 if t in TERMOS_BUSCA else occ[i] for i, t in enumerate(terms)])
Z = np.zeros_like(GX)
for i in range(n):
    if wd[i] <= 0: continue
    Z += wd[i] * np.exp(-(((GX - X[i])**2 + (GY - Y[i])**2) / (h * h)))
Z /= Z.max()


# ---- bloco seguinte ----

anos_termo = []
for t in termos:
    ys = [ano[d] for d, ks in docs.items() if t in ks and d in ano]
    anos_termo.append(float(np.mean(ys)) if ys else np.nan)


# ---- bloco seguinte ----

# separador: o mesmo caractere separa autores e referencias.
# ancore pelo ano entre parenteses.
SEP = re.compile(r'(?<=\(\d{4}\));\s+')

def chave(ref):
    anos = re.findall(r'\((\d{4})\)', ref)
    ano = anos[-1] if anos else ''
    m = re.match(r"([A-Za-zÀ-ÿ'’\-]+)", ref)
    sobrenome = (m.group(1) if m else '').lower()
    segs = [s.strip() for s in re.split(r'[,;]', ref)]
    titulo = max(segs, key=lambda s: len(re.findall(r'[A-Za-z]{3,}', s)), default='')
    tokens = re.findall(r'[a-z]{3,}', titulo.lower())[:6]
    return f"{sobrenome}|{ano}|{' '.join(tokens)}" if tokens else None


# ---- bloco seguinte ----

comuns = [d for d in part_kw if d in part_acop]
indice = ari([part_kw[d] for d in comuns], [part_acop[d] for d in comuns])
