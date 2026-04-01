## 1. Coordinate Enums and Metadata

- [ ] 1.1 Create `src/qsmile/coords.py` with `XCoord` and `YCoord` enums
- [ ] 1.2 Create `src/qsmile/metadata.py` with frozen `SmileMetadata` dataclass and validation
- [ ] 1.3 Add tests for `XCoord`, `YCoord` enums (member count, distinctness)
- [ ] 1.4 Add tests for `SmileMetadata` (construction, validation, immutability)

## 2. Coordinate Maps

- [ ] 2.1 Create `src/qsmile/maps.py` with X-coordinate ladder maps (FixedStrike ↔ MoneynessStrike ↔ LogMoneynessStrike ↔ StandardisedStrike)
- [ ] 2.2 Add Y-coordinate ladder maps (Volatility ↔ Variance ↔ TotalVariance) to `maps.py`
- [ ] 2.3 Add Price ↔ Volatility Y-map using Black76 pricing and inversion
- [ ] 2.4 Implement map composition function that chains adjacent maps for arbitrary source→target
- [ ] 2.5 Add tests for each individual X-map (forward and inverse)
- [ ] 2.6 Add tests for each individual Y-map (forward and inverse)
- [ ] 2.7 Add tests for map composition (single-step, multi-step, identity)
- [ ] 2.8 Add round-trip property tests for X and Y map chains

## 3. SmileData Container

- [ ] 3.1 Create `src/qsmile/smile_data.py` with `SmileData` dataclass, validation, and `y_mid` property
- [ ] 3.2 Implement `SmileData.transform(target_x, target_y)` method using composed maps
- [ ] 3.3 Add tests for SmileData construction and validation
- [ ] 3.4 Add tests for `transform()` — identity, X-only, Y-only, combined, round-trip
- [ ] 3.5 Add test for transform error when sigma_atm is needed but absent

## 4. Integration with Existing Classes

- [ ] 4.1 Add `to_smile_data()` method to `OptionChainVols`
- [ ] 4.2 Add `to_smile_data()` method to `OptionChainPrices`
- [ ] 4.3 Add `to_smile_data()` method to `UnitisedSpaceVols`
- [ ] 4.4 Refactor `OptionChainVols.to_unitised()` to delegate to SmileData transform
- [ ] 4.5 Refactor `OptionChainVols.to_prices()` to delegate to SmileData transform
- [ ] 4.6 Refactor `OptionChainPrices.to_vols()` to delegate to SmileData transform
- [ ] 4.7 Refactor `UnitisedSpaceVols.to_vols()` to delegate to SmileData transform
- [ ] 4.8 Add tests for `to_smile_data()` on each class
- [ ] 4.9 Verify all existing tests still pass (regression)

## 5. Exports and Cleanup

- [ ] 5.1 Export new public symbols (`SmileMetadata`, `SmileData`, `XCoord`, `YCoord`) from `__init__.py`
- [ ] 5.2 Run `make fmt` and `make test` to confirm everything passes
- [ ] 5.3 Run `make deptry` to verify no missing/unused dependencies
