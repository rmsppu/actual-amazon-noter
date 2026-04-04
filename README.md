# actual-amazon-noter
Add tags to Actual Budget notes based on Amazon order history
# actual-amazon-noter

A Python script to update the "notes" field of records in Actual Budget with Amazon purchase details.

## Overview

This tool correlates Amazon transaction records from CSV exports with transactions in Actual Budget, then updates the Notes field with Amazon order details including:
- Amazon Order ID
- Order Date
- Product Name
- Shipping Address

The correlation looks:
- Transactions where the Payee, Imported_Payee, or Notes contains "Amazon"
AND
- Transactions within the date window where the billed cost matches the cost of the Amazon order 

A single transaction in Actual Budget for an Amazon purchase may correspond to multiple lines in the Amazon order history, as an Amazon purchase may be fulfilled by multiple vendors. This program will sum up the cost of each line item in the order history that shares a common Order Id. If a match is found with an Actual Budget transaction, the Notes field is updated with enough detail to allow the transaction to be split between multiple budgets.

For example, if the Amazon Order_History.csv file contained (highly simplified):
```
    Order ID,Description,Cost
    12345,Orange juice,$1.99
    12345,3/4HP Ryobi Router,$59.99
    12345,CISCO 1900 Router,$95.00
```

This would be consider a single purchase of $156.98. If this matched a transaction in Actual Budget, the Notes field would be updated to include the tags:
```
    #Amazon-Order 12345
    #Amazon-Product-Name-Split-1 Orange juice #Amazon-Product-Cost-Split-1 $1.99
    #Amazon-Product-Name-Split-2 3/4HP Ryobi Router #Amazon-Product-Cost-Split-2 $59.99
    #Amazon-Product-Name-Split-3 CISCO 1900 Router #Amazon-Product-Cost-Split-3 $95.00
```
(all as a single line, appended to the existing Notes data).

This allows the transaction in Actual Budget to be split between different categories (groceries, woodworking, computing). The presence of the string "Split-" in the tags allows for regular expression rules in Actual Budget to recognize and act on the tagged data.
## Requirements

- Python 3.7 or higher
- `requests` library (for making HTTP calls to actual-http-api)
- Access to an Actual Budget instance with actual-http-api running
- CSV file of Amazon purchase history. See https://www.amazonforum.com/s/question/0D5at00000UHvv9CAD/how-to-download-transaction-reports-on-amazon-purchases-by-year for export directions.

## Installation

### Option 1: Direct Execution (No Installation)

The script can be run directly without installation:

```chmod +x actual-amazon-noter
./actual-amazon-noter --help
```

### Option 2: Install via pip

```bash
pip install -r requirements.txt
```


### Option 3: Install as a Package

```bash
pip install .
```

## Running actual-amazon-noter
Regardless of the installation method, make the file exectuable via ```chmod```, the run it:

```chmod +x actual-amazon-noter
./actual-amazon-noter --help
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

Create a file (e.g., `config.txt`) with multiple values:

```
ACTUAL_HTTP_API_URL=http://localhost:5007
ACTUAL_HTTP_API_KEY=your-secret-key
ACTUAL_SYNCID=your-sync-id
```

Then reference it:

```
actual-amazon-noter \
    --actual-http-api-file config.txt \
    --actual-http-key-file config.txt \
    --actual-syncid-file config.txt \
    Order_History.csv
```

Or use the bare string format (one value per file):

```
echo "http://localhost:5007" > url.txt
echo "your-secret-key" > key.txt
echo "your-sync-id" > syncid.txt
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

## Amazon CSV File Formats

The only currently supported file format is **Order_History.csv** -- the standard order history (purchases) export

The tool is intended to support these Amazon data export files in the future:

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

## License

MIT.
