import os
import pyodbc
import psycopg2
from typing import Any, Optional
import random
import pandas as pd
from datetime import datetime, timedelta
from fastmcp import FastMCP
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def must_get(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing required env var {key}")
    return val


MYSQL_HOST = must_get("MYSQL_HOST")
MYSQL_PORT = int(must_get("MYSQL_PORT"))
MYSQL_USER = must_get("MYSQL_USER")
MYSQL_PASSWORD = must_get("MYSQL_PASSWORD")
MYSQL_DB = must_get("MYSQL_DB")


def get_mysql_conn(db: str | None = MYSQL_DB):
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=db,
        ssl_disabled=False,
        autocommit=True,
    )


PG_HOST = must_get("PG_HOST")
PG_PORT = int(must_get("PG_PORT"))
PG_DB = os.getenv("PG_DB", "postgres")
PG_USER = must_get("PG_USER")
PG_PASS = must_get("PG_PASSWORD")


def get_pg_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        sslmode="require",
    )


PG_SALES_HOST = must_get("PG_SALES_HOST")
PG_SALES_PORT = int(must_get("PG_SALES_PORT"))
PG_SALES_DB = os.getenv("PG_SALES_DB", "sales_db")
PG_SALES_USER = must_get("PG_SALES_USER")
PG_SALES_PASS = must_get("PG_SALES_PASSWORD")


def get_pg_sales_conn():
    return psycopg2.connect(
        host=PG_SALES_HOST,
        port=PG_SALES_PORT,
        dbname=PG_SALES_DB,
        user=PG_SALES_USER,
        password=PG_SALES_PASS,
        sslmode="require",
    )


mcp = FastMCP("CRUDServer")


def generate_call_transcript(issue_category, resolution_status, sentiment_score, agent_name, duration):
    transcript_templates = {
        'billing': {
            'positive': [
                f"Customer called about billing discrepancy. {agent_name} explained the charges clearly. Customer expressed satisfaction with the detailed breakdown. Issue resolved by applying appropriate credit adjustment. Customer thanked agent for patience.",
                f"Inquiry about unexpected charges on account. {agent_name} reviewed billing history, identified duplicate charge. Immediate refund processed. Customer appreciated quick resolution and professional service provided.",
                f"Customer confused about new billing format. {agent_name} walked through each line item. Customer now understands charges better. Offered paperless billing option which customer accepted happily.",
            ],
            'negative': [
                f"Customer upset about overcharge. {agent_name} attempted to explain but customer remained frustrated. Multiple billing errors found. Escalated to supervisor for resolution. Customer demanded compensation for inconvenience.",
                f"Angry customer disputing charges for third month. {agent_name} unable to locate previous adjustment notes. System showing conflicting information. Customer threatened to cancel service. Immediate escalation required.",
                f"Customer extremely dissatisfied with billing practices. {agent_name} apologized repeatedly but customer remained hostile. Previous promises not honored. Customer considering legal action. Urgent management intervention needed.",
            ],
            'neutral': [
                f"Routine billing inquiry about statement date. {agent_name} explained billing cycle details. Customer requested email confirmation. Standard information provided. Call concluded with no issues identified.",
                f"Customer checking on payment processing status. {agent_name} confirmed payment received yesterday. Updated account reflects current balance. Customer satisfied with information. No further action required.",
            ]
        },
        'technical': {
            'positive': [
                f"Customer experiencing connectivity issues. {agent_name} performed remote diagnostics successfully. Issue identified as router configuration problem. Guided customer through reset process. Service restored, customer very grateful.",
                f"Software installation problem reported. {agent_name} provided step-by-step guidance. Customer followed instructions carefully. Installation completed successfully. Customer praised agent's clear communication skills.",
                f"Customer needed help with new feature setup. {agent_name} shared screen remotely. Configuration completed together. Customer learned valuable tips. Highly satisfied with support received.",
            ],
            'negative': [
                f"Recurring technical problem frustrating customer. {agent_name} attempted multiple troubleshooting steps unsuccessfully. Customer lost patience during lengthy process. Previous tickets show unresolved issues. Escalation to technical team required.",
                f"Customer angry about service outage. {agent_name} acknowledged ongoing system issues. No immediate resolution available. Customer demanding compensation for business losses. Extremely dissatisfied with response.",
                f"Critical system failure affecting customer operations. {agent_name} unable to provide timeline for fix. Customer stressed about impact on business. Multiple failed resolution attempts. Emergency escalation initiated.",
            ],
            'neutral': [
                f"Customer inquiring about system maintenance schedule. {agent_name} provided upcoming maintenance windows. Customer noted dates for planning. Standard information exchanged. Call ended cordially.",
                f"Routine technical specification question. {agent_name} consulted documentation and provided details. Customer taking notes for internal team. Information delivered as requested. No issues noted.",
            ]
        },
        'product_inquiry': {
            'positive': [
                f"Customer interested in new product features. {agent_name} enthusiastically explained benefits and pricing. Customer impressed with capabilities. Decided to upgrade immediately. Very satisfied with information received.",
                f"Inquiry about product compatibility. {agent_name} confirmed full compatibility with customer's setup. Provided additional recommendations. Customer pleased with comprehensive response. Proceeding with purchase.",
                f"Customer seeking product recommendations. {agent_name} analyzed needs and suggested perfect solution. Customer excited about features. Order placed during call. Thanked agent for expertise.",
            ],
            'negative': [
                f"Customer disappointed with product limitations. {agent_name} explained current capabilities. Customer expected more features for price. Unhappy with value proposition. Considering competitor alternatives.",
                f"Product not meeting advertised specifications. {agent_name} acknowledged discrepancy. Customer frustrated with misleading information. Requested full refund. Very dissatisfied with experience.",
            ],
            'neutral': [
                f"General product information request. {agent_name} provided standard specifications and pricing. Customer collecting information for comparison. Will discuss with team. Polite interaction throughout.",
                f"Customer checking product availability. {agent_name} confirmed stock levels and delivery times. Customer will consider options. Standard inquiry handled efficiently. No commitment made.",
            ]
        },
        'complaint': {
            'positive': [
                f"Customer initially upset about service issue. {agent_name} listened empathetically and apologized sincerely. Offered immediate solution and compensation. Customer attitude improved significantly. Ended call satisfied.",
                f"Complaint about previous poor experience. {agent_name} took ownership and implemented corrective measures. Customer appreciated proactive approach. Issue resolved beyond expectations. Relationship restored.",
            ],
            'negative': [
                f"Customer extremely angry about repeated problems. {agent_name} struggled to calm situation. Multiple service failures documented. Customer demanding executive contact. Threatening social media exposure.",
                f"Serious complaint about staff behavior. {agent_name} attempted damage control unsuccessfully. Customer unwilling to accept apologies. Formal complaint being filed. Legal action mentioned.",
                f"Long-standing issue causing major frustration. {agent_name} unable to provide satisfactory resolution. Customer exhausted all patience. Canceling service immediately. Extremely negative experience.",
            ],
            'neutral': [
                f"Customer registering formal complaint for records. {agent_name} documented all details carefully. Standard complaint procedure followed. Reference number provided. Professional interaction maintained throughout.",
            ]
        },
        'order_status': {
            'positive': [
                f"Customer checking on recent order. {agent_name} provided tracking information promptly. Delivery on schedule for tomorrow. Customer pleased with quick update. Expressed satisfaction with service.",
                f"Inquiry about expedited shipping options. {agent_name} arranged priority delivery at no charge. Customer delighted with accommodation. Order upgraded successfully. Very appreciative of help.",
            ],
            'negative': [
                f"Order significantly delayed without notification. {agent_name} found logistics error. Customer upset about lack of communication. Business impact significant. Demanding immediate resolution and compensation.",
                f"Wrong items delivered twice. {agent_name} apologized but no immediate fix available. Customer frustrated with repeated errors. Quality control issues evident. Considering canceling all future orders.",
            ],
            'neutral': [
                f"Routine order status check. {agent_name} confirmed shipment departed this morning. Tracking number provided via email. Customer satisfied with update. Standard inquiry resolved quickly.",
            ]
        },
        'account': {
            'positive': [
                f"Customer needed password reset assistance. {agent_name} verified identity and reset credentials. Access restored immediately. Customer grateful for quick help. Security tips provided and appreciated.",
                f"Account upgrade request. {agent_name} processed changes efficiently. New features activated instantly. Customer excited about enhanced capabilities. Smooth transition completed.",
            ],
            'negative': [
                f"Account hacked, unauthorized charges made. {agent_name} initiated security protocol. Customer panicked about data breach. Investigation will take days. Very upset about security failure.",
                f"Unable to access account for weeks. {agent_name} found system error. Customer missed important deadlines. Business losses mounting. Extremely frustrated with platform reliability.",
            ],
            'neutral': [
                f"Customer updating contact information. {agent_name} processed changes in system. Confirmation email sent. Standard account maintenance completed. No issues encountered.",
            ]
        },
        'refund': {
            'positive': [
                f"Refund request for defective product. {agent_name} approved immediately after verification. Processing within 3-5 days. Customer satisfied with quick approval. Appreciated hassle-free process.",
                f"Customer requesting partial refund for service issue. {agent_name} calculated fair adjustment. Credit applied to account instantly. Customer happy with resolution. Thanked agent for understanding.",
            ],
            'negative': [
                f"Refund denied despite valid complaint. {agent_name} cited policy restrictions. Customer arguing about unfair treatment. Previous promises not honored. Threatening chargeback through bank.",
                f"Multiple refund requests ignored. {agent_name} found processing errors. Customer exhausted and angry. Financial hardship mentioned. Considering legal action for resolution.",
            ],
            'neutral': [
                f"Standard refund inquiry about timeline. {agent_name} explained processing procedures. Customer understood requirements. Documentation submitted. Awaiting standard processing time.",
            ]
        },
        'general': {
            'positive': [
                f"Customer calling to praise recent service. {agent_name} accepted compliments graciously. Customer wanted manager to know about excellent experience. Positive feedback documented. Very satisfied customer.",
                f"General inquiry about services. {agent_name} provided comprehensive overview. Customer impressed with options available. Interested in learning more. Scheduling follow-up consultation.",
            ],
            'negative': [
                f"Customer expressing overall dissatisfaction. {agent_name} listened to multiple concerns. Long list of problems mentioned. Customer considering switching providers. Retention team referral needed.",
                f"Vague complaint about service quality. {agent_name} tried identifying specific issues. Customer frustrated with everything. Unable to pinpoint exact problem. General dissatisfaction expressed.",
            ],
            'neutral': [
                f"Customer had miscellaneous questions. {agent_name} answered each one patiently. Information gathering for future reference. No immediate action needed. Cordial conversation throughout.",
                f"General check-in call about services. {agent_name} reviewed account status. Everything functioning normally. Customer had no concerns. Brief, pleasant interaction.",
            ]
        }
    }

    if sentiment_score >= 0.3:
        sentiment_cat = 'positive'
    elif sentiment_score <= -0.3:
        sentiment_cat = 'negative'
    else:
        sentiment_cat = 'neutral'

    if issue_category in transcript_templates:
        templates = transcript_templates[issue_category].get(sentiment_cat,
                                                             transcript_templates[issue_category]['neutral'])
    else:
        templates = transcript_templates['general'][sentiment_cat]

    base_transcript = random.choice(templates)

    if duration < 120:
        base_transcript = "Quick call. " + base_transcript
    elif duration > 900:
        base_transcript = "Extended call requiring patience. " + base_transcript

    if resolution_status == 'escalated':
        base_transcript += " Supervisor intervention required."
    elif resolution_status == 'pending':
        base_transcript += " Follow-up scheduled."

    words = base_transcript.split()
    if len(words) > 40:
        base_transcript = ' '.join(words[:40])
    elif len(words) < 30:
        padding = [
            "Additional notes added.",
            "Customer database updated.",
            "Ticket created for tracking.",
            "Quality assurance reviewed.",
            "Standard procedures followed.",
        ]
        while len(words) < 30:
            words.extend(random.choice(padding).split())
        base_transcript = ' '.join(words[:40])

    return base_transcript


def seed_databases():
    root_cnx = get_mysql_conn(db=None)
    root_cur = root_cnx.cursor()
    root_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}`;")
    root_cur.close()
    root_cnx.close()

    sql_cnx = get_mysql_conn()
    sql_cur = sql_cnx.cursor()

    sql_cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
    sql_cur.execute("DROP TABLE IF EXISTS Sales;")
    sql_cur.execute("DROP TABLE IF EXISTS ProductsCache;")
    sql_cur.execute("DROP TABLE IF EXISTS Customers;")
    sql_cur.execute("DROP TABLE IF EXISTS CarePlan;")
    sql_cur.execute("DROP TABLE IF EXISTS CallLogs;")
    sql_cur.execute("SET FOREIGN_KEY_CHECKS = 1;")

    sql_cur.execute("""
                    CREATE TABLE Customers
                    (
                        Id        INT AUTO_INCREMENT PRIMARY KEY,
                        FirstName VARCHAR(50) NOT NULL,
                        LastName  VARCHAR(50) NOT NULL,
                        Name      VARCHAR(100) NOT NULL,
                        Email     VARCHAR(100),
                        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)

    sql_cur.executemany(
        "INSERT INTO Customers (FirstName, LastName, Name, Email) VALUES (%s, %s, %s, %s)",
        [("Alice", "Johnson", "Alice Johnson", "alice@example.com"),
         ("Bob", "Smith", "Bob Smith", "bob@example.com"),
         ("Charlie", "Brown", "Charlie Brown", None)]
    )

    sql_cur.execute("""
                    CREATE TABLE ProductsCache
                    (
                        id          INT PRIMARY KEY,
                        name        VARCHAR(100) NOT NULL,
                        price       DECIMAL(10, 4) NOT NULL,
                        description TEXT
                    );
                    """)

    sql_cur.executemany(
        "INSERT INTO ProductsCache (id, name, price, description) VALUES (%s, %s, %s, %s)",
        [(1, "Widget", 9.99, "A standard widget."),
         (2, "Gadget", 14.99, "A useful gadget."),
         (3, "Tool", 24.99, None)]
    )

    sql_cur.execute("""
                    CREATE TABLE Sales
                    (
                        Id           INT AUTO_INCREMENT PRIMARY KEY,
                        customer_id  INT            NOT NULL,
                        product_id   INT            NOT NULL,
                        quantity     INT            NOT NULL DEFAULT 1,
                        unit_price   DECIMAL(10, 4) NOT NULL,
                        total_price  DECIMAL(10, 4) NOT NULL,
                        sale_date    TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (customer_id) REFERENCES Customers(Id) ON DELETE CASCADE,
                        FOREIGN KEY (product_id) REFERENCES ProductsCache(id) ON DELETE CASCADE
                    );
                    """)

    sql_cur.executemany(
        "INSERT INTO Sales (customer_id, product_id, quantity, unit_price, total_price) VALUES (%s, %s, %s, %s, %s)",
        [(1, 1, 2, 9.99, 19.98),
         (2, 2, 1, 14.99, 14.99),
         (3, 3, 3, 24.99, 74.97)]
    )

    sql_cur.execute("""
    CREATE TABLE IF NOT EXISTS CarePlan (
        ID INT AUTO_INCREMENT PRIMARY KEY,
        ActualReleaseDate DATE,
        NameOfYouth VARCHAR(255),
        RaceEthnicity VARCHAR(100),
        MediCalID VARCHAR(50),
        ResidentialAddress TEXT,
        Telephone VARCHAR(20),
        MediCalHealthPlan VARCHAR(100),
        HealthScreenings TEXT,
        HealthAssessments TEXT,
        ChronicConditions TEXT,
        PrescribedMedications TEXT,
        Notes TEXT,
        CarePlanNotes TEXT,
        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """)

        # Check if the file exists first
    try:
        df = pd.read_csv("output.tsv", sep="\t")
        
        # Replace 'nan' strings and NaN values with None (which becomes NULL in SQL)
        df = df.replace('nan', None)
        df = df.replace({pd.NaT: None, float('nan'): None})
        
        insert_sql = """
                    INSERT INTO CarePlan (
                        ActualReleaseDate, NameOfYouth, RaceEthnicity, MediCalID,
                        ResidentialAddress, Telephone, MediCalHealthPlan, HealthScreenings,
                        HealthAssessments, ChronicConditions, PrescribedMedications,
                        Notes, CarePlanNotes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

        for _, row in df.iterrows():
            # Convert each value, handling NaN and None properly
            values = (
                row.get('ActualReleaseDate') if pd.notna(row.get('ActualReleaseDate')) else None,
                row.get('NameOfYouth') if pd.notna(row.get('NameOfYouth')) else None,
                row.get('RaceEthnicity') if pd.notna(row.get('RaceEthnicity')) else None,
                row.get('MediCalID') if pd.notna(row.get('MediCalID')) else None,
                row.get('ResidentialAddress') if pd.notna(row.get('ResidentialAddress')) else None,
                row.get('Telephone') if pd.notna(row.get('Telephone')) else None,
                row.get('MediCalHealthPlan') if pd.notna(row.get('MediCalHealthPlan')) else None,
                row.get('HealthScreenings') if pd.notna(row.get('HealthScreenings')) else None,
                row.get('HealthAssessments') if pd.notna(row.get('HealthAssessments')) else None,
                row.get('ChronicConditions') if pd.notna(row.get('ChronicConditions')) else None,
                row.get('PrescribedMedications') if pd.notna(row.get('PrescribedMedications')) else None,
                row.get('Notes') if pd.notna(row.get('Notes')) else None,
                row.get('CarePlanNotes') if pd.notna(row.get('CarePlanNotes')) else None
            )
            
            sql_cur.execute(insert_sql, values)
            
    except FileNotFoundError:
        print("⚠️  output.tsv file not found. Skipping CarePlan data seeding.")
    except Exception as e:
        print(f"⚠️  Error seeding CarePlan data: {e}")
    
    sql_cur.execute("""
        CREATE TABLE IF NOT EXISTS CallLogs (
            LogID INT AUTO_INCREMENT PRIMARY KEY,
            CallDate DATETIME NOT NULL,
            CustomerID INT,
            AgentName VARCHAR(100),
            CallDuration INT,
            CallType VARCHAR(50),
            CallStatus VARCHAR(50),
            IssueCategory VARCHAR(100),
            ResolutionStatus VARCHAR(50),
            SentimentScore DECIMAL(3,2),
            CallNotes TEXT,
            CallTranscript TEXT,
            WaitTime INT,
            TransferCount INT DEFAULT 0,
            FOREIGN KEY (CustomerID) REFERENCES Customers(Id) ON DELETE SET NULL,
            INDEX idx_call_date (CallDate),
            INDEX idx_customer (CustomerID),
            INDEX idx_category (IssueCategory),
            FULLTEXT INDEX idx_transcript (CallTranscript)
        );
    """)

    call_log_data = []
    agents = ['Sarah Chen', 'Mike Johnson', 'Emily Davis', 'James Wilson',
              'Lisa Anderson', 'David Martinez', 'Jennifer Brown', 'Robert Taylor']
    call_types = ['inbound', 'outbound', 'transfer']
    call_statuses = ['completed', 'dropped', 'voicemail']
    issue_categories = ['billing', 'technical', 'product_inquiry', 'complaint',
                        'order_status', 'account', 'refund', 'general']
    resolution_statuses = ['resolved', 'escalated', 'pending', 'follow_up']

    base_date = datetime.now() - timedelta(days=90)

    for i in range(300):
        call_date = base_date + timedelta(
            days=random.randint(0, 89),
            hours=random.randint(8, 20),
            minutes=random.randint(0, 59)
        )

        agent = random.choice(agents)
        duration = random.randint(30, 1800)
        issue = random.choice(issue_categories)
        resolution = random.choice(resolution_statuses)
        sentiment = round(random.uniform(-0.5, 1.0), 2)

        transcript = generate_call_transcript(issue, resolution, sentiment, agent, duration)

        call_notes = f"Customer called regarding {issue} issue. {random.choice(['Issue resolved successfully.', 'Escalated to supervisor.', 'Follow-up required.', 'Customer satisfied with resolution.'])}"

        call_log_data.append((
            call_date,
            random.randint(1, 3),
            agent,
            duration,
            random.choice(call_types),
            random.choice(call_statuses),
            issue,
            resolution,
            sentiment,
            call_notes,
            transcript,
            random.randint(0, 300),
            random.randint(0, 3)
        ))

    sql_cur.executemany("""
        INSERT INTO CallLogs (CallDate, CustomerID, AgentName, CallDuration, CallType,
                             CallStatus, IssueCategory, ResolutionStatus, SentimentScore,
                             CallNotes, CallTranscript, WaitTime, TransferCount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, call_log_data)

    sql_cnx.close()

    pg_cnxn = get_pg_conn()
    pg_cnxn.autocommit = True
    pg_cur = pg_cnxn.cursor()
    pg_cur.execute("DROP TABLE IF EXISTS products CASCADE;")
    pg_cur.execute("""
                   CREATE TABLE products
                   (
                       id          SERIAL PRIMARY KEY,
                       name        TEXT           NOT NULL,
                       price       NUMERIC(10, 4) NOT NULL,
                       description TEXT
                   );
                   """)
    pg_cur.executemany(
        "INSERT INTO products (name, price, description) VALUES (%s, %s, %s)",
        [("Widget", 9.99, "A standard widget."),
         ("Gadget", 14.99, "A useful gadget."),
         ("Tool", 24.99, "A handy tool.")]
    )
    pg_cnxn.close()

    sales_cnxn = get_pg_sales_conn()
    sales_cnxn.autocommit = True
    sales_cur = sales_cnxn.cursor()
    sales_cur.execute("DROP TABLE IF EXISTS sales;")
    sales_cur.execute("""
                      CREATE TABLE sales
                      (
                          id           SERIAL PRIMARY KEY,
                          customer_id  INT            NOT NULL,
                          product_id   INT            NOT NULL,
                          quantity     INT            NOT NULL DEFAULT 1,
                          unit_price   NUMERIC(10, 4) NOT NULL,
                          total_amount NUMERIC(10, 4) NOT NULL,
                          sale_date    TIMESTAMP               DEFAULT CURRENT_TIMESTAMP
                      );
                      """)
    sales_cur.executemany(
        "INSERT INTO sales (customer_id, product_id, quantity, unit_price, total_amount) VALUES (%s, %s, %s, %s, %s)",
        [(1, 1, 2, 9.99, 19.98),
         (2, 2, 1, 14.99, 14.99),
         (3, 3, 3, 24.99, 74.97)]
    )
    sales_cnxn.close()


def get_customer_id_by_name(name: str) -> Optional[int]:
    conn = get_mysql_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM Customers WHERE Name = %s", (name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_product_id_by_name(name: str) -> Optional[int]:
    conn = get_pg_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Products WHERE name = %s", (name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def get_customer_name(customer_id: int) -> str:
    try:
        mysql_cnxn = get_mysql_conn()
        mysql_cur = mysql_cnxn.cursor()
        mysql_cur.execute("SELECT Name FROM Customers WHERE Id = %s", (customer_id,))
        result = mysql_cur.fetchone()
        mysql_cnxn.close()
        return result[0] if result else f"Unknown Customer ({customer_id})"
    except Exception:
        return f"Unknown Customer ({customer_id})"


def get_product_details(product_id: int) -> dict:
    try:
        pg_cnxn = get_pg_conn()
        pg_cur = pg_cnxn.cursor()
        pg_cur.execute("SELECT name, price FROM products WHERE id = %s", (product_id,))
        result = pg_cur.fetchone()
        pg_cnxn.close()
        if result:
            return {"name": result[0], "price": float(result[1])}
        else:
            return {"name": f"Unknown Product ({product_id})", "price": 0.0}
    except Exception:
        return {"name": f"Unknown Product ({product_id})", "price": 0.0}


def validate_customer_exists(customer_id: int) -> bool:
    try:
        mysql_cnxn = get_mysql_conn()
        mysql_cur = mysql_cnxn.cursor()
        mysql_cur.execute("SELECT COUNT(*) FROM Customers WHERE Id = %s", (customer_id,))
        result = mysql_cur.fetchone()
        mysql_cnxn.close()
        return result[0] > 0 if result else False
    except Exception:
        return False


def validate_product_exists(product_id: int) -> bool:
    try:
        pg_cnxn = get_pg_conn()
        pg_cur = pg_cnxn.cursor()
        pg_cur.execute("SELECT COUNT(*) FROM products WHERE id = %s", (product_id,))
        result = pg_cur.fetchone()
        pg_cnxn.close()
        return result[0] > 0 if result else False
    except Exception:
        return False


def find_customer_by_name_enhanced(name: str) -> dict:
    try:
        mysql_cnxn = get_mysql_conn()
        mysql_cur = mysql_cnxn.cursor()
        all_matches = []
        mysql_cur.execute("SELECT Id, Name, Email FROM Customers WHERE LOWER(Name) = LOWER(%s)", (name,))
        exact_matches = mysql_cur.fetchall()

        if exact_matches:
            if len(exact_matches) == 1:
                mysql_cnxn.close()
                return {
                    "found": True,
                    "multiple_matches": False,
                    "customer_id": exact_matches[0][0],
                    "customer_name": exact_matches[0][1],
                    "customer_email": exact_matches[0][2]
                }
            else:
                for match in exact_matches:
                    all_matches.append({
                        "id": match[0],
                        "name": match[1],
                        "email": match[2],
                        "match_type": "exact_full_name"
                    })

        if not exact_matches:
            mysql_cur.execute("""
                SELECT Id, Name, Email FROM Customers
                WHERE LOWER(FirstName) = LOWER(%s)
                   OR LOWER(LastName) = LOWER(%s)
            """, (name, name))
            name_matches = mysql_cur.fetchall()

            for match in name_matches:
                all_matches.append({
                    "id": match[0],
                    "name": match[1],
                    "email": match[2],
                    "match_type": "exact_name_part"
                })

        if not all_matches:
            mysql_cur.execute("""
                SELECT Id, Name, Email FROM Customers
                WHERE LOWER(Name) LIKE LOWER(%s)
                   OR LOWER(FirstName) LIKE LOWER(%s)
                   OR LOWER(LastName) LIKE LOWER(%s)
            """, (f"%{name}%", f"%{name}%", f"%{name}%"))
            partial_matches = mysql_cur.fetchall()

            for match in partial_matches:
                all_matches.append({
                    "id": match[0],
                    "name": match[1],
                    "email": match[2],
                    "match_type": "partial"
                })

        mysql_cnxn.close()

        if not all_matches:
            return {"found": False, "error": f"Customer '{name}' not found"}

        if len(all_matches) == 1:
            match = all_matches[0]
            return {
                "found": True,
                "multiple_matches": False,
                "customer_id": match["id"],
                "customer_name": match["name"],
                "customer_email": match["email"]
            }

        return {
            "found": True,
            "multiple_matches": True,
            "matches": all_matches,
            "error": f"Multiple customers found matching '{name}'"
        }

    except Exception as e:
        return {"found": False, "error": f"Database error: {str(e)}"}


def find_product_by_name(name: str) -> dict:
    try:
        pg_cnxn = get_pg_conn()
        pg_cur = pg_cnxn.cursor()
        pg_cur.execute("SELECT id, name FROM products WHERE name = %s", (name,))
        result = pg_cur.fetchone()

        if result:
            pg_cnxn.close()
            return {"id": result[0], "name": result[1], "found": True}

        pg_cur.execute("SELECT id, name FROM products WHERE LOWER(name) = LOWER(%s)", (name,))
        result = pg_cur.fetchone()

        if result:
            pg_cnxn.close()
            return {"id": result[0], "name": result[1], "found": True}

        pg_cur.execute("SELECT id, name FROM products WHERE LOWER(name) LIKE LOWER(%s)", (f"%{name}%",))
        result = pg_cur.fetchone()

        if result:
            pg_cnxn.close()
            return {"id": result[0], "name": result[1], "found": True}

        pg_cnxn.close()
        return {"found": False, "error": f"Product '{name}' not found"}

    except Exception as e:
        return {"found": False, "error": f"Database error: {str(e)}"}


@mcp.tool()
async def sqlserver_crud(
        operation: str,
        name: str = None,
        email: str = None,
        limit: int = 10,
        customer_id: int = None,
        new_email: str = None,
        table_name: str = None,
) -> Any:
    cnxn = get_mysql_conn()
    cur = cnxn.cursor()

    if operation == "create":
        if not name or not email:
            cnxn.close()
            return {"sql": None, "result": "❌ 'name' and 'email' required for create."}

        search_name = name.strip()

        cur.execute("""
            SELECT Id, Name, Email FROM Customers
            WHERE LOWER(Name) = LOWER(%s)
               OR LOWER(FirstName) = LOWER(%s)
               OR LOWER(Name) LIKE LOWER(%s)
        """, (search_name, search_name, f"%{search_name}%"))

        existing_customers = cur.fetchall()

        if existing_customers:
            customers_without_email = [c for c in existing_customers if not c[2]]
            customers_with_email = [c for c in existing_customers if c[2]]

            if len(existing_customers) == 1:
                existing_customer = existing_customers[0]
                if existing_customer[2]:
                    cnxn.close()
                    return {"sql": None,
                            "result": f"ℹ️ Customer '{existing_customer[1]}' already has email '{existing_customer[2]}'. If you want to update it, please specify the full name."}
                else:
                    sql_query = "UPDATE Customers SET Email = %s WHERE Id = %s"
                    cur.execute(sql_query, (email, existing_customer[0]))
                    cnxn.commit()
                    cnxn.close()
                    return {"sql": sql_query,
                            "result": f"✅ Email '{email}' added to existing customer '{existing_customer[1]}'."}

            elif len(existing_customers) > 1:
                customer_list = []
                for c in existing_customers:
                    email_status = f"(has email: {c[2]})" if c[2] else "(no email)"
                    customer_list.append(f"- {c[1]} {email_status}")

                customer_details = "\n".join(customer_list)
                cnxn.close()
                return {"sql": None,
                        "result": f"❓ Multiple customers found with name '{search_name}':\n{customer_details}\n\nPlease specify the full name (first and last name) to identify which customer you want to add the email to, or use a different name if you want to create a new customer."}

        name_parts = name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        sql_query = "INSERT INTO Customers (FirstName, LastName, Name, Email) VALUES (%s, %s, %s, %s)"
        cur.execute(sql_query, (first_name, last_name, name, email))
        cnxn.commit()
        cnxn.close()
        return {"sql": sql_query, "result": f"✅ New customer '{name}' created with email '{email}'."}

    elif operation == "read":
        if name:
            sql_query = """
                        SELECT Id, FirstName, LastName, Name, Email, CreatedAt
                        FROM Customers
                        WHERE LOWER(Name) LIKE LOWER(%s)
                           OR LOWER(FirstName) LIKE LOWER(%s)
                           OR LOWER(LastName) LIKE LOWER(%s)
                        ORDER BY Id ASC
                        LIMIT %s
                        """
            cur.execute(sql_query, (f"%{name}%", f"%{name}%", f"%{name}%", limit))
        else:
            sql_query = """
                        SELECT Id, FirstName, LastName, Name, Email, CreatedAt
                        FROM Customers
                        ORDER BY Id ASC
                        LIMIT %s
                        """
            cur.execute(sql_query, (limit,))

        rows = cur.fetchall()
        result = [
            {
                "Id": r[0],
                "FirstName": r[1],
                "LastName": r[2],
                "Name": r[3],
                "Email": r[4],
                "CreatedAt": r[5].isoformat()
            }
            for r in rows
        ]
        cnxn.close()
        return {"sql": sql_query, "result": result}

    elif operation == "update":
        customer_name = None

        if not customer_id and name:
            try:
                customer_info = find_customer_by_name_enhanced(name)
                if not customer_info["found"]:
                    cnxn.close()
                    return {"sql": None, "result": f"❌ {customer_info['error']}"}
                customer_id = customer_info["customer_id"]
                customer_name = customer_info["customer_name"]
            except Exception as search_error:
                cur.execute("""
                    SELECT Id, Name FROM Customers
                    WHERE LOWER(Name) = LOWER(%s)
                       OR LOWER(FirstName) = LOWER(%s)
                       OR LOWER(LastName) = LOWER(%s)
                    LIMIT 1
                """, (name, name, name))
                result = cur.fetchone()

                if result:
                    customer_id = result[0]
                    customer_name = result[1]
                else:
                    cnxn.close()
                    return {"sql": None, "result": f"❌ Customer '{name}' not found"}

        if not customer_id or not new_email:
            cnxn.close()
            return {"sql": None, "result": "❌ 'customer_id' (or 'name') and 'new_email' required for update."}

        cur.execute("SELECT Name, Email FROM Customers WHERE Id = %s", (customer_id,))
        existing_customer = cur.fetchone()

        if not existing_customer:
            cnxn.close()
            return {"sql": None, "result": f"❌ Customer with ID {customer_id} not found."}

        if not customer_name:
            customer_name = existing_customer[0]

        if existing_customer[1] == new_email:
            cnxn.close()
            return {"sql": None, "result": f"ℹ️ Customer '{customer_name}' already has email '{new_email}'."}

        sql_query = "UPDATE Customers SET Email = %s WHERE Id = %s"
        cur.execute(sql_query, (new_email, customer_id))
        cnxn.commit()
        cnxn.close()
        return {"sql": sql_query, "result": f"✅ Customer '{customer_name}' email updated to '{new_email}'."}

    elif operation == "delete":
        customer_name = None

        if not customer_id and name:
            try:
                customer_info = find_customer_by_name_enhanced(name)
                if not customer_info["found"]:
                    cnxn.close()
                    return {"sql": None, "result": f"❌ {customer_info['error']}"}
                customer_id = customer_info["customer_id"]
                customer_name = customer_info["customer_name"]
            except Exception as search_error:
                cur.execute("""
                    SELECT Id, Name FROM Customers
                    WHERE LOWER(Name) = LOWER(%s)
                       OR LOWER(FirstName) = LOWER(%s)
                       OR LOWER(LastName) = LOWER(%s)
                    LIMIT 1
                """, (name, name, name))
                result = cur.fetchone()

                if result:
                    customer_id = result[0]
                    customer_name = result[1]
                else:
                    cnxn.close()
                    return {"sql": None, "result": f"❌ Customer '{name}' not found"}
        elif customer_id:
            cur.execute("SELECT Name FROM Customers WHERE Id = %s", (customer_id,))
            result = cur.fetchone()
            customer_name = result[0] if result else f"Customer {customer_id}"
        else:
            cnxn.close()
            return {"sql": None, "result": "❌ 'customer_id' or 'name' required for delete."}

        sql_query = "DELETE FROM Customers WHERE Id = %s"
        cur.execute(sql_query, (customer_id,))
        cnxn.commit()
        cnxn.close()
        return {"sql": sql_query, "result": f"✅ Customer '{customer_name}' deleted."}

    elif operation == "describe":
        table = table_name or "Customers"
        sql_query = f"DESCRIBE {table}"
        cur.execute(sql_query)
        rows = cur.fetchall()
        result = [
            {
                "Field": r[0],
                "Type": r[1],
                "Null": r[2],
                "Key": r[3],
                "Default": r[4],
                "Extra": r[5]
            }
            for r in rows
        ]
        cnxn.close()
        return {"sql": sql_query, "result": result}

    else:
        cnxn.close()
        return {"sql": None, "result": f"❌ Unknown operation '{operation}'."}


@mcp.tool()
async def postgresql_crud(
        operation: str,
        name: str = None,
        price: float = None,
        description: str = None,
        limit: int = 10,
        product_id: int = None,
        new_price: float = None,
        table_name: str = None,
) -> Any:
    cnxn = get_pg_conn()
    cur = cnxn.cursor()

    if operation == "create":
        if not name or price is None:
            cnxn.close()
            return {"sql": None, "result": "❌ 'name' and 'price' required for create."}
        sql_query = "INSERT INTO products (name, price, description) VALUES (%s, %s, %s)"
        cur.execute(sql_query, (name, price, description))
        cnxn.commit()
        result = f"✅ Product '{name}' added with price ${price:.2f}."
        cnxn.close()
        return {"sql": sql_query, "result": result}

    elif operation == "read":
        if name:
            sql_query = """
                        SELECT id, name, price, description
                        FROM products
                        WHERE LOWER(name) LIKE LOWER(%s)
                        ORDER BY id ASC
                        LIMIT %s
                        """
            cur.execute(sql_query, (f"%{name}%", limit))
        else:
            sql_query = """
                        SELECT id, name, price, description
                        FROM products
                        ORDER BY id ASC
                        LIMIT %s
                        """
            cur.execute(sql_query, (limit,))

        rows = cur.fetchall()
        result = [
            {"id": r[0], "name": r[1], "price": float(r[2]), "description": r[3] or ""}
            for r in rows
        ]
        cnxn.close()
        return {"sql": sql_query, "result": result}

    elif operation == "update":
        if not product_id and name:
            product_info = find_product_by_name(name)
            if not product_info["found"]:
                cnxn.close()
                return {"sql": None, "result": f"❌ {product_info['error']}"}
            product_id = product_info["id"]

        if not product_id or new_price is None:
            cnxn.close()
            return {"sql": None, "result": "❌ 'product_id' (or 'name') and 'new_price' required for update."}

        sql_query = "UPDATE products SET price = %s WHERE id = %s"
        cur.execute(sql_query, (new_price, product_id))
        cnxn.commit()

        cur.execute("SELECT name FROM products WHERE id = %s", (product_id,))
        product_name = cur.fetchone()
        product_name = product_name[0] if product_name else f"Product {product_id}"

        cnxn.close()
        return {"sql": sql_query, "result": f"✅ Product '{product_name}' price updated to ${new_price:.2f}."}

    elif operation == "delete":
        if not product_id and name:
            product_info = find_product_by_name(name)
            if not product_info["found"]:
                cnxn.close()
                return {"sql": None, "result": f"❌ {product_info['error']}"}
            product_id = product_info["id"]
            product_name = product_info["name"]
        elif product_id:
            cur.execute("SELECT name FROM products WHERE id = %s", (product_id,))
            result = cur.fetchone()
            product_name = result[0] if result else f"Product {product_id}"
        else:
            cnxn.close()
            return {"sql": None, "result": "❌ 'product_id' or 'name' required for delete."}

        sql_query = "DELETE FROM products WHERE id = %s"
        cur.execute(sql_query, (product_id,))
        cnxn.commit()
        cnxn.close()
        return {"sql": sql_query, "result": f"✅ Product '{product_name}' deleted."}

    elif operation == "describe":
        table = table_name or "products"
        sql_query = f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                    """
        cur.execute(sql_query, (table,))
        rows = cur.fetchall()
        result = [
            {
                "Column": r[0],
                "Type": r[1],
                "Nullable": r[2],
                "Default": r[3]
            }
            for r in rows
        ]
        cnxn.close()
        return {"sql": sql_query, "result": result}

    else:
        cnxn.close()
        return {"sql": None, "result": f"❌ Unknown operation '{operation}'."}


@mcp.tool()
async def sales_crud(
        operation: str,
        customer_id: int = None,
        product_id: int = None,
        quantity: int = 1,
        unit_price: float = None,
        total_amount: float = None,
        sale_id: int = None,
        new_quantity: int = None,
        table_name: str = None,
        display_format: str = None,
        customer_name: str = None,
        product_name: str = None,
        email: str = None,
        total_price: float = None,
        columns: str = None,
        where_clause: str = None,
        filter_conditions: dict = None,
        limit: int = None
) -> Any:
    sales_cnxn = get_mysql_conn()
    sales_cur = sales_cnxn.cursor()

    if operation == "create":
        if not customer_id or not product_id:
            return {"sql": None, "result": "❌ 'customer_id' and 'product_id' required for create."}

        if not validate_customer_exists(customer_id):
            return {"sql": None, "result": f"❌ Customer ID {customer_id} not found."}

        if not validate_product_exists(product_id):
            return {"sql": None, "result": f"❌ Product ID {product_id} not found."}

        if not unit_price:
            product_details = get_product_details(product_id)
            unit_price = product_details["price"]

        if not total_amount:
            total_amount = unit_price * quantity

        if not customer_id and customer_name:
            customer_id = get_customer_id_by_name(customer_name)
            if not customer_id:
                sales_cnxn.close()
                return {"sql": None, "result": f"❌ Customer with name '{customer_name}' not found."}

        if not product_id and product_name:
            product_id = get_product_id_by_name(product_name)
            if not product_id:
                sales_cnxn.close()
                return {"sql": None, "result": f"❌ Product with name '{product_name}' not found."}

        sql_query = """
            INSERT INTO Sales (customer_id, product_id, quantity, unit_price, total_price)
            VALUES (%s, %s, %s, %s, %s)
        """
        sales_cur.execute(sql_query, (customer_id, product_id, quantity, unit_price, total_amount))
        sales_cnxn.commit()

        customer_name = get_customer_name(customer_id)
        product_details = get_product_details(product_id)
        result = f"✅ Sale created: {customer_name} bought {quantity} {product_details['name']}(s) for ${total_amount:.2f}"
        sales_cnxn.close()
        return {"sql": sql_query, "result": result}

    elif operation == "update":
        if not sale_id or new_quantity is None:
            sales_cnxn.close()
            return {"sql": None, "result": "❌ 'sale_id' and 'new_quantity' required for update."}

        sql_query = """
            UPDATE Sales
            SET quantity = %s,
                total_price = unit_price * %s
            WHERE Id = %s
        """
        sales_cur.execute(sql_query, (new_quantity, new_quantity, sale_id))
        sales_cnxn.commit()
        result = f"✅ Sale id={sale_id} updated to quantity {new_quantity}."
        sales_cnxn.close()
        return {"sql": sql_query, "result": result}

    elif operation == "delete":
        if not sale_id:
            sales_cnxn.close()
            return {"sql": None, "result": "❌ 'sale_id' required for delete."}

        sql_query = "DELETE FROM Sales WHERE Id = %s"
        sales_cur.execute(sql_query, (sale_id,))
        sales_cnxn.commit()
        result = f"✅ Sale id={sale_id} deleted."
        sales_cnxn.close()
        return {"sql": sql_query, "result": result}

    elif operation == "read":
        mysql_cnxn = get_mysql_conn()
        mysql_cur = mysql_cnxn.cursor()

        available_columns = {
            "sale_id": "s.Id",
            "first_name": "c.FirstName",
            "last_name": "c.LastName",
            "customer_name": "c.Name",
            "product_name": "p.name",
            "product_description": "p.description",
            "quantity": "s.quantity",
            "unit_price": "s.unit_price",
            "total_price": "s.total_price",
            "amount": "s.total_price",
            "sale_date": "s.sale_date",
            "date": "s.sale_date",
            "customer_email": "c.Email",
            "email": "c.Email"
        }

        selected_columns = []
        column_aliases = []

        if columns and columns.strip():
            columns_clean = columns.strip()

            if "," in columns_clean:
                requested_cols = [col.strip().lower().replace(" ", "_") for col in columns_clean.split(",") if
                                  col.strip()]
            else:
                requested_cols = [col.strip().lower().replace(" ", "_") for col in columns_clean.split() if col.strip()]

            for col in requested_cols:
                matched = False
                if col in available_columns:
                    selected_columns.append(available_columns[col])
                    column_aliases.append(col)
                    matched = True
                else:
                    for avail_col, db_col in available_columns.items():
                        if (col in avail_col or avail_col in col or
                                col.replace("_", "") in avail_col.replace("_", "") or
                                avail_col.replace("_", "") in col.replace("_", "")):
                            selected_columns.append(db_col)
                            column_aliases.append(avail_col)
                            matched = True
                            break

        if not selected_columns:
            selected_columns = [
                "s.Id", "c.Name", "p.name", "s.quantity", "s.unit_price", "s.total_price", "s.sale_date", "c.Email"
            ]
            column_aliases = [
                "sale_id", "customer_name", "product_name", "quantity", "unit_price", "total_price", "sale_date",
                "email"
            ]

        select_clause = ", ".join([f"{col} AS {alias}" for col, alias in zip(selected_columns, column_aliases)])

        base_sql = f"""
        SELECT  {select_clause}
        FROM    Sales          s
        JOIN    Customers      c ON c.Id = s.customer_id
        JOIN    ProductsCache  p ON p.id = s.product_id
        """

        where_sql = ""
        query_params = []

        if where_clause and where_clause.strip():
            import re
            clause = where_clause.strip().lower()
            where_conditions = []

            price_patterns = [
                r'total[_\s]*price[_\s]*(>|>=|exceed[s]?|above|greater\s+than|more\s+than)\s*\$?(\d+(?:\.\d+)?)',
                r'(>|>=|exceed[s]?|above|greater\s+than|more\s+than)\s*\$?(\d+(?:\.\d+)?)\s*total[_\s]*price',
                r'total[_\s]*price[_\s]*(<|<=|below|less\s+than|under)\s*\$?(\d+(?:\.\d+)?)',
                r'total[_\s]*price[_\s]*(=|equals?|is)\s*\$?(\d+(?:\.\d+)?)'
            ]

            for pattern in price_patterns:
                match = re.search(pattern, clause)
                if match:
                    if len(match.groups()) == 2:
                        operator_text, value = match.groups()
                        if any(word in operator_text for word in ['exceed', 'above', 'greater', 'more', '>']):
                            operator = '>'
                        elif any(word in operator_text for word in ['below', 'less', 'under', '<']):
                            operator = '<'
                        elif any(word in operator_text for word in ['equal', 'is', '=']):
                            operator = '='
                        else:
                            operator = '>'

                        where_conditions.append(f"s.total_price {operator} %s")
                        query_params.append(float(value))
                        break

            quantity_patterns = [
                r'quantity[_\s]*(>|>=|greater\s+than|more\s+than|above)\s*(\d+)',
                r'quantity[_\s]*(<|<=|less\s+than|below|under)\s*(\d+)',
                r'quantity[_\s]*(=|equals?|is)\s*(\d+)'
            ]

            for pattern in quantity_patterns:
                match = re.search(pattern, clause)
                if match:
                    operator_text, value = match.groups()
                    if any(symbol in operator_text for symbol in ['>', 'greater', 'more', 'above']):
                        operator = '>'
                    elif any(symbol in operator_text for symbol in ['<', 'less', 'below', 'under']):
                        operator = '<'
                    else:
                        operator = '='

                    where_conditions.append(f"s.quantity {operator} %s")
                    query_params.append(int(value))
                    break

            customer_patterns = [
                r'customer[_\s]*name[_\s]*like[_\s]*["\']([^"\']+)["\']',
                r'customer[_\s]*name[_\s]*=[_\s]*["\']([^"\']+)["\']',
                r'customer[_\s]*=[_\s]*["\']([^"\']+)["\']',
                r'customer[_\s]*name[_\s]*([a-zA-Z\s]+?)(?:\s|$)'
            ]

            for pattern in customer_patterns:
                match = re.search(pattern, clause)
                if match:
                    name_value = match.group(1).strip()
                    if 'like' in clause:
                        where_conditions.append("c.Name LIKE %s")
                        query_params.append(f"%{name_value}%")
                    else:
                        where_conditions.append("c.Name = %s")
                        query_params.append(name_value)
                    break

            product_patterns = [
                r'product[_\s]*name[_\s]*like[_\s]*["\']([^"\']+)["\']',
                r'product[_\s]*name[_\s]*=[_\s]*["\']([^"\']+)["\']',
                r'product[_\s]*=[_\s]*["\']([^"\']+)["\']'
            ]

            for pattern in product_patterns:
                match = re.search(pattern, clause)
                if match:
                    product_value = match.group(1).strip()
                    if 'like' in clause:
                        where_conditions.append("p.name LIKE %s")
                        query_params.append(f"%{product_value}%")
                    else:
                        where_conditions.append("p.name = %s")
                        query_params.append(product_value)
                    break

            if not where_conditions:
                number_match = re.search(r'\$?(\d+(?:\.\d+)?)', clause)
                if number_match:
                    value = float(number_match.group(1))
                    if any(word in clause for word in ['exceed', 'above', 'greater', 'more']):
                        where_conditions.append("s.total_price > %s")
                    elif any(word in clause for word in ['below', 'less', 'under']):
                        where_conditions.append("s.total_price < %s")
                    else:
                        where_conditions.append("s.total_price > %s")

                    query_params.append(value)

            if where_conditions:
                where_sql = " WHERE " + " AND ".join(where_conditions)

        elif filter_conditions:
            where_conditions = []
            for field, value in filter_conditions.items():
                if field in available_columns:
                    db_field = available_columns[field]
                    if isinstance(value, str):
                        where_conditions.append(f"{db_field} LIKE %s")
                        query_params.append(f"%{value}%")
                    else:
                        where_conditions.append(f"{db_field} = %s")
                        query_params.append(value)

            if where_conditions:
                where_sql = " WHERE " + " AND ".join(where_conditions)

        order_sql = " ORDER BY s.sale_date DESC"
        limit_sql = ""
        if limit:
            limit_sql = f" LIMIT {limit}"

        sql = base_sql + where_sql + order_sql + limit_sql

        try:
            if query_params:
                mysql_cur.execute(sql, query_params)
            else:
                mysql_cur.execute(sql)

            rows = mysql_cur.fetchall()
        except Exception as e:
            mysql_cnxn.close()
            return {"sql": sql, "result": f"❌ SQL Error: {str(e)}"}

        mysql_cnxn.close()

        processed_results = []
        for r in rows:
            row_data = {}
            for i, alias in enumerate(column_aliases):
                if i < len(r):
                    value = r[i]

                    if display_format == "Data Format Conversion":
                        if "date" in alias or "timestamp" in alias:
                            value = value.strftime("%Y-%m-%d %H:%M:%S") if value else "N/A"
                    elif display_format == "Decimal Value Formatting":
                        if "price" in alias or "total" in alias or "amount" in alias:
                            value = f"{float(value):.2f}" if value is not None else "0.00"
                    elif display_format == "Null Value Removal/Handling":
                        if value is None:
                            value = "N/A"

                    row_data[alias] = value

            if display_format == "String Concatenation":
                if "customer_name" in row_data or ("first_name" in row_data and "last_name" in row_data):
                    if "first_name" in row_data and "last_name" in row_data:
                        row_data["customer_full_name"] = f"{row_data['first_name']} {row_data['last_name']}"

                if "product_name" in row_data and "product_description" in row_data:
                    desc = row_data['product_description'] or 'No description'
                    row_data["product_full_description"] = f"{row_data['product_name']} ({desc})"

                if all(field in row_data for field in ['customer_name', 'quantity', 'product_name', 'total_price']):
                    row_data["sale_summary"] = (
                        f"{row_data['customer_name']} bought {row_data['quantity']} "
                        f"of {row_data['product_name']} for ${float(row_data['total_price']):.2f}"
                    )

            if display_format == "Null Value Removal/Handling":
                if any(v is None for v in row_data.values()):
                    continue

            processed_results.append(row_data)

        return {"sql": sql, "result": processed_results}

    else:
        return {"sql": None, "result": f"❌ Unknown operation '{operation}'."}


@mcp.tool()
async def careplan_crud(
        operation: str,
        columns: str = None,
        where_clause: str = None,
        limit: int = None,
        care_plan_type: str = None,
        status: str = None
) -> Any:
    if operation != "read":
        return {"sql": None, "result": "❌ Only 'read' operation is supported for care plans."}

    conn = get_mysql_conn()
    cur = conn.cursor()

    available_columns = {
        "id": "ID",
        "actual_release_date": "ActualReleaseDate",
        "name_of_youth": "NameOfYouth",
        "race_ethnicity": "RaceEthnicity",
        "medi_cal_id": "MediCalID",
        "residential_address": "ResidentialAddress",
        "telephone": "Telephone",
        "medi_cal_health_plan": "MediCalHealthPlan",
        "health_screenings": "HealthScreenings",
        "health_assessments": "HealthAssessments",
        "chronic_conditions": "ChronicConditions",
        "prescribed_medications": "PrescribedMedications",
        "notes": "Notes",
        "careplan_notes": "CarePlanNotes",
        "created_at": "CreatedAt",
        "updated_at": "UpdatedAt"
    }

    selected_columns = []
    column_aliases = []

    if columns and columns.strip():
        raw_cols = columns.strip().lower()
        if raw_cols.startswith("*"):
            selected_columns = list(available_columns.values())
            column_aliases = list(available_columns.keys())

            exclusions = [col.strip().replace("-", "").replace(" ", "_")
                          for col in raw_cols.split(",") if col.startswith("-")]
            selected_columns, column_aliases = zip(*[
                (col_db, col_alias)
                for col_alias, col_db in available_columns.items()
                if col_alias not in exclusions
            ])
        else:
            requested = [c.strip().lower().replace(" ", "_") for c in raw_cols.split(",")]
            for col in requested:
                if col in available_columns:
                    selected_columns.append(available_columns[col])
                    column_aliases.append(col)
                else:
                    for avail_col, db_col in available_columns.items():
                        if (col in avail_col or avail_col in col or
                                col.replace("_", "") in avail_col.replace("_", "") or
                                avail_col.replace("_", "") in col.replace("_", "")):
                            selected_columns.append(db_col)
                            column_aliases.append(avail_col)
                            break
    else:
        selected_columns = [
            "ID", "NameOfYouth", "RaceEthnicity", "MediCalID", "ChronicConditions",
            "PrescribedMedications", "CarePlanNotes"
        ]
        column_aliases = [
            "id", "name_of_youth", "race_ethnicity", "medi_cal_id", "chronic_conditions",
            "prescribed_medications", "careplan_notes"
        ]

    select_clause = ", ".join([f"{db_col} AS {alias}" for db_col, alias in zip(selected_columns, column_aliases)])
    sql = f"SELECT {select_clause} FROM CarePlan WHERE 1=1"
    query_params = []

    if where_clause and where_clause.strip():
        # Map the column names in the where_clause to the actual column names in the database
        for col_alias, db_col in available_columns.items():
            where_clause = where_clause.replace(col_alias, db_col)
        sql += f" AND {where_clause}"

    if limit:
        sql += f" LIMIT {limit}"

    try:
        cur.execute(sql, query_params)
        rows = cur.fetchall()
    except Exception as e:
        conn.close()
        return {"sql": sql, "result": f"❌ SQL Error: {str(e)}"}

    conn.close()

    results = []
    for row in rows:
        row_dict = {}
        for i, alias in enumerate(column_aliases):
            if i < len(row):
                value = row[i]
                if alias in ["actual_release_date", "created_at", "updated_at"] and value:
                    value = value.isoformat()
                row_dict[alias] = value
        results.append(row_dict)

    return {"sql": sql, "result": results}

@mcp.tool()
async def calllogs_crud(
        operation: str,
        analysis_type: str = None,
        date_range: str = None,
        agent_name: str = None,
        issue_category: str = None,
        sentiment_threshold: float = None,
        columns: str = None,
        where_clause: str = None,
        limit: int = 50,
        search_text: str = None,
        keyword_analysis: bool = False,
        include_transcripts: bool = True
) -> Any:
    conn = get_mysql_conn()
    cur = conn.cursor()

    if operation == "read":
        available_columns = {
            "log_id": "cl.LogID",
            "call_date": "cl.CallDate",
            "customer_id": "cl.CustomerID",
            "customer_name": "c.Name",
            "agent_name": "cl.AgentName",
            "call_duration": "cl.CallDuration",
            "call_type": "cl.CallType",
            "call_status": "cl.CallStatus",
            "issue_category": "cl.IssueCategory",
            "resolution_status": "cl.ResolutionStatus",
            "sentiment_score": "cl.SentimentScore",
            "call_notes": "cl.CallNotes",
            "call_transcript": "cl.CallTranscript",
            "wait_time": "cl.WaitTime",
            "transfer_count": "cl.TransferCount"
        }

        selected_columns = []
        column_aliases = []

        if columns and columns.strip():
            columns_clean = columns.strip().lower()

            if columns_clean.startswith("*"):
                if include_transcripts:
                    selected_columns = list(available_columns.values())
                    column_aliases = list(available_columns.keys())
                else:
                    selected_columns = [col for col in available_columns.values() if "CallTranscript" not in col]
                    column_aliases = [alias for alias in available_columns.keys() if alias != "call_transcript"]

                exclusions = [col.strip().replace("-", "").replace(" ", "_").lower()
                              for col in columns_clean.split(",") if col.startswith("-")]

                if exclusions:
                    filtered = [(alias, col) for alias, col in available_columns.items()
                                if alias not in exclusions and (include_transcripts or alias != "call_transcript")]
                    if filtered:
                        column_aliases, selected_columns = zip(*filtered)
                        column_aliases = list(column_aliases)
                        selected_columns = list(selected_columns)
            else:
                requested_cols = [col.strip().lower().replace(" ", "_")
                                  for col in columns_clean.split(",") if col.strip()]

                for col in requested_cols:
                    if col in available_columns:
                        selected_columns.append(available_columns[col])
                        column_aliases.append(col)

        if not selected_columns:
            if include_transcripts:
                selected_columns = list(available_columns.values())
                column_aliases = list(available_columns.keys())
            else:
                selected_columns = [col for col in available_columns.values() if "CallTranscript" not in col]
                column_aliases = [alias for alias in available_columns.keys() if alias != "call_transcript"]

        select_clause = ", ".join([f"{col} AS {alias}"
                                   for col, alias in zip(selected_columns, column_aliases)])

        sql = f"""
            SELECT {select_clause}
            FROM CallLogs cl
            LEFT JOIN Customers c ON cl.CustomerID = c.Id
            WHERE 1=1
        """
        params = []

        if agent_name:
            sql += " AND cl.AgentName = %s"
            params.append(agent_name)

        if issue_category:
            sql += " AND cl.IssueCategory = %s"
            params.append(issue_category)

        if sentiment_threshold is not None:
            sql += " AND cl.SentimentScore >= %s"
            params.append(sentiment_threshold)

        if search_text:
            sql += " AND MATCH(cl.CallTranscript) AGAINST(%s IN NATURAL LANGUAGE MODE)"
            params.append(search_text)

        if where_clause and where_clause.strip():
            sql += f" AND {where_clause}"

        sql += " ORDER BY cl.CallDate DESC LIMIT %s"
        params.append(limit)

        cur.execute(sql, params)
        rows = cur.fetchall()

        result = []
        for r in rows:
            row_dict = {}
            for i, alias in enumerate(column_aliases):
                if i < len(r):
                    value = r[i]
                    if alias == "call_date" and value:
                        value = value.isoformat()
                    elif alias == "sentiment_score" and value is not None:
                        value = float(value)
                    row_dict[alias] = value
            result.append(row_dict)

        conn.close()
        return {"sql": sql, "result": result}

    elif operation == "transcript_search":
        sql = """
            SELECT 
                cl.LogID,
                cl.CallDate,
                c.Name as CustomerName,
                cl.AgentName,
                cl.IssueCategory,
                cl.ResolutionStatus,
                cl.CallTranscript,
                cl.SentimentScore,
                MATCH(cl.CallTranscript) AGAINST(%s IN NATURAL LANGUAGE MODE) as RelevanceScore
            FROM CallLogs cl
            LEFT JOIN Customers c ON cl.CustomerID = c.Id
            WHERE MATCH(cl.CallTranscript) AGAINST(%s IN NATURAL LANGUAGE MODE)
            ORDER BY RelevanceScore DESC
            LIMIT %s
        """
        params = [search_text, search_text, limit]
        cur.execute(sql, params)
        rows = cur.fetchall()

        result = []
        for r in rows:
            result.append({
                "LogID": r[0],
                "CallDate": r[1].isoformat() if r[1] else None,
                "CustomerName": r[2],
                "AgentName": r[3],
                "IssueCategory": r[4],
                "ResolutionStatus": r[5],
                "CallTranscript": r[6],
                "SentimentScore": float(r[7]) if r[7] else 0,
                "RelevanceScore": float(r[8]) if r[8] else 0
            })

        conn.close()
        return {"sql": sql, "result": result}

    elif operation == "analyze":
        sql = ""

        if analysis_type == "sentiment_by_agent":
            sql = """
                SELECT AgentName,
                       AVG(SentimentScore) as AvgSentiment,
                       COUNT(*) as TotalCalls,
                       SUM(CASE WHEN SentimentScore >= 0.5 THEN 1 ELSE 0 END) as PositiveCalls
                FROM CallLogs
                GROUP BY AgentName
                ORDER BY AvgSentiment DESC
            """
            cur.execute(sql)
            rows = cur.fetchall()
            result = [{"AgentName": r[0], "AvgSentiment": float(r[1]),
                       "TotalCalls": r[2], "PositiveCalls": r[3]} for r in rows]

        elif analysis_type == "agent_performance":
            sql = """
                SELECT AgentName,
                       COUNT(*) as TotalCalls,
                       AVG(CallDuration) as AvgCallDuration,
                       AVG(SentimentScore) as AvgSentiment,
                       SUM(CASE WHEN ResolutionStatus = 'resolved' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as ResolutionRate,
                       AVG(TransferCount) as AvgTransfers
                FROM CallLogs
                GROUP BY AgentName
                ORDER BY ResolutionRate DESC
            """
            cur.execute(sql)
            rows = cur.fetchall()
            result = [{"AgentName": r[0], "TotalCalls": r[1],
                       "AvgCallDuration": r[2], "AvgSentiment": float(r[3]),
                       "ResolutionRate": float(r[4]), "AvgTransfers": float(r[5])} for r in rows]

        elif analysis_type == "transcript_keywords":
            sql = """
                SELECT 
                    IssueCategory,
                    COUNT(*) as CallCount,
                    GROUP_CONCAT(CallTranscript SEPARATOR ' ') as CombinedTranscripts
                FROM CallLogs
                GROUP BY IssueCategory
            """
            cur.execute(sql)
            rows = cur.fetchall()

            result = []
            for r in rows:
                issue_cat = r[0]
                call_count = r[1]
                transcripts = r[2] if r[2] else ""

                words = transcripts.lower().split()
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                              'of', 'with', 'by', 'from', 'was', 'were', 'been', 'be', 'have',
                              'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                              'is', 'are', 'am', 'customer', 'agent', 'call', 'called'}

                filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
                word_freq = {}
                for word in filtered_words:
                    word_freq[word] = word_freq.get(word, 0) + 1

                top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]

                result.append({
                    "IssueCategory": issue_cat,
                    "CallCount": call_count,
                    "TopKeywords": [{"keyword": k, "frequency": v} for k, v in top_keywords]
                })

        elif analysis_type == "transcript_sentiment":
            sql = """
                SELECT 
                    IssueCategory,
                    AVG(SentimentScore) as AvgSentiment,
                    COUNT(CASE WHEN CallTranscript LIKE '%frustrated%' 
                           OR CallTranscript LIKE '%angry%' 
                           OR CallTranscript LIKE '%upset%' THEN 1 END) as NegativeLanguageCount,
                    COUNT(CASE WHEN CallTranscript LIKE '%satisfied%' 
                           OR CallTranscript LIKE '%happy%' 
                           OR CallTranscript LIKE '%grateful%' 
                           OR CallTranscript LIKE '%appreciated%' THEN 1 END) as PositiveLanguageCount,
                    COUNT(*) as TotalCalls
                FROM CallLogs
                GROUP BY IssueCategory
            """
            cur.execute(sql)
            rows = cur.fetchall()
            result = [{
                "IssueCategory": r[0],
                "AvgSentiment": float(r[1]) if r[1] else 0,
                "NegativeLanguageCount": r[2],
                "PositiveLanguageCount": r[3],
                "TotalCalls": r[4],
                "PositiveLanguageRate": round((r[3] / r[4]) * 100, 2) if r[4] > 0 else 0,
                "NegativeLanguageRate": round((r[2] / r[4]) * 100, 2) if r[4] > 0 else 0
            } for r in rows]

        elif analysis_type == "agent_communication":
            sql = """
                SELECT 
                    AgentName,
                    COUNT(*) as TotalCalls,
                    AVG(LENGTH(CallTranscript)) as AvgTranscriptLength,
                    COUNT(CASE WHEN CallTranscript LIKE '%apologized%' 
                           OR CallTranscript LIKE '%sorry%' THEN 1 END) as ApologyCount,
                    COUNT(CASE WHEN CallTranscript LIKE '%solution%' 
                           OR CallTranscript LIKE '%resolved%' 
                           OR CallTranscript LIKE '%fixed%' THEN 1 END) as SolutionOrientedCount,
                    COUNT(CASE WHEN CallTranscript LIKE '%escalat%' THEN 1 END) as EscalationMentions,
                    AVG(CallDuration) as AvgDuration
                FROM CallLogs
                GROUP BY AgentName
                ORDER BY TotalCalls DESC
            """
            cur.execute(sql)
            rows = cur.fetchall()
            result = [{
                "AgentName": r[0],
                "TotalCalls": r[1],
                "AvgTranscriptLength": round(r[2]) if r[2] else 0,
                "ApologyRate": round((r[3] / r[1]) * 100, 2) if r[1] > 0 else 0,
                "SolutionOrientedRate": round((r[4] / r[1]) * 100, 2) if r[1] > 0 else 0,
                "EscalationRate": round((r[5] / r[1]) * 100, 2) if r[1] > 0 else 0,
                "AvgDuration": r[6]
            } for r in rows]

        elif analysis_type == "problem_patterns":
            sql = """
                SELECT 
                    IssueCategory,
                    ResolutionStatus,
                    COUNT(*) as Frequency,
                    GROUP_CONCAT(
                        CASE 
                            WHEN CallTranscript LIKE '%recurring%' OR CallTranscript LIKE '%again%' 
                                 OR CallTranscript LIKE '%multiple%' OR CallTranscript LIKE '%repeated%'
                            THEN LogID 
                        END
                    ) as RecurringIssueLogIDs,
                    AVG(SentimentScore) as AvgSentiment
                FROM CallLogs
                GROUP BY IssueCategory, ResolutionStatus
                HAVING Frequency > 5
                ORDER BY Frequency DESC
            """
            cur.execute(sql)
            rows = cur.fetchall()
            result = []
            for r in rows:
                recurring_ids = [id for id in str(r[3]).split(',') if id and id != 'None'] if r[3] else []
                result.append({
                    "IssueCategory": r[0],
                    "ResolutionStatus": r[1],
                    "Frequency": r[2],
                    "RecurringIssueCount": len(recurring_ids),
                    "RecurringIssueRate": round((len(recurring_ids) / r[2]) * 100, 2) if r[2] > 0 else 0,
                    "AvgSentiment": float(r[4]) if r[4] else 0
                })

        elif analysis_type == "issue_frequency":
            sql = """
                SELECT IssueCategory,
                       COUNT(*) as Frequency,
                       AVG(CallDuration) as AvgDuration,
                       SUM(CASE WHEN ResolutionStatus = 'resolved' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as ResolutionRate
                FROM CallLogs
                GROUP BY IssueCategory
                ORDER BY Frequency DESC
            """
            cur.execute(sql)
            rows = cur.fetchall()
            result = [{"IssueCategory": r[0], "Frequency": r[1],
                       "AvgDuration": r[2], "ResolutionRate": float(r[3])} for r in rows]

        elif analysis_type == "call_volume_trends":
            sql = """
                SELECT DATE(CallDate) as Date,
                       COUNT(*) as CallCount,
                       AVG(WaitTime) as AvgWaitTime,
                       AVG(CallDuration) as AvgDuration
                FROM CallLogs
                GROUP BY DATE(CallDate)
                ORDER BY Date DESC
                LIMIT 30
            """
            cur.execute(sql)
            rows = cur.fetchall()
            result = [{"Date": r[0].isoformat(), "CallCount": r[1],
                       "AvgWaitTime": r[2], "AvgDuration": r[3]} for r in rows]

        elif analysis_type == "escalation_analysis":
            sql = """
                SELECT IssueCategory,
                       COUNT(*) as TotalCalls,
                       SUM(CASE WHEN ResolutionStatus = 'escalated' THEN 1 ELSE 0 END) as EscalatedCalls,
                       SUM(CASE WHEN ResolutionStatus = 'escalated' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as EscalationRate
                FROM CallLogs
                GROUP BY IssueCategory
                HAVING EscalationRate > 0
                ORDER BY EscalationRate DESC
            """
            cur.execute(sql)
            rows = cur.fetchall()
            result = [{"IssueCategory": r[0], "TotalCalls": r[1],
                       "EscalatedCalls": r[2], "EscalationRate": float(r[3])} for r in rows]

        else:
            result = """Unknown analysis type. Available types: 
                     sentiment_by_agent, issue_frequency, call_volume_trends, 
                     escalation_analysis, agent_performance, transcript_keywords,
                     transcript_sentiment, agent_communication, problem_patterns"""

        conn.close()
        return {"sql": sql if analysis_type != None else None, "result": result}

    else:
        conn.close()
        return {"sql": "", "result": f"Unknown operation '{operation}'."}


if __name__ == "__main__":
    seed_databases()
    import os

    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)


