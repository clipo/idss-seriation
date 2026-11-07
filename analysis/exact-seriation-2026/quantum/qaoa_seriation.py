#!/usr/bin/env python3
"""
qaoa_seriation.py

Frequency seriation as a QAOA problem, for IBM Quantum (Qiskit 2.x).

Purpose
-------
A methods demonstration for small problems (4 assemblages, possibly 5).
The script:
  1. Reads a frequency table (rows = assemblages, columns = types).
  2. Enumerates every ordering classically and lists the orderings in which
     every type has a unimodal frequency distribution (the reference answer).
  3. Builds a cost Hamiltonian whose lowest-energy states are those orderings.
  4. Optimizes QAOA angles on a local statevector simulator.
  5. Samples the optimized circuit locally, and optionally on IBM hardware.
  6. Reports how much of the sampled probability falls on valid seriations,
     compared with the brute-force reference.

Encoding
--------
Binary variable x[i,p] = 1 if assemblage i occupies position p.
Qubit index q = i*n + p, so n assemblages use n*n qubits.

Cost = A * (one-hot penalties)  +  sum over position triples a<b<c and
       distinct assemblages i,j,k of  V(i,j,k) * x[i,a] x[j,b] x[k,c]

V(i,j,k) = sum over types t of max(0, min(f[i,t], f[k,t]) - f[j,t] - tol)

V > 0 when assemblage j, placed between i and k, has a frequency below both
neighbours for some type (a violation of unimodality). A sequence is
unimodal exactly when no such triple exists, so a permutation has zero
unimodality cost if and only if it is a valid frequency seriation (within
tolerance tol, in proportion units).

The triple terms are cubic. QAOA in Qiskit accepts cubic Z-terms directly,
so no ancilla qubits are needed; the cost is deeper circuits.

Usage
-----
  python qaoa_seriation.py                      # synthetic test data, simulator
  python qaoa_seriation.py --csv mydata.csv     # your data (counts or proportions)
  python qaoa_seriation.py --reps 3 --starts 8  # deeper QAOA, more restarts
  python qaoa_seriation.py --ibm                # also run on least-busy IBM QPU
  python qaoa_seriation.py --ibm --backend ibm_torino

CSV format: first column = assemblage name, remaining columns = type counts.
Rows are converted to proportions.
"""

import argparse
import itertools
import json
import math
import sys
import time

import numpy as np
from scipy.optimize import minimize

from qiskit.circuit.library import qaoa_ansatz
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit.quantum_info import SparsePauliOp


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def synthetic_data():
    """Synthetic 4 x 4 table. NOT archaeological data; for testing only.

    Constructed so that the order D3, D1, D4, D2 (or its reverse) gives
    unimodal frequencies for all four types. Rows are listed out of order.
    """
    names = ["D1", "D2", "D3", "D4"]
    counts = np.array([
        [30, 50, 15,  5],   # D1  (position 2 in the true order)
        [ 2, 13, 35, 50],   # D2  (position 4)
        [60, 30,  8,  2],   # D3  (position 1)
        [10, 40, 35, 15],   # D4  (position 3)
    ], dtype=float)
    return names, counts


def read_csv(path):
    import csv
    names, rows = [], []
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        for r in reader:
            if not r or not r[0].strip():
                continue
            names.append(r[0].strip())
            rows.append([float(v) for v in r[1:]])
    return names, np.array(rows, dtype=float), header[1:]


def to_proportions(counts):
    totals = counts.sum(axis=1, keepdims=True)
    if np.any(totals == 0):
        sys.exit("Error: an assemblage has zero total count.")
    return counts / totals


# ---------------------------------------------------------------------------
# Classical reference
# ---------------------------------------------------------------------------

def violation(f, i, j, k, tol):
    """Unimodality violation when j sits between i and k."""
    return float(np.maximum(0.0, np.minimum(f[i], f[k]) - f[j] - tol).sum())


def ordering_violation(f, order, tol):
    total = 0.0
    for a, b, c in itertools.combinations(range(len(order)), 3):
        total += violation(f, order[a], order[b], order[c], tol)
    return total


def brute_force(f, tol):
    n = f.shape[0]
    results = []
    for perm in itertools.permutations(range(n)):
        results.append((perm, ordering_violation(f, perm, tol)))
    return results


# ---------------------------------------------------------------------------
# Hamiltonian construction
# ---------------------------------------------------------------------------

def qidx(i, p, n):
    return i * n + p


def add_term(poly, variables, coef):
    key = frozenset(variables)  # x^2 = x for binary variables
    poly[key] = poly.get(key, 0.0) + coef


def build_polynomial(f, tol, penalty):
    """Binary polynomial {frozenset(qubits): coefficient}."""
    n = f.shape[0]
    poly = {}

    # One-hot penalties: penalty * (1 - sum x)^2 = penalty * (1 - sum x + 2 sum_{u<v} x_u x_v)
    groups = []
    for i in range(n):
        groups.append([qidx(i, p, n) for p in range(n)])   # each assemblage once
    for p in range(n):
        groups.append([qidx(i, p, n) for i in range(n)])   # each position once
    for g in groups:
        add_term(poly, [], penalty)
        for u in g:
            add_term(poly, [u], -penalty)
        for u, v in itertools.combinations(g, 2):
            add_term(poly, [u, v], 2.0 * penalty)

    # Unimodality: cubic terms
    for a, b, c in itertools.combinations(range(n), 3):
        for i, j, k in itertools.permutations(range(n), 3):
            v = violation(f, i, j, k, tol)
            if v > 0:
                add_term(poly, [qidx(i, a, n), qidx(j, b, n), qidx(k, c, n)], v)
    return poly


def polynomial_to_pauli(poly, num_qubits):
    """Map x_q = (1 - Z_q)/2 and expand products into Z-strings.

    Returns (SparsePauliOp without identity term, constant offset).
    """
    terms = {}
    for variables, coef in poly.items():
        vs = sorted(variables)
        k = len(vs)
        scale = coef / (2 ** k)
        for r in range(k + 1):
            for subset in itertools.combinations(vs, r):
                terms[subset] = terms.get(subset, 0.0) + scale * ((-1) ** r)
    offset = terms.pop((), 0.0)
    labels, coefs = [], []
    for subset, c in terms.items():
        if abs(c) < 1e-12:
            continue
        labels.append(("Z" * len(subset), list(subset), c))
    op = SparsePauliOp.from_sparse_list(labels, num_qubits=num_qubits).simplify()
    return op, offset


# ---------------------------------------------------------------------------
# Decoding
# ---------------------------------------------------------------------------

def decode(bitstring, n):
    """Qiskit bitstrings are little-endian: qubit 0 is the rightmost character.

    Returns a tuple order (assemblage index at each position) or None if the
    bitstring is not a valid permutation matrix.
    """
    bits = bitstring[::-1]
    x = np.array([int(b) for b in bits]).reshape(n, n)  # x[i, p]
    if not (np.all(x.sum(axis=0) == 1) and np.all(x.sum(axis=1) == 1)):
        return None
    order = [None] * n
    for i in range(n):
        order[int(np.argmax(x[i]))] = i
    return tuple(order)


def summarize_counts(counts, f, n, tol, names, valid_set, label, top=10):
    shots = sum(counts.values())
    perm_mass, valid_mass = 0.0, 0.0
    by_order = {}
    for bs, c in counts.items():
        order = decode(bs, n)
        if order is None:
            continue
        perm_mass += c
        by_order[order] = by_order.get(order, 0) + c
        if order in valid_set:
            valid_mass += c
    print(f"\n=== {label}: {shots} shots ===")
    print(f"  Fraction of shots that are valid permutations : {perm_mass / shots:.4f}")
    print(f"  Fraction of shots that are valid seriations   : {valid_mass / shots:.4f}")
    print(f"  Top sampled permutations:")
    ranked = sorted(by_order.items(), key=lambda kv: -kv[1])[:top]
    for order, c in ranked:
        v = ordering_violation(f, order, tol)
        tag = "VALID" if order in valid_set else ""
        seq = " - ".join(names[i] for i in order)
        print(f"    {c / shots:7.4f}  violation={v:.4f}  {seq}  {tag}")
    found = {o for o in by_order if o in valid_set}
    print(f"  Valid seriations observed: {len(found)} of {len(valid_set)}")
    return {
        "shots": shots,
        "perm_fraction": perm_mass / shots,
        "valid_fraction": valid_mass / shots,
        "valid_found": len(found),
        "valid_total": len(valid_set),
        "top": [[" - ".join(names[i] for i in o), c / shots] for o, c in ranked],
    }


# ---------------------------------------------------------------------------
# QAOA optimization (local)
# ---------------------------------------------------------------------------

def optimize_qaoa(cost_op, reps, starts, seed, maxiter):
    ansatz = qaoa_ansatz(cost_op, reps=reps)
    estimator = StatevectorEstimator()
    rng = np.random.default_rng(seed)
    best = None
    for s in range(starts):
        x0 = np.concatenate([rng.uniform(0, np.pi, reps),        # betas
                             rng.uniform(0, 2 * np.pi, reps)])   # gammas
        # Parameter order in the ansatz is alphabetical: beta[...], gamma[...]
        def energy(theta):
            res = estimator.run([(ansatz, cost_op, theta)]).result()
            return float(res[0].data.evs)
        t0 = time.time()
        out = minimize(energy, x0, method="COBYLA", options={"maxiter": maxiter})
        print(f"  start {s + 1}/{starts}: energy={out.fun:.5f}  "
              f"({out.nfev} evaluations, {time.time() - t0:.1f}s)")
        if best is None or out.fun < best.fun:
            best = out
    return ansatz, best


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", help="frequency table (name, type1, type2, ...)")
    ap.add_argument("--tol", type=float, default=0.0,
                    help="tolerance in proportion units before a dip counts as a violation")
    ap.add_argument("--reps", type=int, default=2, help="QAOA layers (p)")
    ap.add_argument("--starts", type=int, default=4, help="random restarts for optimizer")
    ap.add_argument("--maxiter", type=int, default=300, help="COBYLA iterations per start")
    ap.add_argument("--shots", type=int, default=4096)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--ibm", action="store_true", help="also sample on IBM hardware")
    ap.add_argument("--backend", help="IBM backend name (default: least busy)")
    ap.add_argument("--out", default="qaoa_seriation_results.json")
    args = ap.parse_args()

    if args.csv:
        names, counts, _ = read_csv(args.csv)
    else:
        names, counts = synthetic_data()
        print("Using SYNTHETIC test data (not archaeological). Use --csv for real data.")
    f = to_proportions(counts)
    n = len(names)
    nq = n * n
    if n > 5:
        sys.exit(f"Error: {n} assemblages need {nq} qubits plus very deep circuits. "
                 "Use 4 or 5 assemblages for this demonstration.")
    if n == 5:
        print("Warning: 5 assemblages = 25 qubits. Local statevector optimization "
              "needs about 0.5 GB per state and will be slow.")

    # 1. Classical reference
    print(f"\nAssemblages: {n}   Types: {f.shape[1]}   Qubits: {nq}   tol={args.tol}")
    bf = brute_force(f, args.tol)
    valid = [p for p, v in bf if v <= 1e-12]
    max_v = max(v for _, v in bf)
    print(f"Brute force: {math.factorial(n)} orderings, {len(valid)} valid seriations "
          f"(includes reversals)")
    for p in valid:
        print("   ", " - ".join(names[i] for i in p))
    if not valid:
        print("No perfect seriation exists at this tolerance. QAOA will target the "
              "minimum-violation orderings; consider raising --tol.")
        min_v = min(v for _, v in bf)
        valid = [p for p, v in bf if abs(v - min_v) <= 1e-12]
    valid_set = set(valid)

    # 2. Hamiltonian
    # The one-hot penalty must exceed any reduction in unimodality cost that
    # breaking the permutation structure could produce.
    penalty = max(1.0, 1.5 * max_v)
    poly = build_polynomial(f, args.tol, penalty)
    cost_op, offset = polynomial_to_pauli(poly, nq)
    scale = float(np.max(np.abs(cost_op.coeffs.real)))
    cost_op = SparsePauliOp(cost_op.paulis, cost_op.coeffs.real / scale)
    n3 = sum(1 for p in cost_op.paulis if sum(p.z) == 3)
    print(f"\nCost operator: {len(cost_op)} Pauli terms ({n3} three-qubit terms), "
          f"penalty={penalty:.3f}")

    # Sanity check: valid seriations must be ground states of the polynomial
    def poly_value(order):
        x = np.zeros(nq, dtype=int)
        for p, i in enumerate(order):
            x[qidx(i, p, n)] = 1
        return sum(c * all(x[q] for q in vs) for vs, c in poly.items())
    vals = sorted(poly_value(p) for p, _ in bf)
    assert abs(poly_value(valid[0]) - vals[0]) < 1e-9, "encoding check failed"
    print("Encoding check passed: valid seriations are minimum-cost permutations.")

    # 3. Optimize locally
    print(f"\nOptimizing QAOA (reps={args.reps}) on local statevector simulator ...")
    ansatz, best = optimize_qaoa(cost_op, args.reps, args.starts, args.seed, args.maxiter)
    theta = best.x
    print(f"Best energy (scaled): {best.fun:.5f}")

    # 4. Sample locally
    circ = ansatz.copy()
    circ.measure_all()
    sampler = StatevectorSampler(seed=args.seed)
    res = sampler.run([(circ, theta)], shots=args.shots).result()
    local_counts = res[0].data.meas.get_counts()

    # Baseline: uniform random bitstrings
    n_valid_bits = len(valid_set)
    print(f"\nBaseline (uniform random bitstrings): P(valid seriation) = "
          f"{n_valid_bits / 2 ** nq:.2e}; P(any permutation) = {math.factorial(n) / 2 ** nq:.2e}")
    results = {
        "names": names, "tol": args.tol, "reps": args.reps, "qubits": nq,
        "valid_seriations": [" - ".join(names[i] for i in p) for p in valid],
        "parameters": theta.tolist(),
        "local": summarize_counts(local_counts, f, n, args.tol, names, valid_set,
                                  "Local simulator"),
    }

    # 5. IBM hardware
    if args.ibm:
        from qiskit.transpiler import generate_preset_pass_manager
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

        service = QiskitRuntimeService()  # uses saved account credentials
        backend = (service.backend(args.backend) if args.backend
                   else service.least_busy(operational=True, simulator=False,
                                           min_num_qubits=nq))
        print(f"\nIBM backend: {backend.name}")
        pm = generate_preset_pass_manager(optimization_level=3, backend=backend,
                                          seed_transpiler=args.seed)
        isa = pm.run(circ)
        ops = isa.count_ops()
        twoq = sum(v for k, v in ops.items() if k in ("cz", "ecr", "cx"))
        print(f"Transpiled circuit: depth={isa.depth()}, two-qubit gates={twoq}")
        if twoq > 2000:
            print("Note: this many two-qubit gates exceeds what current devices run "
                  "with useful fidelity. Expect results near random noise.")
        hw_sampler = SamplerV2(mode=backend)
        hw_sampler.options.default_shots = args.shots
        hw_sampler.options.dynamical_decoupling.enable = True
        hw_sampler.options.twirling.enable_gates = True
        job = hw_sampler.run([(isa, theta)])
        print(f"Submitted job {job.job_id()}; waiting in queue ...")
        hw_counts = job.result()[0].data.meas.get_counts()
        results["ibm"] = summarize_counts(hw_counts, f, n, args.tol, names, valid_set,
                                          f"IBM {backend.name}")
        results["ibm"].update({"backend": backend.name, "job_id": job.job_id(),
                               "depth": isa.depth(), "two_qubit_gates": twoq})

    with open(args.out, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nResults written to {args.out}")


if __name__ == "__main__":
    main()
