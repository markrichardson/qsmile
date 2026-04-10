## 1. Remove TypeVar from protocol.py

- [x] 1.1 Delete `M = TypeVar("M", bound=SmileModel)` from `src/qsmile/models/protocol.py`

## 2. Simplify SmileResult and fit()

- [x] 2.1 In `src/qsmile/models/fitting.py`: remove `Generic` import and `M` import, make `SmileResult` a plain dataclass, rename `params: M` to `model: SmileModel`
- [x] 2.2 In `src/qsmile/models/fitting.py`: simplify `fit()` signature — `model` param becomes `type[SmileModel]`, `initial_guess` becomes `SmileModel | None`, return type becomes `SmileResult`
- [x] 2.3 In `src/qsmile/models/fitting.py`: update `SmileResult(params=...)` construction to `SmileResult(model=...)`

## 3. Update Tests

- [x] 3.1 In `tests/models/test_fitting.py`: replace all `result.params` with `result.model`
- [x] 3.2 In `tests/models/test_sabr_fitting.py`: replace all `result.params` with `result.model`

## 4. Update Notebook

- [x] 4.1 In `book/marimo/notebooks/qsmile_demo.py`: replace all `result.params` / `svi_result.params` / `sabr_result.params` with `.model`

## 5. Validate

- [x] 5.1 Run `make test` and fix any failures
- [x] 5.2 Run `make fmt` to ensure formatting compliance
