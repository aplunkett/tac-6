# Feature: One Click Table & Query Result Exports

## Metadata
issue_number: `1`
adw_id: `6ef1c4a6`
issue_json: `{"number":1,"title":"One click table exports","body":"Using ads_plan_build_review add one click table exports and one click result feature to get results as csv files.\nCreate two new endpoints to support these features. One exporting tables, one for exporting query results.\nPlace a download button directly to the left of the 'x' icon for available tables.\nPlace a download button directly to the left of the 'hide' button for query results.\nUse the appropriate download icon."}`

## Feature Description
Add one-click CSV export capabilities to the Natural Language SQL Interface. Users will be able to:

1. **Export an available table** as a CSV file by clicking a download button placed directly to the left of the `×` (remove) icon on each table card in the "Available Tables" section.
2. **Export the current query results** as a CSV file by clicking a download button placed directly to the left of the `Hide` button in the "Query Results" header.

Two new backend endpoints support these features: one streams a full table as CSV, and one streams the results of a SQL query as CSV. Both leverage the existing SQL-security layer so identifiers and queries remain validated before execution.

This provides immediate value: users can extract their uploaded data and AI-generated query results into a portable, spreadsheet-friendly format without manually copying rows.

## User Story
As a user of the Natural Language SQL Interface
I want to download tables and query results as CSV files with a single click
So that I can use my data and analysis results in spreadsheets and other tools without manual copying

## Problem Statement
Currently, the application can display tables and query results in the browser, but there is no way to extract that data. Users who want to work with their data outside the app (e.g., in Excel, Google Sheets, or other analysis tools) have no built-in export path and must manually copy data out of the rendered HTML table, which is error-prone and impractical for large result sets.

## Solution Statement
Add two new backend GET/POST endpoints that return CSV files via FastAPI `StreamingResponse` with an `attachment` `Content-Disposition` header:

1. `GET /api/export/table/{table_name}` — validates the table name with the existing security module, reads all rows from the table, and streams them as CSV.
2. `POST /api/export/query` — accepts a SQL query (already generated and shown to the user from `/api/query`), validates it with the existing security module, executes it, and streams the results as CSV.

On the client, add two icon buttons that follow the existing `.remove-table-button` styling pattern and use a download (down-arrow into tray) SVG icon. Each button triggers a fetch of the corresponding endpoint, converts the response to a Blob, and downloads it via a temporary anchor element. Both endpoints reuse existing security helpers (`validate_identifier`, `validate_sql_query`, `execute_query_safely`/`execute_sql_safely`) so no new SQL-injection surface is introduced. CSV generation uses the already-installed `pandas` dependency for consistency with the existing file-processing code.

## Relevant Files
Use these files to implement the feature:

### Backend
- `app/server/server.py` — Main FastAPI app where all endpoints are defined. Add the two new export endpoints here, following the existing endpoint patterns (e.g. `delete_table` at lines 270-305 for path-param validation, and `process_natural_language_query` at lines 111-148 for the query flow). Will need a new `from fastapi.responses import StreamingResponse` import.
- `app/server/core/data_models.py` — Pydantic models. Add a request model for the query export endpoint (e.g. `ExportQueryRequest` mirroring the relevant fields of `QueryRequest`).
- `app/server/core/sql_security.py` — Security helpers: `validate_identifier`, `escape_identifier`, `validate_sql_query`, `execute_query_safely`, `check_table_exists`. Reuse these; do not write new SQL string handling.
- `app/server/core/sql_processor.py` — `execute_sql_safely(sql_query)` returns `{'results', 'columns', 'error'}`; reuse for the query export endpoint. `get_database_schema()` for listing/validating tables.
- `app/server/core/file_processor.py` — Reference for the existing pandas usage pattern (`pd.read_csv`, `df.to_sql`); mirror its style when generating CSV with `df.to_csv`.
- `app/server/pyproject.toml` — Confirms `pandas==2.3.0` is already a dependency (no new library required). Python stdlib `csv` and `io` are also available.
- `app/server/tests/test_sql_processor.py` — Reference test patterns (fixtures, `test_db`, assertion style) for adding new endpoint tests.
- `app/server/tests/test_sql_injection.py` — Reference for security-focused test patterns to ensure the new endpoints reject malicious identifiers/queries.

### Frontend
- `app/client/src/main.ts` — All UI logic. `displayTables()` (lines 254-323) renders the table cards and the remove `×` button (lines 288-295) — add the table download button immediately before `tableHeader.appendChild(removeButton)`. `displayResults()` (lines 184-219) renders results and wires up the `Hide` toggle button — add the results download button to the results header to the left of the `Hide` button. Reuse the in-scope `response` (sql + columns) for the results export.
- `app/client/index.html` — Contains the static `results-header` markup with the `<h2>Query Results</h2>` and `<button id="toggle-results">Hide</button>` (lines 32-39). The download button for results can be added here statically or created in `main.ts`; prefer creating/inserting it in `main.ts` so it is wired with the active query's SQL.
- `app/client/src/api/client.ts` — API client. Add two methods (`exportTableCSV(tableName)` and `exportQueryCSV(sql)`) that fetch the new endpoints and return `Blob` (not JSON — these must NOT go through the JSON-parsing `apiRequest` helper; use `fetch` + `response.blob()` directly with the same `API_BASE_URL` base).
- `app/client/src/types.d.ts` — TypeScript type definitions (`QueryResponse`, `TableSchema`, etc.). Reference for the shape of data available to the download handlers.
- `app/client/src/style.css` — Global CSS. Add a `.download-table-button` / `.download-results-button` style mirroring `.remove-table-button` (lines 316-334) but using the primary color on hover.

### Documentation / Testing references (read before implementing UI test)
- `.claude/commands/test_e2e.md` — Read to understand how E2E tests are executed.
- `.claude/commands/e2e/test_basic_query.md` — Read as the template/example for authoring a new E2E test file (structure: User Story, Test Steps, Success Criteria).
- `README.md` — Project overview, API endpoint list (update the "API Endpoints" section to document the two new endpoints), and start/stop commands.

### New Files
- `.claude/commands/e2e/test_csv_exports.md` — New E2E test file validating both the table export and query-result export buttons, with screenshots.

## Implementation Plan
### Phase 1: Foundation
Add the CSV-generation backend foundation. Introduce a `StreamingResponse` import in `server.py` and a small shared helper approach for turning a list-of-row-dicts + columns into a CSV byte/string stream using pandas (`pd.DataFrame(...).to_csv(index=False)`). Add the `ExportQueryRequest` Pydantic model to `data_models.py`. All identifier/query validation must reuse the existing `sql_security` helpers.

### Phase 2: Core Implementation
Implement the two endpoints in `server.py`:
- `GET /api/export/table/{table_name}` — validate identifier, confirm table exists, select all rows safely, build CSV, return as `StreamingResponse` with `Content-Disposition: attachment; filename="{table_name}.csv"`.
- `POST /api/export/query` — accept `ExportQueryRequest` (the SQL string), validate/execute via `execute_sql_safely`, build CSV, return as `StreamingResponse` with `Content-Disposition: attachment; filename="query_results.csv"`.

Add backend unit/integration tests for both endpoints (success + invalid identifier + dangerous query + nonexistent table).

### Phase 3: Integration
Wire up the client:
- Add `exportTableCSV` and `exportQueryCSV` to `api/client.ts`.
- Add the download buttons in `main.ts` (`displayTables` for tables, `displayResults` for results) with download SVG icons, positioned exactly as specified.
- Add CSS for the download buttons.
- Add download handler functions that fetch the Blob and trigger a browser download via a temporary anchor element.
- Create the E2E test and update README documentation.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Add the query export request model
- In `app/server/core/data_models.py`, add an `ExportQueryRequest` Pydantic model with a `sql: str` field (the validated SQL the client already received from `/api/query`). Keep it minimal and consistent with existing model style.

### Task 2: Implement the table export endpoint
- In `app/server/server.py`, add `from fastapi.responses import StreamingResponse` to the imports.
- Add `GET /api/export/table/{table_name}`:
  - Validate `table_name` with `validate_identifier(table_name, "table")`; raise `HTTPException(400, ...)` on `SQLSecurityError`.
  - Open a SQLite connection to `db/database.db` and use `check_table_exists`; raise `HTTPException(404, ...)` if missing.
  - Select all rows safely via `execute_query_safely(conn, "SELECT * FROM {table}", identifier_params={'table': table_name})`, gathering column names from `cursor.description`.
  - Build CSV using pandas: `df = pd.DataFrame(rows, columns=columns); csv_text = df.to_csv(index=False)`.
  - Return `StreamingResponse(iter([csv_text]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{table_name}.csv"'})`.
  - Follow the existing try/except + logging pattern (re-raise `HTTPException`, log full traceback on generic errors).

### Task 3: Implement the query results export endpoint
- In `app/server/server.py`, add `POST /api/export/query` accepting `ExportQueryRequest`:
  - Execute via the existing `execute_sql_safely(request.sql)` (this already calls `validate_sql_query` internally and returns `{'results', 'columns', 'error'}`).
  - If `error` is set, raise `HTTPException(400, error)`.
  - Build CSV using pandas from `results`/`columns` (ensure correct column order even when results is empty — write header row from `columns`).
  - Return `StreamingResponse` with `Content-Disposition: attachment; filename="query_results.csv"`.
  - Follow existing try/except + logging pattern.

### Task 4: Add backend tests for the export endpoints
- Add a test module (e.g. `app/server/tests/test_export.py`) using FastAPI `TestClient` (import `app` from `server`), following the fixture/assertion style of `tests/test_sql_processor.py` and `tests/test_sql_injection.py`.
- Cover:
  - Successful table export returns 200, `text/csv`, correct `Content-Disposition`, and CSV body containing the header + expected rows.
  - Table export with an invalid/malicious table name returns 400.
  - Table export for a nonexistent table returns 404.
  - Successful query export returns 200 with CSV body matching the query results.
  - Query export with a dangerous query (e.g. contains `DROP`) returns 400.

### Task 5: Add client API methods
- In `app/client/src/api/client.ts`, add to the `api` object:
  - `async exportTableCSV(tableName: string): Promise<Blob>` — `fetch(`${API_BASE_URL}/export/table/${encodeURIComponent(tableName)}`)`, throw on `!response.ok`, return `response.blob()`.
  - `async exportQueryCSV(sql: string): Promise<Blob>` — POST JSON `{ sql }` to `${API_BASE_URL}/export/query`, throw on `!response.ok`, return `response.blob()`.
  - Do NOT route these through the existing `apiRequest` helper (it parses JSON).

### Task 6: Add a shared browser-download helper
- In `app/client/src/main.ts`, add a small helper `triggerDownload(blob: Blob, filename: string)` that creates an object URL, a temporary `<a download>` element, clicks it, removes it, and revokes the URL.

### Task 7: Add the table download button (left of the `×` icon)
- In `displayTables()` in `app/client/src/main.ts`, before `tableHeader.appendChild(removeButton)` (currently line 295), create a `downloadButton`:
  - `className = 'download-table-button'`, `title = 'Download CSV'`, `innerHTML` = a download SVG icon (down arrow into a tray; 16x16, `stroke="currentColor"`).
  - `onclick = async () => { try { const blob = await api.exportTableCSV(table.name); triggerDownload(blob, `${table.name}.csv`); } catch (e) { displayError('Failed to download table'); } }`.
  - Append it to `tableHeader` BEFORE `removeButton` so it sits directly to the left of the `×` icon.

### Task 8: Add the query results download button (left of the `Hide` button)
- In `displayResults()` in `app/client/src/main.ts`, add a download button to the `.results-header`, inserted immediately before the existing `#toggle-results` ("Hide") button so it sits directly to its left.
  - `className = 'download-results-button'`, `title = 'Download CSV'`, download SVG icon.
  - Guard: only enable/show it when `response.results.length > 0` and there is no `response.error`.
  - `onclick = async () => { try { const blob = await api.exportQueryCSV(response.sql); triggerDownload(blob, 'query_results.csv'); } catch (e) { displayError('Failed to download results'); } }`.
  - Ensure the button is not duplicated across multiple queries (remove any previously-inserted download button before adding a new one, since `displayResults` runs per query).

### Task 9: Add CSS for the download buttons
- In `app/client/src/style.css`, add `.download-table-button` and `.download-results-button` rules mirroring `.remove-table-button` (lines 316-334): transparent background, no border, pointer cursor, sized icon, rounded, `transition: all 0.2s`. On hover use the primary color tint (e.g. `background: rgba(102, 126, 234, 0.1); color: var(--primary-color);`). Ensure the results download button aligns vertically with the `Hide` button in the flex `.results-header`.

### Task 10: Create the E2E test file
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_basic_query.md` to understand the format.
- Create `.claude/commands/e2e/test_csv_exports.md` following the same structure (User Story, Test Steps, Success Criteria). The test must:
  - Navigate to the app and ensure sample data (users table) is loaded (use a sample-data button if no tables present).
  - Verify the table download button is present directly to the left of the `×` icon on a table card; take a screenshot.
  - Click the table download button and verify a CSV download is initiated (verify via the triggered network request / download event).
  - Run a query (e.g. "Show me all users from the users table") so results appear.
  - Verify the results download button is present directly to the left of the `Hide` button; take a screenshot.
  - Click it and verify a CSV download is initiated.
  - Keep to the minimal set of steps; include the screenshots described.

### Task 11: Update README documentation
- In `README.md`, add the two new endpoints to the "API Endpoints" section:
  - `GET /api/export/table/{table_name}` - Export a table as CSV
  - `POST /api/export/query` - Export query results as CSV
- Optionally add a short note under "Usage" describing the one-click download buttons.

### Task 12: Run all validation commands
- Execute every command in the `Validation Commands` section and confirm zero errors and zero regressions, including the E2E test.

## Testing Strategy
### Unit Tests
- **Table export (`GET /api/export/table/{table_name}`):**
  - Returns 200, `media_type` `text/csv`, `Content-Disposition: attachment; filename="<table>.csv"`.
  - CSV body has a header row matching the table columns and one line per row.
  - Invalid/malicious table name → 400.
  - Nonexistent table → 404.
- **Query export (`POST /api/export/query`):**
  - Valid SELECT → 200 with CSV body matching results and column order.
  - Dangerous SQL (`DROP`, multiple statements, comments) → 400 (enforced by `validate_sql_query` inside `execute_sql_safely`).
  - Empty result set → 200 with header-only CSV (no row data) — no crash.
- Use FastAPI `TestClient`; seed the test database with a known table (mirror `test_sql_processor.py`'s `test_db` fixture approach).

### Edge Cases
- Table with zero rows → CSV contains only the header row.
- Query returning zero rows → header-only CSV.
- Column values containing commas, quotes, or newlines → properly CSV-escaped (pandas `to_csv` handles quoting).
- Table/column names with spaces (allowed by `validate_identifier`) → still export correctly via escaped identifiers.
- Filenames: table names are already validated, so the `Content-Disposition` filename is safe.
- Client: clicking download with no results present (results download button should be hidden/disabled).
- Client: running multiple queries should not stack duplicate download buttons in the results header.

## Acceptance Criteria
- A `GET /api/export/table/{table_name}` endpoint exists and returns a downloadable CSV of the full table with correct headers and rows; invalid names return 400 and missing tables return 404.
- A `POST /api/export/query` endpoint exists and returns a downloadable CSV of query results; dangerous queries are rejected with 400.
- In the "Available Tables" section, each table card shows a download button with a download icon positioned directly to the left of the `×` (remove) icon; clicking it downloads `<table_name>.csv`.
- In the "Query Results" header, a download button with a download icon appears directly to the left of the `Hide` button; clicking it downloads `query_results.csv` matching the displayed results.
- The download buttons match the existing icon-button styling conventions.
- All backend tests pass (`uv run pytest`), the client type-checks (`bun tsc --noEmit`), and the client builds (`bun run build`).
- The new E2E test (`.claude/commands/e2e/test_csv_exports.md`) passes.
- No regressions in existing functionality.

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd app/server && uv run pytest` - Run all server tests (including the new export tests) to validate the feature works with zero regressions.
- `cd app/server && uv run pytest tests/test_sql_injection.py -v` - Confirm the security suite still passes with the new endpoints in place.
- `cd app/client && bun tsc --noEmit` - Type-check the frontend to validate the new client code with zero type errors.
- `cd app/client && bun run build` - Build the frontend to validate the feature compiles with zero regressions.
- `Read .claude/commands/test_e2e.md`, then read and execute your new E2E `.claude/commands/e2e/test_csv_exports.md` test file to validate this functionality works (app must be running via `./scripts/start.sh`).

## Notes
- No new Python libraries are required: `pandas==2.3.0` is already a dependency and is used for CSV generation; `io` and `csv` are stdlib if a pandas-free approach is preferred. Per the planning constraints, no new library is added.
- No decorators beyond FastAPI's existing route decorators (consistent with the rest of `server.py`).
- The query export endpoint deliberately accepts the already-generated SQL (returned to the client by `/api/query`) rather than re-running the LLM, keeping the export deterministic, fast, and free of extra LLM cost. It still passes through `validate_sql_query` via `execute_sql_safely`, so it cannot be used to run dangerous SQL.
- CSV downloads are streamed via `StreamingResponse`, matching FastAPI idioms; for the current data sizes a single-chunk iterator is sufficient and simple.
- Security is preserved by reusing `validate_identifier`, `check_table_exists`, `execute_query_safely`, and `validate_sql_query`; no user input is concatenated directly into SQL.
- Future consideration: add a configurable row cap or true row-by-row streaming for very large tables, and optionally support additional export formats (JSON/Excel) behind the same buttons.
