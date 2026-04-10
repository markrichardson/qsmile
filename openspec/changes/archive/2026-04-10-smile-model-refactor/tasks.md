## 1. Update SmileModel Protocol

- [x] 1.1 Update `SmileModel` protocol in `src/qsmile/models/protocol.py` to add `current_x_coord`, `current_y_coord`, `metadata`, `__call__`, `params`, `transform`, `plot` declarations
- [x] 1.2 Update `from_array` signature in protocol to accept `metadata: SmileMetadata`

## 2. Refactor AbstractSmileModel

- [x] 2.1 Add `metadata: SmileMetadata`, `current_x_coord: XCoord`, `current_y_coord: YCoord` fields to `AbstractSmileModel` with defaults from native coords
- [x] 2.2 Implement `params` property returning dict from `param_names`
- [x] 2.3 Implement `__call__(x)` with coordinate transforms: input x from current→native, evaluate, output y from native→current
- [x] 2.4 Implement `transform(target_x, target_y)` returning a copy with updated current coords
- [x] 2.5 Implement `plot()` method generating a line-plot figure in current coordinates
- [x] 2.6 Update `from_array()` to accept `metadata` parameter instead of `**kwargs`

## 3. Update SVIModel

- [x] 3.1 Update `SVIModel` constructor to accept `metadata` (remove any standalone context fields if present)
- [x] 3.2 Verify `SVIModel` conforms to updated `SmileModel` protocol and passes `isinstance` check

## 4. Update SABRModel

- [x] 4.1 Remove `expiry` and `forward` fields from `SABRModel` — they move to `metadata`
- [x] 4.2 Update `SABRModel.evaluate()` to read `self.metadata.texpiry` and `self.metadata.forward`
- [x] 4.3 Update `SABRModel.__post_init__()` validation to use metadata for expiry/forward checks
- [x] 4.4 Update `SABRModel.from_array()` to use metadata instead of `**kwargs`
- [x] 4.5 Verify `SABRModel` conforms to updated `SmileModel` protocol

## 5. Update Fitting Infrastructure

- [x] 5.1 Update `fit()` in `src/qsmile/models/fitting.py` to pass `metadata` to `from_array()` instead of context kwargs
- [x] 5.2 Remove `SmileResult.evaluate()` method (superseded by `result.params(x)`)
- [x] 5.3 Remove `fit_svi()` convenience function if present (superseded by generic `fit()`)

## 6. Update Package Exports

- [x] 6.1 Update `src/qsmile/__init__.py` exports: remove `fit_svi` if present, ensure new model interface is exported
- [x] 6.2 Update `src/qsmile/models/__init__.py` exports

## 7. Update Tests

- [x] 7.1 Rewrite `tests/models/` tests for `AbstractSmileModel` — cover `params`, `__call__`, `transform`, `plot`, metadata handling
- [x] 7.2 Rewrite `tests/models/` tests for `SVIModel` — construction with metadata, round-trip serialisation, transform, call, plot
- [x] 7.3 Rewrite `tests/models/` tests for `SABRModel` — construction with metadata (no expiry/forward fields), validation, evaluate, transform, call, plot
- [x] 7.4 Rewrite `tests/models/` tests for `fit()` — fitted model carries metadata and coords, `result.params(x)` works, no `result.evaluate`
- [x] 7.5 Run `make test` and fix any failures
- [x] 7.6 Run `make fmt` to ensure formatting compliance
