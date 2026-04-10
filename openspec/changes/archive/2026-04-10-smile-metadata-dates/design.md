## Context

`SmileMetadata` is a frozen dataclass carrying parameters needed by coordinate transforms: `expiry` (float), `forward`, `discount_factor`, and `sigma_atm`. It is constructed in two production code paths (`OptionChain.__post_init__` via `replace()`, and `SmileData.from_mid_vols`) and ~30 test sites. Every coordinate map, Black76 pricing function, and fitting routine reads `meta.expiry` as a float year fraction.

The change introduces date-awareness: `date` (valuation date) and `expiry` (expiry date) as `pd.Timestamp`, with `texpiry` derived via a `DayCount` convention. This replaces the raw float with richer, reproducible temporal data.

## Goals / Non-Goals

**Goals:**
- Store valuation date and expiry date as `pd.Timestamp` on `SmileMetadata`.
- Derive `texpiry: float` (year fraction) automatically from `(date, expiry, daycount)`.
- Introduce a `DayCount` enum with `year_fraction(start, end)` method and sensible default (`ACT365`).
- Maintain all existing coordinate-transform and pricing behaviour by migrating `meta.expiry` → `meta.texpiry`.
- Keep `SmileMetadata` frozen and immutable.

**Non-Goals:**
- Business-day calendars or holiday schedules — `DayCount` is a simple calendar-agnostic fraction.
- Changing `SABRModel.expiry` or any model-level expiry fields (they remain independent floats).
- Term-structure or multi-expiry containers — this is single-expiry metadata only.
- Timezone handling — timestamps are timezone-naive by convention.

## Decisions

### 1. Use `pd.Timestamp` for dates (not `datetime.date`)

**Choice**: `pd.Timestamp` for both `date` and `expiry`.

**Rationale**: The project already has pandas as a dev dependency and market data pipelines commonly deliver timestamps as `pd.Timestamp`. It provides nanosecond precision, natural arithmetic, and interoperates with `datetime.date` via `pd.Timestamp(date_obj)`. Using stdlib `datetime.date` would require conversion at every pandas boundary.

**Trade-off**: pandas becomes a production dependency (~30 MB). Acceptable given the project already depends on numpy/scipy/cvxpy.

**Alternative rejected**: `datetime.date` — avoids the dependency but creates friction in pandas-heavy workflows where all dates are already Timestamps.

### 2. DayCount as an `Enum` with a `year_fraction` method

**Choice**: `DayCount` is a Python `Enum` in `src/qsmile/core/daycount.py` with variants `ACT365` and `ACT360`. Each variant implements `year_fraction(start: pd.Timestamp, end: pd.Timestamp) -> float`.

**Rationale**: An enum is the simplest abstraction that supports dispatch on convention. Adding new conventions (30/360, BUS/252) later requires only a new enum member and its fraction logic.

**Default**: `ACT365` — the standard convention for equity and commodity options.

```python
class DayCount(Enum):
    ACT365 = "ACT/365"
    ACT360 = "ACT/360"

    def year_fraction(self, start: pd.Timestamp, end: pd.Timestamp) -> float:
        days = (end - start).days
        match self:
            case DayCount.ACT365:
                return days / 365.0
            case DayCount.ACT360:
                return days / 360.0
```

**Alternative rejected**: Protocol/ABC — over-engineered for simple calendar-agnostic fractions. An enum is sufficient and keeps the API surface minimal.

### 3. SmileMetadata field layout

**Choice**: New frozen dataclass fields:

```python
@dataclass(frozen=True)
class SmileMetadata:
    date: pd.Timestamp
    expiry: pd.Timestamp
    daycount: DayCount = DayCount.ACT365
    forward: float | None = None
    discount_factor: float | None = None
    sigma_atm: float | None = None

    @property
    def texpiry(self) -> float:
        return self.daycount.year_fraction(self.date, self.expiry)
```

**Rationale**:
- `texpiry` as a `@property` rather than a stored field: ensures consistency — it is always derived from `(date, expiry, daycount)` and never stale. No `__post_init__` computation needed for a frozen class (avoids `object.__setattr__` hacks).
- `daycount` defaults to `ACT365` so most callers don't need to specify it.
- `date` and `expiry` are required (positional) — you must always know both dates.
- Field order: `date`, `expiry` (required), then `daycount` (defaulted), then optional floats.

**Validation** in `__post_init__`:
- `expiry > date` (expiry must be strictly after valuation date).
- `forward`, `discount_factor`, `sigma_atm` validation unchanged (positive when not None).
- Remove the old `expiry > 0` check (replaced by date ordering).

**Alternative rejected**: `texpiry` as a stored `float` computed in `__post_init__` — requires `object.__setattr__` on a frozen class and risks inconsistency if `replace()` is used to change `daycount` without recomputing.

### 4. Migration of `meta.expiry` → `meta.texpiry` in downstream code

**Choice**: Mechanical rename — every `meta.expiry` (or `self.metadata.expiry`) that expects a float changes to `meta.texpiry` (or `self.metadata.texpiry`). No behavioural change.

**Scope**: `maps.py` (14 usages), `vols.py`, `prices.py`, all test files, notebooks, README.

### 5. `from_mid_vols` factory signature change

**Choice**: Replace `expiry: float` parameter with `date: pd.Timestamp` and `expiry: pd.Timestamp`, plus optional `daycount: DayCount = DayCount.ACT365`.

```python
@classmethod
def from_mid_vols(cls, strikes, ivs, forward, date, expiry, discount_factor=1.0, daycount=DayCount.ACT365):
```

**Rationale**: Aligns the factory with the new SmileMetadata constructor. The float year-fraction is no longer a user-facing input.

### 6. pandas as a production dependency

**Choice**: Add `pandas>=2.0,<3.1` to `project.dependencies` in `pyproject.toml`.

**Rationale**: Required for `pd.Timestamp`. The version range covers pandas 2.x and 3.x (currently 3.x in dev deps). Lower bound of 2.0 ensures modern Timestamp behaviour.

## Risks / Trade-offs

- **Larger install footprint** → pandas adds ~30 MB. Mitigated by the fact that the project already depends on numpy/scipy/cvxpy and users working with options data almost universally have pandas installed.
- **Breaking change for all SmileMetadata callers** → Every construction site changes. Mitigated by comprehensive test coverage (231 tests) and mechanical nature of the migration.
- **Property computation overhead** → `texpiry` is computed on every access. Mitigated by the computation being trivial (integer subtraction + division). If profiling shows hot-path overhead, it can be cached later via `__post_init__` + `object.__setattr__`.
