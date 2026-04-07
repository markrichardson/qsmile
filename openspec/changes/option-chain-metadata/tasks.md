## 1. SmileMetadata — make forward/discount_factor optional

- [x] 1.1 Change `forward` and `discount_factor` fields to `float | None = None` in `SmileMetadata`
- [x] 1.2 Update `__post_init__` validation to skip positive checks when value is `None`
- [x] 1.3 Add tests for constructing `SmileMetadata` with `None` forward/discount_factor

## 2. OptionChain — replace scalar fields with metadata

- [x] 2.1 Remove `expiry`, `forward`, `discount_factor` fields from `OptionChain`
- [x] 2.2 Add `metadata: SmileMetadata` field to `OptionChain`
- [x] 2.3 Update `__post_init__` to read expiry/forward/discount_factor from `self.metadata`, calibrate if `None`, and replace `self.metadata` with completed instance via `dataclasses.replace`
- [x] 2.4 Update `to_smile_data()` to source forward/discount_factor/expiry from `self.metadata`
- [x] 2.5 Update `filter()` to pass `metadata=SmileMetadata(expiry=self.metadata.expiry)` to the returned `OptionChain`

## 3. Tests

- [x] 3.1 Update all `OptionChain` construction calls in `tests/data/test_prices.py` to use `metadata=SmileMetadata(...)`
- [x] 3.2 Update all attribute accesses (`chain.forward` → `chain.metadata.forward`, etc.) in tests
- [x] 3.3 Verify `make test` passes with full coverage

## 4. Docs and notebooks

- [x] 4.1 Update `README.md` examples to use `metadata=SmileMetadata(...)`
- [x] 4.2 Update `book/marimo/notebooks/qsmile_demo.py` to construct `OptionChain` with metadata
- [x] 4.3 Update `book/marimo/notebooks/chain_demo.py` if it constructs `OptionChain`

## 5. Specs

- [x] 5.1 Run `make fmt` and `make test` to validate the complete change
