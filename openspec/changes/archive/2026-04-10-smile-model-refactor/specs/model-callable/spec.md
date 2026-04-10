## ADDED Requirements

### Requirement: Model supports __call__ as primary evaluation interface
`AbstractSmileModel` SHALL implement `__call__(x: ArrayLike) -> NDArray[np.float64]` as a concrete method that evaluates the model at x values in the current coordinate system.

#### Scenario: Call model directly
- **WHEN** `y = model(x)` is called with a NumPy array
- **THEN** y SHALL be a NumPy array of the same length containing model values in `current_y_coord`

#### Scenario: Call scalar input
- **WHEN** `y = model(0.0)` is called with a scalar
- **THEN** the result SHALL be a scalar float or single-element array

#### Scenario: Call delegates to evaluate for native coords
- **WHEN** `model(x)` is called and the model is in native coordinates
- **THEN** the result SHALL be identical to `model.evaluate(x)`
