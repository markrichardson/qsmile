## MODIFIED Requirements

### Requirement: SVIModel represents raw SVI parameters
The system SHALL provide an `SVIModel` dataclass inheriting from `AbstractSmileModel` with fitted fields `a`, `b`, `rho`, `m`, and `sigma` representing the five raw SVI parameters. `SVIModel` SHALL carry `metadata: SmileMetadata`, `current_x_coord`, and `current_y_coord` inherited from `AbstractSmileModel`. `SVIModel` SHALL conform to the `SmileModel` protocol.

#### Scenario: Create SVIModel with metadata
- **WHEN** a user constructs `SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2, metadata=meta)`
- **THEN** all five parameters and metadata are stored and accessible as attributes
- **AND** `current_x_coord` SHALL default to `XCoord.LogMoneynessStrike`
- **AND** `current_y_coord` SHALL default to `YCoord.TotalVariance`

#### Scenario: SVIModel conforms to SmileModel
- **WHEN** an `SVIModel` instance is checked against the `SmileModel` protocol
- **THEN** the check SHALL pass (all required methods/properties are present)

### Requirement: SVIModel provides parameter serialisation
`SVIModel` SHALL inherit `to_array()` and `from_array()` from `AbstractSmileModel`. The serialisation SHALL produce `[a, b, rho, m, sigma]` based on `param_names`. `from_array` SHALL accept metadata.

#### Scenario: Round-trip serialisation
- **WHEN** `SVIModel.from_array(model.to_array(), metadata=model.metadata)` is called
- **THEN** the resulting `SVIModel` SHALL have the same field values

#### Scenario: from_array returns SVIModel instance
- **WHEN** `SVIModel.from_array(arr, metadata=meta)` is called
- **THEN** the result SHALL be an instance of `SVIModel` with the provided metadata

### Requirement: SVIModel supports transform and __call__
`SVIModel` SHALL inherit `transform()`, `__call__()`, `plot()`, and `params` from `AbstractSmileModel`.

#### Scenario: Transform SVI to FixedStrike/Volatility
- **WHEN** `model.transform(XCoord.FixedStrike, YCoord.Volatility)` is called
- **THEN** the returned model SHALL evaluate in FixedStrike × Volatility space via `__call__`

#### Scenario: Plot SVI model
- **WHEN** `model.plot()` is called
- **THEN** a matplotlib Figure SHALL be returned

#### Scenario: Access SVI params
- **WHEN** `model.params` is accessed
- **THEN** a dict `{"a": ..., "b": ..., "rho": ..., "m": ..., "sigma": ...}` SHALL be returned
