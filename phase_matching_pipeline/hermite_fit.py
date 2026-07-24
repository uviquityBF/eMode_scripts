"""Low-order polynomial surface fitting via Hermite-style least squares (value + local gradient at
each sample point) -- used by General_PhaseMatching_Pipeline.ipynb's Step 7 (n(WL,h,w), WL_pm(h,w))
and Step 9 (overlap(h,w)) surfaces. Generic: pure numpy/math, no EMode dependency.
"""

import itertools

import numpy as np


def poly_terms(n_vars, degree):
    """All exponent-tuples (monomials) in n_vars variables with total degree <= `degree`."""
    terms = []
    for total in range(degree + 1):
        for exps in itertools.product(range(total + 1), repeat=n_vars):
            if sum(exps) == total:
                terms.append(exps)
    return terms


def _eval_monomial(exps, point):
    v = 1.0
    for e, x in zip(exps, point):
        v *= x ** e
    return v


def _eval_monomial_deriv(exps, point, var_idx):
    e = exps[var_idx]
    if e == 0:
        return 0.0
    new_exps = list(exps)
    new_exps[var_idx] -= 1
    v = float(e)
    for ee, x in zip(new_exps, point):
        v *= x ** ee
    return v


class PolyFit:
    """A low-order polynomial surface fit, solved in centered/scaled coordinates for conditioning
    but callable directly in original units: fit(wl, h, w) -> predicted value."""

    def __init__(self, var_names, terms, coeffs, centers, scales, rms_value_residual):
        self.var_names = var_names
        self.terms = terms
        self.coeffs = coeffs
        self.centers = centers
        self.scales = scales
        self.rms_value_residual = rms_value_residual

    def __call__(self, *point):
        p_norm = tuple((x - c) / s for x, c, s in zip(point, self.centers, self.scales))
        return sum(c * _eval_monomial(t, p_norm) for c, t in zip(self.coeffs, self.terms))

    def summary(self):
        lines = [f"fit RMS residual on values: {self.rms_value_residual:.3e}"]
        for t, c in zip(self.terms, self.coeffs):
            factors = '*'.join(f"{n}'^{e}" for n, e in zip(self.var_names, t) if e > 0) or '1'
            lines.append(f"  {c:+.6g} * {factors}")
        lines.append("  (primed variables are normalized: x' = (x - center) / scale)")
        for n, c, s in zip(self.var_names, self.centers, self.scales):
            lines.append(f"  {n}: center={c:.4g}, scale={s:.4g}")
        return '\n'.join(lines)


def fit_hermite_polynomial(samples, degree, var_names):
    """samples: list of {'point': (x1,...,xn), 'value': f, 'grad': (df/dx1,...,df/dxn) or None}.
    Least-squares fit against BOTH the value and the known local gradient at every sample point --
    pass grad=None (or omit the key) for a sample to fall back to a value-only equation.
    """
    n_vars = len(samples[0]['point'])
    points = np.array([s['point'] for s in samples], dtype=float)
    centers = points.mean(axis=0)
    scales = points.std(axis=0)
    scales[scales == 0] = 1.0

    terms = poly_terms(n_vars, degree)
    rows, targets = [], []
    for s in samples:
        p_norm = tuple((x - c) / sc for x, c, sc in zip(s['point'], centers, scales))
        rows.append([_eval_monomial(t, p_norm) for t in terms])
        targets.append(s['value'])
        grad = s.get('grad')
        if grad is not None:
            for var_idx, g in enumerate(grad):
                if g is None:
                    continue
                # chain rule: d/dx'_i = scale_i * d/dx_i, since x_i = center_i + scale_i * x'_i
                rows.append([_eval_monomial_deriv(t, p_norm, var_idx) for t in terms])
                targets.append(g * scales[var_idx])

    A = np.array(rows)
    b = np.array(targets)
    coeffs, *_ = np.linalg.lstsq(A, b, rcond=None)

    value_rows = np.array([[_eval_monomial(t, tuple((x - c) / sc for x, c, sc in zip(s['point'], centers, scales)))
                             for t in terms] for s in samples])
    value_targets = np.array([s['value'] for s in samples])
    rms_value_residual = float(np.sqrt(np.mean((value_rows @ coeffs - value_targets) ** 2)))

    return PolyFit(var_names, terms, coeffs, centers, scales, rms_value_residual)


def _poly_add(p1, p2):
    out = dict(p1)
    for k, v in p2.items():
        out[k] = out.get(k, 0.0) + v
    return out


def _poly_scale(p, s):
    return {k: v * s for k, v in p.items()}


def _poly_mul(p1, p2):
    out = {}
    for k1, v1 in p1.items():
        for k2, v2 in p2.items():
            k = tuple(a + b for a, b in zip(k1, k2))
            out[k] = out.get(k, 0.0) + v1 * v2
    return out


def _affine_var_power(n_vars, var_idx, center, scale, power):
    """Polynomial (in raw units) for ((x_i - center) / scale)^power."""
    zero = tuple(0 for _ in range(n_vars))
    one_hot = tuple(1 if j == var_idx else 0 for j in range(n_vars))
    base = {one_hot: 1.0 / scale, zero: -center / scale}
    result = {zero: 1.0}
    for _ in range(power):
        result = _poly_mul(result, base)
    return result


def raw_unit_terms(fit):
    """Expand a PolyFit's normalized-coordinate fit into a {exponent_tuple: coeff} polynomial in
    the ORIGINAL units (e.g. plain w, h, WL in nm) -- exact, not a re-fit, so it carries no new
    numerical error (verified to agree with PolyFit.__call__ to ~1e-14)."""
    n_vars = len(fit.var_names)
    zero = tuple(0 for _ in range(n_vars))
    raw = {}
    for term_exps, coeff in zip(fit.terms, fit.coeffs):
        monomial = {zero: 1.0}
        for var_idx, e in enumerate(term_exps):
            if e == 0:
                continue
            monomial = _poly_mul(monomial, _affine_var_power(n_vars, var_idx, fit.centers[var_idx],
                                                               fit.scales[var_idx], e))
        raw = _poly_add(raw, _poly_scale(monomial, coeff))
    return raw


def format_formula(fit, lhs):
    """Human-readable 'lhs(vars) = ...' string in raw (original) units, highest-degree terms first."""
    raw = raw_unit_terms(fit)
    ordered = sorted(raw.items(), key=lambda kv: (-sum(kv[0]), kv[0]))
    parts = []
    for exps, coeff in ordered:
        factors = ''.join(f"*{n}" if e == 1 else f"*{n}^{e}" for n, e in zip(fit.var_names, exps) if e > 0)
        parts.append(f"{coeff:+.6g}{factors}")
    return f"{lhs} = " + " ".join(parts)
