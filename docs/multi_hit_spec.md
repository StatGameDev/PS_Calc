# Multi-Hit Damage Distribution — Implementation Spec

## Context

Extends the existing RO damage calculator (pre-renewal, Python desktop app, pyqtgraph GUI).
Adds a damage distribution histogram (Phase 7 GUI feature) driven by exact discrete convolution
for single-hit PMF construction, FFT-based N-fold convolution for small N, and CLT normal
approximation for large N.

### Pipeline integration — DamageRange replaced by PMF

`DamageRange` is **removed entirely**. All pipeline modifiers operate on `dict[int, float]`
(a PMF summing to 1.0) instead of `(min, max, avg)` tuples. `DamageResult` gains a `pmf`
field populated by the pipeline; `min_damage`, `max_damage`, `avg_damage` are derived from
it at the end of each pipeline branch. PMF operations live in `pmf/operations.py`.

The three stochastic sources in BF_WEAPON (all others are deterministic):

| RV | Hercules formula | Typical range width |
|---|---|---|
| Weapon ATK roll | `rnd()%(atkmax-atkmin)+atkmin` → `[atkmin, atkmax-1]` | 0–150 |
| Overrefine roll | `rnd()%overrefine+1` → `[1, overrefine]` | 0–50 |
| VIT DEF roll (subtracted) | Mob: `rnd()%(def2/20)²`; PC: `rnd()%(def2*(def2-15)/150)` | 0–100 mob, 0–250 PC |

DamageRange operations map 1:1 to PMF operations:

| DamageRange method | PMF equivalent |
|---|---|
| `.scale(num, denom)` | remap each `v → v*num//denom`, accumulate probability at collisions |
| `.add(flat)` | shift all keys by `+flat` |
| `.add_range(lo, hi, _)` | convolve with discrete uniform `[lo, hi]` |
| `.subtract(vd_min, vd_max, _)` | convolve with negated uniform `[vd_min, vd_max]` |
| `.floor_at(n)` | accumulate all mass at values `< n` into key `n` |

---

## New dependency

Add to `requirements.txt`:
```
scipy>=1.13
```

---

## Files to Create or Modify

```
requirements.txt            MODIFY — add scipy>=1.13  [DONE]
pmf/__init__.py             CREATE — empty package init  [DONE]
pmf/operations.py           CREATE — 7 PMF operations (_uniform_pmf, _scale_floor, _add_flat,
                                     _convolve, _subtract_uniform, _floor_at, pmf_stats)
pmf/single_hit.py           CREATE — SingleHitPMF dataclass, finalize(), from_damage_result()
pmf/statistics.py           CREATE — pmf_dict_to_array, percentiles_from_array
pmf/multi_hit.py            CREATE — MultiHitResult, compute_multi_hit, n_hits helper, FFT + CLT
core/models/damage.py       MODIFY — remove DamageRange; add pmf field to DamageResult
core/calculators/modifiers/base_damage.py  MODIFY — Session H
core/calculators/modifiers/*.py (×9)       MODIFY — Session I
core/calculators/battle_pipeline.py        MODIFY — Session I
core/calculators/magic_pipeline.py         MODIFY — Session I
gui/histogram_widget.py     CREATE — pyqtgraph widget, receives MultiHitResult, dispatches on method
tests/perf_multi_hit.py     CREATE — standalone perf tests, no GUI dependency
```

Note: `tests/` directory does not yet exist — create it.

---

## Create: pmf/operations.py

All PMF operations. Imported by every pipeline modifier.
`pmf_stats` is used to populate `DamageStep.min_value/max_value/value` at each step.

```python
def _uniform_pmf(lo: int, hi: int) -> dict[int, float]:
    """Discrete uniform PMF over [lo, hi] inclusive."""
    n = hi - lo + 1
    p = 1.0 / n
    return {v: p for v in range(lo, hi + 1)}

def _scale_floor(pmf: dict[int, float], num: int, denom: int) -> dict[int, float]:
    """Deterministic floor-division remap: v → v*num//denom.
    Multiple input values can map to the same output — probabilities accumulate.
    No-op when num == denom."""
    if num == denom:
        return pmf
    out: dict[int, float] = {}
    for v, p in pmf.items():
        key = v * num // denom
        out[key] = out.get(key, 0.0) + p
    return out

def _add_flat(pmf: dict[int, float], flat: int) -> dict[int, float]:
    """Shift all keys by flat. No-op when flat == 0."""
    if flat == 0:
        return pmf
    return {v + flat: p for v, p in pmf.items()}

def _convolve(pmf: dict[int, float], other: dict[int, float]) -> dict[int, float]:
    """General convolution (addition) of two independent PMFs. O(|pmf| * |other|)."""
    out: dict[int, float] = {}
    for v1, p1 in pmf.items():
        for v2, p2 in other.items():
            key = v1 + v2
            out[key] = out.get(key, 0.0) + p1 * p2
    return out

def _subtract_uniform(pmf: dict[int, float], lo: int, hi: int) -> dict[int, float]:
    """Subtract a discrete uniform [lo, hi] from pmf.
    Equivalent to convolving with the negated uniform [-hi, -lo]."""
    if lo == hi:
        return _add_flat(pmf, -lo)
    neg_uniform = _uniform_pmf(-hi, -lo)
    return _convolve(pmf, neg_uniform)

def _floor_at(pmf: dict[int, float], n: int = 1) -> dict[int, float]:
    """Accumulate all probability mass at values < n into key n."""
    out = {v: p for v, p in pmf.items() if v >= n}
    floor_mass = sum(p for v, p in pmf.items() if v < n)
    if floor_mass > 0:
        out[n] = out.get(n, 0.0) + floor_mass
    return out

def pmf_stats(pmf: dict[int, float]) -> tuple[int, int, int]:
    """Return (min_dmg, max_dmg, avg_dmg) from a PMF. avg is floor of expected value."""
    mu = sum(v * p for v, p in pmf.items())
    return min(pmf), max(pmf), int(mu)
```

---

## Create: pmf/single_hit.py

`SingleHitPMF` is a thin wrapper used as input to `compute_multi_hit`. Built from a
`DamageResult` after the pipeline populates `result.pmf`.

```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class SingleHitPMF:
    pmf: dict[int, float]   # sums to 1.0
    min_dmg: int
    max_dmg: int
    mean: float             # set by finalize()
    variance: float         # set by finalize()

    def finalize(self) -> "SingleHitPMF":
        mu = sum(v * p for v, p in self.pmf.items())
        var = sum((v - mu) ** 2 * p for v, p in self.pmf.items())
        self.mean = mu
        self.variance = var
        return self

    @classmethod
    def from_damage_result(cls, result: "DamageResult") -> "SingleHitPMF":
        """Extract SingleHitPMF from a completed pipeline DamageResult.
        Requires result.pmf to be populated (Session H+).
        """
        pmf = result.pmf
        obj = cls(
            pmf=pmf,
            min_dmg=min(pmf),
            max_dmg=max(pmf),
            mean=0.0,
            variance=0.0,
        )
        return obj.finalize()
```

---

## Create: pmf/statistics.py

Two helpers used by multi_hit.py.

```python
import numpy as np

def pmf_dict_to_array(pmf: dict[int, float], lo: int, hi: int) -> np.ndarray:
    arr = np.zeros(hi - lo + 1, dtype=np.float64)
    for v, p in pmf.items():
        arr[v - lo] = p
    return arr

def percentiles_from_array(
    arr: np.ndarray, support: range, percentiles: list[int]
) -> list[float]:
    """Exact CDF walk. O(len(arr))."""
    cdf = np.cumsum(arr)
    results = []
    for pct in percentiles:
        idx = int(np.searchsorted(cdf, pct / 100.0))
        idx = min(idx, len(arr) - 1)
        results.append(float(support[idx]))
    return results
```

---

## Create: pmf/multi_hit.py

### n_hits helper

```python
import math

def compute_n_hits(target_hp: int, avg_damage: float) -> int:
    """Number of hits to reduce target HP to 0, based on average damage.
    Returns 1 if avg_damage <= 0 (avoid division by zero / infinite loop)."""
    if avg_damage <= 0:
        return 1
    return math.ceil(target_hp / avg_damage)
```

### Dataclasses

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
import numpy as np
from pmf.single_hit import SingleHitPMF   # SingleHitPMF lives in single_hit.py only

@dataclass
class MultiHitResult:
    method: Literal["exact", "normal"]
    n_hits: int
    # Always set — exact arithmetic, no approximation
    min_total: int          # n * single.min_dmg
    max_total: int          # n * single.max_dmg
    mean_total: float       # n * single.mean
    std_total: float        # sqrt(n * single.variance)
    p10: float
    p90: float
    median: float
    # Set only when method == "exact"
    pmf_array: np.ndarray | None    # probabilities aligned to support_range
    support_range: range | None     # range(min_total, max_total + 1)
    # When method == "normal": pmf_array and support_range are None.
    # Histogram widget builds curve from mean_total, std_total, min_total, max_total.
```

### Module-level state

```python
import time
from scipy.signal import fftconvolve
import scipy.stats
from pmf.statistics import pmf_dict_to_array, percentiles_from_array

FFT_THRESHOLD: int = 75          # overwritten at startup by benchmark_fft_threshold()
_stat_signature: tuple = ()      # tracks current stat state for cache invalidation
_power_cache: dict[int, np.ndarray] = {}   # {bit: PMF array} for current signature
```

### Entry point

```python
def compute_multi_hit(single: SingleHitPMF, n_hits: int) -> MultiHitResult:
    if n_hits == 1:
        return _wrap_single_hit(single)
    elif n_hits <= FFT_THRESHOLD:
        return _fft_exact(single, n_hits)
    else:
        return _clt_normal(single, n_hits)

def invalidate_caches(new_signature: tuple) -> None:
    global _stat_signature, _power_cache
    if new_signature != _stat_signature:
        _stat_signature = new_signature
        _power_cache.clear()
```

`new_signature` should be a tuple of all integer inputs to the damage pipeline,
e.g. `(atkmin, atkmax, overrefine, size_mult, skill_ratio, def1, vd_min, vd_max, ...)`.
Call `invalidate_caches()` whenever any stat changes before calling `compute_multi_hit()`.

### _wrap_single_hit

```python
def _wrap_single_hit(single: SingleHitPMF) -> MultiHitResult:
    arr = pmf_dict_to_array(single.pmf, single.min_dmg, single.max_dmg)
    p10, median, p90 = percentiles_from_array(
        arr, range(single.min_dmg, single.max_dmg + 1), [10, 50, 90]
    )
    return MultiHitResult(
        method="exact", n_hits=1,
        min_total=single.min_dmg, max_total=single.max_dmg,
        mean_total=single.mean, std_total=float(np.sqrt(single.variance)),
        p10=p10, p90=p90, median=median,
        pmf_array=arr,
        support_range=range(single.min_dmg, single.max_dmg + 1),
    )
```

### _fft_exact

```python
def _fft_exact(single: SingleHitPMF, n: int) -> MultiHitResult:
    arr = pmf_dict_to_array(single.pmf, single.min_dmg, single.max_dmg)
    result_arr = _array_power_fft(arr, n)
    result_arr = np.maximum(result_arr, 0)
    result_arr /= result_arr.sum()

    support = range(single.min_dmg * n, single.max_dmg * n + 1)
    p10, median, p90 = percentiles_from_array(result_arr, support, [10, 50, 90])

    return MultiHitResult(
        method="exact", n_hits=n,
        min_total=single.min_dmg * n, max_total=single.max_dmg * n,
        mean_total=single.mean * n, std_total=float(np.sqrt(single.variance * n)),
        p10=p10, p90=p90, median=median,
        pmf_array=result_arr, support_range=support,
    )

def _array_power_fft(arr: np.ndarray, n: int) -> np.ndarray:
    """N-fold self-convolution via binary exponentiation with power caching."""
    result = None
    bit = 1
    temp = arr.copy()

    while n > 0:
        if n & 1:
            if bit not in _power_cache:
                _power_cache[bit] = temp.copy()
            result = temp.copy() if result is None else fftconvolve(result, temp)
        if bit not in _power_cache:
            _power_cache[bit] = temp.copy()
        temp = fftconvolve(temp, temp)
        bit <<= 1
        n >>= 1

    return result
```

Use `scipy.signal.fftconvolve` directly. Do not implement raw FFT.
Default `mode='full'` is correct — output length equals N × single support width.

### _clt_normal

```python
def _clt_normal(single: SingleHitPMF, n: int) -> MultiHitResult:
    mu = single.mean * n
    sigma = float(np.sqrt(single.variance * n))
    dist = scipy.stats.norm(mu, sigma)
    lo, hi = single.min_dmg * n, single.max_dmg * n

    return MultiHitResult(
        method="normal", n_hits=n,
        min_total=lo, max_total=hi,
        mean_total=mu, std_total=sigma,
        p10=float(np.clip(dist.ppf(0.10), lo, hi)),
        p90=float(np.clip(dist.ppf(0.90), lo, hi)),
        median=mu,      # normal distribution: mean == median
        pmf_array=None, support_range=None,
    )
```

All percentiles must be clipped to [min_total, max_total].
The true distribution has hard bounds at these values; the normal extends beyond them.

### Startup benchmark

```python
def benchmark_fft_threshold(single: SingleHitPMF) -> int:
    """
    Call once at app startup. Assign return value to module-level FFT_THRESHOLD.
    Finds the highest N where _fft_exact completes in under 20ms on this machine.
    20ms target (not 100ms) leaves headroom for GUI render overhead during slider drags.
    """
    global FFT_THRESHOLD
    for n in [50, 75, 100, 125, 150]:
        t0 = time.perf_counter()
        _fft_exact(single, n)
        if (time.perf_counter() - t0) * 1000 > 20:
            FFT_THRESHOLD = max(n - 25, 10)
            return FFT_THRESHOLD
    FFT_THRESHOLD = 150
    return FFT_THRESHOLD
```

---

## Create: gui/histogram_widget.py

Widget receives a `MultiHitResult` and dispatches on `result.method`.

### method == "exact" (bar chart)

Bin the PMF array into 200–500 display bins using `np.add.reduceat`. Do not loop over bins.

```python
n_bins = min(500, len(result.pmf_array))
bin_edges = np.linspace(0, len(result.pmf_array), n_bins + 1, dtype=int)
bin_edges = np.unique(bin_edges)
bin_probs = np.add.reduceat(result.pmf_array, bin_edges[:-1])
bin_centers = [result.support_range[e] for e in bin_edges[:-1]]
# plot bin_centers vs bin_probs as bar chart
```

### method == "normal" (line curve)

```python
x = np.linspace(result.min_total, result.max_total, 500)
y = scipy.stats.norm.pdf(x, result.mean_total, result.std_total)
# plot x vs y as line
# do NOT render tails beyond min_total / max_total
```

### Annotations (both modes)

- Vertical dashed lines at `p10`, `median`, `p90` with text labels
- Shaded band between `mean_total - std_total` and `mean_total + std_total`
- Bracket markers at `min_total` and `max_total` on the x-axis
- Hover tooltip: damage value + cumulative probability (exact mode) or CDF value (normal mode)

---

## Performance Tests: tests/perf_multi_hit.py

Implement as a standalone script with no GUI dependency. Must run without a display.
Print PASS/FAIL per test. Store baseline timings to a JSON file for regression tracking.

### Test 1 — Per-method latency across N

```
worst_case_single = SingleHitPMF with support width 500, realistic mean/variance
for N in range(1, 151):
    time compute_multi_hit(worst_case_single, N) over 20 warm calls
    record min, max, mean latency
assert: all N <= FFT_THRESHOLD finish in < 20ms
assert: all N > FFT_THRESHOLD finish in < 1ms
warn:   any N where mean latency > 15ms
output: latency vs N table
```

### Test 2 — Cache effectiveness

```
clear _power_cache
T_cold = time compute_multi_hit(single, 75)
call compute_multi_hit(single, 74)   # primes cache
T_warm = time compute_multi_hit(single, 75)
assert: T_warm < T_cold * 0.3
simulate stat change: invalidate_caches(new_sig), verify T_cold is consistent
```

### Test 3 — CLT accuracy vs exact at crossover

```
for N in [50, 60, 70, 75, 80, 100]:
    exact = _fft_exact(single, N)
    approx = _clt_normal(single, N)
    compute max absolute CDF error across all integer damage values
    compute absolute error at p10, median, p90
assert for N >= 76: max CDF error < 2%, tail errors < 1.5%
output: accuracy table — re-run if single-hit PMF shape changes significantly
```

### Test 4 — End-to-end refresh budget

```
for N in [1, 50, 75, 100, 500, 1000]:
    invalidate_caches(new_sig)
    T = time(finalize SingleHitPMF + compute_multi_hit(single, N))
    assert T < 80ms
save baseline timings to tests/perf_baseline.json
```

Run Test 4 on the target deployment machine, not only dev machine.
Re-run all tests if any of the following change:
- single-hit PMF support width (new damage sources)
- multiplier chain (new skill ratios or floor-division steps)
- Python or scipy version
- deployment hardware

---

## Threshold Summary

| N range | Method | Rationale |
|---|---|---|
| 1 | Return exact PMF directly | Already computed |
| 2–75 | FFT binary exponentiation | Exact, ~2–12ms at W=500 |
| 76–1000 | CLT Normal | <1.5% CDF error, <1ms |

Threshold of 75 chosen at the point where:
- FFT at N=75 costs ~8ms (well within 20ms budget)
- CLT at N=76 has <1.5% max CDF error (visually indistinguishable on any rendered histogram)
- The exact PMF at N=75 is already near-Gaussian due to convolution smoothing, so no visual jump at the transition

`FFT_THRESHOLD` is overwritten at startup by `benchmark_fft_threshold()` to self-calibrate per machine.
