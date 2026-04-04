# actual-amazon-noter

A Python script to update the "notes" field of records in Actual Budget with Amazon purchase details.

## Overview

This tool correlates Amazon transaction records from CSV exports with transactions in Actual Budget, then updates the Notes field with Amazon order details including:
- Amazon Order ID
- Order Date
- Product Name
- Shipping Address

## Requirements

- Python 3.7 or higher
- `requests` library (for making HTTP calls to actual-http-api)
- Access to an Actual Budget instance with actual-http-api running

## Installation

### Option 1: Direct Execution (No Installation)

The script can be run directly without installation:

```bash
python3 actual-amazon-noter --help
```

### Option 2: Install via pip

```bash
pip install -r requirements.txt
```

Then you can run it as:

```bash
python3 actual-amazon-noter --help
```

### Option 3: Install as a Package

```bash
pip install .
```

This will install `actual-amazon-noter` as a command-line tool:

```bash
actual-amazon-noter --help
```

## Configuration

The script requires three connection parameters to access the actual-http-api:

1. **API URL** - The URL of the actual-http-api server (e.g., http://localhost:5007)
2. **API Key** - The secret key used by actual-http-api
3. **Sync ID** - The synchronization ID for the budget instance

These can be provided in three ways:

### Option 1: Environment Variables

```bash
export ACTUAL_HTTP_API_URL=http://localhost:5007
export ACTUAL_HTTP_API_KEY=your-secret-key
export ACTUAL_SYNCID=your-sync-id
```

### Option 2: Command-Line Arguments

```bash
actual-amazon-noter \
    --actual-http-api http://localhost:5007 \
    --actual-http-api-key your-secret-key \
    --actual-syncid your-sync-id \
    Order_History.csv
```

### Option 3: Configuration Files

Create a file (e.g., `config.txt`) with the values:

```
ACTUAL_HTTP_API_URL=http://localhost:5007
ACTUAL_HTTP_API_KEY=your-secret-key
ACTUAL_SYNCID=your-sync-id
```

Then reference it:

```bash
actual-amazon-noter \
    --actual-http-api-file config.txt \
    --actual-http-key-file config.txt \
    --actual-syncid-file config.txt \
    Order_History.csv
```

Or use the bare string format (one value per file):

```bash
actual-amazon-noter \
    --actual-http-api-file /path/to/url.txt \
    --actual-http-api-key-file /path/to/key.txt \
    --actual-syncid-file /path/to/syncid.txt \
    Order_History.csv
```

## Usage

### Basic Usage (Dry-Run Mode)

By default, the script runs in dry-run mode and only displays what changes would be made:

```bash
actual-amazon-noter Order_History.csv
```

### Execute Changes

To actually update the records in Actual Budget, use the `--execute` flag:

```bash
actual-amazon-noter --execute Order_History.csv
```

### JSON Output

To see the changes in JSON format:

```bash
actual-amazon-noter --dry-run json Order_History.csv
```

### Date Tolerance

By default, transactions are matched if the Amazon date is within 3 days before the Actual Budget transaction. Change this with `--days`:

```bash
actual-amazon-noter --days 7 Order_History.csv
```

### Force Update

If a transaction already has Amazon tags but you want to replace them:

```bash
actual-amazon-noter --force Order_History.csv
```

### Multiple CSV Files

You can process multiple Amazon CSV files at once:

```bash
actual-amazon-noter Order_History.csv Digital_Content_Orders.csv Refund_Details.csv
```

## Amazon CSV File Formats

The tool supports these Amazon data export files:

- **Order_History.csv** - Standard order history (purchases)
- **Digital_Content_Orders.csv** - Digital content orders
- **Refund_Details.csv** - Refund details
- **Digital_Returns.csv** - Digital returns

## Command-Line Options

```
--dry-run [csv|json]    Show changes without updating (default: csv)
--execute               Actually update records in Actual Budget
--days X                Number of days tolerance for matching (default: 3)
--force                 Replace existing Amazon tags
--actual-http-api URL   API server URL
--actual-http-api-file /path/to/file    File containing API URL
--actual-http-api-key SecretKey        API key
--actual-http-api-key-file /path/to/file   File containing API key
--actual-syncid SyncID                  Budget SyncID
--actual-syncid-file /path/to/file      File containing SyncID
```

## Examples

### Example 1: Using environment variables

```bash
export ACTUAL_HTTP_API_URL=http://cubanalle:5007
export ACTUAL_HTTP_API_KEY=ef6678dee3fc4f44b7db53752c63621d
export ACTUAL_SYNCID=7cb4a210-b87f-4b38-8f07-1380e6c30b3c

actual-amazon-noter --execute Order_History.csv
```

### Example 2: Using a config file

```bash
# Create config file
echo "ACTUAL_HTTP_API_URL=http://cubanalle:5007" > config.txt
echo "ACTUAL_HTTP_API_KEY=ef6678dee3fc4f44b7db53752c63621d" >> config.txt
echo "ACTUAL_SYNCID=7cb4a210-b87f-4b38-8f07-1380e6c30b3c" >> config.txt

# Run the tool
actual-amazon-noter --actual-http-api-file config.txt \
                    --actual-http-key-file config.txt \
                    --actual-syncid-file config.txt \
                    --execute \
                    Order_History.csv
```

### Example 3: Preview changes before executing

```bash
actual-amazon-noter --dry-run json Order_History.csv | jq
```

## License

This project is provided as-is.