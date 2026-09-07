# PROTOCOLO EXECUTÁVEL: análise bibliométrica replicando o método do VOSviewer

**Destinatário deste arquivo: agente de IA com acesso a shell, Python e sistema de arquivos.**
**Modo de uso: execute as fases na ordem. Não pule fases. Não prossiga com um gate reprovado.**

---

## 0. OBJETIVO E CONTRATO

Você vai executar uma análise bibliométrica completa sobre um corpus de documentos científicos, replicando em código o método do VOSviewer e acrescentando os controles de reprodutibilidade que o software não oferece. Ao final você entrega: 6 figuras, 7 tabelas descritivas, 2 arquivos de importação para o VOSviewer, as matrizes gravadas, os scripts e um relatório de parâmetros.

### 0.1 Regras invioláveis

Estas regras não são preferências. Violá-las invalida a análise.

1. **NUNCA reporte uma partição obtida em execução única.** Toda partição reportada é a moda de no mínimo 200 execuções.
2. **NUNCA passe apenas `seed` ao `leidenalg` e assuma determinismo.** Fixe o gerador global do igraph (ver 4.2). Sem isso o resultado muda entre execuções e a falha é silenciosa.
3. **NUNCA adote uma partição com ARI médio abaixo de 0,70** no teste de estabilidade. Descarte e registre o descarte.
4. **NUNCA aplique tamanho mínimo de cluster como parâmetro do agrupamento.** É limiar de reporte, aplicado depois.
5. **NUNCA invente dados.** Se um campo não existe na exportação, declare a ausência. Se um casamento de referências falhou, declare a taxa.
6. **NUNCA afirme que a análise foi feita no VOSviewer.** Foi feita em código replicando o método. Escreva isso.
7. **NUNCA use a paleta padrão vermelho/verde.** Não é distinguível sob deuteranopia.
8. **Ao final de cada fase, execute o gate de verificação e reporte o resultado antes de prosseguir.**

### 0.2 Entradas que você precisa obter do usuário antes de começar

Se qualquer item abaixo estiver ausente, pergunte antes de executar. Não presuma.

| Entrada | Formato | Se ausente |
|---|---|---|
| Exportação da base primária | CSV com título, autores, ano, periódico, palavras-chave, DOI, citações, resumo | Bloqueie. Pergunte. |
| Exportação da base secundária | idem | Prossiga com uma base, declare a limitação |
| Data da busca | AAAA-MM-DD | Bloqueie. Pergunte. |
| String de busca, por plataforma | texto literal | Bloqueie. Pergunte. |
| Blocos conceituais da pergunta | 2 ou mais | Bloqueie. Pergunte. |
| Critérios de inclusão e exclusão | texto | Bloqueie. Pergunte. |
| Reexportação com campo de referências | CSV | Pule a Fase 7; declare que o acoplamento não foi feito |

### 0.3 Estrutura de diretórios a criar

```
projeto/
  00_dados_brutos/       exportações originais, nunca editadas
  01_corpus/             corpus_merged.csv, corpus_final.json, triagem.xlsx
  02_scripts/            vosmap.py, run_kw.py, mapa_final.py, stability.py,
                         acoplamento.py, fig_*.py, prisma.py, indicadores.py
  03_matrizes/           Co.npy, S.npy, mapa_final.json, overlay_anos.json
  04_figuras/            as 6 figuras em png (300 dpi), pdf e jpeg
  05_tabelas/            indicadores.xlsx, redes.xlsx, atribuicao_clusters.csv
  06_vosviewer/          VOSviewer_map.txt, VOSviewer_network.txt, thesaurus.txt
  07_relatorio/          parametros.md, log_execucao.md
```

### 0.4 Dependências

```bash
pip install numpy pandas networkx matplotlib python-igraph leidenalg scikit-learn openpyxl
```

Verifique a importação de `igraph` e `leidenalg` antes de prosseguir. São as duas que costumam falhar.

---

## FASE 1: CONSTITUIÇÃO DO CORPUS

### 1.1 Deduplicação

```python
def norm_doi(x):
    return (x or '').strip().lower().replace('https://doi.org/', '').rstrip('.')
```

Chave primária: DOI normalizado. Chave secundária, para registros sem DOI: `primeiro_sobrenome|ano|primeiras_6_palavras_do_titulo` em minúsculas.

**Calcule e registre**: `n_primaria`, `n_secundaria`, `n_compartilhados`, `n_unicos_secundaria`, e o percentual `n_unicos_secundaria / n_primaria`.

**Regra de decisão**: se o percentual exceder o limiar de dispersão que você adotar (declare-o), a fusão se justifica. Abaixo dele, use só a primária e trate a segunda como verificação de cobertura.

### 1.2 Triagem em três estados

Não use binário. Use:

- **A** = inclusão direta pelo título e resumo
- **B** = exige leitura do texto completo para decidir
- **C** = exclusão

Para cada registro grave: `id` estável (ex.: D001…Dnnn), `decisao` (A/B/C), `condicao_1` e `condicao_2` (sim/não/dúvida, uma por bloco conceitual), `confianca` (alta/média/baixa), `codigo_exclusao`, `justificativa`.

Códigos de exclusão devem ser numerados, mutuamente excludentes e aplicados na ordem escrita. Modelo:

```
E1  atende o bloco tecnológico mas não o bloco organizacional
E2  fora do objeto tecnológico definido
E3  contexto inadequado
E4  tipo de documento inadequado
E5  idioma fora do escopo
```

**Condição de inclusão dupla**: quando a revisão une duas literaturas, o documento só entra se satisfizer os dois blocos simultaneamente. Tabule essa condição explicitamente, é reutilizável.

**Sobre confiabilidade**: se a triagem for feita por um único revisor ou agente, escreva "confiabilidade não estimada". NÃO calcule Krippendorff's Alpha contra um comparador que você não auditou. Se houver verificação independente, audite-a primeiro: se as justificativas se repetirem em mais de 80% dos casos, a classificação veio de regra lexical e não de leitura, e o coeficiente calculado contra ela mede a inadequação do comparador. Nesse caso, reporte a verificação como tentada e inválida.

### 1.3 Saída da fase

`corpus_final.json`, lista de objetos com: `id`, `titulo`, `periodico`, `ano`, `autores`, `citacoes`, `keywords`, `doi`, `resumo`.

### GATE 1 - verifique e reporte

```
[ ] n_primaria + n_unicos_secundaria == n_total_deduplicado
[ ] n_A + n_B + n_C == n_total
[ ] soma dos codigos E == n_C
[ ] n_incluidos == n_A + n_B_confirmados
[ ] todo id do corpus final existe na planilha de triagem
```

Reprovou? Corrija antes de prosseguir. Não prossiga com somas que não fecham.

---

## FASE 2: NORMALIZAÇÃO DO VOCABULÁRIO

Construa um tesauro como dicionário de regex para forma canônica. Ancore SEMPRE com `^` e `$`.

```python
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
```

Grave o tesauro em `06_vosviewer/thesaurus.txt`, uma regra por linha.

### GATE 2 - verifique e reporte

```
[ ] n_documentos_com_keywords  (e o percentual do corpus)
[ ] n_termos_distintos
[ ] n_regras_do_tesauro
[ ] distribuicao: quantos termos ocorrem 1x, 2x, 3x, 4x+
```

**Se mais de 85% dos termos ocorrem uma única vez**, registre no relatório: "vocabulário não assentado; o limiar mínimo é permissivo por necessidade e os clusters descrevem um sinal fino". Essa ressalva precisa reaparecer na leitura dos clusters.

---

## FASE 3: CONSTRUÇÃO DA REDE

### 3.1 Módulo base (`02_scripts/vosmap.py`)

```python
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
```

### 3.2 Escolha de configuração

| Fonte dos termos | `minocc` | `dedup` | `rel_keep` |
|---|---|---|---|
| Palavras-chave de autor | 2 (testar 2, 3, 4) | `False` | `None` |
| Termos de título e resumo | 10 | `True` | 0,60 a 0,65 |

Rode **as duas** configurações. A segunda quase sempre será reprovada na Fase 5, e essa reprovação é resultado reportável.

### GATE 3 - verifique e reporte

```
[ ] n_termos na rede, para cada minocc testado (2, 3, 4)
[ ] n_arestas
[ ] densidade = (Co>0).sum() / (n*(n-1))
[ ] S e simetrica e tem diagonal zero
[ ] nenhum valor NaN ou infinito em S
```

Grave `03_matrizes/Co.npy` e `03_matrizes/S.npy`.

---

## FASE 4: AGRUPAMENTO

### 4.1 Grade de resolução

Rode `cluster_cpm` para resolução em `(0.8, 1.0, 1.2)` e registre número de clusters e os tamanhos. Não escolha ainda.

### 4.2 Partição modal - obrigatório

```python
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
```

Renumere os clusters por tamanho decrescente, para que o cluster 1 seja sempre o maior.

### 4.3 Limiar de reporte

Fixe o limiar ANTES de olhar o resultado. Recomendado: 10% do corpus. Clusters acima do limiar são interpretados como temas; abaixo, reportados como residuais com o tamanho declarado. **Não remova os residuais da partição.**

### GATE 4 - verifique e reporte

```
[ ] vezes / N_EXEC  (frequencia da moda)
[ ] n_particoes_distintas
[ ] n_clusters e tamanhos
[ ] quantos clusters atingem o limiar de reporte
[ ] soma dos tamanhos == n_termos
```

**Se a moda foi obtida em menos de 40% das execuções**, registre: "solução defensável mas não única". Isso precisa constar do artigo.

---

## FASE 5: TESTE DE ESTABILIDADE - GATE DECISÓRIO

```python
from sklearn.metrics import adjusted_rand_score as ari

for RES in (0.8, 1.0, 1.2):
    parts = [cluster_cpm(S, resolution=RES, seed=s)[0] for s in range(10)]
    sc = [ari(parts[i], parts[j]) for i in range(10) for j in range(i+1, 10)]
    nk = sorted({len(set(p)) for p in parts})
    print(f"res {RES}: ARI medio {np.mean(sc):.3f} min {np.min(sc):.3f} clusters {nk}")
```

### Regra de decisão, aplique literalmente

| ARI médio | Ação |
|---|---|
| ≥ 0,90 | adotar |
| 0,70 a 0,89 | adotar, declarando a estabilidade no artigo |
| < 0,70 | **descartar a configuração**; registrar o descarte |

Entre duas configurações aprovadas, adote a **menos fragmentada** (menos clusters).

Preencha e entregue esta tabela:

| Rede | Resolução | ARI médio | ARI mínimo | Clusters | Decisão |
|---|---|---|---|---|---|
| Termos de título e resumo | 1,0 | | | | |
| Termos de título e resumo | 1,3 | | | | |
| Palavras-chave de autor | 0,8 | | | | |
| Palavras-chave de autor | 1,0 | | | | |

Referência de ordem de grandeza obtida no projeto de origem, para calibrar expectativa: termos de título e resumo devolveram 0,534 e 0,580 e foram descartados; palavras-chave de autor devolveram 0,947 a 0,8 e 0,938 a 1,0, e a resolução 0,8 foi adotada por ser menos fragmentada.

### GATE 5

```
[ ] ao menos uma configuracao aprovada
[ ] tabela de estabilidade preenchida com decisao explicita por linha
[ ] configuracoes reprovadas registradas, nao apagadas
```

**Se nenhuma configuração passar**: pare. Não produza mapa. Reporte ao usuário que a estrutura de clusters não é estável neste corpus e proponha alternativas (aumentar o corpus, mudar a fonte dos termos, reportar apenas descritivos).

---

## FASE 6: LAYOUT

Use `vos_layout(S)` ou MDS Kamada-Kawai sobre `1/S`. Grave as coordenadas em `03_matrizes/mapa_final.json` com, por termo: `label`, `cluster`, `occ`, `links`, `total_link_strength`, `x`, `y`.

**REGRA**: as mesmas coordenadas em TODAS as figuras derivadas deste mapa (network, densidade, overlay). Se as três não compartilharem o layout, o leitor não consegue compará-las.

---

## FASE 7: AS SEIS FIGURAS

Produza **todas as seis**, mesmo que nem todas entrem no artigo. As excedentes vão para material de apoio. Cada figura: PNG 300 dpi, PDF e JPEG 300 dpi.

### Figura 1 - Fluxo PRISMA 2020

Blocos: identificação por base, duplicados removidos, triados, excluídos por código, avaliados em texto completo, não recuperados, incluídos.

Embuta verificações de soma no próprio gerador, de modo que a inconsistência apareça no arquivo e não sobreviva à revisão por pares.

### Figura 2 - Curva de crescimento

Barras de contagem anual de publicações.

**Obrigatório**: marque o ano parcial (busca no meio do ano) com hachura ou cor distinta e explique na legenda. Barra de ano incompleto lida como cheia distorce a tendência.

**Se mais de 60% do corpus for do último ano completo ou do parcial**, acrescente a ressalva: "indicadores de citação descrevem a idade dos documentos mais do que sua influência". Essa ressalva deve acompanhar toda tabela de mais citados.

### Figura 3 - Network visualization

Tamanho do círculo = ocorrência; espessura da linha = coocorrência; distância ≈ força de associação; cor = cluster.

Requisitos:
- Paleta acessível sob deuteranopia. Declare a substituição na legenda, porque quem conhece o software vai notar.
- Rotulagem seletiva com supressão de colisões. Reporte quantos rótulos ficaram visíveis, de quantos itens.
- Termos da estratégia de busca permanecem no mapa mas a legenda declara que nenhuma afirmação repousa na centralidade deles.

### Figura 4 - Density visualization

```python
D = np.hypot(X[:, None] - X[None, :], Y[:, None] - Y[None, :])
h = float(np.median(np.sort(D, axis=1)[:, 3])) * 0.70   # regra do 4o vizinho
TERMOS_BUSCA = {...}   # os termos da propria consulta
wd = np.array([0.0 if t in TERMOS_BUSCA else occ[i] for i, t in enumerate(terms)])
Z = np.zeros_like(GX)
for i in range(n):
    if wd[i] <= 0: continue
    Z += wd[i] * np.exp(-(((GX - X[i])**2 + (GY - Y[i])**2) / (h * h)))
Z /= Z.max()
```

Excluir os termos de busca do **peso** (não do rótulo) é obrigatório: mantê-los colapsa a superfície num pico único. Declare a exclusão na legenda.

Exporte limpo, sem título e sem barra de escala, como o VOSviewer exporta.

### Figura 5 - Overlay temporal

Mesmo layout, mesmos tamanhos, cor pelo ano médio de publicação dos documentos que carregam cada termo. Rampa sequencial do mais antigo ao mais recente.

```python
anos_termo = []
for t in termos:
    ys = [ano[d] for d, ks in docs.items() if t in ks and d in ano]
    anos_termo.append(float(np.mean(ys)) if ys else np.nan)
```

**Esta figura tem o maior rendimento analítico por unidade de esforço e é a mais subutilizada.** Ela pode inverter a direção de influência que os números de volume sugerem: um cluster que parece reação tardia pode carregar os termos mais antigos do mapa.

**Ressalva obrigatória**: reporte a faixa de ocorrências dos termos mais antigos. Se ocorrerem poucas vezes, as médias **ordenam** os termos mas não os **medem**. Escreva isso.

### Figura 6 - Acoplamento bibliográfico

Requer campo de referências citadas, ausente da exportação padrão. Reexporte com o template que o inclui.

```python
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
```

Parâmetros: mínimo de 2 referências compartilhadas para haver aresta; resolução 0,60; partição modal sobre 200 execuções; mesma `association_strength` e mesmo `cluster_cpm`.

**Validação obrigatória do casamento**: liste as 10 referências mais compartilhadas. Se não forem as obras que qualquer conhecedor do campo esperaria ver, o casamento falhou - corrija antes de prosseguir. Se forem, declare mesmo assim que "uma taxa residual de casamentos perdidos não pode ser descartada e enviesa as forças de acoplamento para baixo".

**Procedência**: se a reexportação for posterior à busca, declare que ela serve apenas como fonte do campo de referências para documentos já triados, e que nenhum documento novo entrou. Se uma base não devolver referências, declare que o acoplamento repousa só na outra e quantos documentos do corpus estão cobertos.

### GATE 7

```
[ ] 6 figuras geradas, cada uma em png/pdf/jpeg a 300 dpi
[ ] figuras 3, 4 e 5 compartilham exatamente as mesmas coordenadas
[ ] paleta validada para deuteranopia
[ ] cada figura tem legenda com fonte, parametros e ressalvas
[ ] PRISMA fecha aritmeticamente
```

---

## FASE 8: VALIDAÇÃO CRUZADA ENTRE TÉCNICAS

```python
comuns = [d for d in part_kw if d in part_acop]
indice = ari([part_kw[d] for d in comuns], [part_acop[d] for d in comuns])
```

### Interpretação, aplique literalmente

| ARI | Leitura |
|---|---|
| ≥ 0,50 | convergência; a solução está validada por técnica independente |
| 0,20 a 0,49 | convergência parcial; reporte o que as duas concordam |
| < 0,20 | **ausência de concordância, não concordância fraca** |

**Ausência de concordância é resultado substantivo, não falha.** Significa que os documentos que usam o mesmo vocabulário não se apoiam na mesma base intelectual. Reporte como achado, com esta leitura: um rótulo se difundiu depressa por literaturas estabelecidas que mantiveram seus próprios hábitos de citação.

### Grade de robustez - obrigatória antes de afirmar o achado

Varie limiar de referências compartilhadas (1, 2, 3) e resolução (0,6 e 1,0). Reporte a faixa completa do ARI:

| Limiar | Resolução | ARI |
|---|---|---|
| 1 | 0,6 | |
| 1 | 1,0 | |
| 2 | 0,6 | |
| 2 | 1,0 | |
| 3 | 0,6 | |
| 3 | 1,0 | |

Se a faixa inteira permanecer na mesma leitura, escreva no artigo: "robusto às escolhas que poderiam tê-lo produzido, variando de X a Y".

**Quando a convergência falha, procure o que as duas técnicas concordam, ainda que seja pouco.** Essa concordância mínima costuma ser o achado sobre o qual o argumento se constrói.

---

## FASE 9: ATRIBUIÇÃO DE DOCUMENTOS A CLUSTERS

O mapa particiona **termos**, não documentos. Para a leitura qualitativa:

Atribua cada documento ao cluster cujos termos dominam a sua lista normalizada de palavras-chave, com **os termos da estratégia de busca ponderados a 0,25 de um casamento pleno**, para que os documentos não sejam alocados pelos termos que os recuperaram.

Documentos sem nenhuma palavra-chave acima do limiar de ocorrência ficam **sem atribuição**. Conte-os como tal. Não os distribua à força.

Entregue `05_tabelas/atribuicao_clusters.csv` e a tabela resumo:

| Cluster | Documentos | % do corpus | Acima do limiar | Tipo de evidência predominante |
|---|---|---|---|---|

### GATE 9

```
[ ] soma dos documentos por cluster + residuais + sem atribuicao == n_corpus
```

---

## FASE 10: TABELAS DE INDICADORES

Sete abas em `05_tabelas/indicadores.xlsx`:

1. **Publicações por ano** - ano, documentos, % do corpus, acumulado, observação (marcar ano parcial)
2. **Periódicos** - periódico, documentos, citações, citações por documento
3. **Documentos mais citados** - id, ano, título, periódico, citações
4. **Citações normalizadas** - idem, mais `cit_normalizadas` (citações divididas pela média do ano); é a única comparação justa entre anos distintos em campo recente
5. **Autores** - autor, documentos, citações
6. **Palavras-chave normalizadas** - termo, ocorrências, % dos documentos
7. **Países** - país, documentos

**A tabela de periódicos merece leitura explícita.** Concentração indica campo com centro editorial. Dispersão, com a maioria dos periódicos publicando um único documento, é achado descritivo forte e frequentemente o mais robusto de toda a análise, porque não depende de nenhuma escolha de parâmetro. Reporte: n_periodicos, n_com_um_documento, maior número de documentos em um periódico, e a participação dos três maiores.

Grave também `05_tabelas/redes.xlsx` com abas: Parâmetros, Clusters, Nós, Arestas, Estabilidade.

---

## FASE 11: EXPORTAÇÃO PARA O VOSVIEWER

`06_vosviewer/VOSviewer_map.txt`, tabulado, com cabeçalho:

```
id	label	x	y	cluster	weight<Occurrences>	weight<Links>	weight<Total link strength>
1	agentic AI	-0.1027	-0.1739	3	63	42	111.00
```

`06_vosviewer/VOSviewer_network.txt`, tabulado, sem cabeçalho: origem, destino, peso.

```
1	2	2
1	3	6
```

Grave também `Co.npy`, `S.npy`, `mapa_final.json` e `thesaurus.txt`.

---

## FASE 12: RELATÓRIO DE PARÂMETROS

Preencha `07_relatorio/parametros.md` com todos os valores efetivamente usados:

| Parâmetro | Valor usado | Referência típica |
|---|---|---|
| Bases e data da busca | | duas bases, data única |
| Regras de tesauro | | ordem de 30 |
| Ocorrência mínima | | 2 em vocabulário disperso |
| Filtro de relevância | | 0,60 a 0,65; nunca em palavras-chave |
| Normalização | | força de associação |
| Função de qualidade | | Constant Potts Model |
| Algoritmo | | Leiden, `n_iterations=-1` |
| Resolução | | a estável menos fragmentada |
| Execuções para a modal | | 200 |
| Frequência da modal | | reportar x de 200 |
| Sementes do teste de estabilidade | | 10, par a par |
| Limiar de estabilidade | | ARI < 0,70 reprova |
| Tamanho mínimo de cluster | | ~10% do corpus, limiar de REPORTE |
| Layout | | VOS ou Kamada-Kawai, o mesmo em todas as figuras |
| Largura de banda da densidade | | mediana da distância ao 4º vizinho × 0,70 |
| Limiar de acoplamento | | 2 referências compartilhadas |
| Resolução do acoplamento | | 0,60 |
| Peso dos termos de busca na atribuição | | 0,25 |

---

## 13. ARMADILHAS - verifique cada uma antes de entregar

Estas ocorreram de fato. Cheque uma a uma.

1. **RNG global do igraph não fixado.** Falha silenciosa. Ver 4.2 do módulo.
2. **Partição de execução única reportada como estrutura do campo.** Erro mais comum na literatura publicada.
3. **Moda tomada sem canonizar rótulos.** Partições idênticas contadas como distintas.
4. **Separador de referências cortado sem âncora no ano.** Produz fragmentos que não casam com nada.
5. **Paleta padrão vermelho/verde.** Inacessível.
6. **Termos da estratégia de busca dominando mapa e densidade sem ressalva.** Convida a ler artefato como achado.
7. **Texto do manuscrito afirmando que uma análise está pendente depois de executada.** Releia o manuscrito inteiro contra o estado final da análise, não só as seções recém-editadas.
8. **Citar documentos do corpus por identificador interno (D001) na redação final.** O identificador serve ao trabalho interno. Na redação use citação bibliográfica normal e inclua as entradas na lista de referências. Converter isso no fim é caro em extensão - orce as palavras desde o início: 30 a 40 palavras por entrada nova, mais a expansão das citações no corpo.
9. **Conferir correspondência citação/referência só pelo sobrenome.** Produz falso negativo quando o mesmo sobrenome aparece por outra obra. Case por sobrenome **e** ano, nos dois sentidos.
10. **Homônimos de autor e ano sem sufixo.** Ao acrescentar referências em bloco, verifique colisões autor-ano e propague os sufixos (2026a, 2026b, 2026c) para todas as citações no corpo.
11. **Contagem de palavras sob critério errado.** Alguns periódicos contam referências, figuras e tabelas dentro do limite (ex.: 280 palavras por figura ou tabela). Confirme o critério da revista antes de orçar cortes, e conte legendas e notas de fonte como texto na leitura estrita.
12. **Regenerar um arquivo a partir da fonte em vez de editar o arquivo que o usuário revisou.** Se o usuário editou um `.docx`, edite esse `.docx`. Regenerar descarta as correções dele.

---

## 14. CHECKLIST FINAL - não entregue sem completar

**Material de apoio contém:**

```
[ ] consulta transcrita literalmente nas duas plataformas, com mapeamento de campos
[ ] rodadas de calibracao com os totais de cada uma
[ ] controles positivos e negativos do teste de recall
[ ] regra de deduplicacao e os tres numeros da fusao
[ ] criterios de triagem, codigos de exclusao e contagem por codigo
[ ] declaracao de confiabilidade da triagem, ou de sua nao estimacao
[ ] tesauro completo
[ ] tabela de parametros da Fase 12
[ ] tabela de estabilidade com decisao explicita por configuracao
[ ] n de execucoes e frequencia da particao modal
[ ] grade de robustez da validacao cruzada
[ ] atribuicao documento a cluster
[ ] as 7 tabelas descritivas
[ ] VOSviewer_map.txt e VOSviewer_network.txt
[ ] matrizes Co.npy e S.npy
[ ] todos os scripts
```

**Corpo do artigo declara, explicitamente:**

```
[ ] que a particao reportada e modal, e sobre quantas execucoes
[ ] que a estabilidade foi testada, e com que resultado
[ ] que a convergencia entre tecnicas foi buscada, e o que devolveu
[ ] que a analise replica o metodo do VOSviewer em codigo, e nao e saida do software
[ ] as limitacoes: cobertura do acoplamento, confiabilidade da triagem, termos da busca
```

**Verificação final de consistência:**

```
[ ] todo numero do artigo tem origem rastreavel em um arquivo de saida
[ ] nenhuma afirmacao no texto contradiz o estado final da analise
[ ] toda citacao tem referencia e toda referencia e citada, casando por sobrenome E ano
[ ] as somas fecham: corpus, clusters, codigos de exclusao, bases
```

---

## 15. PRINCÍPIO ORIENTADOR

Toda escolha que poderia ter mudado o resultado precisa estar escrita, e todo resultado que dependeu de uma escolha precisa vir acompanhado do teste que mostra o quanto ele dependia dela.

Quando um teste reprovar uma análise, **reporte a reprovação**. Um descarte documentado é evidência de rigor; um descarte silencioso é o que a revisão por pares existe para encontrar.
