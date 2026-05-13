# Sage Intacct MCP Server

A Model Context Protocol (MCP) server that connects Claude to Sage Intacct, enabling AI-powered financial analysis across GL, AP, AR, and financial statements.

## Tools

| Tool | Description |
|------|-------------|
| `intacct_get_gl_entries` | Fetch GL journal entries by date range and account |
| `intacct_get_trial_balance` | Run the Trial Balance saved report |
| `intacct_get_ap_bills` | Fetch AP bills filtered by status, vendor, date |
| `intacct_get_ap_aging` | Run the AP Aging saved report |
| `intacct_get_ar_invoices` | Fetch AR invoices filtered by status, customer, date |
| `intacct_get_ar_aging` | Run the AR Aging saved report |
| `intacct_get_profit_and_loss` | Run the P&L saved report for a date range |
| `intacct_get_balance_sheet` | Run the Balance Sheet saved report as of a date |
| `intacct_get_cash_flow` | Run the Cash Flow Statement saved report |
| `intacct_list_reports` | List all saved reports in your Sage Intacct instance |
| `intacct_run_report` | Run any saved report by name |

## Prerequisites

- Python 3.10+
- A Sage Intacct account with **Web Services** enabled
- A **Web Services Sender ID** and password from Intacct support
- A dedicated Web Services user in Sage Intacct

## Setup

1. **Clone and install**
   ```bash
   git clone <repo-url>
   cd sage-intacct-mcp
   pip install -e .
   ```

2. **Configure credentials**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your Sage Intacct credentials:
   ```
   INTACCT_SENDER_ID=your_sender_id
   INTACCT_SENDER_PASSWORD=your_sender_password
   INTACCT_COMPANY_ID=your_company_id
   INTACCT_USER_ID=your_ws_user_id
   INTACCT_USER_PASSWORD=your_ws_user_password
   ```

3. **Run the server**
   ```bash
   sage-intacct-mcp
   # or
   python -m sage_mcp.main
   ```

## Connect to Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sage-intacct": {
      "command": "sage-intacct-mcp",
      "env": {
        "INTACCT_SENDER_ID": "your_sender_id",
        "INTACCT_SENDER_PASSWORD": "your_sender_password",
        "INTACCT_COMPANY_ID": "your_company_id",
        "INTACCT_USER_ID": "your_user_id",
        "INTACCT_USER_PASSWORD": "your_user_password"
      }
    }
  }
}
```

## Financial Statement Reports

The P&L, Balance Sheet, Cash Flow, Trial Balance, AP Aging, and AR Aging tools run **saved reports** from your Sage Intacct instance. The default report names used are:

- `Profit and Loss`
- `Balance Sheet`
- `Cash Flow Statement`
- `Trial Balance`
- `AP Aging`
- `AR Aging`

If your saved reports have different names, pass the exact name via the `report_name` parameter. Use `intacct_list_reports` to discover all available report names.

## Frontend Dashboard

This server is designed to work alongside a **Lovable** frontend dashboard for visualising Sage Intacct data. The MCP server handles all data retrieval; the dashboard consumes the JSON responses.
