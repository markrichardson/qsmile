## ADDED Requirements

### Requirement: Model can transform to arbitrary coordinate system
`AbstractSmileModel` SHALL provide a `transform(target_x: XCoord, target_y: YCoord)` method that returns a new model instance expressed in the target coordinate system. The returned model SHALL have `current_x_coord == target_x` and `current_y_coord == target_y`. The underlying parameters and `evaluate()` behavior SHALL be unchanged.

#### Scenario: Transform SVI from native to FixedStrike/Volatility
- **WHEN** `model.transform(XCoord.FixedStrike, YCoord.Volatility)` is called on an SVI model in native coords
- **THEN** the returned model SHALL have `current_x_coord == XCoord.FixedStrike` and `current_y_coord == YCoord.Volatility`
- **AND** the original model's `current_x_coord` and `current_y_coord` SHALL be unchanged

#### Scenario: Transform preserves parameters
- **WHEN** `transformed = model.transform(target_x, target_y)` is called
- **THEN** `transformed.params` SHALL equal `model.params`
- **AND** `transformed.evaluate(x)` in native coords SHALL produce the same result as `model.evaluate(x)`

#### Scenario: Identity transform
- **WHEN** `model.transform(model.current_x_coord, model.current_y_coord)` is called
- **THEN** the returned model SHALL behave identically to the original

### Requirement: Model carries current coordinate system
`AbstractSmileModel` SHALL have `current_x_coord` and `current_y_coord` attributes that indicate the coordinate system the model is currently expressed in. These SHALL default to `native_x_coord` and `native_y_coord` respectively.

#### Scenario: Default current coords equal native coords
- **WHEN** a model is constructed without specifying current coordinates
- **THEN** `model.current_x_coord` SHALL equal `model.native_x_coord`
- **AND** `model.current_y_coord` SHALL equal `model.native_y_coord`

#### Scenario: Current coords updated by transform
- **WHEN** `model.transform(XCoord.FixedStrike, YCoord.Variance)` is called
- **THEN** the returned model's `current_x_coord` SHALL be `XCoord.FixedStrike`
- **AND** the returned model's `current_y_coord` SHALL be `YCoord.Variance`

### Requirement: Model carries SmileMetadata
`AbstractSmileModel` SHALL have a `metadata: SmileMetadata` attribute providing the market context (forward, expiry, discount factor, sigma_atm) needed for coordinate transforms.

#### Scenario: Metadata available after construction
- **WHEN** a model is constructed with metadata
- **THEN** `model.metadata` SHALL return the provided `SmileMetadata` instance

#### Scenario: Metadata used in transforms
- **WHEN** `model.transform(XCoord.FixedStrike, YCoord.Volatility)` is called
- **THEN** the transform SHALL use `model.metadata` for forward, sigma_atm, and texpiry values

### Requirement: __call__ evaluates in current coordinates
`AbstractSmileModel` SHALL implement `__call__(x)` that evaluates the model at x values expressed in `current_x_coord` and returns y values in `current_y_coord`. When current coords differ from native coords, the input SHALL be transformed to native coords before `evaluate()`, and the output SHALL be transformed from native coords to current coords.

#### Scenario: Call in native coordinates
- **WHEN** `model(x)` is called and `current_x_coord == native_x_coord` and `current_y_coord == native_y_coord`
- **THEN** the result SHALL equal `model.evaluate(x)`

#### Scenario: Call in non-native coordinates
- **WHEN** a model in (FixedStrike, Volatility) is called with strike values
- **THEN** the system SHALL transform strikes to native x-coords, evaluate, and transform the result to Volatility
- **AND** the result SHALL be numerically consistent with the equivalent `SmileData.transform()` operation
