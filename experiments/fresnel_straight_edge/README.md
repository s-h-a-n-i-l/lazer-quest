# Fresnel Straight-Edge Wavelength Experiment

## Aim
Estimate the laser wavelength from straight-edge Fresnel diffraction data while explicitly correcting for imaging magnification.

## Geometry Used
- `z`: distance from aperture to Fresnel diffraction pattern plane (m), inferred from lens-track displacement relative to the focused-image track position.
- `M`: magnification from diffraction-pattern plane to screen.
- Measured screen separations `\Delta y` are converted to pattern-plane separations `\Delta x = \Delta y / M`.

## Key Equations
- Fresnel variable: `v = x * sqrt(2 / (\lambda z))`
- Half-plane intensity: `I(v) = (1/2 + C(v))^2 + (1/2 + S(v))^2`
- For minima separations: `\Delta x = sqrt(\lambda z / 2) * \Delta v`
- Per-row wavelength: `\lambda = 2 * (\Delta x / \Delta v)^2 / z`
- Global fit form: `(\Delta x)^2 = (\lambda/2) * (\Delta v)^2 * z`

## How to Run
From repo root:

```bash
.venv/bin/jupyter nbconvert \
  --to notebook \
  --execute \
  --inplace \
  experiments/fresnel_straight_edge/fresnel_straight_edge_wavelength.ipynb

.venv/bin/jupyter nbconvert \
  --to html \
  experiments/fresnel_straight_edge/fresnel_straight_edge_wavelength.ipynb \
  --output fresnel_straight_edge_wavelength.html
```

## Assumptions
- All internal computations are SI (meters).
- Primary `M` comes from diameter-ratio notes with propagated uncertainty.
- Thin-lens `M` is only computed when complete geometry (`u`, `v`, or `f` plus one distance) is explicitly supplied.
- If SciPy is unavailable, Fresnel integrals/minima are computed with a NumPy-only numerical fallback.
