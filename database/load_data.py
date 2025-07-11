# database/load_data.py
import sqlite3
import pandas as pd
import os

def initialize_database():
    db_path = os.path.join(os.path.dirname(__file__), "Dashboard.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS group_performance (
        sqapp_fiscal_period_cd INTEGER,
        parentgroupno TEXT PRIMARY KEY,
        parentgroupname TEXT,
        grp_marketing_tier TEXT,
        region TEXT,
        province TEXT,
        top3Q TEXT,
        grp_segment TEXT,
        product TEXT,
        subproduct TEXT,
        bol_eligibility TEXT,
        incoming_channel TEXT,
        closing_channel TEXT,
        nb_quote INTEGER,
        nb_nwb INTEGER,
        nb_ren INTEGER,
        nb_can INTEGER,
        nb_end INTEGER,
        prime_nwb REAL,
        prime_ren REAL,
        prime_can REAL,
        prime_end REAL,
        total_wp REAL,
        start_date TEXT,
        group_age REAL,
        nb_eligibles INTEGER,
        inforce_clients INTEGER,
        zones TEXT,
        nb_policies TEXT
    );
    """)

    # Load CSV into the table
    base_path = os.path.dirname(__file__)
    data_df = pd.read_csv(os.path.join(base_path, "data.csv"))

    print("[INFO] Preview of data.csv:")
    print(data_df.head())

    data_df.to_sql("group_performance", conn, if_exists="replace", index=False)

    print("[INFO] Preview of lines in the DB:")
    df = pd.read_sql("SELECT COUNT(*) FROM group_performance", conn)
    print(df)

    print("[INFO] Database loaded and table populated.")
    conn.commit()
    conn.close()
