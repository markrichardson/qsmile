## ADDED Requirements

### Requirement: StrikeArray uses hierarchical DataFrame storage
The system SHALL store columns in a `pd.DataFrame` with a two-level `pd.MultiIndex` on columns. Level-0 SHALL represent the category (e.g. `"call"`, `"put"`, `"y"`) and level-1 SHALL represent the field (e.g. `"bid"`, `"ask"`, `"volume"`, `"open_interest"`). The DataFrame index SHALL be the sorted, positive, float64 strike array.

#### Scenario: Internal DataFrame has MultiIndex columns
- **WHEN** columns are added via `set_call_bid`, `set_call_ask`, `set_put_bid`, `set_put_ask`
- **THEN** the internal DataFrame SHALL have columns `("call", "bid")`, `("call", "ask")`, `("put", "bid")`, `("put", "ask")` as a two-level `MultiIndex`

#### Scenario: Volume and open interest stored hierarchically
- **WHEN** `set_volume` and `set_open_interest` are called
- **THEN** the internal DataFrame SHALL store them as `("call", "volume")`, `("call", "open_interest")`, `("put", "volume")`, `("put", "open_interest")` or as the appropriate category column depending on builder context

### Requirement: StrikeArray adaptive union reindexing
When a new column is added whose strike index differs from the current global index, the system SHALL compute the sorted union of all strike indices and reindex every existing column to that union, inserting `NaN` for missing strikes.

#### Scenario: Adding column with new strikes extends index
- **WHEN** a `StrikeArray` has strikes `[100, 110, 120]` and a new column is added with strikes `[105, 110, 115]`
- **THEN** the global strike index SHALL become `[100, 105, 110, 115, 120]` and all columns SHALL be reindexed to the union

#### Scenario: Adding column with identical strikes preserves index
- **WHEN** a column is added with the same strike index as the existing global index
- **THEN** the global strike index SHALL remain unchanged

### Requirement: StrikeArray named setters
The system SHALL provide builder-style setter methods: `set_call_bid(series)`, `set_call_ask(series)`, `set_put_bid(series)`, `set_put_ask(series)`, `set_volume(series)`, `set_open_interest(series)`. Each SHALL accept a `pd.Series` whose index contains strike prices.

#### Scenario: set_call_bid stores data
- **WHEN** `set_call_bid(pd.Series([5.0, 3.0, 1.0], index=[100, 110, 120]))` is called
- **THEN** `values("call_bid")` SHALL return `[5.0, 3.0, 1.0]` and `strikes` SHALL be `[100, 110, 120]`

#### Scenario: Generic set method
- **WHEN** `set(name, series)` is called with an arbitrary name
- **THEN** the column SHALL be stored and retrievable via `values(name)`

### Requirement: StrikeArray read accessors
The system SHALL provide: `strikes` property (NDArray), `columns` property (list of column names), `values(name)` method (NDArray, raises `KeyError`), `get_values(name)` method (NDArray or None), `has(name)` method (bool), and `__len__` returning the number of strikes.

#### Scenario: Access strikes
- **WHEN** `strikes` is accessed on a populated `StrikeArray`
- **THEN** it SHALL return the sorted global strike index as an `NDArray[np.float64]`

#### Scenario: Access missing column
- **WHEN** `values("nonexistent")` is called
- **THEN** the system SHALL raise `KeyError`

#### Scenario: get_values returns None for missing
- **WHEN** `get_values("nonexistent")` is called
- **THEN** it SHALL return `None`

### Requirement: StrikeArray to_dataframe
The system SHALL provide a `to_dataframe()` method returning a `pd.DataFrame` with the hierarchical `MultiIndex` columns and strikes as the index.

#### Scenario: to_dataframe returns hierarchical DataFrame
- **WHEN** `to_dataframe()` is called on a `StrikeArray` with call bid and put ask columns
- **THEN** the returned DataFrame SHALL have a two-level `MultiIndex` on columns and strikes as the row index

### Requirement: StrikeArray filter
The system SHALL provide a `filter(mask)` method that applies a boolean mask to all columns and the strike index, returning a new `StrikeArray`.

#### Scenario: Filter subsets all columns
- **WHEN** `filter(mask)` is called with a boolean array
- **THEN** the returned `StrikeArray` SHALL contain only the strikes and column values where the mask is `True`

### Requirement: StrikeArray validates per-column
The system SHALL validate that strike indices are positive and contain no duplicates when a column is added. The system SHALL raise `ValueError` for invalid strikes.

#### Scenario: Non-positive strike rejected
- **WHEN** a column is added with a strike value of 0 or negative
- **THEN** the system SHALL raise `ValueError`

#### Scenario: Duplicate strikes rejected
- **WHEN** a column is added with duplicate strike values
- **THEN** the system SHALL raise `ValueError`
