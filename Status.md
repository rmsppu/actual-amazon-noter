
# Dependencies:
	A working instance of "actual budget" (https://github.com/actualbudget)
	A working instance of "actual-http-api" (https://github.com/jhonderson/actual-http-api)
	CSV files of Amazon purchase and refund histories, exported via a data request.

# Method:
	Using calls to actual-http-api, get transaction records where the Payee field contains the string "Amazon" (case insensitive). This may be a substring -- for example, the Payee field may contain "Amazoncom", "Amazon.com", "Amazconmkt", etc.

	Read the named CSV files, using the first line in the CSV file to determined the field (column) names.

	For those records, correlate with CSV data from the download of Amazon transactions. To correlate an Amazon record with a record from Actual Budget:
		the price must match
	  AND
	 	the Amazon transaction date must be within a given number of days (default=3, may be set on the command line) before the transaction record in Actual Budget


	For withdrawal (purchase) transactions, read the files Order_History.csv and Digital_Content_Orders.csv.
	For income (return) transactions, read the files Refund_Details.csv and Digital_Returns.csv.

	To correlate prices:
		Amazon data file		Field
		================		=====
		Order_History.csv		"Total Amount"
		Digital_Content_Orders.csv	"Transaction Amount"
		Refund_Details.csv		"Refund Amount"
		Digital_Returns.csv		"Transaction Amount"

	For each matching transaction that does NOT already have a tag "#Amazon-Order-ID", append data to the Actual Budget "Notes" field in the form of tags. The first appended field will always be " #AMAZON-Order-Id", followed by other tags. Each tag begins with [SPACE]# and then has the following field[s] from the Amazon record.

		Amazon data file		Tag
		================		===
		Order_History.csv		#Amazon-Order-ID
		Order_History.csv		#Amazon-Order-Date
		Order_History.csv		#Amazon-Product-Name
		Order_History.csv		#Amazon-Shipping-Address

	Example:
		If a record from Actual Budget correlates to an Amazon transaction and initially contains the Notes data:
			Withdrawal ACH AMAZON MARKETPLA TYPE: INTERNET ID: 9123456782DATA: TELECHK 800-697-9263CO: AMAZON MARKETPLA NAME: John Doe ACH Trace 12345678918

		that would be updated to contain:

			Withdrawal ACH AMAZON MARKETPLA TYPE: INTERNET ID: 9123456782DATA: TELECHK 800-697-9263CO: AMAZON MARKETPLA NAME: John Doe ACH Trace 12345678918 #Amazon-Order-ID ABC123 #Amazon-Order-Date 04-04-2024 #Amazon-Product-Name Really Big Anvil #Amazon-Shipping-Address 123 Main St, Anytown, USA 1234567



# Required Arguments
The required fields are:
	
			ACTUAL_HTTP_API_URL
			ACTUAL_HTTP_API_KEY
			ACTUAL_SYNCID

Those fields can be provided as environment variables, or specified on the command line as individual fields or on the command line giving a path to a file defining the field.

If both an environment variable (ACTUAL_HTTP_API_URL) and a command-line argument (--actual-http-api) are given, the command-line argument takes precedence and this is not an error.

It is an error if the command line options give both a value and a file (ie., if the command line arguments had "--actual-http-api" and "--actual-http-api-file").

If any of the required arguments is missing, print a usage message with details on the missing argument and exit with an error.

## Configuration File Formats
All lines beginning with "#" are comments and are ignored.
All blank lines are ignored.
All trailing whitespace on a line is ignored.

The configuration file specified by the arguments "--actual-http-api-file", "--actual-http-key-file", or "--actual-syncid-file" can have data in two forms. 

### Bare string
If the file contains ONLY the value for a single field, it can be a bare string.
If the file contains more than one non-comment, non-whitespace line, it is an error.

For example, if the command line arguments were:
    --actual-http-api-file /path/to/file1 --actual-http-key-file  /path/to/file2 --actual-syncid-file /path/to/file3
then the files might have:
    file1:   https://actual-http-server:5007
    file2:   123SecretKey567
    file3:   987-syncID-654


### Key=Value
If the file contains ONLY the value for a single field, it can be a bare string.

For example, if the command line arguments were:
    --actual-http-api-file /path/to/combinedfile --actual-http-key-file  /path/to/combinedfile --actual-syncid-file /path/to/combinedfile

then "combinedfile" must contain lines in the form:

    ACTUAL_HTTP_API_URL=https://actual-http-server:5007
    ACTUAL_HTTP_API_KEY=123SecretKey567
    ACTUAL_SYNCID=987-syncID-654

Additional lines in this file are not considered an error.

# Required Amazon Data File[s]
Path[s] to CSV files containing downloaded Amazon records are required. At least one of Order_History.csv, Digital_Content_Orders.csv, Refund_Details.csv, or Digital_Returns.csv must be given.

If no data file is given, print a usage message with details and  exit with an error.

For each datafile given, read the first line of the file to determine the field names (column headers).

# Command Line Usage

Read the file "USAGE.txt" for details of the command-line flags that must be included in the executable.

By default, the actual-amazon-noter exectable will only output the updated records (ie., the "--dry-run" command-line option is the default). Only if the "--execute" command-line option is given will actual-amazon-noter use actual-http-api to write updated records to the Actual Budget instance.


# TODO
## Testing!
This has only been minimally tested. Backup your Actual Budget database and use at your own risk. This script may turn your budget records into pretty cat pictures.

Untested:
* --force option
* Correlation against order  data from Digital_Content_Orders.csv

## Recent Additions
### Custom Tags Option (-t)
Added command-line option `-t` (or `--tag`) to allow users to add custom tags to matching transactions.

**Usage:**
```
./actual-amazon-noter -t "tag1" -t "tag2" -t "tag3" Order_History.csv
```

**Features:**
- Can be specified multiple times, each occurrence adds a tag
- Tags are automatically normalized to follow the format " #tag"
- Tag normalization rules:
  - Input "tag" → normalized to " #tag"
  - Input "# tag" → normalized to " #tag" (space after # is removed)
  - Input " #tag" → kept as-is (already correct format)
  - Empty tags are discarded
- User-provided tags are appended after the standard Amazon tags (#Amazon-Order-ID, #Amazon-Order-Date, etc.)
- All custom tags appear with a space followed by hash (SPACE#)

**Examples:**
```
# Simple tag
./actual-amazon-noter -t "invoice" Order_History.csv
Result: ... #Amazon-Order-ID ABC123 ... #invoice

# Multiple tags
./actual-amazon-noter -t "follow-up" -t "urgent" Order_History.csv
Result: ... #Amazon-Order-ID ABC123 ... #follow-up #urgent

# Tags with spaces
./actual-amazon-noter -t "needs verification" Order_History.csv
Result: ... #Amazon-Order-ID ABC123 ... #needs verification
```

## Refunds
No processing of refunds is present yet. Providing the datafiles Refund_Details.csv or Digital_Returns.csv will almost certainly fail.


# Output formats
The current output format in default (--dry-run) mode is supposed to be CSV. It is not. The output is quite nice, human readable, and somewhat machine parsable. But it's not CSV as claimed. Either update the docs or implement CSV output, or both.

There's a flag that claims to do JSON output. It doesn't. See above.
