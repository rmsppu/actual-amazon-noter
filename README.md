# actual-ecommerce-noter

A companion utility and web companion for [Actual Budget](https://actualbudget.org) that enriches transaction records with purchase details from Amazon and PayPal CSV exports, natively integrated with [rr4444/actual-ai](https://github.com/rr4444/actual-ai) for advanced LLM-powered transaction classification.

> [!NOTE]
> This project is a completely independent, production-grade fork of the wonderful [actual-amazon-noter](https://github.com/rmsppu/actual-amazon-noter) by [rmsppu](https://github.com/rmsppu), based on upstream commit [95b0f42](https://github.com/rmsppu/actual-amazon-noter/commit/95b0f42). We thank `rmsppu` for their exceptional foundation!

---

## Table of Contents

* [Key Features](#key-features)
* [Data Retrieval & Platform Limitations](#data-retrieval--platform-limitations)
* [Design Decisions & Matching Logic](#design-decisions--matching-logic)
  * [Why Noting instead of Ledger Imports?](#why-noting-instead-of-ledger-imports)
  * [Why Standard PayPal CSV over QuickBooks IIF?](#why-standard-paypal-csv-over-quickbooks-iif)
  * [Dynamic Date Tolerance](#dynamic-date-tolerance)
  * [Comparative Amount Tolerance & Payee Verification](#comparative-amount-tolerance--payee-verification)
* [🤖 actual-ai Integration (On-Demand & Auto-Trigger)](#-actual-ai-integration-on-demand--auto-trigger)
  * [🌟 Key Features](#-key-features-1)
  * [⚙️ Collision-Free Workflows](#-collision-free-workflows)
  * [Logical Workflow Diagram](#logical-workflow-diagram)
* [Configuration](#configuration)
  * [Providing Configuration](#providing-configuration)
* [CLI Usage](#cli-usage)
  * [Basic Usage (Dry-Run Mode)](#basic-usage-dry-run-mode)
  * [Execute Changes](#execute-changes)
  * [Custom Date Tolerance & Format Override](#custom-date-tolerance--format-override)
  * [Custom Tags](#custom-tags)
  * [CLI Options Reference](#cli-options-reference)
* [Web Interface](#web-interface)
* [Kubernetes Deployment Examples](#kubernetes-deployment-examples)
  * [1. Build and Import the Image](#1-build-and-import-the-image)
  * [2. Deployment Manifests](#2-deployment-manifests)
* [Fork Enhancements & Release Notes](#fork-enhancements--release-notes)
  * [Amazon Split & Engine Baseline (v1.1.0)](#amazon-split--engine-baseline-v110)
  * [PayPal Integration & eCommerce Upgrade (v2.1.0)](#paypal-integration--ecommerce-upgrade-v210)
* [License](#license)

---

## Key Features

- **Structural Split Transactions**: Converts multi-item Amazon orders into parent-child split transactions in your Actual Budget UI, pre-populated with exact item prices and individual notes.
- **PayPal Currency Correlation**: Filters for `Completed` status, ignores internal card deposit buffers, and automatically matches EUR/USD foreign currency purchases to their GBP equivalents by correlating adjacent General Currency Conversion entries (tested extensively on PayPal UK data).
- **First-Class `rr4444/actual-ai` Integration**: Features premium, built-in integration with the [rr4444/actual-ai](https://github.com/rr4444/actual-ai) transaction classifier. The web companion dashboard includes a dedicated **AI Assistant** panel allowing you to monitor connectivity status, trigger classification sweeps manually on-demand, or toggle **automated post-noter cascades** immediately following successful CSV uploads.
- **Smart Explicit Format Selection**: Provides explicit dropdown selection in the GUI and a `--format amazon|paypal|auto` flag in the CLI to avoid header schema ambiguities.
- **Integrated Web Interface**: Features an interactive dashboard with a drag-and-drop CSV uploader, execution controls, dry-run simulation, real-time colorized logs, and raw connection diagnostics.
- **Multi-Currency Support**: Dynamically extracts currency details from the source CSV to ensure dry-run previews and split notes are accurately localized.

---

## Data Retrieval & Platform Limitations

Due to restrictive platform policies, transaction history exports from major e-commerce platforms must be retrieved manually. E-commerce platforms generally restrict user-accessible data exports to the absolute minimum functionality legally enforced by consumer protection and privacy regulations.

### 💳 Amazon & PayPal Manual Export
Exporting data from Amazon and PayPal is an unavoidably manual workflow:
* **Amazon Purchase History**: Download your detailed orders CSV by submitting a data request via the [Amazon Privacy Central Data Request Page](https://www.amazon.co.uk/hz/privacy-central/data-requests/preview.html). You can also refer to this helpful community guide on [How to download transaction reports on Amazon purchases by year](https://www.amazonforum.com/s/question/0D5at00000UHvv9CAD/how-to-download-transaction-reports-on-amazon-purchases-by-year).
* **Amazon Refund Details**: Download your refund details CSV (labeled `Refund_Details.csv`) through the same Amazon data request page.
  > [!IMPORTANT]
  > **Refund Matching Requirement**: Refund details exports *cannot* be processed alone because they lack product names. The uploader requires your `Order_History.csv` to cross-reference order IDs and resolve product names/splits. Always upload or pass **both files together** (e.g. dragging both into the drop zone in the Web GUI, or passing both to the CLI).
* **PayPal Statement History**: Download a Standard Transaction CSV via the [PayPal Reports Activity Download Page](https://www.paypal.com/reports/dlog).

### 🛍️ eBay & The GDPR SAR Limitation
For eBay, the official route to request account data is via a Subject Access Request (GDPR SAR) at the official [eBay SAR Web Portal](https://www.sarweb.ebay.com/sar). However, using the official eBay SAR route is completely impractical for standard budgeting purposes:
* **Unacceptable Delays**: The official SAR process takes an unacceptable length of time (typically around 10 days) to generate the report.
* **Not Acceptable Expiration**: Once eBay finally generates the download link, it expires after only 7 days. Because the turnaround time exceeds the validity window of a typical weekly budget reconciliation, relying on this official path is not acceptable.
* **Recommended Chrome Extension**: To circumvent these limitations, the current approach is to download your purchase history as an `.xlsx` spreadsheet using the third-party Chrome extension [Ebay Purchase History Downloader](https://chromewebstore.google.com/detail/ebay-purchase-history-dow/dhccpfcjgmlajnnoigjhokbfgpaamhpe/). Note that there is currently no Firefox add-on or direct CSV export option available for eBay.

---

## Design Decisions & Matching Logic

### Why Noting instead of Ledger Imports?
Ledger imports of e-commerce statements often result in transaction duplication and bypass native bank account feeds. By choosing **Noting**, the tool matches and enriches already imported bank or credit card transactions, preserving the correct, cleared exchange rates and bank statement records.

### Why Standard PayPal CSV over QuickBooks IIF?
While the QuickBooks IIF format offers consistent item descriptions, it strips PayPal's unique Transaction and Receipt IDs. Without these hashes, matching is vulnerable to duplicate annotations when multiple transactions of identical amounts occur on the same day. Using the **Standard CSV** allows the tool to generate precise tags anchored by the `#PayPal-Transaction-ID <ID>` hash, ensuring duplicate protection and safety (tested extensively on PayPal UK data).

### Dynamic Date Tolerance
E-commerce bank clearing times vary by payment mechanism:
- **Amazon (Default: 3 Days)**: Direct credit/debit card transactions typically clear on standard bank statements within 3 days.
- **PayPal (Default: 7 Days)**: Bank transactions for PayPal settlements take up to **a week (7 days)** because PayPal operates as a pass-through wallet (funding transfers, eChecks, and bank clearing delays).

The tool automatically shifts its matching date tolerance to 7 days when the PayPal format is selected or detected.

### Comparative Amount Tolerance & Payee Verification
Different e-commerce platforms necessitate distinct matching strictness:
- **Amazon (Default: £1.00 / 100 cents)**: Amazon orders are often split dynamically into multiple sub-shipments (which clear the bank as separate, minor charge adjustments) or include additional local taxes/shipping charges. A higher amount tolerance of up to £1.00 allows matching these split charges with the parent order.
- **PayPal (Default: £0.00 / 0 cents)**: PayPal operates on exact passthrough bank settlement amounts. Because bank statement debits align exactly with the PayPal ledger transaction, any amount variance represents a distinct transaction. The tool enforces a strict **£0.00 amount tolerance** for PayPal matches, completely eliminating false-positive subscription mappings.
- **Payee String Validation**: For PayPal transactions, the tool extracts alphanumeric keywords from the budget transaction payee and correlates them against the PayPal CSV's merchant Name (ignoring generic words like *PayPal*, *payment*, *ltd*). Specific merchant codes (e.g. `ROBLOX` vs `LEBARA`) are strictly segregated, preventing cross-matching (swapping) of near-identical small amounts on close dates.

---

## 🤖 actual-ai Integration (On-Demand & Auto-Trigger)

This companion uploader features a first-class, premium integration with [rr4444/actual-ai](https://github.com/rr4444/actual-ai) to categorize transactions automatically.

> [!NOTE]
> **Exclusive to the Web Interface**: This integration is accessible **only** when running the companion uploader via the Web GUI (`app.py`). 
> 
> * **Why?**: The core Python script (`actual-ecommerce-noter`) is kept strictly as a standalone, single-purpose matching and splitting CLI utility. Decoupling the AI integration into the Web GUI keeps the CLI lightweight and allows the web dashboard's HTTP orchestrator to handle the asynchronous task lifecycle, Kubernetes RBAC job spawning, and live streaming of container logs directly to your browser.

### 🌟 Key Features
- **AI Assistant Card**: Displays your active connectivity mode via an `"Initial Integration Test"` on page load (`AI Status: Initial Integration Checked (Kubernetes Mode|Local Mode)`).
- **On-Demand Manual Classifier**: Run a classification pass at any time directly from the companion dashboard. Spawns an associated one-shot K8s Job linked natively to your existing parent `actual-ai` CronJob via `ownerReferences` (ensuring perfect Rancher/Lens resource grouping and clean garbage collection).
- **Post-Process Auto-Trigger**: A slider switch (saved in `localStorage`) that automatically schedules a classification pass immediately after a successful CSV noter process!
- **Asynchronous Progress Logs**: Polling logs dynamically with pod status awareness (`Pending` startup -> `Running` container stream -> `Success`/`Failed` completion).

### ⚙️ Collision-Free Workflows
To prevent double-classification and transaction collisions, add feature tags inside your `actual-ai` `FEATURES` array:
- **`amazonNoterWorkflow`**: Tells `actual-ai` to ignore standard Amazon/AMZN transactions (as they are already split and split-itemized by `actual-ecommerce-noter`).
- **`paypalNoterWorkflow`**: Tells `actual-ai` to ignore standard raw PayPal/PYPL transactions (as they are already auto-correlated, matched, and payee-verified by this companion uploader).
- **High-Fidelity Prompt Simplification**: `actual-ai` automatically extracts and simplifies note tags generated by the uploader (such as `#Amazon-Product-Name`, `#PayPal-Item-Title`, and split index suffixes) into pure, clean merchant descriptions inside its prompt, ensuring the Gemini model classifies them with maximum category accuracy.

#### **Logical Workflow Diagram**
```
           [Actual Budget Uncategorized Transaction]
                              │
                              ▼
                (amazonNoterWorkflow ENABLED?)
                 ┌────────────┴────────────┐
                 │ YES                     │ NO
                 ▼                         ▼
         [Has Noter Notes?]         [AI CATEGORIZES]
          ┌──────┴──────┐          (Standard AI Flow)
       NO │             │ YES
          ▼             ▼
     [AI IGNORES]  [AI CATEGORIZES]
    (Wait for CSV) (Using Clean Notes)
```

---

## Configuration

The utility requires connection parameters for your `actual-http-api` instance and supports multi-currency configurations:

1. **API URL** (`ACTUAL_HTTP_API_URL`): The URL of your actual-http-api server (e.g., `http://localhost:5007`).
2. **API Key** (`ACTUAL_HTTP_API_KEY`): The secret key used by actual-http-api.
3. **Sync ID** (`ACTUAL_SYNCID`): The synchronization ID for your specific budget.
4. **Base Currency** (`ACTUAL_BASE_CURRENCY`): (Optional) The base settlement currency of your budget/bank statements (e.g. `USD`, `GBP`). Defaults directly to `GBP`. Used to correlate foreign purchases to your base ledger balance during PayPal general currency conversions.

### Providing Configuration

These parameters can be provided via environment variables, CLI flags, or file-based configuration.

#### Option 1: Environment Variables
```bash
export ACTUAL_HTTP_API_URL=http://localhost:5007
export ACTUAL_HTTP_API_KEY=your-secret-key
export ACTUAL_SYNCID=your-sync-id
export ACTUAL_BASE_CURRENCY=GBP
```

#### Option 2: Command-Line Arguments
```bash
actual-ecommerce-noter \
    --actual-http-api http://localhost:5007 \
    --actual-http-api-key your-secret-key \
    --actual-syncid your-sync-id \
    --base-currency GBP \
    Order_History.csv
```

#### Option 3: Configuration Files (e.g. `config.txt`)
```ini
ACTUAL_HTTP_API_URL=http://localhost:5007
ACTUAL_HTTP_API_KEY=your-secret-key
ACTUAL_SYNCID=your-sync-id
ACTUAL_BASE_CURRENCY=GBP
```
```bash
actual-ecommerce-noter --actual-http-api-file config.txt Order_History.csv
```

---

## CLI Usage

### Basic Usage (Dry-Run Mode)
Runs a dry-run and prints proposed budget matches to stdout:
```bash
chmod +x actual-ecommerce-noter
./actual-ecommerce-noter Order_History.csv
```

### Execute Changes
Applies the updates directly to your Actual Budget instance:
```bash
./actual-ecommerce-noter --execute Order_History.csv
```

### Custom Date Tolerance & Format Override
```bash
./actual-ecommerce-noter --days 10 --format paypal Paypal_Download.csv
```

### Custom Tags
Append custom tags (e.g., `#invoice` or `#follow-up`) to matched transactions:
```bash
./actual-ecommerce-noter -t "invoice" -t "needs verification" Order_History.csv
```

### CLI Options Reference
```
--dry-run [csv|json]    Show changes without updating (default: csv)
--execute               Actually update records in Actual Budget
--days X                Number of days tolerance for matching
--amount-tolerance X    Max amount tolerance in currency units (e.g. 1.00 or 0.00)
--format amazon|paypal  Explicitly set the CSV schema format
--force                 Replace existing e-commerce tags
--actual-http-api URL   API server URL
--actual-http-api-file  File containing API URL
--actual-http-api-key   API key
--actual-syncid SyncID  Budget Sync ID
-t, --tag TAG           Custom tag to append (can be specified multiple times)
```

---

## Web Interface

To host the web dashboard locally:
```bash
pip install -r requirements.txt
python3 app.py
```
Access the interface at `http://localhost:8080`.

---

## Kubernetes Deployment Examples

> [!IMPORTANT]
> **Illustrative Examples Only**: The following configurations and manifests are provided purely as educational templates and conceptual examples. They are not direct, exact steps to follow for production installations, and should be customized to fit your specific cluster network, namespaces, routing architecture, and secret management schemes.

### 1. Build and Import the Image
Because this companion uses a customized local build, you must build the Docker image and make it available to your Kubernetes nodes before deploying:

```bash
# Build the image locally
docker build -t actual-ecommerce-noter:1.0.1 .

# Save and import the image into containerd on your nodes:
docker save actual-ecommerce-noter:1.0.1 -o actual-ecommerce-noter.tar
sudo k3s ctr images import actual-ecommerce-noter.tar
```

### 2. Deployment Manifests

#### Traefik Routing & Middleware
```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: actual-ecommerce-noter-strip
  namespace: finance
spec:
  stripPrefix:
    prefixes:
      - /actual-ecommerce-noter

---
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: actual-ingress
  namespace: finance
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`actual.example.com`) && PathPrefix(`/actual-ecommerce-noter`)
      kind: Rule
      middlewares:
        - name: actual-ecommerce-noter-strip
          namespace: finance
      services:
        - name: actual-ecommerce-noter
          port: 8080
          namespace: finance
```

#### Deployment & Service
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: actual-ecommerce-noter
  namespace: finance
spec:
  replicas: 1
  selector:
    matchLabels:
      app: actual-ecommerce-noter
  template:
    metadata:
      labels:
        app: actual-ecommerce-noter
    spec:
      containers:
      - name: uploader
        image: actual-ecommerce-noter:1.0.1
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080
        env:
        - name: ACTUAL_HTTP_API_URL
          value: "http://actual-http-api:5007"
        - name: ACTUAL_HTTP_API_KEY
          valueFrom:
            secretKeyRef:
              name: finance-secrets
              key: ACTUAL_HTTP_API_KEY
        - name: ACTUAL_SYNCID
          value: "YOUR-BUDGET-SYNC-ID"

---
apiVersion: v1
kind: Service
metadata:
  name: actual-ecommerce-noter
  namespace: finance
spec:
  selector:
    app: actual-ecommerce-noter
  ports:
    - port: 8080
      targetPort: 8080
```

---

## Fork Enhancements & Release Notes

### Amazon Split & Engine Baseline (v1.1.0)
* **Expanded Payee Matching**: Dynamically searches `Amz` payees alongside `Amazon` to capture all `Amznmktplace` charges cleanly.
* **Flexible Date Window**: Allowed a `-2` day date tolerance offset to handle timezone and same-day dispatch differences.
* **CSV Schema Validation**: Fixed critical CSV header mismatch (`Shipment Address` -> `Shipping Address`).
* **Multi-Currency Support**: Extracts the currency field directly from the CSV (defaulting to `GBP`) for high-fidelity notes and dry-run previews.
* **Double-Booking Protection**: Fixed identical-amount duplication bugs via rigorous `used_amazon` set tracking.
* **Automated Split Transactions**: Adds a powerful `split_transaction` API method to natively create parent-child splits for multi-item orders:
  * **Idempotency**: Checks `is_parent` before splitting to allow safe duplicate runs, while supporting duplicate items in the same order.
  * **Precision Rounding**: Performs fraction-of-cent rounding correction on the final sub-transaction to match parent amounts exactly.
  * **UUID Inheritance**: Split sub-transactions inherit parent payee UUIDs.
  * **Dry-Run Observability**: Outputs comprehensive split previews with formatted currency amounts and summary counts.

### PayPal Integration & eCommerce Upgrade (v2.1.0)
* **Unified eCommerce Dashboard**: Frame Amazon and PayPal as core examples of e-commerce noting.
* **PayPal Integration**: Filters for `Completed` status, ignores internal funding buffers, and maps USD/EUR currency conversions to their GBP bank equivalents.
* **Payee-Keyword Correlation**: Extracts and matches payee keywords to prevent cross-matching close amounts on adjacent dates (e.g. Roblox vs Lebara).
* **Configurable Amount Tolerance**: Exposes amount tolerance on both the CLI (`--amount-tolerance`) and GUI card.
* **Responsive ACTUAL Theme**: Modern, high-performance UI tailored specifically to Actual Budget's deep-navy and violet design colors.

---

## License

MIT.
