## ADDED Requirements

### Requirement: SmileModel protocol defines the model contract
The system SHALL provide a `SmileModel` `typing.Protocol` that every smile model must satisfy. The protocol SHALL declare: `native_x_coord` (XCoord), `native_y_coord` (YCoord), `param_names` (tuple of str), `bounds` (tuple of lower/upper lists), `evaluate(x: ArrayLike) -> NDArray`, `to_array() -> NDArray`, `from_array(x: NDArray) -> SmileModel`, and `initial_guess(x: NDArray, y: NDArray) -> NDArray`.

#### Scenario: A conforming model satisfies the protocol
- **WHEN** a class implements all required attributes and methods of `SmileModel`
- **THEN** `isinstance(instance, SmileModel)` SHALL return `True` at runtime (with `runtime_checkable`)

#### Scenario: A non-conforming class is rejected
- **WHEN** a class is missing one or more required methods
- **THEN** it SHALL NOT satisfy the `SmileModel` protocol check

### Requirement: SmileModel declares native coordinates
The `SmileModel` protocol SHALL require `native_x_coord: XCoord` and `native_y_coord: YCoord` properties that declare the coordinate system the model operates in natively.

#### Scenario: SVI declares LogMoneynessStrike and TotalVariance
- **WHEN** the SVI model's `native_x_coord` and `native_y_coord` are accessed
- **THEN** they SHALL return `XCoord.LogMoneynessStrike` and `YCoord.TotalVariance` respectively

### Requirement: SmileModel provides parameter serialisation
The protocol SHALL require `to_array() -> NDArray[np.float64]` to pack parameters into a flat array and `from_array(x: NDArray[np.float64]) -> SmileModel` to reconstruct a model instance from a flat array.

#### Scenario: Round-trip serialisation
- **WHEN** `from_array(model.to_array())` is called
- **THEN** the resulting model SHALL have parameters equal to the original within floating-point tolerance

### Requirement: SmileModel provides bounds
The protocol SHALL require a `bounds` property returning `tuple[list[float], list[float]]` (lower bounds, upper bounds) for the optimiser.

#### Scenario: Bounds length matches parameter count
- **WHEN** `bounds` is accessed on a conforming model
- **THEN** both lower and upper lists SHALL have length equal to `len(param_names)`

### Requirement: SmileModel provides evaluation
The protocol SHALL require an `evaluate(x: ArrayLike) -> NDArray[np.float64]` method that computes the model's output at the given x values in the model's native coordinate system.

#### Scenario: Evaluate at array of x values
- **WHEN** `evaluate(x)` is called with a NumPy array
- **THEN** the result SHALL be a NumPy array of the same length

### Requirement: SmileModel provides initial guess
The protocol SHALL require an `initial_guess(x: NDArray, y: NDArray) -> NDArray` class/static method that computes a heuristic starting point from observed data in native coordinates.

#### Scenario: Initial guess returns valid array
- **WHEN** `initial_guess(x, y)` is called with market data arrays
- **THEN** the result SHALL be a NumPy array with length equal to `len(param_names)`
