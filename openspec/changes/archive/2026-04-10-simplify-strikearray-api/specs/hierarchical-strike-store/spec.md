## MODIFIED Requirements

### Requirement: StrikeArray uses hierarchical DataFrame storage
The system SHALL store columns in a `pd.DataFrame` with a two-level `pd.MultiIndex` on columns. Level-0 SHALL represent the category (e.g. `"call"`, `"put"`, `"y"`) and level-1 SHALL represent the field (e.g. `"bid"`, `"ask"`, `"volume"`, `"open_interest"`). The DataFrame index SHALL be the sorted, positive, float64 strike array.

#### Scenario: Internal DataFrame has MultiIndex columns
- **WHEN** columns are added via `set(("call", "bid"), series)`, `set(("call", "ask"), series)`, `set(("put", "bid"), series)`, `set(("put", "ask"), series)`
- **THEN** the internal DataFrame SHALL have columns `("call", "bid")`, `("call", "ask")`, `("put", "bid")`, `("put", "ask")` as a two-level `MultiIndex`

#### Scenario: Volume and open interest stored hierarchically
- **WHEN** `set(("meta", "volume"), series)` and `set(("meta", "open_interest"), series)` are called
- **THEN** the internal DataFrame SHALL store them as `("meta", "volume")` and `("meta", "open_interest")` columns

### Requirement: StrikeArray adaptive union reindexing
When a new column is added whose strike index differs from the current global index, the system SHALL compute the sorted union of all strike indices and reindex every existing column to that union, inserting `NaN` for missing strikes.

#### Scenario: Adding column with new strikes extends index
- **WHEN** a `StrikeArray` has strikes `[100, 110, 120]` and a new column is added with strikes `[105, 110, 115]`
- **THEN** the global strike index SHALL become `[100, 105, 110, 115, 120]` and all columns SHALL be reindexed to the union

#### Scenario: Adding column with identical strikes preserves index
- **WHEN** a column is added with the same strike index as the existing global index
- **THEN** the global strike index SHALL remain unchanged

### Requirement: StrikeArray tuple-key setter
The system SHALL provide a single `set(key: tuple[str, str], series: pd.Series)` method that accepts a `(category, field)` tuple as the column key and a `pd.Series` whose index contains strike prices. The system SHALL NOT provide named setter convenience methods.

#### Scenario: Set a column with tuple key
- **WHEN** `set(("call", "bid"), pd.Series([5.0, 3.0, 1.0], index=[100, 110, 120]))` is called
- **THEN** `values(("call", "bid"))` SHALL return `[5.0, 3.0, 1.0]` and `strikes` SHALL be `[100, 110, 120]`

#### Scenario: Set an arbitrary column
- **WHEN** `set(("custom", "data"), series)` is called with an arbitrary tuple key
- **THEN** the column SHALL be stored and retrievable via `values(("custom", "data"))`

### Requirement: StrikeArray tuple-key read accessors
The system SHALL provide: `strikes` property (NDArray), `columns` property (list of `tuple[str, str]`), `values(key: tuple[str, str])` method (NDArray, raises `KeyError`), `get_values(key: tuple[str, str])` method (NDArray or None), `has(key: tuple[str, str])` method (bool), and `__len__` returning the number of strikes.

#### Scenario: Access strikes
- **WHEN** `strikes` is accessed on a populated `StrikeArray`
- **THEN** it SHALL return the sorted global strike index as an `NDArray[np.float64]`

#### Scenario: columns returns tuples
- **WHEN** `columns` is accessed on a `StrikeArray` with `("call", "bid")` and `("put", "ask")` columns
- **THEN** it SHALL return `[("call", "bid"), ("put", "ask")]`

#### Scenario: Access missing column
- **WHEN** `values(("nonexistent", "col"))` is called
- **THEN** the system SHALL raise `KeyError`

#### Scenario: get_values returns None for missing
- **WHEN** `get_values(("nonexistent", "col"))` is called
- **THEN** it SHALL return `None`

#### Scenario: has returns bool
- **WHEN** `has(("call", "bid"))` is called on a `StrikeArray` that has that column
- **THEN** it SHALL return `True`

### Requirement: StrikeArray to_dataframe
The system SHALL provide a `to_dataframe()` method returning a `pd.DataFrame` with the hierarchical `MultiIndex` columns and strikes as the index.

#### Scenario: to_dataframe returns hierarchical DataFrame
- **WHEN** `to_dataframe()` is called on a `StrikeArray` with `("call", "bid")` and `("put", "ask")` columns
- **THEN** the returned DataFrame SHALL have a two-level `MultiIndex` on columns and strikes as the row index

### Requirement: StrikeArray filter
The system SHALL provide a `filter(mask)` method that applies a boolean mask to all columns and the strike index, returning a new `StrikeArray`.

#### Scenario: Filter subsets all columns
- **WHEN** `filter(mask)` is called with a boolean array
- **THEN** the returned `StrikeArray` SHALL contain only the strikes and column values where the mask is `True`

### Requirement: StrikeArray validates per-column
The system SHALL validate that strike indices contain no duplicates when a column is added. The system SHALL raise `ValueError` for invalid strikes.

#### Scenario: Duplicate strikes rejected
- **WHEN** a column is added with duplicate strike values
- **THEN** the system SHALL raise `ValueError`

## REMOVED Requirements

### Requirement: StrikeArray named setters
**Reason**: Replaced by the generic `set(key: tuple[str, str], series)` method with direct tuple keys. Named setters (`set_call_bid`, `set_call_ask`, `set_put_bid`, `set_put_ask`, `set_volume`, `set_open_interest`) are no longer needed.
**Migration**: Replace `sa.set_call_bid(series)` with `sa.set(("call", "bid"), series)`. Replace `sa.set_volume(series)` with `sa.set(("meta", "volume"), series)`.
