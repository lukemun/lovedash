import json
import sys
from datetime import datetime
import iso8601  # For parsing ISO datetimes; install with pip if needed
import argparse

# Constants from Sentry (hardcoded for standalone use)
MAX_WIDGETS = 30
DISPLAY_TYPES = ["line", "area", "stacked_area", "bar", "table", "big_number", "top_n"]
WIDGET_TYPES = ["issue", "metrics", "error-events", "transaction-like", "spans", "logs"]
MAX_QUERIES_PER_WIDGET = 10
MAX_TITLE_LENGTH = 255
GRID_COLUMNS = 6  # For layout validation

def validate_dashboard(data):
    errors = []
    # Title
    if "title" not in data or not isinstance(data["title"], str) or len(data["title"].strip()) == 0:
        errors.append("title: Required string, cannot be empty.")
    elif len(data["title"]) > MAX_TITLE_LENGTH:
        errors.append("title: Max 255 characters.")

    # Widgets
    widgets = data.get("widgets", [])
    if not isinstance(widgets, list):
        errors.append("widgets: Must be an array.")
    elif len(widgets) > MAX_WIDGETS:
        errors.append(f"widgets: Max {MAX_WIDGETS} allowed.")
    for i, widget in enumerate(widgets):
        errors.extend([f"widgets[{i}]: {err}" for err in validate_widget(widget)])

    # Projects
    projects = data.get("projects", [])
    if not isinstance(projects, list) or not all(isinstance(p, int) for p in projects):
        errors.append("projects: Must be an array of integers.")

    # Environment
    environment = data.get("environment", [])
    if not isinstance(environment, list) or not all(isinstance(e, str) for e in environment):
        errors.append("environment: Must be an array of strings.")

    # Period
    if "period" in data and not isinstance(data["period"], str):
        errors.append("period: Must be a string (e.g., '14d').")
    # Start/End
    if "start" in data and "end" in data:
        try:
            start = iso8601.parse_date(data["start"])
            end = iso8601.parse_date(data["end"])
            if start >= end:
                errors.append("start must be before end.")
        except iso8601.ParseError:
            errors.append("start/end: Must be valid ISO 8601 datetimes.")
    if "period" in data and ("start" in data or "end" in data):
        errors.append("period cannot be used with start/end.")

    # Filters
    filters = data.get("filters", {})
    if not isinstance(filters, dict):
        errors.append("filters: Must be an object.")
    for key in filters:
        if key not in ["release", "release_id"]:
            errors.append(f"filters[{key}]: Invalid key (only 'release' or 'release_id' allowed).")
        if not isinstance(filters[key], list):
            errors.append(f"filters[{key}]: Must be an array.")

    # UTC
    if "utc" in data and not isinstance(data["utc"], bool):
        errors.append("utc: Must be a boolean.")

    # Permissions
    permissions = data.get("permissions", {})
    if not isinstance(permissions, dict):
        errors.append("permissions: Must be an object.")
    if "isEditableByEveryone" in permissions and not isinstance(permissions["isEditableByEveryone"], bool):
        errors.append("permissions.isEditableByEveryone: Must be a boolean.")
    if "teamsWithEditAccess" in permissions:
        teams = permissions["teamsWithEditAccess"]
        if not isinstance(teams, list) or not all(isinstance(t, int) for t in teams):
            errors.append("permissions.teamsWithEditAccess: Must be an array of integers (team IDs).")

    return errors

def validate_widget(widget):
    errors = []
    if not isinstance(widget, dict):
        errors.append("Must be an object.")
        return errors

    # Title
    if "title" in widget and not isinstance(widget["title"], str):
        errors.append("title: Must be a string if provided.")
    elif "title" in widget and len(widget["title"]) > MAX_TITLE_LENGTH:
        errors.append("title: Max 255 characters.")

    # Description: no strict validation to match server tolerance

    # Display Type
    if "displayType" not in widget or widget["displayType"] not in DISPLAY_TYPES:
        errors.append(f"displayType: Required, one of: {', '.join(DISPLAY_TYPES)}")

    # Widget Type
    if "widgetType" in widget and widget["widgetType"] not in WIDGET_TYPES:
        errors.append(f"widgetType: Optional, one of: {', '.join(WIDGET_TYPES)}")

    # Queries
    queries = widget.get("queries", [])
    if not isinstance(queries, list) or len(queries) == 0:
        errors.append("queries: Required array with at least 1 query.")
    elif len(queries) > MAX_QUERIES_PER_WIDGET:
        errors.append(f"queries: Max {MAX_QUERIES_PER_WIDGET} per widget.")
    else:
        for i, query in enumerate(queries):
            errors.extend([f"queries[{i}]: {err}" for err in validate_query(query)])

    # Layout
    layout = widget.get("layout", {})
    if layout:
        if not isinstance(layout, dict):
            errors.append("layout: Must be an object.")
        else:
            for key in ["x", "y", "w", "h", "minH"]:
                if key in layout and not isinstance(layout[key], int):
                    errors.append(f"layout.{key}: Must be an integer.")
            if "x" in layout and not (0 <= layout["x"] < GRID_COLUMNS):
                errors.append(f"layout.x: 0 to {GRID_COLUMNS-1}.")
            if "w" in layout and not (1 <= layout["w"] <= GRID_COLUMNS):
                errors.append(f"layout.w: 1 to {GRID_COLUMNS}.")
            if "h" in layout and "minH" in layout and layout["h"] < layout["minH"]:
                errors.append("layout.h: Must be >= minH.")

    # Thresholds
    thresholds = widget.get("thresholds", {})
    if thresholds and not isinstance(thresholds, dict):
        errors.append("thresholds: Must be an object with numeric values.")
    else:
        for key in thresholds or {}:
            if not isinstance(thresholds[key], (int, float)):
                errors.append(f"thresholds.{key}: Must be a number.")

    # Interval
    if "interval" in widget and not isinstance(widget["interval"], str):
        errors.append("interval: String (e.g., '5m').")

    # Limit (do not error if missing for top_n; sanitizer sets default)
    if "limit" in widget and (not isinstance(widget["limit"], int) or not (1 <= widget["limit"] <= 10)):
        errors.append("limit: Integer 1-10.")

    # Incompatibilities based on displayType
    if widget.get("displayType") == "big_number" and isinstance(queries, list) and len(queries) > 1:
        errors.append("big_number displayType: Only 1 query allowed.")

    return errors

def validate_query(query):
    errors = []
    if not isinstance(query, dict):
        errors.append("Must be an object.")
        return errors

    # Name
    if "name" in query and (not isinstance(query["name"], str) or len(query["name"]) > MAX_TITLE_LENGTH):
        errors.append("name: String, max 255 characters.")

    # Check at least one of fields/aggregates/columns
    has_fields = "fields" in query and isinstance(query["fields"], list) and len(query["fields"]) > 0
    has_aggregates = "aggregates" in query and isinstance(query["aggregates"], list) and len(query["aggregates"]) > 0
    has_columns = "columns" in query and isinstance(query["columns"], list) and len(query["columns"]) > 0
    if not (has_fields or has_aggregates or has_columns):
        errors.append("Must have at least one of fields, aggregates, or columns.")

    # Conditions
    if "conditions" in query and not isinstance(query["conditions"], str):
        errors.append("conditions: String.")

    # Orderby
    if "orderby" in query and not isinstance(query["orderby"], str):
        errors.append("orderby: String (e.g., '-count').")

    # Field Aliases
    if "fieldAliases" in query:
        aliases = query["fieldAliases"]
        if not isinstance(aliases, list) or not all(isinstance(a, str) for a in aliases):
            errors.append("fieldAliases: Array of strings.")

    # Is Hidden
    if "isHidden" in query and not isinstance(query["isHidden"], bool):
        errors.append("isHidden: Boolean.")

    return errors

def sanitize_dashboard(data):
    """Trim known fields to satisfy schema limits (e.g., title max length) and set defaults."""
    if isinstance(data, dict):
        # Dashboard title
        if isinstance(data.get("title"), str) and len(data["title"]) > MAX_TITLE_LENGTH:
            data["title"] = data["title"][:MAX_TITLE_LENGTH]
        widgets = data.get("widgets", [])
        if isinstance(widgets, list):
            for widget in widgets:
                if not isinstance(widget, dict):
                    continue
                if isinstance(widget.get("title"), str) and len(widget["title"]) > MAX_TITLE_LENGTH:
                    widget["title"] = widget["title"][:MAX_TITLE_LENGTH]
                # Coerce description to string if provided and not a string
                if "description" in widget and not isinstance(widget["description"], str):
                    widget["description"] = ""
                # Default for top_n limit if missing
                if widget.get("displayType") == "top_n" and "limit" not in widget:
                    widget["limit"] = 5
    return data

def main():
    parser = argparse.ArgumentParser(description="Validate Sentry Dashboard JSON")
    parser.add_argument("path", help="Path to dashboard JSON file")
    parser.add_argument("--fix-out", dest="fix_out", help="Write a sanitized JSON to this path (truncates long titles, sets defaults)")
    args = parser.parse_args()

    try:
        with open(args.path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {args.path}")
        sys.exit(1)

    if args.fix_out:
        fixed = sanitize_dashboard(json.loads(json.dumps(data)))  # deep-ish copy
        with open(args.fix_out, 'w') as out:
            json.dump(fixed, out, indent=2)
        print(f"Sanitized JSON written to: {args.fix_out}")
        # Validate the sanitized output as well
        data = fixed

    errors = validate_dashboard(data)
    if errors:
        print("Validation failed with errors:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("Validation successful! The JSON matches the schema.")

if __name__ == "__main__":
    main()
