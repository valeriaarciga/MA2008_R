"""
=============================================================================
  MODELO DE OPTIMIZACIÓN DE PLANOGRAMA — OXXO
  Solver: Gurobi (gurobipy)
  Archivo de entrada: df_filtered.csv
=============================================================================

REQUISITOS:
  pip install gurobipy pandas numpy

USO:
  python planograma_gurobi.py
  python planograma_gurobi.py --segmento HRN --gamma 5 --tiempo 300
  python planograma_gurobi.py --heuristica-solo
  python planograma_gurobi.py --sensibilidad --heuristica-solo
=============================================================================
"""

import argparse
import time
import warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# ARGUMENTOS
# ─────────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Planograma OXXO — Gurobi MILP")
parser.add_argument("--csv",           default="df_filtered.csv")
parser.add_argument("--segmento",      default=None,             help="Filtrar por SEGMENTO_ID (ej: BCO)")
parser.add_argument("--alpha",         type=float, default=2.0,  help="Peso cambio de charola")
parser.add_argument("--beta",          type=float, default=1.0,  help="Peso cambio de posición")
parser.add_argument("--gamma",         type=float, default=3.0,  help="Premio visibilidad charola premium")
parser.add_argument("--lambda-slack",  type=float, default=10.0, dest="lam", help="Penalización sobreuso")
parser.add_argument("--delta",         type=float, default=0.5,  help="Separación entre productos (cm)")
parser.add_argument("--tiempo",        type=int,   default=1500,  help="Tiempo máximo del solver (s)")
parser.add_argument("--gap",           type=float, default=0.0, help="MIP gap de terminación (0.05 = 5%%)")
parser.add_argument("--heuristica-solo", action="store_true",    help="Solo heurística, sin MILP")
parser.add_argument("--sensibilidad",    action="store_true",    help="Análisis de sensibilidad de gamma")
parser.add_argument("--output",        default="resultado_planograma.csv")
args = parser.parse_args()

# ─────────────────────────────────────────────────────────────────────────────
# 1. CARGA Y LIMPIEZA DE DATOS
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 65)
print("  PLANOGRAMA OXXO — GUROBI OPTIMIZER")
print("=" * 65)

df = pd.read_csv(args.csv, encoding="latin-1")
df.columns = [c.encode("ascii", "ignore").decode().strip() for c in df.columns]
seg_col = next(c for c in df.columns if "SEG" in c.upper())
df.rename(columns={seg_col: "SEGMENTO_ID"}, inplace=True)

if args.segmento:
    df = df[df["SEGMENTO_ID"] == args.segmento].copy()
    print(f"\n  Segmento filtrado: {args.segmento}")

print(f"\n  Registros cargados : {len(df):,}")
print(f"  Segmentos en datos : {sorted(df['SEGMENTO_ID'].unique())}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. PARÁMETROS
# ─────────────────────────────────────────────────────────────────────────────
prod_df = (
    df.groupby("ITEM")
    .agg(
        desc        = ("ITEM_DESC",         "first"),
        c_star      = ("CHAROLA",           "median"),
        s_star      = ("UBICACION_BANDEJA", "median"),
        ancho       = ("ANCHO",             "first"),
        frentes_med = ("NUM_FRENTES",       "median"),
        frentes_min = ("NUM_FRENTES",       "min"),
        frentes_max = ("NUM_FRENTES",       "max"),
        frentes_std = ("NUM_FRENTES",       "std"),
        apariciones = ("SEGMENTO_ID",       "count"),
        k_p         = ("CHAROLA",           "nunique"),
    )
    .reset_index()
)
prod_df["v_p"]   = prod_df["apariciones"] / prod_df["apariciones"].sum()
prod_df["w_p"]   = prod_df["ancho"] * prod_df["frentes_med"]
prod_df["sigma"] = prod_df["frentes_std"].fillna(0)
prod_df          = prod_df.sort_values("ITEM").reset_index(drop=True)

charola_df = (
    df.groupby("CHAROLA")
    .agg(Width=("Width","first"), Height=("Height","first"), Y=("Y","first"))
    .reset_index()
    .sort_values("CHAROLA")
    .reset_index(drop=True)
)

P      = prod_df["ITEM"].tolist()
C      = charola_df["CHAROLA"].tolist()
W      = {r["CHAROLA"]: float(r["Width"]) for _, r in charola_df.iterrows()}
Y_c    = {r["CHAROLA"]: float(r["Y"])     for _, r in charola_df.iterrows()}
w_p    = {r["ITEM"]: float(r["w_p"])      for _, r in prod_df.iterrows()}
v_p    = {r["ITEM"]: float(r["v_p"])      for _, r in prod_df.iterrows()}
c_star = {r["ITEM"]: float(r["c_star"])   for _, r in prod_df.iterrows()}
s_star = {r["ITEM"]: float(r["s_star"])   for _, r in prod_df.iterrows()}
k_p_d  = {r["ITEM"]: int(r["k_p"])        for _, r in prod_df.iterrows()}

y70    = float(np.percentile(list(Y_c.values()), 70))
C_star = [c for c in C if Y_c[c] >= y70]

# Máximo de productos observados por charola en el histórico → define SLOTS
max_prods_charola = int(
    df.groupby(["SEGMENTO_ID","CHAROLA"])["ITEM"].nunique().max()
)
SLOTS = list(range(1, max_prods_charola + 1))   # ej. [1,2,...,8]

# Montecarlo para v_mc
np.random.seed(42)
mc_df = {}
for _, r in prod_df.iterrows():
    sim = np.random.normal(
        float(r["frentes_med"]), max(float(r["sigma"]), 1e-6), 1000
    ).clip(float(r["frentes_min"]), float(r["frentes_max"]))
    mc_df[r["ITEM"]] = float(sim.mean())

esp_total = sum(w_p.values())
cap_total = len(C) * list(W.values())[0]

print(f"\n  Productos  |P|     : {len(P)}")
print(f"  Charolas   |C|     : {len(C)}")
print(f"  Slots por charola  : {len(SLOTS)}  (máx histórico: {max_prods_charola})")
print(f"  Charolas premium C*: {C_star}  (Y_c >= {y70:.0f} cm)")
print(f"  Ancho charola (cm) : {list(W.values())[0]:.0f} cm")
print(f"  Espacio requerido  : {esp_total:.1f} cm")
print(f"  Capacidad total    : {cap_total:.0f} cm")
print(f"  Sobredemanda       : {esp_total - cap_total:.1f} cm  ({(esp_total-cap_total)/cap_total*100:.1f}%)")
print(f"  Pesos a={args.alpha} b={args.beta} g={args.gamma} l={args.lam} d={args.delta}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. HEURÍSTICA GREEDY
# ─────────────────────────────────────────────────────────────────────────────
def heuristica(P, C, C_star, W, Y_c, w_p, v_p, c_star, k_p_d,
               alpha_w, beta_w, gamma_w, delta):
    """
    Fase 1: Ordenar por score = gamma * v_p.
    Fase 2: Asignar cada producto a la charola más cercana al histórico
            con espacio disponible (holgura 5%).
    """
    t0            = time.time()
    orden         = sorted(P, key=lambda p: -gamma_w * v_p[p])
    espacio_usado = {c: 0.0 for c in C}
    asig_charola  = {}

    for p in orden:
        hist_c     = int(round(c_star[p]))
        candidatos = sorted(C, key=lambda c: abs(c - hist_c))
        placed     = False
        for c in candidatos:
            sep = delta if espacio_usado[c] > 0 else 0
            req = w_p[p] + sep
            if espacio_usado[c] + req <= W[c] * 1.05:
                espacio_usado[c] += req
                asig_charola[p]   = c
                placed            = True
                break
        if not placed:
            c_mx = max(C, key=lambda c: W[c] - espacio_usado[c])
            espacio_usado[c_mx] += w_p[p]
            asig_charola[p]      = c_mx

    Z_h = (
        alpha_w * sum(abs(asig_charola.get(p, c_star[p]) - c_star[p]) for p in P)
      - gamma_w * sum(
            v_p[p] * Y_c[asig_charola[p]]
            for p in P if asig_charola.get(p) in C_star
        )
    )
    return asig_charola, Z_h, time.time() - t0


print("\n" + "─" * 65)
print("  FASE HEURÍSTICA")
print("─" * 65)
asig_h, Z_h, t_h = heuristica(
    P, C, C_star, W, Y_c, w_p, v_p, c_star, k_p_d,
    args.alpha, args.beta, args.gamma, args.delta
)
print(f"  Z heurístico   : {Z_h:.4f}")
print(f"  Tiempo         : {t_h:.3f} s")

print(f"\n  {'Charola':>8} | {'Y_cm':>6} | {'Prods':>5} | {'Espacio (cm)':>12} | {'Premium':>7}")
print("  " + "-" * 50)
esp_h = {c: 0.0 for c in C}
cnt_h = {c: 0   for c in C}
for p, c in asig_h.items():
    esp_h[c] += w_p[p]; cnt_h[c] += 1
for c in C:
    prem = "  *" if c in C_star else ""
    print(f"  {c:>8} | {Y_c[c]:>6.1f} | {cnt_h[c]:>5} | {esp_h[c]:>12.1f} | {prem}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. ANÁLISIS DE SENSIBILIDAD (opcional)
# ─────────────────────────────────────────────────────────────────────────────
if args.sensibilidad:
    print("\n" + "─" * 65)
    print("  ANÁLISIS DE SENSIBILIDAD — GAMMA")
    print("─" * 65)
    print(f"  {'gamma':>6} | {'Z_heurístico':>14} | {'Prods en C*':>11} | {'Δ_charola prom':>14}")
    print("  " + "-" * 55)
    for g in [0, 1, 2, 3, 5, 8, 12]:
        ac_g, Z_g, _ = heuristica(
            P, C, C_star, W, Y_c, w_p, v_p, c_star, k_p_d,
            args.alpha, args.beta, g, args.delta
        )
        prems     = sum(1 for p in P if ac_g.get(p) in C_star)
        avg_delta = np.mean([abs(ac_g.get(p, c_star[p]) - c_star[p]) for p in P])
        print(f"  {g:>6} | {Z_g:>14.2f} | {prems:>11} | {avg_delta:>14.3f}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. MODELO MILP CON GUROBI
# ─────────────────────────────────────────────────────────────────────────────
if not args.heuristica_solo:
    try:
        import gurobipy as gp
        from gurobipy import GRB
    except ImportError:
        print("\n  [ERROR] gurobipy no está instalado: pip install gurobipy")
        raise SystemExit(1)

    print("\n" + "─" * 65)
    print("  MODELO MILP — GUROBI")
    print("─" * 65)

    t_milp_start = time.time()
    m = gp.Model("Planograma_OXXO")
    m.setParam("TimeLimit",  args.tiempo)
    m.setParam("MIPGap",     args.gap)
    m.setParam("OutputFlag", 1)

    # ── Variables ────────────────────────────────────────────────────────────

    # x[p,c] ∈ {0,1} — producto p asignado a charola c
    x = m.addVars(P, C, vtype=GRB.BINARY, name="x")

    # a[p,c,s] ∈ {0,1} — producto p ocupa el slot s en charola c
    # Reemplaza a pos[p,c] y a las variables z de precedencia.
    # Tamaño: 125 × 18 × 8 = 18,000 variables (manejable).
    a = m.addVars(
        [(p, c, s) for p in P for c in C for s in SLOTS],
        vtype=GRB.BINARY, name="a"
    )

    # d_ch[p] ≥ 0 — cambio absoluto de charola (linealización)
    d_ch = m.addVars(P, lb=0.0, name="d_ch")

    # d_pos[p] ≥ 0 — cambio absoluto de posición (linealización, 1 por producto)
    d_pos = m.addVars(P, lb=0.0, name="d_pos")

    # slack_c ≥ 0 — exceso de capacidad; penalizado pero no prohibido
    slack = m.addVars(C, lb=0.0, name="slack")

    m.update()
    print(f"\n  Variables creadas  : {m.NumVars:,}")

    # ── Función objetivo ─────────────────────────────────────────────────────
    #
    # Notar que d_pos ahora es 1 variable por producto (no por producto×charola)
    # porque cada producto va en exactamente 1 charola → 1 posición relevante.
    #
    obj = (
        args.alpha * gp.quicksum(d_ch[p] for p in P)
      + args.beta  * gp.quicksum(d_pos[p] for p in P)
      - args.gamma * gp.quicksum(
            v_p[p] * Y_c[c] * x[p, c]
            for p in P for c in C_star
        )
      + args.lam   * gp.quicksum(slack[c] for c in C)
    )
    m.setObjective(obj, GRB.MINIMIZE)

    # ── Restricciones ────────────────────────────────────────────────────────

    # R1 — Cada producto va en como máximo k_p charolas
    for p in P:
        m.addConstr(
            gp.quicksum(x[p, c] for c in C) <= k_p_d[p],
            name=f"R1_{p}"
        )

    # R2 — Capacidad de charola con separadores y slack
    for c in C:
        m.addConstr(
            gp.quicksum((w_p[p] + args.delta) * x[p, c] for p in P) - args.delta
            <= W[c] + slack[c],
            name=f"R2_{c}"
        )

    # R3 — Máximo de productos por charola = número de slots disponibles
    for c in C:
        m.addConstr(
            gp.quicksum(x[p, c] for p in P) <= len(SLOTS),
            name=f"R3_{c}"
        )

    # R4 — Vínculo x ↔ a: si x[p,c]=1, el producto ocupa exactamente 1 slot.
    #      Si x[p,c]=0, ningún slot está activo para ese par (p,c).
    for p in P:
        for c in C:
            # Exactamente 1 slot activo si y solo si x[p,c]=1
            m.addConstr(
                gp.quicksum(a[p, c, s] for s in SLOTS) == x[p, c],
                name=f"R4_{p}_{c}"
            )

    # R5 — UNICIDAD: cada slot puede tener máximo 1 producto en cada charola.
    #      Esta es la restricción clave que evita traslapes de posición.
    #      Solo tiene C × |SLOTS| = 18 × 8 = 144 restricciones. Muy liviana.
    for c in C:
        for s in SLOTS:
            m.addConstr(
                gp.quicksum(a[p, c, s] for p in P) <= 1,
                name=f"R5_{c}_{s}"
            )

    # R6 — Linealización del cambio de charola
    for p in P:
        charola_asig = gp.quicksum(c * x[p, c] for c in C)
        m.addConstr(d_ch[p] >= charola_asig - c_star[p], name=f"R6a_{p}")
        m.addConstr(d_ch[p] >= c_star[p] - charola_asig, name=f"R6b_{p}")

    # R7 — Linealización del cambio de posición
    #      posición asignada = Σ_c Σ_s s · a[p,c,s]
    #      d_pos[p] ≥ |posicion_asignada - s*_p|
    for p in P:
        pos_asig = gp.quicksum(s * a[p, c, s] for c in C for s in SLOTS)
        m.addConstr(d_pos[p] >= pos_asig - s_star[p], name=f"R7a_{p}")
        m.addConstr(d_pos[p] >= s_star[p] - pos_asig, name=f"R7b_{p}")

    m.update()
    print(f"  Restricciones      : {m.NumConstrs:,}")

    # ── Warm start desde la heurística ───────────────────────────────────────
    # La heurística asigna 1 charola por producto y no asigna slots,
    # así que solo inicializamos x. Gurobi completa el resto.
    print("\n  Aplicando warm start desde la heurística...")
    for p in P:
        for c in C:
            x[p, c].Start = 1.0 if asig_h.get(p) == c else 0.0

    # ── Resolver ─────────────────────────────────────────────────────────────
    print(f"\n  Tiempo límite: {args.tiempo}s  |  MIP gap: {args.gap*100:.1f}%\n")
    m.optimize()
    t_milp = time.time() - t_milp_start

    # ── Resultados ───────────────────────────────────────────────────────────
    estado_map = {
        GRB.OPTIMAL:    "Óptimo",
        GRB.TIME_LIMIT: "Límite de tiempo (solución factible)",
        GRB.INFEASIBLE: "Infactible",
        GRB.UNBOUNDED:  "No acotado",
        GRB.SUBOPTIMAL: "Subóptimo",
    }
    estado = estado_map.get(m.status, f"Código {m.status}")

    print("\n" + "─" * 65)
    print("  RESULTADOS GUROBI")
    print("─" * 65)
    print(f"  Estado           : {estado}")

    if m.status in (GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL):
        print(f"  Z óptimo         : {m.ObjVal:.4f}")
        print(f"  MIP gap          : {m.MIPGap*100:.3f}%")
        print(f"  Tiempo solver    : {t_milp:.1f}s")
        print(f"  Nodos explorados : {int(m.NodeCount):,}")

        # Extraer solución
        resultado = []
        for p in P:
            for c in C:
                if x[p, c].X > 0.5:
                    # Slot asignado = el s donde a[p,c,s] = 1
                    slot_asig = next(
                        (s for s in SLOTS if a[p, c, s].X > 0.5), 0
                    )
                    desc = prod_df.loc[prod_df["ITEM"] == p, "desc"].values[0]
                    resultado.append({
                        "ITEM":               p,
                        "descripcion":        desc[:50],
                        "charola_asignada":   c,
                        "charola_historica":  c_star[p],
                        "delta_charola":      abs(c - c_star[p]),
                        "posicion_asignada":  slot_asig,
                        "posicion_historica": s_star[p],
                        "v_p":                round(v_p[p], 6),
                        "v_mc":               round(mc_df.get(p, v_p[p]), 4),
                        "w_p_cm":             w_p[p],
                        "Y_charola_cm":       Y_c[c],
                        "es_premium":         c in C_star,
                        "slack_charola_cm":   round(slack[c].X, 2),
                    })

        res_df = pd.DataFrame(resultado)

        # Verificar unicidad de posiciones (debe ser 0 colisiones)
        colisiones = (
            res_df.groupby(["charola_asignada", "posicion_asignada"])
            .size()
            .reset_index(name="n")
        )
        n_colisiones = (colisiones["n"] > 1).sum()
        print(f"\n  Colisiones de posición : {n_colisiones}  "
              f"{'✓ Ninguna' if n_colisiones == 0 else '✗ HAY TRASLAPES'}")

        # Utilización por charola
        print("\n  Utilización de charolas:")
        print(f"  {'Charola':>8} | {'Y(cm)':>6} | {'Prods':>5} | "
              f"{'Usado(cm)':>10} | {'Slack(cm)':>9} | {'%Uso':>6} | {'Premium':>7}")
        print("  " + "-" * 65)
        for c in C:
            sub   = res_df[res_df["charola_asignada"] == c]
            n_p   = len(sub)
            usado = sub["w_p_cm"].sum() + args.delta * max(n_p - 1, 0)
            sl    = round(slack[c].X, 2)
            pct   = round(usado / W[c] * 100, 1)
            prem  = "  *" if c in C_star else ""
            print(f"  {c:>8} | {Y_c[c]:>6.1f} | {n_p:>5} | "
                  f"{usado:>10.1f} | {sl:>9.2f} | {pct:>5.1f}% | {prem}")

        # Comparación con heurística
        print("\n  Comparación MILP vs Heurística:")
        print(f"  {'Métrica':<30} | {'MILP':>12} | {'Heurística':>12}")
        print("  " + "-" * 60)
        print(f"  {'Z (función objetivo)':<30} | {m.ObjVal:>12.4f} | {Z_h:>12.4f}")
        print(f"  {'Tiempo (s)':<30} | {t_milp:>12.1f} | {t_h:>12.3f}")
        print(f"  {'Δ_charola promedio':<30} | "
              f"{res_df['delta_charola'].mean():>12.3f} | "
              f"{np.mean([abs(asig_h.get(p, c_star[p]) - c_star[p]) for p in P]):>12.3f}")
        print(f"  {'Prods en charola premium':<30} | "
              f"{int(res_df['es_premium'].sum()):>12} | "
              f"{sum(1 for p in P if asig_h.get(p) in C_star):>12}")
        print(f"  {'Colisiones de posición':<30} | {n_colisiones:>12} | {'N/A':>12}")

        # Top productos por cambio de charola
        print("\n  Productos con mayor cambio de charola (top 8):")
        top_delta = res_df.nlargest(8, "delta_charola")[
            ["descripcion", "charola_historica", "charola_asignada",
             "delta_charola", "v_p", "es_premium"]
        ]
        print(top_delta.to_string(index=False))

        # Alta demanda en premium
        print("\n  Alta demanda en charolas premium (top 8):")
        top_prem = res_df[res_df["es_premium"]].nlargest(8, "v_p")[
            ["descripcion", "charola_asignada", "posicion_asignada",
             "Y_charola_cm", "v_p"]
        ]
        print(top_prem.to_string(index=False))

        # Guardar CSV
        res_df.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"\n  Resultados guardados en: {args.output}")

    elif m.status == GRB.INFEASIBLE:
        print("\n  [!] Modelo infactible. Calculando IIS...")
        m.computeIIS()
        m.write("infactible.ilp")
        print("  IIS guardado en: infactible.ilp")

print("\n" + "=" * 65)
print("  FIN DE LA EJECUCIÓN")
print("=" * 65)
