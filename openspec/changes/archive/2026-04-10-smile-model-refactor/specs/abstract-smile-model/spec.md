## MODIFIED Requirements

### Requirement: AbstractSmileModel is abstract
`AbstractSmileModel` SHALL be an abstract dataclass. Concrete subclasses MUST define `native_x_coord`, `native_y_coord`, `param_names`, `bounds`, `evaluate()`, and `initial_guess()`. Instances SHALL carry `metadata: SmileMetadata`, `current_x_coord: XCoord`, and `current_y_coord: YCoord` as instance fields. `current_x_coord` and `current_y_coord` SHALL default to the class-level `native_x_coord` and `native_y_coord`.

#### Scenario: Cannot instantiate AbstractSmileModel directly
- **WHEN** a user attempts to instantiate `AbstractSmileModel()` directly
- **THEN** a `TypeError` SHALL be raised

#### Scenario: Concrete subclass carries metadata and current coords
- **WHEN** a concrete subclass is instantiated with metadata
- **THEN** the instance SHALL have `metadata`, `current_x_coord`, and `current_y_coord` attributes

#### Scenario: Current coords default to native
- **WHEN** a concrete subclass is instantiated without explicit `current_x_coord`/`current_y_coord`
- **THEN** `current_x_coord` SHALL equal the class-level `native_x_coord`
- **AND** `current_y_coord` SHALL equal the class-level `native_y_coord`

### Requirement: AbstractSmileModel provides default to_array
`AbstractSmileModel` SHALL provide a default `to_array()` implementation that packs the values of all fields listed in `param_names` into a NumPy float64 array, in the order they appear in `param_names`.

#### Scenario: to_array uses param_names ordering
- **WHEN** `to_array()` is called on a subclass instance
- **THEN** the result SHALL be a NumPy array containing the values of fields listed in `param_names`, in order

### Requirement: AbstractSmileModel provides default from_array
`AbstractSmileModel` SHALL provide a default `from_array(x, metadata)` classmethod that reconstructs an instance by mapping array elements to the fields listed in `param_names`, in order, and attaching the provided `SmileMetadata`.

#### Scenario: from_array reconstructs instance with metadata
- **WHEN** `SubClass.from_array(arr, metadata=meta)` is called
- **THEN** the result SHALL be an instance of `SubClass` with parameter fields set from the array values and `metadata` set to the provided `SmileMetadata`

#### Scenario: from_array is a classmethod returning Self
- **WHEN** `from_array()` is called on a subclass
- **THEN** the return type SHALL be an instance of that subclass

### Requirement: AbstractSmileModel provides params property
`AbstractSmileModel` SHALL provide a `params` property that returns a dict mapping each name in `param_names` to its current value.

#### Scenario: Access params dict
- **WHEN** `model.params` is accessed on a concrete subclass
- **THEN** a dict SHALL be returned with keys matching `param_names` and values matching the model's parameter fields

### Requirement: AbstractSmileModel provides __call__
`AbstractSmileModel` SHALL provide a concrete `__call__(x)` method that evaluates the model at x values in `current_x_coord`/`current_y_coord`, transforming through native coordinates internally.

#### Scenario: __call__ in native coords equals evaluate
- **WHEN** `model(x)` is called and current coords equal native coords
- **THEN** the result SHALL equal `model.evaluate(x)`

#### Scenario: __call__ in non-native coords transforms correctly
- **WHEN** `model(x)` is called with current coords differing from native
- **THEN** x SHALL be transformed to native coords, evaluated, and output transformed back to current coords

### Requirement: AbstractSmileModel provides transform
`AbstractSmileModel` SHALL provide a `transform(target_x, target_y)` method returning a new model instance with updated `current_x_coord` and `current_y_coord`. Parameters and metadata SHALL be preserved.

#### Scenario: Transform returns new model with updated coords
- **WHEN** `model.transform(target_x, target_y)` is called
- **THEN** a new model instance SHALL be returned with `current_x_coord == target_x` and `current_y_coord == target_y`

### Requirement: AbstractSmileModel provides plot
`AbstractSmileModel` SHALL provide a `plot()` method that evaluates the model over a grid and returns a matplotlib Figure with the curve plotted in current coordinates.

#### Scenario: Plot returns a Figure
- **WHEN** `model.plot()` is called
- **THEN** a `matplotlib.figure.Figure` SHALL be returned

### Requirement: AbstractSmileModel subclasses satisfy SmileModel protocol
Any concrete subclass of `AbstractSmileModel` that defines all required ClassVars and methods SHALL satisfy the `SmileModel` protocol.

#### Scenario: Concrete subclass passes isinstance check
- **WHEN** a concrete subclass instance is checked against `SmileModel`
- **THEN** `isinstance(instance, SmileModel)` SHALL return `True`
