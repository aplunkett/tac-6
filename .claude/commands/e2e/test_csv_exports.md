# E2E Test: One-Click CSV Exports

Test the one-click CSV export buttons for tables and query results in the Natural Language SQL Interface application.

## User Story

As a user of the Natural Language SQL Interface
I want to download tables and query results as CSV files with a single click
So that I can use my data and analysis results in spreadsheets and other tools without manual copying

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the "Available Tables" section is present
4. If no tables are present, load sample data:
   - Click the "Upload Data" button
   - Click the "Users Data" sample button
   - Wait for the modal to close and the `users` table to appear in "Available Tables"
5. **Verify** a table card for the `users` table is shown
6. **Verify** the table card has a download button (download icon) positioned directly to the left of the `×` (remove) icon
7. Take a screenshot of the table card showing the download button next to the `×` icon
8. Click the table download button
9. **Verify** a CSV download is initiated for `users.csv` (observe the triggered download / the `GET /api/export/table/users` network request returns 200 with `Content-Type: text/csv`)
10. Enter the query: "Show me all users from the users table"
11. Click the Query button
12. **Verify** the query results appear in a results table
13. **Verify** a download button (download icon) appears in the "Query Results" header directly to the left of the `Hide` button
14. Take a screenshot of the results header showing the download button next to the `Hide` button
15. Click the results download button
16. **Verify** a CSV download is initiated for `query_results.csv` (observe the triggered download / the `POST /api/export/query` network request returns 200 with `Content-Type: text/csv`)

## Success Criteria
- The table download button is present directly to the left of the `×` icon on the table card
- Clicking the table download button initiates a `users.csv` download (200, text/csv)
- The results download button is present directly to the left of the `Hide` button
- Clicking the results download button initiates a `query_results.csv` download (200, text/csv)
- 3 screenshots are taken (initial state, table download button, results download button)
