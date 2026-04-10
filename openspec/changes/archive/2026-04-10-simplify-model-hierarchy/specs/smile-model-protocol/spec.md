## REMOVED Requirements

### Requirement: SmileModel protocol defines the model contract
**Reason**: The Protocol is redundant — every model subclasses the ABC. The ABC is renamed to `SmileModel` and serves as both the base class and the type contract.
**Migration**: Replace `from qsmile.models.protocol import SmileModel` (Protocol) with the same import (now the ABC). Replace `isinstance(x, SmileModel)` — works identically with the ABC.

### Requirement: SmileModel declares native coordinates
**Reason**: Moved to the `SmileModel` ABC (formerly `AbstractSmileModel`). Requirement unchanged, just lives on the single class.
**Migration**: No code change needed — `model.native_x_coord` still works.

### Requirement: SmileModel declares current coordinates
**Reason**: Moved to the `SmileModel` ABC.
**Migration**: No code change needed.

### Requirement: SmileModel carries metadata
**Reason**: Moved to the `SmileModel` ABC.
**Migration**: No code change needed.

### Requirement: SmileModel provides parameter serialisation
**Reason**: Moved to the `SmileModel` ABC.
**Migration**: No code change needed.

### Requirement: SmileModel provides bounds
**Reason**: Moved to the `SmileModel` ABC.
**Migration**: No code change needed.

### Requirement: SmileModel provides evaluation
**Reason**: The Protocol's dual `evaluate`/`__call__` contract is removed. The ABC provides a single coordinate-aware `evaluate()`. See `abstract-smile-model` spec for the replacement.
**Migration**: Replace `model(x)` with `model.evaluate(x)`. Both now mean "evaluate in current coordinates."

### Requirement: SmileModel provides initial guess
**Reason**: Moved to the `SmileModel` ABC.
**Migration**: No code change needed.

### Requirement: SmileModel provides params property
**Reason**: Moved to the `SmileModel` ABC.
**Migration**: No code change needed.

### Requirement: SmileModel provides transform
**Reason**: Moved to the `SmileModel` ABC.
**Migration**: No code change needed.
