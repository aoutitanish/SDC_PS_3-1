"""
SQLite Database Layer for KrishiMitra AI.
Stores chat sessions, message history, and user farm profiles.
"""

import sqlite3
import json
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "krishimitra.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Chat Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            language TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            sender TEXT,
            content TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
        )
    """)

    # Farm Profile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farm_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'guest',
            farm_name TEXT,
            state TEXT,
            district TEXT,
            soil_type TEXT,
            farm_size_acres REAL,
            irrigation_type TEXT,
            primary_crops TEXT,
            preferred_language TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Market Price Cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_price_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state TEXT,
            district TEXT,
            mandi_name TEXT,
            commodity_name TEXT,
            min_price REAL,
            max_price REAL,
            modal_price REAL,
            price_unit TEXT DEFAULT 'INR/quintal',
            arrival_date TEXT,
            data_source TEXT,
            data_type TEXT,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(state, district, mandi_name, commodity_name, arrival_date)
        )
    """)

    # Crop Economic Benchmarks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crop_economic_benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT UNIQUE,
            commodity_aliases TEXT,
            msp_price REAL,
            msp_unit TEXT,
            msp_year TEXT,
            cost_of_cultivation_per_acre REAL,
            cost_unit TEXT,
            cost_year TEXT,
            source TEXT,
            data_type TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")


# Initialize on import
init_db()
