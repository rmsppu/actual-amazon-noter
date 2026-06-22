# Dependencies:
	A working instance of "actual budget" (https://github.com/actualbudget)
	A working instance of "actual-http-api" (https://github.com/jhonderson/actual-http-api)
	CSV files of Amazon or PayPal purchase histories.

# Method:
	Using calls to actual-http-api, get transaction records where the Payee field contains matching keywords (e.g. "Amazon", "PayPal", etc.).

	Read the named CSV files, using the first line in the CSV file to determine the field (column) names.

	For those records, correlate with CSV data. To correlate a CSV record with a record from Actual Budget:
		the price must match
	  AND
	 	the transaction date must be within a given number of days (default 3 for Amazon, 7 for PayPal) before the transaction record in Actual Budget.

	For each matching transaction that does NOT already have a tag indicating it was processed, append data to the Actual Budget "Notes" field.

# Required Arguments
The required fields are:
	
			ACTUAL_HTTP_API_URL
			ACTUAL_HTTP_API_KEY
			ACTUAL_SYNCID

Those fields can be provided as environment variables, or specified on the command line as individual fields or on the command line giving a path to a file defining the field.

If both an environment variable (ACTUAL_HTTP_API_URL) and a command-line argument (--actual-http-api) are given, the command-line argument takes precedence.

It is an error if the command line options give both a value and a file (e.g., if the command line arguments had "--actual-http-api" and "--actual-http-api-file").

If any of the required arguments is missing, print a usage message and exit with an error.

## Configuration File Formats
All lines beginning with "#" are comments and are ignored.
All blank lines are ignored.
All trailing whitespace on a line is ignored.

The configuration file specified by the arguments "--actual-http-api-file", "--actual-http-key-file", or "--actual-syncid-file" can have data in two forms:

### Bare string
If the file contains ONLY the value for a single field, it can be a bare string.

### Key=Value
If the file contains multiple values:

    ACTUAL_HTTP_API_URL=https://actual-http-server:5007
    ACTUAL_HTTP_API_KEY=123SecretKey567
    ACTUAL_SYNCID=987-syncID-654

# Command Line Usage

Read the file "USAGE.txt" for details of the command-line flags.

By default, the actual-ecommerce-noter executable will only output the updated records (i.e., the "--dry-run" command-line option is the default). Only if the "--execute" command-line option is given will actual-ecommerce-noter use actual-http-api to write updated records to the Actual Budget instance.

## Features

### Split Transactions via API (v2.0.0)
The script interacts with the Actual Budget REST API to structurally split transactions for multi-item orders.
- Uses `is_parent: true` and `subtransactions` properties to build splits directly into Actual Budget.
- Idempotent execution (skips split generation if `is_parent` is already true).
- Balances rounding issues by adjusting the final sub-transaction to perfectly match the parent.
- Inherits the `payee` UUID from the parent transaction for each sub-transaction.

### Dynamic Currency & Keywords
- Currency is extracted directly from the CSV, ensuring dry-runs and split notes appear localized to your store context.

### Custom Tags Option (-t)
Added command-line option `-t` (or `--tag`) to allow users to add custom tags to matching transactions.

**Usage:**
```
./actual-ecommerce-noter -t "tag1" -t "tag2" -t "tag3" Order_History.csv
```

**Features:**
- Can be specified multiple times, each occurrence adds a tag
- Tags are automatically normalized to follow the format " #tag"
- User-provided tags are appended after the standard tags
