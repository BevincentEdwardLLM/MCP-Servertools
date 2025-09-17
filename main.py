# local_mcp_server_5_tools.py
# from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP

from google.cloud import bigquery
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"D:\MCP_NEW\service_account.json"

# === Create an MCP server ===
mcp = FastMCP("CustomerProductSalesMCP")

# === BigQuery Client Initialization ===
bq_client = bigquery.Client()

def run_bq(sql: str):
    """Run a BigQuery SQL and return rows as list of dicts."""
    if not sql or not sql.strip():
        raise ValueError("Expected a non-empty SQL string.")
    job = bq_client.query(sql)
    result = job.result()
    return [dict(row.items()) for row in result]


# -----------------------------------------------------------------------------
# 1) Bigquery_Customer
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery `Customer` table containing customer profile information.

**Schema:** `genai-poc-424806.MCP_demo.Customer`
- CustomerID (INT64, PRIMARY KEY)
- FirstName (STRING)
- LastName (STRING)
- Email (STRING)
- Phone (STRING)
- Address (STRING)
- JoinDate (DATE)

Use this tool to:
- Retrieve customer demographic and contact information
- Filter customers by join date, name, or location
- Join customer data with sales, feedback, or call logs

**Example:** SELECT * FROM `genai-poc-424806.MCP_demo.Customer` WHERE JoinDate >= '2024-01-01'
""")
def Bigquery_Customer(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "Customer", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 2) Cloud_SQL_Product  (name preserved; queries BigQuery table)
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery `Product` table containing product catalog information.

**Schema:** `genai-poc-424806.MCP_demo.Product`
- ProductID (INT64, PRIMARY KEY)
- ProductName (STRING)
- Category (STRING)
- Price (FLOAT64)
- StockQuantity (INT64)
- AddedDate (DATE)

Use this tool to:
- Retrieve product details, categories, and pricing
- Filter products by category, stock levels, or date added
- Support product catalog analytics and inventory management

**Example:** SELECT * FROM `genai-poc-424806.MCP_demo.Product` WHERE Category = 'Electronics'
""")
def Cloud_SQL_Product(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "Product", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 3) SAP_Hana_Sales
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery `Sales` table containing transaction records.

**Schema:** `genai-poc-424806.MCP_demo.Sales`
- SalesID (INT64, PRIMARY KEY)
- CustomerID (INT64)
- ProductID (INT64)
- Quantity (INT64)
- TotalAmount (FLOAT64)
- SaleDate (DATE)

Use this tool to:
- Analyze total sales amounts and quantities
- Filter transactions by date, customer, or product
- Aggregate sales metrics for reporting and dashboards

**Example:** SELECT CustomerID, SUM(TotalAmount) FROM `genai-poc-424806.MCP_demo.Sales` GROUP BY CustomerID
""")
def SAP_Hana_Sales(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "Sales", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 4) Oracle_CustomerFeedback
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery `CustomerFeedback` table containing customer reviews and comments.

**Schema:** `genai-poc-424806.MCP_demo.CustomerFeedback`
- FeedbackID (INT64, PRIMARY KEY)
- CustomerID (INT64)
- ProductID (INT64)
- SalesID (INT64)
- FeedbackDate (DATE)
- Feedback (STRING)

Use this tool to:
- Retrieve customer feedback and satisfaction data
- Filter reviews by date, product, or sentiment keywords
- Link feedback to sales transactions for quality analysis

**Example:** SELECT * FROM `genai-poc-424806.MCP_demo.CustomerFeedback` WHERE ProductID = 101
""")
def Oracle_CustomerFeedback(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "CustomerFeedback", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 5) amazon_redshift_CustomerCallLog
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery `CustomerCallLog` table containing customer service call history.

**Schema:** `genai-poc-424806.MCP_demo.CustomerCallLog`
- CallID (INT64, PRIMARY KEY)
- CustomerID (INT64)
- CallDate (DATE)
- CallReason (STRING)
- CallDurationMinutes (INT64)
- CallNotes (STRING)

Use this tool to:
- Retrieve and analyze customer service interactions
- Filter call logs by reason, duration, or date
- Track customer engagement and support history

**Example:** SELECT * FROM `genai-poc-424806.MCP_demo.CustomerCallLog` WHERE CallReason = 'Product Inquiry'
""")
def amazon_redshift_CustomerCallLog(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "CustomerCallLog", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 6) Azure_SQL_database_daily_market_indices_with_news
# -----------------------------------------------------------------------------
@mcp.tool(
    name="Azure_SQL_database_daily_market_indices_with_news",
    description="""
Execute a SQL query on the BigQuery `daily_market_indices_with_news` table containing daily financial market indices and related news headlines.

**Schema:** `genai-poc-424806.MCP_demo.daily_market_indices_with_news`
- Date (DATE)
- AAPL (FLOAT64) — Apple Inc. closing price
- NASDAQ (FLOAT64) — NASDAQ Composite index closing value
- NYA (FLOAT64) — NYSE Composite index closing value
- SP500 (FLOAT64) — S&P 500 index closing value
- DJI (FLOAT64) — Dow Jones Industrial Average closing value
- Headline (STRING) — Key market-related news headline for the day

Use this tool to:
- Retrieve historical or recent market performance data
- Correlate market movements with relevant news headlines
- Filter by specific dates or date ranges
- Compare performance across indices on given dates

**Example:** 
SELECT Date, SP500, Headline 
FROM `genai-poc-424806.MCP_demo.daily_market_indices_with_news` 
WHERE Date >= '2025-01-01'
""",
)
def tool_daily_market_indices_with_news(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {
            "table": "daily_market_indices_with_news",
            "row_count": len(rows),
            "rows": rows
        }
    except Exception as e:
        print("Azure_SQL_database_daily_market_indices_with_news failed")
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 7) DMV_Customer_Feedback
# -----------------------------------------------------------------------------
@mcp.tool(
    name="Bigquery_dmv_customer_feedback",
    description="""
Execute a SQL query on the BigQuery `DMV_Customer_Feedback` table containing dmv customer feedback with feedback score range.

**Schema:** `genai-poc-424806.MCP_demo.DMV_Customer_Feedback`
- Response Date (Timestamp)
- Feedback (String) — DMV customer feedback text
- Score (String) — DMV customer feedback score range (e.g., "1-2", "3-5"). The Score range (1-2) is considered negative feedback, while (3-5) is considered positive feedback.

Use this tool to:
- Retrieve DMV customer feedback text with score range
- Analyze customer satisfaction trends over time
- Filter feedback by specific score ranges or dates

**Example:** 
SELECT * FROM `genai-poc-424806.MCP_demo.DMV_Customer_Feedback` where Score='(3-5)' and `Response Date`>'2025-07-05'
""",
)
def tool_dmv_customer_feedback(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {
            "table": "DMV_Customer_Feedback",
            "row_count": len(rows),
            "rows": rows
        }
    except Exception as e:
        print("Bigquery_dmv_customer_feedback failed")
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 8).Threat_intelligence
# -----------------------------------------------------------------------------
@mcp.tool(
    name="Threat_Intelligence_IOCs",
    description="""
Query the BigQuery `threat_iocs` table containing threat intelligence indicators of compromise (IOCs).

**Schema:** `genai-poc-424806.MCP_demo.threat_iocs`
- ioc_type (STRING) — Type of IOC (IP, URL, domain, hash)
- value (STRING) — Actual IOC value
- threat_actor (STRING) — Associated threat actor
- source (STRING) — Source of the IOC
- confidence (STRING) — Confidence level
- first_seen (TIMESTAMP)
- last_seen (TIMESTAMP)
- ttps (STRING) — Tactics, Techniques, and Procedures

Use this tool to:
- Investigate IOCs and their context
- Filter by time, threat actor, or confidence
- Link IOCs with alerting, threat feeds, or TTPs

**Example:** SELECT * FROM `genai-poc-424806.MCP_demo.threat_iocs` WHERE threat_actor = 'APT29'
"""
)
def tool_threat_iocs(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "threat_iocs", "row_count": len(rows), "rows": rows}
    except Exception as e:
        print("Threat_Intelligence_IOCs failed")
        return {"error": str(e)}
# -----------------------------------------------------------------------------
# 9).SOC Alerts Log 
# -----------------------------------------------------------------------------
@mcp.tool(
    name="SOC_Alerts_Log",
    description="""
Query the BigQuery `soc_alerts` table containing SOC alert logs.

**Schema:** `genai-poc-424806.MCP_demo.soc_alerts`
- timestamp (TIMESTAMP)
- alert_type (STRING)
- source_ip (STRING)
- destination_ip (STRING)
- alert_severity (STRING)
- description (STRING)
- status (STRING)
- resolved_by (STRING)
- resolution_time (TIMESTAMP)

Use this tool to:
- Retrieve and filter alerts by time, type, IPs, or severity
- Investigate open vs resolved alerts
- Link alerts to IOCs or threat actors

**Example:** SELECT * FROM `genai-poc-424806.MCP_demo.soc_alerts` WHERE alert_severity = 'Critical' AND status = 'Open'
"""
)
def tool_soc_alerts(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "soc_alerts", "row_count": len(rows), "rows": rows}
    except Exception as e:
        print("SOC_Alerts_Log failed")
        return {"error": str(e)}    

# -----------------------------------------------------------------------------
# 10).User Details 
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery `oeis_users` table containing user profile and license information.

**Schema:** `genai-poc-424806.vapi_ai_demo.oeis_users`
- username (STRING)
- password (STRING)
- DL_id (STRING, driver's license ID)
- Phone_No (STRING)
- Address (STRING)
-emp_id(STRING)

Use this tool to:
- Retrieve user credentials and contact details
- Filter users by location, DL_id, or phone number
- Join with other activity or ticket data by username

**Example:** SELECT * FROM `genai-poc-424806.vapi_ai_demo.oeis_users` WHERE Address LIKE '%San Jose%'
""")
def tool_Users(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "oeis_users", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 11).Ticket details
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery `ticket_details` table containing ticket and issue tracking information.

**Schema:** `genai-poc-424806.vapi_ai_demo.ticket_details`
- ticket_id (STRING)
- user_id (STRING) — refers to `username` in the users table
- issues (STRING)

Use this tool to:
- Retrieve support or issue tickets
- Filter by user, ticket ID, or keyword in issues
- Join with user data to get profile details

**Example:** SELECT * FROM `genai-poc-424806.vapi_ai_demo.ticket_details` WHERE issues LIKE '%login%'
""")
def tool_TicketDetails(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "ticket_details", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 12) BigQuery_RefundFraudDetection
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery `Refund_Fraud_Detection` table containing taxpayer filings and potential refund fraud indicators.

**Schema:** `genai-poc-424806.MCP_demo.Refund_Fraud_Detection`
- taxpayer_id (STRING)
- name (STRING)
- filing_status (STRING)
- claimed_income (FLOAT64)
- w2_income (FLOAT64)
- `1099_income` (FLOAT64)
- sched_c_income (FLOAT64)
- total_credits (FLOAT64)
- claimed_dependents (INT64)
- actual_dependents (INT64)
- earned_income_credit (FLOAT64)
- child_tax_credit (FLOAT64)
- flagged (STRING)
- explanation (STRING)

Use this tool to:
- Analyze mismatches between claimed and third-party income
- Identify suspicious credit or dependent claims
- Surface records flagged for refund fraud with explanations

**Example:** SELECT * FROM `genai-poc-424806.MCP_demo.Refund_Fraud_Detection` WHERE flagged = 'Yes'
""")
def BigQuery_RefundFraudDetection(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "Refund_Fraud_Detection", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"error": str(e)}
    
# -----------------------------------------------------------------------------
# 13) Bigquery_CarData
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery CarData table containing used car details .

**Schema:** genai-poc-424806.MCP_demo.CarData
- Car_Name (STRING)
- Year (DATE)  
- Selling_Price (FLOAT64)
- Present_Price (FLOAT64)
- Kms_Driven (INT64)
- Fuel_Type (STRING)
- Seller_Type (STRING)
- Transmission (STRING)
- Owner (INT64)

Use this tool to:
- Analyze car resale prices
- Filter cars by year (using EXTRACT(YEAR FROM Year)), fuel type, seller type, or transmission
- Detect anomalies in pricing and mileage
- Retrieve cars with specific attributes (e.g., "Petrol cars after 2015")
- Pre-process the data (whenever the user asks about preprocessing the data)

**Example:** 
SELECT * 
FROM `genai-poc-424806.MCP_demo.CarData` 
WHERE Fuel_Type = 'Petrol' AND EXTRACT(YEAR FROM Year) > 2015
""")
def BigQuery_CarData(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "CarData", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 14) BigQuery_CarDataPreprocess (Create/Update Cleaned Data)
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute SQL commands to create, insert, update, or delete data in the `CleanedCarData` table.  
This tool is specifically for preprocessing tasks on the `CarData` dataset and saving results into `CleanedCarData`.

**Behavior:**
- If the user requests preprocessing and updating:
  - Create the table `CleanedCarData` if it does not exist.
  - If it exists, replace all rows with the newly preprocessed data.
- Supports CREATE, INSERT, UPDATE, DELETE operations.
- Ensures the `CleanedCarData` table always contains the latest cleaned version of `CarData`.

**Schema of CleanedCarData (after preprocessing):**
- Car_Name (STRING)
- Year (DATE)
- Selling_Price (FLOAT64)
- Present_Price (FLOAT64)
- Kms_Driven (INT64)
- Fuel_Type (STRING)
- Seller_Type (STRING)
- Transmission (STRING)
- Owner (INT64)

**Preprocessing applied from CarData → CleanedCarData:**
- Remove duplicates
- Handle missing values (imputation or removal)
- Treat outliers (filter extreme/invalid values)
- Correct invalid categories (`Fuel_Type`, `Transmission`)
- Ensure proper data types

**Example (create/replace with cleaned data):**
CREATE OR REPLACE TABLE `genai-poc-424806.MCP_demo.CleanedCarData` AS
SELECT DISTINCT
  Car_Name,
  EXTRACT(YEAR FROM Year) AS Year,
  SAFE_CAST(Selling_Price AS FLOAT64) AS Selling_Price,
  SAFE_CAST(Present_Price AS FLOAT64) AS Present_Price,
  Kms_Driven,
  CASE WHEN Fuel_Type IN ('Petrol','Diesel','CNG') THEN Fuel_Type ELSE NULL END AS Fuel_Type,
  Seller_Type,
  CASE WHEN Transmission IN ('Manual','Automatic') THEN Transmission ELSE NULL END AS Transmission,
  Owner
FROM `genai-poc-424806.MCP_demo.CarData`
WHERE Selling_Price > 0 AND Kms_Driven < 500000;
""")
def BigQuery_CarDataPreprocess(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "CleanedCarData", "row_count": len(rows) if rows else 0, "rows": rows}
    except Exception as e:
        return {"error": str(e)}


# -----------------------------------------------------------------------------
# 15) gallo_wine_reviews
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery dataset `genai-poc-424806.gallo_mcp_demo` containing financial operations data.

**Available Tables:**

1. **vendors**
   - `vendor_id` (STRING, PK)
   - `name` (STRING)
   - `contact_email` (STRING)
   - `status` (STRING) — e.g., 'Active', 'Inactive'
   - `created_at` (TIMESTAMP)

2. **invoices**
   - `invoice_id` (STRING, PK)
   - `vendor_id` (STRING, FK to vendors)
   - `invoice_number` (STRING)
   - `amount` (FLOAT64)
   - `status` (STRING) — 'Pending', 'Paid', 'Short-paid'
   - `po_number` (STRING, nullable)
   - `invoice_date` (DATE)
   - `due_date` (DATE)

3. **purchase_orders**
   - `po_number` (STRING, PK)
   - `vendor_id` (STRING, FK to vendors)
   - `amount` (FLOAT64)
   - `status` (STRING) — 'Open', 'Closed'
   - `po_date` (DATE)

4. **payments**
   - `payment_id` (STRING, PK)
   - `invoice_id` (STRING, FK to invoices)
   - `amount_paid` (FLOAT64)
   - `payment_date` (DATE)
   - `payment_method` (STRING) — 'ACH', 'Check', 'Wire'
   - `status` (STRING) — 'Completed'

---

**Use this tool to:**
- Query individual tables or perform joins
- Filter by vendor status, invoice/payment status, PO lifecycle
- Aggregate invoice/payment/PO data by vendor or time
- Identify mismatches (e.g., short payments, overdue invoices)

---

**Examples:**
- Retrieve all active vendors:
```sql
SELECT * FROM `genai-poc-424806.gallo_mcp_demo.vendors` WHERE status = 'Active'
```

- List pending invoices with no payment:
```sql
SELECT invoice_id, amount FROM `genai-poc-424806.gallo_mcp_demo.invoices`
WHERE status = 'Pending' AND invoice_id NOT IN (
  SELECT invoice_id FROM `genai-poc-424806.gallo_mcp_demo.payments`
)
```

- Match PO vs. invoice vs. payment totals:
```sql
SELECT po.po_number, po.amount AS po_amount, 
       SUM(i.amount) AS invoice_total,
       SUM(p.amount_paid) AS payment_total
FROM `genai-poc-424806.gallo_mcp_demo.purchase_orders` po
LEFT JOIN `genai-poc-424806.gallo_mcp_demo.invoices` i ON po.po_number = i.po_number
LEFT JOIN `genai-poc-424806.gallo_mcp_demo.payments` p ON i.invoice_id = p.invoice_id
GROUP BY po.po_number, po.amount
```
""")
def Bigquery_gallo_DB_MCP_Demo(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {
            "query_success": True,
            "row_count": len(rows),
            "sample_row": rows[0] if rows else None,
            "rows": rows
        }
    except Exception as e:
        return {
            "query_success": False,
            "error": str(e)
        }

# -----------------------------------------------------------------------------
# 16) youth_health_records
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery `genai-poc-424806.MCP_demo.youth_health_records` table containing youth health records.

**Schema:** `genai-poc-424806.MCP_demo.youth_health_records`
- id (INT64, PRIMARY KEY)
- actual_release_date (DATE)
- name_of_youth (STRING)
- race_ethnicity (STRING)
- medi_cal_id (STRING)
- residential_address (STRING)
- telephone (STRING)
- medi_cal_health_plan (STRING)
- health_screenings (STRING)
- health_assessments (STRING)
- chronic_conditions (STRING)
- prescribed_medications (STRING)
- notes (STRING)
- care_plan_notes (STRING)

Use this tool to:
- Retrieve youth health, plan, and assessment information
- Filter by release date, race/ethnicity, health plan, or chronic conditions
- Search by Medi-Cal ID or youth name (case-insensitive)
- Aggregate/segment by plan, condition, or date

**Examples:**
- SELECT * FROM `your-project.your_dataset.youth_health_records` WHERE actual_release_date >= '2024-01-01'
- SELECT race_ethnicity, COUNT(*) AS n FROM `your-project.your_dataset.youth_health_records` GROUP BY race_ethnicity ORDER BY n DESC
- SELECT * FROM `your-project.your_dataset.youth_health_records` WHERE LOWER(name_of_youth) LIKE '%garcia%'
""")
def Bigquery_YouthHealthRecords(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {"table": "youth_health_records", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# 17) ucc_records (filings & collateral)
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery dataset `genai-poc-424806.Fusable`
containing **UCC filings** and **collateral**.

**Tables & Key Columns**

1) `genai-poc-424806.Fusable.ucc_filings`
   - document_id (STRING, PK / shared key)
   - filing_number (STRING), document_number (STRING)
   - filing_datetime (TIMESTAMP), filed_with (STRING), state_code (STRING)
   - debtor_*(type,name,address1,city,state,postal_code,country)
   - debtor2_*(type,name,address1,city,state,postal_code,country)
   - secured_party_*(name,address1,city,state,postal_code,country)
   - collateral_held_in_trust (BOOL), decedent_administered (BOOL),
     public_finance_transaction (BOOL), manufactured_home_transaction (BOOL),
     debtor_is_transmitting_utility (BOOL), agricultural_lien (BOOL),
     non_ucc_filing (BOOL), alt_designation (STRING), optional_filer_reference (STRING)

2) `genai-poc-424806.Fusable.ucc_collateral`
   - collateral_id (STRING, default GENERATE_UUID())
   - document_id (STRING, FK → ucc_filings.document_id)
   - description_full (STRING), collateral_category (STRING)
   - year (INT64), manufacturer (STRING), model (STRING),
     equip_description (STRING), serial_number (STRING), vin (STRING),
     additional_notes (STRING)

**Use this tool to:**
- Join filings ↔ collateral by `document_id`
- Search by VIN/serial/manufacturer/model/year
- Aggregate by state, debtor, secured party, or designation flags
- Validate data quality (orphans, duplicates, VIN length)

**Examples:**
- One filing with all collateral:
  SELECT f.*, c.*
  FROM `genai-poc-424806.Fusable.ucc_filings` f
  LEFT JOIN `genai-poc-424806.Fusable.ucc_collateral` c USING (document_id)
  WHERE f.document_id = '1723941';

- Search by VIN:
  SELECT c.vin, c.serial_number, f.document_id, f.debtor_name, f.secured_party_name, f.filing_datetime
  FROM `genai-poc-424806.Fusable.ucc_collateral` c
  JOIN `genai-poc-424806.Fusable.ucc_filings` f USING (document_id)
  WHERE c.vin = '1HGCM82633A004352';

- Flag prevalence:
  SELECT flag, COUNTIF(val) AS count_true FROM (
    SELECT
      IFNULL(collateral_held_in_trust, FALSE) AS collateral_held_in_trust,
      IFNULL(decedent_administered, FALSE) AS decedent_administered,
      IFNULL(public_finance_transaction, FALSE) AS public_finance_transaction,
      IFNULL(manufactured_home_transaction, FALSE) AS manufactured_home_transaction,
      IFNULL(debtor_is_transmitting_utility, FALSE) AS debtor_is_transmitting_utility,
      IFNULL(agricultural_lien, FALSE) AS agricultural_lien,
      IFNULL(non_ucc_filing, FALSE) AS non_ucc_filing
    FROM `genai-poc-424806.Fusable.ucc_filings`
  ) UNPIVOT(val FOR flag IN (
    collateral_held_in_trust, decedent_administered, public_finance_transaction,
    manufactured_home_transaction, debtor_is_transmitting_utility,
    agricultural_lien, non_ucc_filing
  ))
  GROUP BY flag ORDER BY count_true DESC;
""")
def Bigquery_UCC(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {
            "query_success": True,
            "row_count": len(rows),
            "sample_row": rows[0] if rows else None,
            "rows": rows,
        }
    except Exception as e:
        return {
            "query_success": False,
            "error": str(e),
        }

# -----------------------------------------------------------------------------
# 18) sac_ceqa_analytics
# -----------------------------------------------------------------------------
@mcp.tool(description="""
Execute a SQL query on the BigQuery dataset `genai-poc-424806.SAC_CEQA`
for Sacramento CEQA-related analytics, summaries, correlations, and clustering.

**Indirect keyword (for routing among many tools):** `ceqa`
- You can prefix your request with **ceqa** to target this tool, e.g.:
  - `ceqa → show fire severity distribution by class`
  - `ceqa → build 4-cluster model on heat metrics`

**Available Tables**
1) **sac_calenviroscreen**
   - `tract_geoid` (INT64) — census tract GEOID
   - `county` (STRING)
   - `ces_score` (FLOAT64)
   - `ces_percentile` (FLOAT64)
   - `pollution_burden` (FLOAT64)
   - `pop_characteristics` (FLOAT64)
   - `total_pop` (INT64)

2) **sac_heat**
   - `time` (DATETIME/TIMESTAMP or STRING as ingested)
   - `temperature_2m_max` (FLOAT64)
   - `temperature_2m_mean` (FLOAT64)
   - `temperature_2m_min` (FLOAT64)
   - `apparent_temperature_max` (FLOAT64)

3) **sac_fire_severity**
   - `OBJECTID` (INT64)
   - `SRA at original adoption by recommendation` (STRING)
   - `SRA SRA22_2` (STRING)
   - `FHSZ` (INT64) — severity code
   - `FHSZ_Description` (STRING)
   - `FHSZ_7Class` (STRING)
   - `Shape__Area` (FLOAT64)
   - `Shape__Length` (FLOAT64)

4) **sac_ceqa_documents**
   - `sch` (INT64) — project id
   - `document_id` (INT64)
   - `doc_title` (STRING)
   - `doc_type` (STRING)
   - `lead_agency` (STRING)
   - `received_date` (DATE)
   - `posted_date` (DATE)
   - `cities` (STRING)
   - `county` (STRING)
   - `detail_url` (STRING)
   - (optional) `attachment_url`, `file_size_kb`, `is_pdf`, `is_primary_doc`

5) **sac_ceqa_manifest**
   - `sch` (INT64)
   - `document_id` (INT64)
   - `doc_title` (STRING)
   - `doc_type` (STRING)
   - `lead_agency` (STRING)
   - `received_date` (DATE)
   - `posted_date` (DATE)
   - `cities` (STRING)
   - `county` (STRING)
   - `detail_url` (STRING)

6) **sac_population**
   - Example columns:
     - `Label Grouping` (STRING)
     - `Sacramento County California Estimate` (NUMERIC/STRING)
     - `Sacramento County California Margin of Error` (NUMERIC/STRING)
     - `Sacramento County California Percent` (NUMERIC/STRING)
     - `Sacramento County California Percent Margin of Error` (NUMERIC/STRING)

---

**Use this tool to:**
- Inspect schemas & counts (INFORMATION_SCHEMA).
- Compute numeric summaries & categorical distributions.
- Detect outliers (e.g., IQR or z-score) in selected metrics.
- Calculate correlations between features.
- Train & score KMeans clusters with BigQuery ML (3–5 segments).
- Produce time-series rollups ready for charting.

---

**Handy SQL snippets (copy/paste & modify):**

• List columns/types for a table
```sql
SELECT table_name, column_name, data_type, is_nullable, description
FROM `genai-poc-424806.SAC_CEQA`.INFORMATION_SCHEMA.COLUMNS
WHERE table_name = 'sac_calenviroscreen'
ORDER BY ordinal_position;

Table: fire severity        
SELECT FHSZ_Description, COUNT(*) AS n
FROM `genai-poc-424806.SAC_CEQA.sac_fire_severity`

Table: sac_heat
SELECT
  COUNT(*) AS n,
  AVG(temperature_2m_max) AS avg_tmax,
  STDDEV_SAMP(temperature_2m_max) AS sd_tmax,
  MIN(temperature_2m_max) AS min_tmax,
  MAX(temperature_2m_max) AS max_tmax
FROM `genai-poc-424806.SAC_CEQA.sac_heat`;       
""")
def Bigquery_SAC_CEQA_Analytics(sql: str) -> dict:
    try:
        rows = run_bq(sql)
        return {
            "dataset": "genai-poc-424806.SAC_CEQA",
            "query_success": True,
            "row_count": len(rows),
            "sample_row": rows[0] if rows else None,
            "rows": rows
        }
    except Exception as e:
        return {
            "query_success": False,
            "error": str(e)
        }
            

# === Entrypoint ===
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)