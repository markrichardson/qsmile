## REMOVED Requirements

### Requirement: Model supports __call__ as primary evaluation interface
**Reason**: `__call__` is removed from the model hierarchy. The coordinate-aware evaluation logic is now provided by `evaluate()` on `SmileModel`. Models are not callable — use `model.evaluate(x)` instead.
**Migration**: Replace `model(x)` with `model.evaluate(x)`.
