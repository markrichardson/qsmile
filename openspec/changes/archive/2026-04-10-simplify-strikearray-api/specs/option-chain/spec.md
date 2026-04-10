## MODIFIED Requirements

### Requirement: OptionChain stores market data
The system SHALL provide an `OptionChain` dataclass that holds `strikedata: StrikeArray` and `metadata: SmileMetadata` as its core fields. The `StrikeArray` SHALL contain call/put bid/ask price columns keyed as `("call", "bid")`, `("call", "ask")`, `("put", "bid")`, `("put", "ask")`. The `metadata` parameter SHALL be a `SmileMetadata` instance provided by the caller at construction time. `expiry` on the metadata SHALL always be provided (not None). `forward` and `discount_factor` on the metadata MAY be None, in which case they SHALL be calibrated from put-call parity during `__post_init__`.

#### Scenario: Construct OptionChain with StrikeArray and full metadata
- **WHEN** a user creates an `OptionChain` with a populated `StrikeArray` (containing `("call", "bid")`, `("call", "ask")`, `("put", "bid")`, `("put", "ask")` columns) and full metadata
- **THEN** all metadata fields SHALL be stored and accessible

#### Scenario: Construct OptionChain with metadata needing calibration
- **WHEN** a user creates an `OptionChain` with a populated `StrikeArray` and metadata where forward and discount_factor are None
- **THEN** `chain.metadata.forward` and `chain.metadata.discount_factor` SHALL be calibrated from put-call parity and SHALL be positive floats (not None)

#### Scenario: Construct OptionChain with only forward needing calibration
- **WHEN** a user creates an `OptionChain` with metadata where discount_factor is provided but forward is None
- **THEN** `chain.metadata.forward` SHALL be calibrated from put-call parity

#### Scenario: Non-positive expiry rejected
- **WHEN** the metadata's expiry is zero or negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: OptionChain validates inputs
The system SHALL validate option chain data on construction by reading from the `StrikeArray` using tuple keys, rejecting invalid inputs with clear error messages.

#### Scenario: Non-positive strike
- **WHEN** any strike value in the `StrikeArray` is zero or negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Fewer than three data points
- **WHEN** the `StrikeArray` contains fewer than 3 strikes
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Negative prices rejected
- **WHEN** any price value in a call or put column is negative
- **THEN** the system SHALL raise a `ValueError`

#### Scenario: Bid exceeds ask rejected
- **WHEN** any `("call", "bid")` value exceeds the corresponding `("call", "ask")`, or any `("put", "bid")` exceeds `("put", "ask")`
- **THEN** the system SHALL raise a `ValueError`

### Requirement: OptionChain accepts optional volume data
The system SHALL accept volume data via the `StrikeArray`'s `set(("meta", "volume"), series)` method. If no volume column is present in the `StrikeArray`, volume SHALL be treated as absent.

#### Scenario: OptionChain with volume in StrikeArray
- **WHEN** the `StrikeArray` has a `("meta", "volume")` column set before constructing `OptionChain`
- **THEN** the volume data SHALL be accessible via `chain.strikedata.values(("meta", "volume"))`

#### Scenario: OptionChain without volume
- **WHEN** the `StrikeArray` has no volume column
- **THEN** `chain.strikedata.get_values(("meta", "volume"))` SHALL return `None`

#### Scenario: Negative volume rejected
- **WHEN** any value in the volume column is negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: OptionChain accepts optional open interest data
The system SHALL accept open interest data via the `StrikeArray`'s `set(("meta", "open_interest"), series)` method. If no open interest column is present in the `StrikeArray`, open interest SHALL be treated as absent.

#### Scenario: OptionChain with open interest in StrikeArray
- **WHEN** the `StrikeArray` has a `("meta", "open_interest")` column set before constructing `OptionChain`
- **THEN** the open interest data SHALL be accessible via `chain.strikedata.values(("meta", "open_interest"))`

#### Scenario: OptionChain without open interest
- **WHEN** the `StrikeArray` has no open_interest column
- **THEN** `chain.strikedata.get_values(("meta", "open_interest"))` SHALL return `None`

#### Scenario: Negative open interest rejected
- **WHEN** any value in the open_interest column is negative
- **THEN** the system SHALL raise a `ValueError`

### Requirement: OptionChain filter preserves volume and open interest
The `filter()` method SHALL delegate to `StrikeArray.filter(mask)`, which propagates all columns including volume and open interest. If the source columns are absent, the filtered `StrikeArray` SHALL also lack them.

#### Scenario: Filter subsets volume and open interest
- **WHEN** `filter()` is called on an `OptionChain` whose `StrikeArray` has volume and open_interest columns
- **THEN** the returned chain's `StrikeArray` SHALL contain only the entries corresponding to the surviving strikes

#### Scenario: Filter with absent volume and open interest
- **WHEN** `filter()` is called on an `OptionChain` whose `StrikeArray` lacks volume and open_interest columns
- **THEN** the returned chain's `StrikeArray` SHALL also lack those columns
