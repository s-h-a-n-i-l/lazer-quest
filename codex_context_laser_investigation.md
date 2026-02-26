# Context document for GPT-5.3 Codex
## Project: convert the diffraction investigation workbook into a polished Jupyter notebook

## 1. Objective of this notebook
Build a well-written `.ipynb` that uses the Excel workbook `lazer quest.xlsx` and the investigation brief to do the following:

1. explain the physical aim of the investigation,
2. load and clean the data from the workbook,
3. reconstruct what experiments were actually carried out,
4. plot the relevant data clearly,
5. fit the main linear relationships,
6. extract wavelength estimates from each method,
7. compare the methods critically,
8. include concise evaluation of uncertainty, assumptions, and likely systematic errors.

This should read like a strong Cambridge lab-analysis notebook: clear narrative, transparent data handling, reproducible calculations, and restrained claims.

---

## 2. High-level context from the investigation brief
The extended investigation asks:

> How precisely can the wavelength of a fibre-coupled diode laser be determined using diffraction experiments alone?

The apparatus is deliberately simple. The manual makes the following points that matter for the notebook:

- both Fraunhofer and Fresnel diffraction patterns can be observed;
- aperture dimensions need to be measured carefully;
- the measuring microscope has a resolution of a few micrometres;
- students should focus mainly on **spatial information** in the diffraction patterns because intensity measurements are not available;
- suitable graphs are explicitly encouraged as a major part of the analysis;
- the lab notebook should record not just results, but also what was measured, why it was measured, how it was analysed, and how much the results are trusted.

The notebook should therefore frame the work as a **measurement problem**, not just a pattern-viewing exercise.

---

## 3. Best overall narrative for the notebook
The cleanest story is:

1. The unknown laser wavelength was estimated using several diffraction methods.
2. The team measured positions of diffraction features on a screen.
3. They avoided needing the exact central position by taking **symmetric separations** between matching positive and negative orders.
4. They converted each theory into a linear graph so that the wavelength could be extracted from a fitted gradient.
5. They compared several methods to see whether the values agreed and to identify likely systematic errors.

The notebook should make clear that the data suggests the team used **three main experimental strands**:

- **single-slit Fraunhofer diffraction**,
- **5-slit grating diffraction**,
- **Fresnel diffraction**.

---

## 4. Source files
Use these two files as the core sources:

- `Part_IB_extended_investigation_manual_2026.pdf`
- `lazer quest.xlsx`

The notebook should rely mainly on the Excel workbook for quantitative data and use the manual only for light contextual framing.

---

## 5. Workbook structure and what each sheet appears to contain

### Sheet 1: `Single slit`
This sheet contains three single-slit datasets:

- **medium single slit**
- **thick single slit**
- **thin single slit**

It also contains:

- the screen distance,
- the measured slit widths,
- computed symmetric separations `y+ - y-`,
- a combined scaled dataset intended to collapse all slit data onto one line.

#### Important metadata on this sheet
- distance from aperture to screen: `L = 5.12 +- 0.03 m`
- thick slit width: `0.000497 +- 0.000002 m`
- medium slit width: `0.000198 +- 0.000002 m`
- thin slit width: `0.000100 +- 0.000002 m`

#### Raw-data layout
- medium slit raw orders and positions: columns `A:B`, rows `2:11`
- thick slit raw orders and positions: columns `D:E`, rows `2:24`
- thin slit raw orders and positions: columns `G:H`, rows `2:5`

#### Processed-data layout
- medium symmetric separations: `A33:B37`
- thick symmetric separations: `D33:E43`
- thin symmetric separations: `G33:H34`
- combined scaled data: around `D46:F63`

#### What the sheet is doing physically
For each slit, positions of minima were recorded on the `+n` and `-n` sides. The sheet then forms:

\[
\Delta y_n = y_{+n} - y_{-n}
\]

This avoids needing the exact central fringe location.

---

### Sheet 2: `Grating`
This sheet contains six 5-slit grating datasets and two distinct analyses.

#### Raw-data layout
Each grating has raw maxima positions for positive and negative orders.

- grating 1: `A:B`
- grating 2: `E:F`
- grating 3: `H:I`
- grating 4: `K:L`
- grating 5: `N:O`
- grating 6: `Q:R`

Rows are mainly `3:14`.

Some entries are written as `"missing"`.

#### Processed-data layout
Symmetric separations `y+ - y-` are tabulated on row block `16:22`.

#### Second grating analysis
Rows `24:30` contain a table with:

- grating number,
- slit width in mm,
- inverse slit width in `m^-1`,
- missing-order separation,
- associated errors.

#### Final values already written in the workbook
The sheet appears to report:

- wavelength from missing-order method: about **656.25 nm**
- wavelength from grating-maxima method: about **681.67 nm**

#### Physical interpretation
The grating sheet supports two analyses:

1. **ordinary grating maxima**, using the separation of diffraction orders;
2. **missing orders / envelope analysis**, where certain interference maxima vanish because they coincide with single-slit envelope minima.

The missing entries are therefore not just absent measurements; they are part of the physics.

---

### Sheet 3: `Fresnel `
Note that the sheet name contains a trailing space in Excel.

This sheet contains:

- a measured quantity `d`,
- a stated percentage error,
- an order-like index `n`,
- a transformed quantity `1/(27.32 - d) * 1000`,
- an associated propagated error,
- a final wavelength calculation in the top-right area.

#### Layout
- data rows: `2:13`
- key columns: `A:E`
- final formula visible in `H1`

#### What it seems to be doing
The data is arranged for a straight-line plot of:

\[
\frac{1}{R} \text{ versus } n
\]

with `R` apparently related to `27.32 - d`.

The sheet's final formula uses a slope of about `15.907` and a slit width of about `0.199 mm`, leading to a wavelength near **630 nm**.

This is likely a linearised Fresnel analysis using a projected diffraction pattern and a known geometric distance shift.

---

## 6. Reconstructed experimental methods

### Method A: single-slit Fraunhofer diffraction
Likely procedure:

1. choose a slit of known width `a`,
2. place a screen at distance `L`,
3. record positions of minima on both sides of the central maximum,
4. form symmetric separations `\Delta y_n`,
5. fit `\Delta y_n` against order `n`,
6. extract the wavelength from the slope.

The relevant theory is:

\[
a \sin\theta = n\lambda
\]

For small angles, with `y_n \approx L \tan\theta \approx L \sin\theta`,

\[
y_n \approx \frac{Ln\lambda}{a}
\]

Using symmetric pairs,

\[
\Delta y_n = y_{+n} - y_{-n} \approx \frac{2Ln\lambda}{a}
\]

So a plot of `\Delta y_n` against `n` should be linear with gradient

\[
m = \frac{2L\lambda}{a}
\]

and therefore

\[
\lambda = \frac{a m}{2L}
\]

### Method B: combined scaled single-slit analysis
The workbook also scales each single-slit dataset by multiplying the separation by slit width:

\[
a\,\Delta y_n = 2L\lambda\,n
\]

This means all slit datasets should collapse onto one line when plotting:

- x-axis: `n`
- y-axis: `a \Delta y_n`

The slope of this combined fit is `2L\lambda`.

This is a strong analysis because it checks whether all slit datasets are consistent with the same wavelength and the expected `1/a` scaling.

### Method C: 5-slit grating maxima
For a grating with slit separation or pitch `d_g`,

\[
d_g \sin\theta = n\lambda
\]

For small angles,

\[
\Delta y_n \approx \frac{2Ln\lambda}{d_g}
\]

So a plot of `\Delta y_n` against `n` should again be linear, and

\[
\lambda = \frac{d_g m}{2L}
\]

where `m` is the fitted slope in metres per order.

The workbook strongly suggests that the pitch used in this analysis is about `0.198 mm` to `0.199 mm`.

### Method D: missing-order / diffraction-envelope analysis for the gratings
The grating pattern is the product of:

- a multi-slit interference pattern,
- a single-slit diffraction envelope.

Some interference maxima disappear when they fall on an envelope minimum.

For the envelope,

\[
a \sin\theta \sim \lambda
\]

so the screen separation associated with the missing-order feature should scale like:

\[
\Delta y_{\text{miss}} \propto \frac{\lambda L}{a}
\]

Hence plotting missing-order separation against `1/a` should be approximately linear.

This appears to be exactly what the workbook is doing in rows `24:30`.

### Method E: Fresnel analysis
The Fresnel sheet is less transparent than the others, but the structure is clear:

1. a measured distance-like quantity `d` is recorded,
2. it is transformed into a reciprocal distance variable,
3. that variable is plotted against an integer index `n`,
4. a gradient is extracted,
5. the wavelength is computed from that gradient multiplied by a characteristic slit-width scale squared.

The final worksheet formula implies:

\[
\lambda = (\text{slope})\,a^2
\]

with `a \approx 0.199 mm` and slope about `15.907`, giving about `630 nm`.

The notebook should state clearly that this method is more model-dependent and less immediately transparent from the workbook alone.

---

## 7. Numerical values recoverable from the workbook
These values can be reconstructed directly from the Excel file and should be shown in the notebook.

### Single-slit raw symmetric separations

#### Medium slit (`a = 0.198 mm`)
- `n = 1`: `3.7 cm`
- `n = 2`: `7.1 cm`
- `n = 3`: `10.6 cm`
- `n = 4`: `14.0 cm`
- `n = 5`: `17.7 cm`

#### Thick slit (`a = 0.497 mm`)
- `n = 1`: `1.60 cm`
- `n = 2`: `2.75 cm`
- `n = 3`: `4.15 cm`
- `n = 4`: `5.55 cm`
- `n = 5`: `6.90 cm`
- `n = 6`: `8.30 cm`
- `n = 7`: `9.65 cm`
- `n = 8`: `11.15 cm`
- `n = 9`: `12.50 cm`
- `n = 10`: `13.90 cm`
- `n = 11`: `15.25 cm`

#### Thin slit (`a = 0.100 mm`)
- `n = 1`: `7.0 cm`
- `n = 2`: `14.1 cm`

### Approximate fitted gradients from the workbook data
These can be recomputed in code.

- medium single slit: slope about `3.49 cm/order`
- thick single slit: slope about `1.3805 cm/order`
- thin single slit: slope about `7.10 cm/order`
- combined scaled single-slit fit: slope about `6.856e-06 m^2/order` if plotted in consistent SI units
- combined grating maxima fit: slope about `3.517 cm/order`
- missing-order fit: slope about `6.724e-06 m^2`
- Fresnel fit: slope about `15.907` in the sheet's chosen transformed units

### Approximate wavelength estimates already implied by the workbook
- combined single-slit method: about **670 nm**
- grating missing-order method: about **656 nm**
- grating maxima method: about **682 nm**
- Fresnel method: about **630 nm**

The notebook should present these as **internal estimates from different methods**, not as final truth values.

---

## 8. Key unit-handling warning
A major source of error risk is mixed units.

The workbook uses a mixture of:

- metres for slit widths and `L`,
- centimetres for screen positions and separations,
- millimetres for some aperture or slit-width entries,
- transformed reciprocal distances in the Fresnel sheet.

Codex should be instructed to:

1. convert everything into SI units before fitting where possible,
2. state explicitly when a fit is carried out in non-SI units and how the unit conversion is applied afterward,
3. avoid silently carrying over worksheet conventions.

This point is essential.

---

## 9. Recommended notebook structure
The output notebook should have a strong structure with markdown and code interleaved.

### Section 1 - Title and aim
- Title of investigation
- One-paragraph summary of the measurement problem
- State that diffraction-only methods are being used to estimate the unknown laser wavelength

### Section 2 - Context and physical overview
- Brief explanation of why single-slit, grating, and Fresnel diffraction can all constrain `\lambda`
- Explain why the analysis uses positions, not intensities
- Explain the importance of symmetric separations

### Section 3 - Load workbook and inspect structure
- Load Excel workbook robustly
- Print available sheet names
- Extract and display the relevant tables
- Note that the `Fresnel ` sheet has a trailing space in its name

### Section 4 - Single-slit analysis
- Reconstruct raw `+n` and `-n` position tables
- Pair positive and negative orders by absolute value
- Compute `\Delta y_n`
- Plot raw positions if helpful
- Plot `\Delta y_n` vs `n` for each slit separately
- Fit straight lines
- Compute `\lambda` for each slit
- Then build the combined scaled dataset and fit that as the preferred single-slit summary method

### Section 5 - Grating maxima analysis
- Extract symmetric separations for all six gratings
- Handle `"missing"` safely as non-numeric data
- Plot `\Delta y_n` vs `n` for each grating and/or as a combined dataset
- Fit a global line if justified
- Use the grating pitch to estimate `\lambda`
- Explain that the grating maxima are almost equally spaced because the slit pitch is fixed while slit width varies across gratings

### Section 6 - Missing-order / envelope analysis
- Extract the table of slit width vs missing-order separation
- Convert slit width to metres and build `1/a`
- Plot missing-order separation vs `1/a`
- Fit a line
- Compute the wavelength from the slope
- Explain the physical origin of missing orders

### Section 7 - Fresnel analysis
- Recreate the transformed variable from the sheet
- Plot `1/R` vs `n`
- Fit the line
- Reproduce the worksheet wavelength calculation
- State clearly that this is a cross-check and may be more sensitive to geometric assumptions

### Section 8 - Comparison table
- Create a tidy summary table with columns such as:
  - method,
  - slope,
  - main formula used,
  - wavelength estimate in nm,
  - comments on trustworthiness

### Section 9 - Evaluation
- Discuss consistency of results
- Identify likely systematic errors
- Identify strongest and weakest methods
- Comment on data quality, scatter, and model assumptions

### Section 10 - Final conclusion
- Give a cautious final wavelength range or best estimate
- Explain why a range may be more honest than a single over-precise value

---

## 10. Recommended plots
The notebook should include the following plots at minimum.

### Single-slit plots
1. `\Delta y_n` vs `n` for medium slit
2. `\Delta y_n` vs `n` for thick slit
3. `\Delta y_n` vs `n` for thin slit
4. combined scaled plot: `a \Delta y_n` vs `n`

### Grating plots
5. combined grating maxima plot: `\Delta y_n` vs `n`
6. optional per-grating overlay plot for visual comparison
7. missing-order separation vs `1/a`

### Fresnel plot
8. transformed Fresnel plot: `1/R` vs `n`

### Comparison visual
9. optional bar chart or scatter plot of wavelength estimate by method

All plots should have:

- axis labels with units,
- fitted lines where appropriate,
- legends where needed,
- a short caption or markdown explanation below the plot.

---

## 11. Data-cleaning expectations for Codex
The notebook code should be robust and explicit.

### General rules
- use `openpyxl` or `pandas.read_excel` carefully;
- treat the workbook as semi-structured rather than perfectly tabular;
- convert text like `"missing"` and `"not measurable "` to `NaN`;
- do not hardcode results that can be derived from the workbook;
- if hardcoding any cell locations, explain why.

### Single-slit pairing logic
For each slit:

1. read the order column and position column,
2. split positive and negative orders,
3. pair order `+n` with `-n`,
4. compute `\Delta y_n = y_{+n} - y_{-n}`.

### Grating pairing logic
For each grating:

1. read the order column and position column,
2. separate positive and negative orders,
3. match by absolute order,
4. compute symmetric separations,
5. skip any order where a position is recorded as missing.

### Fresnel logic
- read `d`, `% error`, and `n`;
- either use the cached transformed column or reconstruct it from the formula `1000/(27.32 - d)`;
- reproduce the fitted slope;
- reproduce the worksheet wavelength calculation.

---

## 12. Recommended coding style for the notebook
Ask Codex to write the notebook in a way that is easy to read and easy to mark.

### Preferred style
- small helper functions for repeated extraction logic,
- clear variable names,
- markdown cells between code blocks,
- equations typeset in markdown where useful,
- concise comments in code,
- summary tables as pandas DataFrames.

### Suggested helper functions
- `extract_pos_neg_pairs(...)`
- `linear_fit_with_r2(...)`
- `plot_with_fit(...)`
- `compute_single_slit_lambda(...)`
- `clean_numeric_column(...)`

### Libraries
Reasonable defaults:
- `pandas`
- `numpy`
- `openpyxl`
- `matplotlib`
- optionally `scipy.stats` for regression if desired

Do not depend on obscure libraries.

---

## 13. Evaluation points the notebook should make
The evaluation section should not be generic. It should be tied to this workbook.

### Strengths of the analysis
- symmetric separations reduce centre-location error;
- linear plots make the wavelength extraction transparent;
- multiple independent methods allow cross-checking;
- the combined scaled single-slit plot is a particularly strong consistency test;
- the grating missing-order analysis uses genuine extra physics rather than only repeating the same idea.

### Weaknesses / limitations
- mixed units create risk of conversion mistakes;
- some data series are short, especially the thin single-slit and Fresnel analyses;
- the Fresnel model is less transparent from the worksheet and likely more sensitive to geometry;
- maxima/minima were probably identified by eye, which can introduce systematic error;
- aperture widths and grating pitch measurements are crucial and can dominate the final uncertainty;
- some chart labels in the workbook are minimal or truncated, so the notebook should improve the presentation substantially.

### Likely systematic errors to mention
- uncertainty in slit width or grating dimensions,
- uncertainty in the screen distance `L`,
- imperfect alignment of beam, aperture, lens, and screen,
- uncertainty in locating diffuse minima or maxima,
- possible small-angle approximation limitations for larger orders,
- ambiguity in the Fresnel geometry and transformed distance definition.

### What conclusion is justified
A careful conclusion would say that the laser is clearly in the **red** part of the visible spectrum and that the various methods cluster roughly in the **630 to 682 nm** range, with the strongest cluster around **mid-600 nm to high-600 nm**. The notebook should avoid pretending that the methods agree perfectly.

A sensible final sentence might be that the most convincing methods are the combined single-slit fit and the grating-based analyses, while the Fresnel result acts more as a model-sensitive cross-check.

---

## 14. Specific instructions to give Codex for the notebook build
Use the following as direct implementation guidance.

### Mandatory deliverable requirements
Create a `.ipynb` that:

- runs top-to-bottom without manual editing,
- reads the Excel file directly,
- reconstructs the datasets from the workbook rather than relying only on manually typed values,
- produces polished plots,
- includes markdown explanations before or after every important calculation,
- ends with a compact comparison and evaluation section.

### Tone and style requirements
The notebook should be:

- formal but readable,
- concise rather than bloated,
- explanatory enough for a marker or supervisor to follow,
- honest about assumptions and uncertainty.

### Analysis requirements
- prefer symmetric-separation analyses where possible,
- reproduce worksheet logic where it is clear,
- point out when a formula is inferred rather than explicitly documented in the workbook,
- report fitted slope, intercept, and `R^2` for each straight-line model,
- convert wavelength results to nm for readability.

### Presentation requirements
- begin each major section with a short markdown explanation,
- show cleaned tables before plotting,
- use consistent units in displayed tables,
- include a final summary table of all wavelength estimates.

---

## 15. Suggested final conclusion shape for the notebook
The final notebook conclusion should probably say something close to this:

- The workbook indicates that the laser wavelength was estimated using multiple diffraction methods.
- The best-supported Fraunhofer analyses give values in the red range, around `~656 to ~682 nm`, with the combined single-slit result near `~670 nm`.
- The Fresnel analysis gives a somewhat lower value near `~630 nm`, which may reflect greater sensitivity to geometry and modelling assumptions.
- The spread of values suggests that systematic errors dominate over random scatter.
- A cautious final estimate should therefore be expressed as a best estimate with a realistic uncertainty or as a method-dependent range, rather than a single highly precise number.

---

## 16. Optional extension ideas if time allows
If Codex has time and the notebook would benefit, it may also:

- compare exact-angle and small-angle versions of the single-slit formula,
- estimate uncertainty in the fitted slope using standard regression formulas,
- propagate uncertainties into each wavelength estimate,
- include a short sensitivity test showing which input variables dominate the uncertainty.

These are optional but useful.

---

## 17. Final note to Codex
Do not treat the workbook as perfectly self-explanatory. Reconstruct the intent carefully, but do not invent physics that is not justified. Where the Fresnel method is uncertain, say so explicitly. The goal is a notebook that is **reproducible, explanatory, and measured in its claims**.
