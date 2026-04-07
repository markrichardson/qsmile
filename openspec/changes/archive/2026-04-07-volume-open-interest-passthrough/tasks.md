## 1. SmileData — add optional volume/open_interest fields

- [x] 1.1 Add `volume: NDArray[np.float64] | None = None` and `open_interest: NDArray[np.float64] | None = None` fields to `SmileData` dataclass
- [x] 1.2 Add validation in `__post_init__`: length check against `x`, non-negative check, coerce to float64 when provided
- [x] 1.3 Propagate `volume` and `open_interest` through `SmileData.transform()` return value
- [x] 1.4 Write tests for SmileData construction with/without volume and open_interest, validation errors, and transform passthrough

## 2. OptionChain — add optional volume/open_interest fields

- [x] 2.1 Add `volume: NDArray[np.float64] | None = None` and `open_interest: NDArray[np.float64] | None = None` fields to `OptionChain` dataclass
- [x] 2.2 Add validation in `__post_init__`: length check against `strikes`, non-negative check, coerce to float64 when provided
- [x] 2.3 Write tests for OptionChain construction with/without volume and open_interest, and validation errors

## 3. OptionChain conversions — pass through to SmileData

- [x] 3.1 Pass `volume` and `open_interest` through `to_smile_data()` to the returned SmileData
- [x] 3.2 Pass `volume` and `open_interest` (subset to valid strikes) through `to_smile_data_blended()` to the returned SmileData
- [x] 3.3 Pass `volume` and `open_interest` (subset by keep mask) through `denoise()` to the returned OptionChain
- [x] 3.4 Write tests for passthrough in `to_smile_data()`, `to_smile_data_blended()`, and `denoise()`

## 4. Verify backward compatibility

- [x] 4.1 Run full test suite (`make test`) and confirm all existing tests pass without modification
