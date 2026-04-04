## Requirements

### Requirement: SVIModel represents raw SVI parameters
The system SHALL provide an `SVIModel` dataclass inheriting from `AbstractSmileModel` with fields `a`, `b`, `rho`, `m`, and `sigma` representing the five raw SVI parameters. `SVIModel` SHALL conform to the `SmileModel` protocol.

#### Scenario: Create SVIModel
- **WHEN** a user constructs `SVIModel(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)`
- **THEN** all five parameters are stored and accessible as attributes

#### Scenario: SVIModel conforms to SmileModel
- **WHEN** an `SVIModel` instance is checked against the `SmileModel` protocol
- **THEN** the check SHALL pass (all required methods/properties are present)

### Requirement: SVIModel provides parameter serialisation
`SVIModel` SHALL inherit `to_array()` and `from_array()` from `AbstractSmileModel`. The serialisation SHALL produce `[a, b, rho, m, sigma]` based on `param_names`.

#### Scenario: Round-trip serialisation
- **WHEN** `SVIModel.from_array(model.to_array())` is called
- **THEN** the resulting `SVIModel` SHALL have the same field values

#### Scenario: from_array returns SVIModel instance
- **WHEN** `SVIModel.from_array(arr)` is called
- **THEN** the result SHALL be an instance of `SVIModel`
