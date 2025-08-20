// dashboard-schema.md

# Sentry Dashboard JSON Schema

This schema describes the expected JSON format for importing dashboards into Sentry. It is based on the backend validation in `src/sentry/api/serializers/rest_framework/dashboard.py`.

## Dashboard Structure

The top-level object for a dashboard:

```json
{
  "title": "string",  // Required: Dashboard name (max 255 characters)
  "widgets": [  // Optional: Array of widget objects (max 30)
    // See Widget Structure below
  ],
  "projects": [integer],  // Optional: Array of project IDs
  "environment": ["string"],  // Optional: Array of environments
  "period": "string",  // Optional: Stats period (e.g., "14d")
  "start": "datetime",  // Optional: Custom start time (ISO format)
  "end": "datetime",  // Optional: Custom end time (ISO format)
  "filters": {  // Optional: Additional filters
    "release": ["string"],  // e.g., array of release versions
    "release_id": [integer]  // e.g., array of release IDs
  },
  "utc": boolean,  // Optional: Use UTC time (default: false)
  "permissions": {  // Optional: Edit permissions
    "isEditableByEveryone": boolean,  // Allow editing by all (default: false)
    "teamsWithEditAccess": [integer]  // Array of team IDs with edit access
  }
}
```

### Constraints

- `start` must be before `end` if both provided.
- Cannot mix `period` with custom `start`/`end`.
- Max widgets: 30.

## Widget Structure

Each widget in the `"widgets"` array:

```json
{
  "title": "string",  // Optional: Widget title (max 255 characters)
  "description": "string",  // Optional: Description (max 255 characters)
  "displayType": "string",  // Required: "line", "area", "stacked_area", "bar", "table", "big_number", "top_n"
  "widgetType": "string",  // Optional: "issue", "metrics", "error-events", "transaction-like", "spans", "logs"
  "queries": [  // Required: At least 1 query (max 10)
    {
      "name": "string",  // Optional: Query name (max 255 characters)
      "fields": ["string"],  // Required (or aggregates/columns): Fields to select
      "aggregates": ["string"],  // Optional: Aggregates (e.g., "count()")
      "columns": ["string"],  // Optional: Grouping columns
      "conditions": "string",  // Optional: Search conditions
      "orderby": "string",  // Optional: Sort order (e.g., "-count")
      "fieldAliases": ["string"],  // Optional: Aliases (must match fields length)
      "isHidden": boolean  // Optional: Hide query (default: false)
    }
  ],
  "layout": {  // Optional: Auto-assigned if omitted
    "x": integer,  // 0-5
    "y": integer,  // >=0
    "w": integer,  // 1-6
    "h": integer,  // >= min for type
    "minH": integer  // Min height
  },
  "thresholds": {  // Optional: Thresholds object
    "high": number,
    "low": number,
    "critical": number
  },
  "interval": "string",  // Optional: "5m", "1h", etc. (default: "5m")
  "limit": integer  // Optional: 1-10 (required for "top_n")
}
```

### Additional Notes

- Fields must be valid for `widgetType` (e.g., no transaction fields in "issue" widgets).
- Queries must be unique within a widget.
- For "big_number", only one query allowed, no groupings.
- Validation errors are returned as JSON objects with field-specific messages.

## Top-Level Dashboard Keys

The root of the JSON is a single object.

- **`title`**:

  - **Description**: The user-facing name of the dashboard.
  - **Type**: String.
  - **Required/Optional**: Required.
  - **Possible Values**: Any string (e.g., "My Errors Dashboard").
  - **Constraints/Incompatibilities**: Max length 255 characters. Cannot be empty.

- **`widgets`**:

  - **Description**: An array of widgets displayed on the dashboard.
  - **Type**: Array of widget objects (see Widget Keys below).
  - **Required/Optional**: Optional (defaults to empty array).
  - **Possible Values**: Array of valid widget objects (e.g., `[{"title": "Errors", "displayType": "line", ...}]`).
  - **Constraints/Incompatibilities**: Max 30 widgets. Cannot exceed this limit. Widgets must not overlap in layout (enforced during import).

- **`projects`**:

  - **Description**: Filters the dashboard to specific project IDs (limits data to those projects).
  - **Type**: Array of integers.
  - **Required/Optional**: Optional (defaults to all accessible projects).
  - **Possible Values**: Array of valid project IDs from your organization (e.g., `[1, 2]`).
  - **Constraints/Incompatibilities**: IDs must exist and be accessible to the user. If set to `[-1]` (a special value), it means "all projects". Cannot include invalid or inaccessible IDs.

- **`environment`**:

  - **Description**: Filters data to specific environments (e.g., prod, staging).
  - **Type**: Array of strings.
  - **Required/Optional**: Optional (defaults to all environments).
  - **Possible Values**: Array of environment names (e.g., `["prod", "staging"]`).
  - **Constraints/Incompatibilities**: Must be valid environments in your projects. Empty array means no filter.

- **`period`**:

  - **Description**: A relative time period for dashboard data (e.g., last 14 days).
  - **Type**: String.
  - **Required/Optional**: Optional (defaults to "14d" or system default).
  - **Possible Values**: Valid periods like "24h", "7d", "14d", "30d", "90d".
  - **Constraints/Incompatibilities**: Cannot be used with `start` and `end` (mutually exclusive; use one or the other). Must be a valid duration string.

- **`start`**:

  - **Description**: Custom start timestamp for the dashboard's time range.
  - **Type**: String (ISO 8601 datetime format).
  - **Required/Optional**: Optional.
  - **Possible Values**: Valid ISO datetime (e.g., "2023-01-01T00:00:00Z").
  - **Constraints/Incompatibilities**: Must be before `end` if both provided. Cannot be used with `period`. Must be a valid datetime.

- **`end`**:

  - **Description**: Custom end timestamp for the dashboard's time range.
  - **Type**: String (ISO 8601 datetime format).
  - **Required/Optional**: Optional.
  - **Possible Values**: Valid ISO datetime (e.g., "2023-01-31T23:59:59Z").
  - **Constraints/Incompatibilities**: Must be after `start` if both provided. Cannot be used with `period`. Must be a valid datetime.

- **`filters`**:

  - **Description**: Additional key-value filters applied to all widgets (e.g., by release).
  - **Type**: Object (key-value pairs).
  - **Required/Optional**: Optional (defaults to empty object).
  - **Possible Values**: Object with specific keys like `{"release": ["v1.0", "v2.0"], "release_id": [123, 456]}`.
  - **Constraints/Incompatibilities**: Keys must be valid filter types (currently only "release" and "release_id" are standard). Values are arrays. Cannot include invalid keys.

- **`utc`**:

  - **Description**: Whether to display times in UTC (instead of local timezone).
  - **Type**: Boolean.
  - **Required/Optional**: Optional (defaults to false).
  - **Possible Values**: `true` or `false`.
  - **Constraints/Incompatibilities**: None specific.

- **`permissions`**:
  - **Description**: Controls who can edit the dashboard.
  - **Type**: Object.
  - **Required/Optional**: Optional (defaults to creator-only edit access).
  - **Possible Values**: `{"isEditableByEveryone": true, "teamsWithEditAccess": [1, 2]}`.
  - **Constraints/Incompatibilities**: `teamsWithEditAccess` must be valid team IDs. Only the dashboard creator or org admins can set this. If `isEditableByEveryone` is true, team restrictions are ignored.

## Widget Keys (Inside `"widgets"` Array)

Each widget is an object in the array.

- **`id`**:

  - **Description**: Unique identifier for the widget.
  - **Type**: String (UUID format).
  - **Required/Optional**: Optional (auto-generated if omitted).
  - **Possible Values**: Valid UUID string (e.g., "123e4567-e89b-12d3-a456-426614174000").
  - **Constraints/Incompatibilities**: Must be unique within the dashboard. If provided, must not conflict with existing widgets.

- **`title`**:

  - **Description**: Display name of the widget.
  - **Type**: String.
  - **Required/Optional**: Optional (defaults to empty string).
  - **Possible Values**: Any string (e.g., "Error Counts").
  - **Constraints/Incompatibilities**: Max 255 characters.

- **`description`**:

  - **Description**: Additional notes or details about the widget.
  - **Type**: String.
  - **Required/Optional**: Optional.
  - **Possible Values**: Any string (e.g., "Shows errors over time").
  - **Constraints/Incompatibilities**: Max 255 characters.

- **`displayType`**:

  - **Description**: How the widget's data is visualized (chart type).
  - **Type**: String (enum).
  - **Required/Optional**: Required.
  - **Possible Values**: Exactly one of: "line", "area", "stacked_area", "bar", "table", "big_number", "top_n".
  - **Constraints/Incompatibilities**: Certain types incompatible with widget data (e.g., "big_number" can't have multiple queries or groupings; "top_n" requires `limit`). Must match query structure (e.g., "table" needs columns).

- **`widgetType`**:

  - **Description**: The data source/type for the widget.
  - **Type**: String (enum).
  - **Required/Optional**: Optional (inferred from queries if omitted).
  - **Possible Values**: Exactly one of: "issue", "metrics", "error-events", "transaction-like", "spans", "logs".
  - **Constraints/Incompatibilities**: Queries must align with type (e.g., no transaction fields in "issue"; "metrics" requires release-health feature). Cannot mix incompatible query fields.

- **`queries`**:

  - **Description**: Defines what data the widget fetches (e.g., filters, fields).
  - **Type**: Array of query objects (see Query Keys below).
  - **Required/Optional**: Required (at least 1 query).
  - **Possible Values**: Array of valid query objects (e.g., `[{"fields": ["count()"], "conditions": "event.type:error"}]`).
  - **Constraints/Incompatibilities**: Max 10 queries. Queries must be unique within widget. For "big_number", only 1 query allowed. Must have at least one of fields/aggregates/columns.

- **`layout`**:

  - **Description**: Position and size on the dashboard grid.
  - **Type**: Object.
  - **Required/Optional**: Optional (auto-assigned if omitted).
  - **Possible Values**: `{"x": 0, "y": 0, "w": 2, "h": 2, "minH": 2}`.
  - **Constraints/Incompatibilities**: x: 0-5, y: >=0, w: 1-6, h: >= minH (varies by displayType, e.g., 1 for "big_number"). Cannot overlap other widgets. minH must >= displayType minimum.

- **`thresholds`**:

  - **Description**: Alerting thresholds for values (e.g., color-coding).
  - **Type**: Object with numeric keys.
  - **Required/Optional**: Optional.
  - **Possible Values**: `{"high": 100, "low": 10, "critical": 500}`.
  - **Constraints/Incompatibilities**: Only for certain widgetTypes (e.g., "metrics"). Values must be numbers. No specific incompatibilities, but ignored if not applicable.

- **`interval`**:

  - **Description**: Time bucketing for data (e.g., group by 5 minutes).
  - **Type**: String.
  - **Required/Optional**: Optional (defaults to "5m").
  - **Possible Values**: Valid intervals like "1m", "5m", "15m", "1h", "1d", "1w", "30d".
  - **Constraints/Incompatibilities**: Must be a valid duration. Shorter intervals may not work with long periods (performance constraint, not hard validation).

- **`limit`**:
  - **Description**: Max number of results (e.g., for "top_n" or tables).
  - **Type**: Integer.
  - **Required/Optional**: Optional (required for "top_n").
  - **Possible Values**: 1-10 (e.g., 5).
  - **Constraints/Incompatibilities**: Only 1-10. Required and enforced for "top_n" displayType. Ignored or invalid for other types (e.g., can't use with "big_number").

## Query Keys (Inside `"queries"` Array)

Each query is an object in the array.

- **`id`**:

  - **Description**: Unique ID for the query within the widget.
  - **Type**: String (UUID format).
  - **Required/Optional**: Optional (auto-generated).
  - **Possible Values**: Valid UUID.
  - **Constraints/Incompatibilities**: Must be unique within widget.

- **`name`**:

  - **Description**: Label for the query (e.g., series name in charts).
  - **Type**: String.
  - **Required/Optional**: Optional (defaults to empty).
  - **Possible Values**: Any string (e.g., "Fatal Errors").
  - **Constraints/Incompatibilities**: Max 255 characters.

- **`fields`**:

  - **Description**: Fields to select (combines raw fields and aggregates).
  - **Type**: Array of strings.
  - **Required/Optional**: Required if no `aggregates` or `columns` (at least one of these three must be present).
  - **Possible Values**: Valid fields/functions (e.g., `["project", "count()"]`).
  - **Constraints/Incompatibilities**: Must be valid for `widgetType` (e.g., no "transaction.duration" in "issue"). Cannot duplicate aggregates/columns.

- **`aggregates`**:

  - **Description**: Aggregate functions (e.g., for metrics).
  - **Type**: Array of strings.
  - **Required/Optional**: Optional (but required for metrics-like widgets).
  - **Possible Values**: Valid aggregates (e.g., `["count()", "p95(duration)"]`).
  - **Constraints/Incompatibilities**: Must match `widgetType` (e.g., percentile functions only for "transaction-like"). Cannot mix with incompatible `fields`.

- **`columns`**:

  - **Description**: Columns for grouping (e.g., in tables).
  - **Type**: Array of strings.
  - **Required/Optional**: Optional (required for "table" or "top_n").
  - **Possible Values**: Valid column names (e.g., `["project", "transaction"]`).
  - **Constraints/Incompatibilities**: Must be valid for `widgetType`. Required for certain `displayType` (e.g., "table").

- **`conditions`**:

  - **Description**: Filter query string.
  - **Type**: String.
  - **Required/Optional**: Optional.
  - **Possible Values**: Valid search syntax (e.g., "event.type:error level:fatal").
  - **Constraints/Incompatibilities**: Must parse successfully. Cannot use invalid operators.

- **`orderby`**:

  - **Description**: Sort order.
  - **Type**: String.
  - **Required/Optional**: Optional.
  - **Possible Values**: Field with direction (e.g., "-count" for descending).
  - **Constraints/Incompatibilities**: Must reference a field in `fields`/`aggregates`/`columns`. Invalid for some displayTypes (e.g., "big_number").

- **`fieldAliases`**:

  - **Description**: Custom names for fields/aggregates/columns.
  - **Type**: Array of strings.
  - **Required/Optional**: Optional.
  - **Possible Values**: Array matching length of fields/etc. (e.g., `["Project Name", "Error Count"]`).
  - **Constraints/Incompatibilities**: Length must match combined fields/aggregates/columns. Max 255 chars per alias.

- **`isHidden`**:
  - **Description**: Hide this query from display (e.g., for internal calculations).
  - **Type**: Boolean.
  - **Required/Optional**: Optional (defaults to false).
  - **Possible Values**: `true` or `false`.
  - **Constraints/Incompatibilities**: None specific, but if all queries are hidden, the widget may not render.

## Additional Notes

- Fields must be valid for `widgetType` (e.g., no transaction fields in "issue" widgets).
- Queries must be unique within a widget.
- For "big_number", only one query allowed, no groupings.
- Validation errors are returned as JSON objects with field-specific messages.
