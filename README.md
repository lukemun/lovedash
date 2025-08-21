# Lovedash - Sentry Dashboard Tools

A collection of tools for working with Sentry dashboards, including validation and schema documentation.

## Contents

- `standalone_dashboard_validator.py` - Standalone Python validator for Sentry dashboard JSON files
- `dashboard-schema.md` - Complete schema documentation for Sentry dashboard JSON format
- Example dashboard JSON files exported from Sentry

## Dashboard Validator

The standalone validator can validate Sentry dashboard JSON files without requiring a full Sentry server environment.

### Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install iso8601
```

### Usage

```bash
# Validate a dashboard JSON file
python standalone_dashboard_validator.py path/to/dashboard.json

# Auto-fix common issues and write sanitized output
python standalone_dashboard_validator.py path/to/dashboard.json --fix-out fixed_dashboard.json
```

### Features

- Validates dashboard structure, widgets, queries, and layout
- Enforces field types, constraints, and compatibility rules
- Can sanitize/fix common issues like overly long descriptions
- Provides detailed error messages for debugging

## Schema Documentation

See `dashboard-schema.md` for complete documentation of:

- Dashboard-level fields and constraints
- Widget structure and display types
- Query format and validation rules
- Layout grid system
- Permissions and filters

## Example Dashboards

The repository includes several example dashboard JSON files exported from Sentry:

- Frontend monitoring templates
- Web vitals dashboards
- Critical user journey tracking

These can be used as templates or for testing the validator.

