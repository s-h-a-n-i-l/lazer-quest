from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import display

try:
    from scipy.special import fresnel as scipy_fresnel
    SCIPY_AVAILABLE = True
except Exception:
    scipy_fresnel = None
    SCIPY_AVAILABLE = False


plt.rcParams.update(
    {
        "figure.dpi": 140,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "legend.fontsize": 8,
        "font.size": 10,
        "lines.linewidth": 1.8,
    }
)


def clean_numeric(value):
    if value is None:
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = str(value).strip()
    if text == "":
        return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan


def normalize_text(value):
    if value is None:
        return ""
    if isinstance(value, (float, np.floating)) and np.isnan(value):
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"[\u2010-\u2015\u2212]", "-", text)
    return re.sub(r"\s+", " ", text)


def detect_unit(text):
    t = normalize_text(text)
    for unit in ("mm", "cm", "m"):
        if re.search(rf"(^|[^a-z]){unit}([^a-z]|$)", t):
            return unit
    return None


def unit_factor_to_m(unit):
    if unit is None:
        return np.nan
    mapping = {"m": 1.0, "cm": 1e-2, "mm": 1e-3}
    key = unit.strip().lower()
    if key not in mapping:
        raise ValueError(f"Unsupported unit: {unit}")
    return mapping[key]


def extract_notes_entries(notes_df):
    rows = []
    for _, row in notes_df.iterrows():
        label_raw = row.iloc[0]
        if not isinstance(label_raw, str):
            continue
        label_norm = normalize_text(label_raw)
        if label_norm in {"", "transcribed notes", "general", "magnification", "divergence method", "transcription note"}:
            continue

        numeric_vals = []
        detail_parts = []
        for value in row.iloc[1:]:
            num = clean_numeric(value)
            if np.isfinite(num):
                numeric_vals.append(float(num))
            elif isinstance(value, str) and value.strip():
                detail_parts.append(value.strip())

        detail_text = " ".join(detail_parts)
        unit = detect_unit(label_norm + " " + detail_text)
        nominal = numeric_vals[0] if len(numeric_vals) >= 1 else np.nan
        uncertainty = numeric_vals[1] if len(numeric_vals) >= 2 else np.nan

        factor = unit_factor_to_m(unit) if unit else np.nan
        nominal_m = nominal * factor if np.isfinite(nominal) and np.isfinite(factor) else np.nan
        uncertainty_m = uncertainty * factor if np.isfinite(uncertainty) and np.isfinite(factor) else np.nan

        rows.append(
            {
                "label_raw": label_raw,
                "label_norm": label_norm,
                "value": nominal,
                "uncertainty": uncertainty,
                "unit": unit,
                "value_m": nominal_m,
                "uncertainty_m": uncertainty_m,
                "detail_text": detail_text,
            }
        )

    return pd.DataFrame(rows)


def require_entry(entries_df, include_terms, exclude_terms=None):
    subset = entries_df.copy()
    for term in include_terms:
        subset = subset[subset["label_norm"].str.contains(re.escape(term), na=False)]
    if exclude_terms:
        for term in exclude_terms:
            subset = subset[~subset["label_norm"].str.contains(re.escape(term), na=False)]
    if subset.empty:
        raise KeyError(f"Could not find Notes entry with include_terms={include_terms} exclude_terms={exclude_terms}")
    return subset.iloc[0]


def parse_main_measurements(main_df):
    header_idx = None
    for i in range(len(main_df)):
        first = normalize_text(main_df.iloc[i, 0])
        if "track position" in first and "cm" in first:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Could not locate Main Data header row.")

    header = [normalize_text(v) for v in main_df.iloc[header_idx, :6].tolist()]
    data = main_df.iloc[header_idx + 1 :, :6].copy()
    data.columns = header

    col_map = {}
    for col in data.columns:
        text = normalize_text(col)
        if "track position uncertainty" in text:
            col_map["track_position_unc_cm"] = col
        elif "track position" in text and "uncertainty" not in text:
            col_map["track_position_cm"] = col
        elif "3-4" in text:
            col_map["dy34_cm"] = col
        elif "2-3" in text:
            col_map["dy23_cm"] = col
        elif "1-2" in text and "distance" in text:
            col_map["dy12_cm"] = col
        elif "approx" in text and "error" in text:
            col_map["dy_unc_cm"] = col

    required = ["track_position_cm", "track_position_unc_cm", "dy12_cm", "dy23_cm", "dy34_cm"]
    missing = [k for k in required if k not in col_map]
    if missing:
        raise ValueError(f"Missing required Main Data columns: {missing}")

    cleaned = pd.DataFrame({key: pd.to_numeric(data[src], errors="coerce") for key, src in col_map.items()})
    if "dy_unc_cm" not in cleaned.columns:
        cleaned["dy_unc_cm"] = np.nan

    mask = cleaned[required].notna().all(axis=1)
    return cleaned.loc[mask].reset_index(drop=True)
def compute_diameter_ratio_magnification(screen_value, screen_unc, screen_unit, lens_value, lens_unc, lens_unit):
    d_screen_m = screen_value * unit_factor_to_m(screen_unit)
    d_lens_m = lens_value * unit_factor_to_m(lens_unit)
    M = d_screen_m / d_lens_m

    rel_terms = []
    if np.isfinite(screen_unc) and screen_value > 0:
        rel_terms.append((screen_unc / screen_value) ** 2)
    if np.isfinite(lens_unc) and lens_value > 0:
        rel_terms.append((lens_unc / lens_value) ** 2)

    M_sigma = abs(M) * math.sqrt(sum(rel_terms)) if rel_terms else np.nan
    return M, M_sigma


def compute_thin_lens_magnification(thin_inputs):
    if not isinstance(thin_inputs, dict) or len(thin_inputs) == 0:
        return {"available": False, "reason": "No thin_lens_inputs provided."}

    def _finite(x):
        return isinstance(x, (int, float, np.integer, np.floating)) and np.isfinite(float(x))

    u = float(thin_inputs["u_m"]) if _finite(thin_inputs.get("u_m")) else np.nan
    v = float(thin_inputs["v_m"]) if _finite(thin_inputs.get("v_m")) else np.nan
    f = float(thin_inputs["f_m"]) if _finite(thin_inputs.get("f_m")) else np.nan

    u_sigma = float(thin_inputs.get("u_sigma_m", np.nan)) if _finite(thin_inputs.get("u_sigma_m")) else np.nan
    v_sigma = float(thin_inputs.get("v_sigma_m", np.nan)) if _finite(thin_inputs.get("v_sigma_m")) else np.nan
    f_sigma = float(thin_inputs.get("f_sigma_m", np.nan)) if _finite(thin_inputs.get("f_sigma_m")) else np.nan

    if np.isfinite(u) and np.isfinite(v) and u > 0 and v > 0:
        M = v / u
        rel_terms = []
        if np.isfinite(u_sigma) and u > 0:
            rel_terms.append((u_sigma / u) ** 2)
        if np.isfinite(v_sigma) and v > 0:
            rel_terms.append((v_sigma / v) ** 2)
        M_sigma = abs(M) * math.sqrt(sum(rel_terms)) if rel_terms else np.nan
        return {"available": True, "method": "u_v", "M": M, "M_sigma": M_sigma}

    if np.isfinite(f) and np.isfinite(u) and f > 0 and u > 0 and abs(u - f) > 1e-12:
        M = f / (u - f)
        dM_du = -f / (u - f) ** 2
        dM_df = u / (u - f) ** 2
        terms = []
        if np.isfinite(u_sigma):
            terms.append((dM_du * u_sigma) ** 2)
        if np.isfinite(f_sigma):
            terms.append((dM_df * f_sigma) ** 2)
        M_sigma = math.sqrt(sum(terms)) if terms else np.nan
        return {"available": True, "method": "f_u", "M": M, "M_sigma": M_sigma}

    if np.isfinite(f) and np.isfinite(v) and f > 0 and v > 0:
        M = (v - f) / f
        dM_dv = 1.0 / f
        dM_df = -v / (f ** 2)
        terms = []
        if np.isfinite(v_sigma):
            terms.append((dM_dv * v_sigma) ** 2)
        if np.isfinite(f_sigma):
            terms.append((dM_df * f_sigma) ** 2)
        M_sigma = math.sqrt(sum(terms)) if terms else np.nan
        return {"available": True, "method": "f_v", "M": M, "M_sigma": M_sigma}

    return {"available": False, "reason": "Incomplete thin-lens geometry; provide u and v, or f with u/v."}


def fresnel_cs_numpy(v):
    v = np.asarray(v, dtype=float)
    if np.any(v < 0):
        raise ValueError("fresnel_cs_numpy expects v >= 0")
    C = np.zeros_like(v)
    S = np.zeros_like(v)
    if v.size <= 1:
        return C, S

    phase = 0.5 * np.pi * v * v
    cos_phase = np.cos(phase)
    sin_phase = np.sin(phase)
    dv = np.diff(v)

    C[1:] = np.cumsum(0.5 * (cos_phase[1:] + cos_phase[:-1]) * dv)
    S[1:] = np.cumsum(0.5 * (sin_phase[1:] + sin_phase[:-1]) * dv)
    return C, S


def fresnel_cs(v, use_scipy=True):
    vv = np.asarray(v, dtype=float)
    if use_scipy and SCIPY_AVAILABLE:
        S, C = scipy_fresnel(vv)
        return C, S, "scipy.special.fresnel"
    C, S = fresnel_cs_numpy(vv)
    return C, S, "numpy_trapezoid"


def fresnel_intensity(v, use_scipy=True):
    C, S, method = fresnel_cs(v, use_scipy=use_scipy)
    I = (0.5 + C) ** 2 + (0.5 + S) ** 2
    return I, C, S, method


def find_local_minima(v, y, n_min=4, v_threshold=0.05):
    v = np.asarray(v, dtype=float)
    y = np.asarray(y, dtype=float)
    if v.size < 3:
        return pd.DataFrame(columns=["v_min", "I_min"])

    candidate_idx = np.where((y[1:-1] < y[:-2]) & (y[1:-1] <= y[2:]))[0] + 1
    candidate_idx = [idx for idx in candidate_idx if v[idx] > v_threshold]

    minima = []
    for idx in candidate_idx:
        if idx <= 0 or idx >= len(v) - 1:
            continue
        x_triplet = v[idx - 1 : idx + 2]
        y_triplet = y[idx - 1 : idx + 2]
        v_refined = v[idx]
        I_refined = y[idx]

        coeff = np.polyfit(x_triplet, y_triplet, 2)
        if coeff[0] > 0:
            x0 = -coeff[1] / (2 * coeff[0])
            if x_triplet[0] <= x0 <= x_triplet[-1]:
                v_refined = x0
                I_refined = np.polyval(coeff, x0)

        minima.append({"v_min": float(v_refined), "I_min": float(I_refined)})
        if len(minima) >= n_min:
            break

    return pd.DataFrame(minima)
def weighted_linear_fit(x, y, y_sigma):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    y_sigma = np.asarray(y_sigma, dtype=float)

    mask = np.isfinite(x) & np.isfinite(y) & np.isfinite(y_sigma) & (y_sigma > 0)
    x = x[mask]
    y = y[mask]
    y_sigma = y_sigma[mask]

    if x.size < 2:
        raise ValueError("Need at least two valid points for weighted linear fit.")

    w = 1.0 / (y_sigma ** 2)
    S = np.sum(w)
    Sx = np.sum(w * x)
    Sy = np.sum(w * y)
    Sxx = np.sum(w * x * x)
    Sxy = np.sum(w * x * y)

    Delta = S * Sxx - Sx * Sx
    if Delta <= 0:
        raise ValueError("Degenerate weighted fit system.")

    slope = (S * Sxy - Sx * Sy) / Delta
    intercept = (Sxx * Sy - Sx * Sxy) / Delta
    slope_stderr = math.sqrt(S / Delta)
    intercept_stderr = math.sqrt(Sxx / Delta)

    y_hat = slope * x + intercept
    y_bar_w = np.sum(w * y) / np.sum(w)
    ss_res = np.sum(w * (y - y_hat) ** 2)
    ss_tot = np.sum(w * (y - y_bar_w) ** 2)
    r2 = np.nan if ss_tot <= 0 else 1.0 - ss_res / ss_tot

    dof = max(int(x.size - 2), 1)
    chi2_red = ss_res / dof
    x_fit = np.linspace(np.min(x), np.max(x), 200)
    y_fit = slope * x_fit + intercept

    return {
        "x": x,
        "y": y,
        "y_sigma": y_sigma,
        "slope": float(slope),
        "intercept": float(intercept),
        "slope_stderr": float(slope_stderr),
        "intercept_stderr": float(intercept_stderr),
        "r2": float(r2),
        "chi2_red": float(chi2_red),
        "n_points": int(x.size),
        "x_fit": x_fit,
        "y_fit": y_fit,
    }


def inverse_variance_combine(values, sigmas):
    values = np.asarray(values, dtype=float)
    sigmas = np.asarray(sigmas, dtype=float)
    mask = np.isfinite(values) & np.isfinite(sigmas) & (sigmas > 0)
    if np.sum(mask) == 0:
        return np.nan, np.nan
    weights = 1.0 / (sigmas[mask] ** 2)
    combined = float(np.sum(weights * values[mask]) / np.sum(weights))
    combined_sigma = float(math.sqrt(1.0 / np.sum(weights)))
    return combined, combined_sigma


def round_to_sig_figs(value, sig_figs):
    if not np.isfinite(value):
        return np.nan
    if value == 0:
        return 0.0
    if sig_figs < 1:
        raise ValueError("sig_figs must be >= 1")
    exponent = math.floor(math.log10(abs(value)))
    ndigits = sig_figs - 1 - exponent
    return round(value, int(ndigits))


def format_value_uncertainty(value, uncertainty, uncertainty_sig_figs=1, max_decimal_places=10):
    if not np.isfinite(value):
        return "nan", "nan"
    if not np.isfinite(uncertainty) or uncertainty < 0:
        return f"{value:.6g}", "nan"
    if uncertainty == 0:
        return f"{value:.6g}", "0"

    unc_rounded = round_to_sig_figs(float(abs(uncertainty)), uncertainty_sig_figs)
    if unc_rounded == 0:
        unc_rounded = float(abs(uncertainty))

    precision_exp = math.floor(math.log10(abs(unc_rounded))) - (uncertainty_sig_figs - 1)
    ndigits = int(-precision_exp)
    ndigits = min(ndigits, int(max_decimal_places))

    value_rounded = round(float(value), ndigits)
    if ndigits > 0:
        fmt = f"{{:.{ndigits}f}}"
        return fmt.format(value_rounded), fmt.format(unc_rounded)
    return f"{value_rounded:.0f}", f"{unc_rounded:.0f}"


def format_value_plus_minus(value, uncertainty, uncertainty_sig_figs=1):
    value_text, unc_text = format_value_uncertainty(
        value=value,
        uncertainty=uncertainty,
        uncertainty_sig_figs=uncertainty_sig_figs,
    )
    return f"{value_text} +/- {unc_text}"


def monte_carlo_lambda_uncertainty(dy_cm, dy_sigma_cm, z_m, z_sigma_m, M, M_sigma, delta_v, rng, n_samples):
    dy_sigma = 0.0 if not np.isfinite(dy_sigma_cm) else max(float(dy_sigma_cm), 0.0)
    z_sigma = 0.0 if not np.isfinite(z_sigma_m) else max(float(z_sigma_m), 0.0)
    M_sigma_local = 0.0 if not np.isfinite(M_sigma) else max(float(M_sigma), 0.0)

    dy_samples = rng.normal(float(dy_cm), dy_sigma, int(n_samples))
    z_samples = rng.normal(float(z_m), z_sigma, int(n_samples))
    M_samples = rng.normal(float(M), M_sigma_local, int(n_samples))

    valid = (dy_samples > 0) & (z_samples > 0) & (M_samples > 0)
    if np.sum(valid) < max(200, int(0.05 * n_samples)):
        return np.nan

    dx_samples = (dy_samples[valid] / 100.0) / M_samples[valid]
    lambda_samples = 2.0 * (dx_samples / delta_v) ** 2 / z_samples[valid]
    return float(np.std(lambda_samples, ddof=1))


def fit_pairs_for_magnification(data_df, pair_specs_map, M_value, M_sigma_value=np.nan, include_M_unc=True):
    fit_rows = []
    fit_payload = {}

    for pair, spec in pair_specs_map.items():
        dy = data_df[spec["dy_col"]].to_numpy(dtype=float)
        dy_sigma = data_df["dy_unc_cm"].to_numpy(dtype=float)
        z = data_df["z_m"].to_numpy(dtype=float)

        dx = (dy / 100.0) / M_value

        rel_var = np.zeros_like(dx)
        valid_dy = (dy > 0) & np.isfinite(dy_sigma)
        rel_var[valid_dy] += (dy_sigma[valid_dy] / dy[valid_dy]) ** 2
        if include_M_unc and np.isfinite(M_sigma_value) and M_value > 0:
            rel_var += (M_sigma_value / M_value) ** 2

        dx_sigma = np.abs(dx) * np.sqrt(rel_var)
        y = dx ** 2
        y_sigma = 2.0 * np.abs(dx) * dx_sigma

        fit = weighted_linear_fit(z, y, y_sigma)
        delta_v = float(spec["delta_v"])
        lambda_m = 2.0 * fit["slope"] / (delta_v ** 2)
        lambda_unc_m = 2.0 * fit["slope_stderr"] / (delta_v ** 2)

        fit_rows.append(
            {
                "pair": pair,
                "delta_v": delta_v,
                "slope_m": fit["slope"],
                "slope_sigma_m": fit["slope_stderr"],
                "intercept_m2": fit["intercept"],
                "intercept_sigma_m2": fit["intercept_stderr"],
                "r2": fit["r2"],
                "chi2_red": fit["chi2_red"],
                "n_points": fit["n_points"],
                "lambda_m": lambda_m,
                "lambda_unc_m": lambda_unc_m,
                "lambda_nm": lambda_m * 1e9,
                "lambda_unc_nm": lambda_unc_m * 1e9,
            }
        )

        fit_payload[pair] = {
            "z": z,
            "dx": dx,
            "dx_sigma": dx_sigma,
            "y": y,
            "y_sigma": y_sigma,
            "fit": fit,
        }

    fit_df = pd.DataFrame(fit_rows).sort_values("pair").reset_index(drop=True)
    return fit_df, fit_payload


def build_presentation_straight_line_payload(row_lambda_long):
    presentation_df = row_lambda_long.copy()
    dx = presentation_df["delta_x_true_m"].to_numpy(dtype=float)
    dx_sigma = presentation_df["delta_x_true_sigma_m"].to_numpy(dtype=float)
    delta_v = presentation_df["delta_v"].to_numpy(dtype=float)

    lambda_z_m2 = 2.0 * (dx / delta_v) ** 2
    lambda_z_sigma_m2 = np.abs((4.0 * dx / (delta_v ** 2)) * dx_sigma)

    presentation_df["lambda_z_m2"] = lambda_z_m2
    presentation_df["lambda_z_sigma_m2"] = lambda_z_sigma_m2

    fit = weighted_linear_fit(
        x=presentation_df["z_m"].to_numpy(dtype=float),
        y=presentation_df["lambda_z_m2"].to_numpy(dtype=float),
        y_sigma=presentation_df["lambda_z_sigma_m2"].to_numpy(dtype=float),
    )
    return presentation_df, fit
def run_analysis(
    data_path,
    thin_lens_inputs=None,
    force_numpy_fresnel=False,
    mc_samples=25000,
    rng_seed=20260305,
    show_plots=True,
):
    thin_lens_inputs = thin_lens_inputs or {}
    data_path = Path(data_path)

    notes_raw = pd.read_excel(data_path, sheet_name="Notes", header=None)
    main_raw = pd.read_excel(data_path, sheet_name="Main Data", header=None)

    notes_entries = extract_notes_entries(notes_raw)
    main_measurements = parse_main_measurements(main_raw)

    focus_entry = require_entry(notes_entries, include_terms=["focus"], exclude_terms=["equivalent"])
    track_focus_entry = require_entry(notes_entries, include_terms=["equivalent", "track", "position"])
    beam_lens_entry = require_entry(notes_entries, include_terms=["beam", "diameter", "lens"])
    beam_screen_entry = require_entry(notes_entries, include_terms=["beam", "diameter", "screen"])

    analysis_df = main_measurements.copy()
    track_focus_cm = float(track_focus_entry["value"])
    track_focus_sigma_cm = float(track_focus_entry["uncertainty"]) if np.isfinite(track_focus_entry["uncertainty"]) else 0.0
    analysis_df["z_cm"] = analysis_df["track_position_cm"] - track_focus_cm
    analysis_df["z_sigma_cm"] = np.sqrt(analysis_df["track_position_unc_cm"] ** 2 + track_focus_sigma_cm ** 2)
    analysis_df["z_m"] = analysis_df["z_cm"] / 100.0
    analysis_df["z_sigma_m"] = analysis_df["z_sigma_cm"] / 100.0
    analysis_df = analysis_df[analysis_df["z_m"] > 0].reset_index(drop=True)

    M_diameter, M_diameter_sigma = compute_diameter_ratio_magnification(
        beam_screen_entry["value"],
        beam_screen_entry["uncertainty"],
        beam_screen_entry["unit"],
        beam_lens_entry["value"],
        beam_lens_entry["uncertainty"],
        beam_lens_entry["unit"],
    )

    M_primary = float(M_diameter)
    M_primary_sigma = float(M_diameter_sigma) if np.isfinite(M_diameter_sigma) else np.nan

    thin_lens_result = compute_thin_lens_magnification(thin_lens_inputs)

    use_scipy_backend = SCIPY_AVAILABLE and (not force_numpy_fresnel)
    v_grid = np.linspace(0.0, 8.0, 180001)
    I_grid, _, _, fresnel_method = fresnel_intensity(v_grid, use_scipy=use_scipy_backend)
    minima_df = find_local_minima(v_grid, I_grid, n_min=4, v_threshold=0.05).copy()
    if minima_df.shape[0] < 4:
        raise RuntimeError("Could not locate four minima in Fresnel intensity grid.")

    minima_df["min_index"] = np.arange(1, len(minima_df) + 1)
    minima_df = minima_df[["min_index", "v_min", "I_min"]]

    delta_v_12 = float(minima_df.loc[minima_df["min_index"] == 2, "v_min"].iloc[0] - minima_df.loc[minima_df["min_index"] == 1, "v_min"].iloc[0])
    delta_v_23 = float(minima_df.loc[minima_df["min_index"] == 3, "v_min"].iloc[0] - minima_df.loc[minima_df["min_index"] == 2, "v_min"].iloc[0])
    delta_v_34 = float(minima_df.loc[minima_df["min_index"] == 4, "v_min"].iloc[0] - minima_df.loc[minima_df["min_index"] == 3, "v_min"].iloc[0])

    pair_specs = {
        "12": {"dy_col": "dy12_cm", "delta_v": delta_v_12},
        "23": {"dy_col": "dy23_cm", "delta_v": delta_v_23},
        "34": {"dy_col": "dy34_cm", "delta_v": delta_v_34},
    }
    delta_v_df = pd.DataFrame([{"pair": k, "delta_v": v["delta_v"]} for k, v in pair_specs.items()]).sort_values("pair")

    rng = np.random.default_rng(rng_seed)
    row_records = []
    for _, row in analysis_df.iterrows():
        for pair, spec in pair_specs.items():
            dy_cm = float(row[spec["dy_col"]])
            dy_sigma_cm = float(row["dy_unc_cm"]) if np.isfinite(row["dy_unc_cm"]) else np.nan
            z_m = float(row["z_m"])
            z_sigma_m = float(row["z_sigma_m"])
            delta_v = float(spec["delta_v"])

            delta_x_true_m = (dy_cm / 100.0) / M_primary
            lambda_m = 2.0 * (delta_x_true_m / delta_v) ** 2 / z_m

            rel_terms = []
            if np.isfinite(dy_sigma_cm) and dy_cm > 0:
                rel_terms.append((dy_sigma_cm / dy_cm) ** 2)
            if np.isfinite(M_primary_sigma) and M_primary > 0:
                rel_terms.append((M_primary_sigma / M_primary) ** 2)
            delta_x_sigma_m = abs(delta_x_true_m) * math.sqrt(sum(rel_terms)) if rel_terms else np.nan

            lambda_unc_m = monte_carlo_lambda_uncertainty(
                dy_cm=dy_cm,
                dy_sigma_cm=dy_sigma_cm,
                z_m=z_m,
                z_sigma_m=z_sigma_m,
                M=M_primary,
                M_sigma=M_primary_sigma,
                delta_v=delta_v,
                rng=rng,
                n_samples=mc_samples,
            )

            row_records.append(
                {
                    "track_position_cm": float(row["track_position_cm"]),
                    "z_m": z_m,
                    "z_sigma_m": z_sigma_m,
                    "pair": pair,
                    "delta_v": delta_v,
                    "delta_y_cm": dy_cm,
                    "delta_y_sigma_cm": dy_sigma_cm,
                    "delta_x_true_m": delta_x_true_m,
                    "delta_x_true_sigma_m": delta_x_sigma_m,
                    "lambda_m": lambda_m,
                    "lambda_nm": lambda_m * 1e9,
                    "lambda_unc_m": lambda_unc_m,
                    "lambda_unc_nm": lambda_unc_m * 1e9 if np.isfinite(lambda_unc_m) else np.nan,
                }
            )

    row_lambda_long = pd.DataFrame(row_records).sort_values(["pair", "z_m"]).reset_index(drop=True)

    global_fit_df, fit_payload = fit_pairs_for_magnification(
        data_df=analysis_df,
        pair_specs_map=pair_specs,
        M_value=M_primary,
        M_sigma_value=M_primary_sigma,
        include_M_unc=True,
    )
    lambda_final_nm, lambda_final_unc_nm = inverse_variance_combine(
        global_fit_df["lambda_nm"].to_numpy(dtype=float),
        global_fit_df["lambda_unc_nm"].to_numpy(dtype=float),
    )
    presentation_df, presentation_fit = build_presentation_straight_line_payload(row_lambda_long)
    presentation_lambda_nm = presentation_fit["slope"] * 1e9
    presentation_lambda_unc_nm = presentation_fit["slope_stderr"] * 1e9

    def combined_lambda_for_M(M_test):
        fit_df_local, _ = fit_pairs_for_magnification(
            data_df=analysis_df,
            pair_specs_map=pair_specs,
            M_value=M_test,
            M_sigma_value=np.nan,
            include_M_unc=False,
        )
        lam, _ = inverse_variance_combine(
            fit_df_local["lambda_nm"].to_numpy(dtype=float),
            fit_df_local["lambda_unc_nm"].to_numpy(dtype=float),
        )
        return lam

    if np.isfinite(M_primary_sigma) and M_primary_sigma > 0:
        M_low = max(1e-6, M_primary - M_primary_sigma)
        M_high = M_primary + M_primary_sigma
    else:
        M_low = max(1e-6, 0.8 * M_primary)
        M_high = 1.2 * M_primary

    M_grid = np.linspace(M_low, M_high, 101)
    sensitivity_df = pd.DataFrame({"M": M_grid, "lambda_nm": [combined_lambda_for_M(m) for m in M_grid]})

    if show_plots:
        plot_diagnostics(analysis_df, pair_specs, fit_payload, row_lambda_long, lambda_final_nm, sensitivity_df, M_primary, M_primary_sigma)
        plot_presentation_straight_line(
            presentation_df=presentation_df,
            presentation_fit=presentation_fit,
            lambda_final_nm=lambda_final_nm,
            lambda_final_unc_nm=lambda_final_unc_nm,
            M_primary=M_primary,
            M_primary_sigma=M_primary_sigma,
        )

    return {
        "notes_raw": notes_raw,
        "main_raw": main_raw,
        "notes_entries": notes_entries,
        "focus_entry": focus_entry,
        "analysis_df": analysis_df,
        "pair_specs": pair_specs,
        "fit_payload": fit_payload,
        "M_diameter": M_diameter,
        "M_diameter_sigma": M_diameter_sigma,
        "M_primary": M_primary,
        "M_primary_sigma": M_primary_sigma,
        "thin_lens_result": thin_lens_result,
        "fresnel_method": fresnel_method,
        "minima_df": minima_df,
        "delta_v_df": delta_v_df,
        "row_lambda_long": row_lambda_long,
        "global_fit_df": global_fit_df,
        "lambda_final_nm": lambda_final_nm,
        "lambda_final_unc_nm": lambda_final_unc_nm,
        "presentation_df": presentation_df,
        "presentation_fit": presentation_fit,
        "presentation_lambda_nm": presentation_lambda_nm,
        "presentation_lambda_unc_nm": presentation_lambda_unc_nm,
        "sensitivity_df": sensitivity_df,
    }
def plot_diagnostics(analysis_df, pair_specs, fit_payload, row_lambda_long, lambda_final_nm, sensitivity_df, M_primary, M_primary_sigma):
    pair_colors = {"12": "C0", "23": "C1", "34": "C2"}

    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.5), constrained_layout=True)

    ax = axes[0, 0]
    for pair, spec in pair_specs.items():
        ax.errorbar(
            analysis_df["z_m"],
            analysis_df[spec["dy_col"]],
            yerr=analysis_df["dy_unc_cm"],
            fmt="o-",
            color=pair_colors[pair],
            capsize=3,
            markersize=4.5,
            label=f"Delta y_{pair} (screen)",
        )
    ax.set_title("Measured screen separations vs z")
    ax.set_xlabel("z (m)")
    ax.set_ylabel("Delta y_screen (cm)")
    ax.legend(frameon=False)

    ax = axes[0, 1]
    for pair, payload in fit_payload.items():
        fit = payload["fit"]
        ax.errorbar(
            payload["z"],
            payload["y"],
            yerr=payload["y_sigma"],
            fmt="o",
            capsize=3,
            markersize=4.5,
            color=pair_colors[pair],
            label=f"Pair {pair} data",
        )
        ax.plot(fit["x_fit"], fit["y_fit"], color=pair_colors[pair], alpha=0.9)
    ax.set_title("(Delta x_true)^2 vs z (weighted fits)")
    ax.set_xlabel("z (m)")
    ax.set_ylabel("(Delta x_true)^2 (m^2)")
    ax.legend(frameon=False, fontsize=7.8)

    ax = axes[1, 0]
    for pair in ("12", "23", "34"):
        sub = row_lambda_long[row_lambda_long["pair"] == pair]
        ax.errorbar(
            sub["z_m"],
            sub["lambda_nm"],
            yerr=sub["lambda_unc_nm"],
            fmt="o-",
            capsize=3,
            markersize=4.0,
            color=pair_colors[pair],
            label=f"Pair {pair}",
        )
    ax.axhline(lambda_final_nm, color="black", linestyle="--", linewidth=1.2, label="Combined final lambda")
    ax.set_title("Per-row wavelength estimates vs z")
    ax.set_xlabel("z (m)")
    ax.set_ylabel("lambda (nm)")
    ax.legend(frameon=False, fontsize=7.8)

    ax = axes[1, 1]
    ax.plot(sensitivity_df["M"], sensitivity_df["lambda_nm"], color="C4")
    ax.axvline(M_primary, color="black", linestyle="--", linewidth=1.0, label="Primary M")
    if np.isfinite(M_primary_sigma) and M_primary_sigma > 0:
        ax.axvspan(M_primary - M_primary_sigma, M_primary + M_primary_sigma, color="0.9", alpha=0.7, label="M +/- 1 sigma")
    ax.set_title("Sensitivity of combined lambda to magnification M")
    ax.set_xlabel("Magnification M")
    ax.set_ylabel("Combined lambda (nm)")
    ax.legend(frameon=False)

    plt.show()


def plot_presentation_straight_line(
    presentation_df,
    presentation_fit,
    lambda_final_nm,
    lambda_final_unc_nm,
    M_primary,
    M_primary_sigma,
):
    pair_colors = {"12": "C0", "23": "C1", "34": "C2"}

    fig, ax = plt.subplots(figsize=(9.6, 6.0), constrained_layout=True)
    for pair in ("12", "23", "34"):
        sub = presentation_df[presentation_df["pair"] == pair]
        ax.errorbar(
            sub["z_m"],
            sub["lambda_z_m2"] * 1e9,
            yerr=sub["lambda_z_sigma_m2"] * 1e9,
            fmt="o",
            capsize=3,
            markersize=5.0,
            color=pair_colors[pair],
            label=f"Pair {pair}",
        )

    ax.plot(
        presentation_fit["x_fit"],
        presentation_fit["y_fit"] * 1e9,
        color="black",
        linewidth=2.2,
        label="Weighted straight-line fit",
    )

    fit_lambda_nm = presentation_fit["slope"] * 1e9
    fit_lambda_unc_nm = presentation_fit["slope_stderr"] * 1e9
    final_lambda_text = format_value_plus_minus(lambda_final_nm, lambda_final_unc_nm, uncertainty_sig_figs=1)
    fit_lambda_text = format_value_plus_minus(fit_lambda_nm, fit_lambda_unc_nm, uncertainty_sig_figs=1)
    magnification_text = format_value_plus_minus(M_primary, M_primary_sigma, uncertainty_sig_figs=1)
    summary_text = "\n".join(
        [
            f"Final lambda (combined): {final_lambda_text} nm",
            f"Straight-line fit lambda: {fit_lambda_text} nm",
            f"R^2 = {presentation_fit['r2']:.4f}   chi2_red = {presentation_fit['chi2_red']:.2f}",
            f"Points = {presentation_fit['n_points']}",
            f"M = {magnification_text}",
        ]
    )
    ax.text(
        0.02,
        0.98,
        summary_text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9.2,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "0.3", "alpha": 0.95},
    )

    ax.set_title("Final straight-line wavelength plot")
    ax.set_xlabel("z (m)")
    ax.set_ylabel("2 (Delta x / Delta v)^2 (nm m)")
    ax.legend(frameon=False, loc="lower right")

    plt.show()


def print_summary(results):
    print("Fresnel backend:", results["fresnel_method"])
    print(
        "Primary magnification M =",
        format_value_plus_minus(results["M_primary"], results["M_primary_sigma"], uncertainty_sig_figs=1),
    )
    if results["thin_lens_result"].get("available", False):
        print("Thin-lens estimate:", results["thin_lens_result"])
    else:
        print("Thin-lens estimate not used:", results["thin_lens_result"].get("reason"))
    print(
        "Final wavelength estimate:",
        format_value_plus_minus(results["lambda_final_nm"], results["lambda_final_unc_nm"], uncertainty_sig_figs=1),
        "nm",
    )


__all__ = [
    "SCIPY_AVAILABLE",
    "run_analysis",
    "plot_diagnostics",
    "plot_presentation_straight_line",
    "format_value_uncertainty",
    "format_value_plus_minus",
    "print_summary",
]
