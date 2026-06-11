# Patch: Position table download button left of close button

## Metadata
adw_id: `6ef1c4a6`
review_change_request: `For 'Available Tables', make sure that the download button is just to the left of the close (x) button`

## Issue Summary
**Original Spec:** specs/ (one-click CSV table exports)
**Issue:** In the "Available Tables" section, each table header's download button does not sit directly to the left of the close (×) button. The `.table-header` flex container uses `justify-content: space-between` with three direct children (table name/info group, download button, close button), so the space distributes the download button into the middle of the row instead of grouping it beside the close button on the right.
**Solution:** Group the download button and the close (×) button into a single right-aligned action container so `space-between` keeps the table info on the left and the two buttons together on the right, with the download button immediately to the left of the close button.

## Files to Modify
Use these files to implement the patch:

- `app/client/src/main.ts` - Wrap the download and remove buttons in a shared actions container in the table header.

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Group the action buttons in `renderTables` (app/client/src/main.ts, ~lines 327-348)
- After creating `downloadButton` and `removeButton`, create a wrapper element:
  - `const tableActions = document.createElement('div');`
  - `tableActions.style.display = 'flex';`
  - `tableActions.style.alignItems = 'center';`
  - `tableActions.style.gap = '0.25rem';`
- Append the buttons to the wrapper in left-to-right order so download sits left of close:
  - `tableActions.appendChild(downloadButton);`
  - `tableActions.appendChild(removeButton);`
- Replace the existing two separate appends to `tableHeader`:
  - Remove `tableHeader.appendChild(downloadButton);` and `tableHeader.appendChild(removeButton);`
  - Keep `tableHeader.appendChild(tableLeft);` then add `tableHeader.appendChild(tableActions);`
- Result: `tableHeader` has two children (`tableLeft`, `tableActions`); `space-between` pushes `tableLeft` left and `tableActions` (download + close) right.

## Validation
Execute every command to validate the patch is complete with zero regressions.

- `cd app/client && yarn build` (or `npm run build`) — confirm TypeScript compiles with no errors.
- Start the app (`./scripts/start.sh` or per README), load a sample table, open the "Available Tables" section, and visually confirm the download icon button sits immediately to the left of the × close button on the right edge of each table header.
- Click the download button and confirm the CSV still downloads (no regression in `exportTableCSV` behavior).

## Patch Scope
**Lines of code to change:** ~8 lines
**Risk level:** low
**Testing required:** Visual confirmation of button order/position in the Available Tables header and a quick download click test.
