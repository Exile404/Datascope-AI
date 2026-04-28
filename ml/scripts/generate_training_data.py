"""
DataScope AI — Training Data Generator
Generates (CSV profile → thinking → insight) training pairs in .toon format.

Usage:
    python generate_training_data.py --num_examples 3000
    python generate_training_data.py --num_examples 5 --preview 2
"""

import json
import random
import argparse
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

SEED = 42
random.seed(SEED)
np.random.seed(SEED)


# ── Domain Templates ─────────────────────────────────────────────
# Each domain generates realistic synthetic data with specific
# statistical properties (skewness, bimodality, outliers, etc.)

def _safe_array(arr, n):
    """Ensure array is exactly length n."""
    arr = np.asarray(arr).flatten()
    if len(arr) >= n:
        return arr[:n]
    return np.resize(arr, n)


DOMAIN_TEMPLATES = [
    {
        "name": "E-Commerce Customer Analytics",
        "description": "Customer behavior data from an online retail platform",
        "rows_range": (500, 5000),
        "columns": [
            {"name": "customer_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "age", "type": "numeric",
             "gen": lambda n: np.clip(np.random.normal(35, 12, n), 18, 80).astype(int),
             "missing": 0.02},
            {"name": "annual_income", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(10.8, 0.5, n), -2),
             "missing": 0.05},
            {"name": "spending_score", "type": "numeric",
             "gen": lambda n: np.random.randint(1, 101, n), "missing": 0.01},
            {"name": "tenure_months", "type": "numeric",
             "gen": lambda n: np.clip(np.random.exponential(18, n), 0, 120).astype(int),
             "missing": 0.0},
            {"name": "segment", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Budget", "Standard", "Premium", "Enterprise"], n,
                 p=[0.35, 0.40, 0.15, 0.10]), "missing": 0.0},
            {"name": "region", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["North", "South", "East", "West", "Central"], n), "missing": 0.03},
            {"name": "churn_risk", "type": "numeric",
             "gen": lambda n: np.round(np.random.beta(2, 5, n), 3), "missing": 0.0},
        ],
    },
    {
        "name": "Patient Health Records",
        "description": "Clinical measurements from a hospital outpatient department",
        "rows_range": (200, 3000),
        "columns": [
            {"name": "patient_id", "type": "numeric",
             "gen": lambda n: np.arange(1001, 1001 + n), "missing": 0.0},
            {"name": "age", "type": "numeric",
             "gen": lambda n: _safe_array(np.concatenate([
                 np.random.normal(8, 3, n // 4).clip(1, 17),
                 np.random.normal(55, 15, n - n // 4).clip(18, 95)
             ]).astype(int), n), "missing": 0.01},
            {"name": "bmi", "type": "numeric",
             "gen": lambda n: np.round(np.random.normal(27.5, 5.5, n).clip(14, 50), 1),
             "missing": 0.08},
            {"name": "blood_pressure_systolic", "type": "numeric",
             "gen": lambda n: np.random.normal(125, 18, n).clip(80, 200).astype(int),
             "missing": 0.04},
            {"name": "blood_glucose", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(4.6, 0.3, n), 1),
             "missing": 0.12},
            {"name": "cholesterol_total", "type": "numeric",
             "gen": lambda n: np.random.normal(200, 40, n).clip(100, 400).astype(int),
             "missing": 0.10},
            {"name": "diagnosis", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Healthy", "Hypertension", "Diabetes", "Obesity", "Cardiac"], n,
                 p=[0.30, 0.25, 0.20, 0.15, 0.10]), "missing": 0.0},
            {"name": "smoker", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Yes", "No", "Former"], n, p=[0.18, 0.60, 0.22]), "missing": 0.05},
        ],
    },
    {
        "name": "Stock Portfolio Transactions",
        "description": "Trading activity and portfolio metrics for retail investors",
        "rows_range": (1000, 8000),
        "columns": [
            {"name": "trade_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "trade_value_usd", "type": "numeric",
             "gen": lambda n: np.round((np.random.pareto(2.5, n) + 1) * 500, 2),
             "missing": 0.01},
            {"name": "daily_return_pct", "type": "numeric",
             "gen": lambda n: np.round(scipy_stats.t.rvs(df=4, loc=0.02, scale=1.8, size=n), 4),
             "missing": 0.0},
            {"name": "volatility_30d", "type": "numeric",
             "gen": lambda n: np.round(np.abs(np.random.normal(0.22, 0.12, n)), 4),
             "missing": 0.03},
            {"name": "portfolio_size", "type": "numeric",
             "gen": lambda n: np.random.lognormal(9.5, 1.2, n).astype(int),
             "missing": 0.0},
            {"name": "sector", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Tech", "Finance", "Healthcare", "Energy", "Consumer", "Industrial"], n,
                 p=[0.28, 0.18, 0.16, 0.14, 0.14, 0.10]), "missing": 0.02},
            {"name": "trade_type", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Buy", "Sell", "Short", "Cover"], n,
                 p=[0.40, 0.35, 0.15, 0.10]), "missing": 0.0},
            {"name": "risk_score", "type": "numeric",
             "gen": lambda n: np.round(np.random.beta(5, 2, n) * 100, 1), "missing": 0.0},
        ],
    },
    {
        "name": "Employee Performance Dataset",
        "description": "HR records with performance reviews and compensation data",
        "rows_range": (300, 2000),
        "columns": [
            {"name": "employee_id", "type": "numeric",
             "gen": lambda n: np.arange(10001, 10001 + n), "missing": 0.0},
            {"name": "years_experience", "type": "numeric",
             "gen": lambda n: np.clip(np.random.exponential(7, n), 0, 40).astype(int),
             "missing": 0.02},
            {"name": "salary", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(11.0, 0.4, n), -2),
             "missing": 0.07},
            {"name": "performance_score", "type": "numeric",
             "gen": lambda n: np.clip(np.random.beta(6, 3, n) * 5, 1, 5).round(1),
             "missing": 0.04},
            {"name": "satisfaction_score", "type": "numeric",
             "gen": lambda n: np.random.randint(1, 11, n), "missing": 0.06},
            {"name": "department", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Engineering", "Sales", "Marketing", "Operations", "HR", "Finance"], n,
                 p=[0.30, 0.22, 0.15, 0.15, 0.08, 0.10]), "missing": 0.0},
            {"name": "education_level", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["High School", "Bachelor", "Master", "PhD"], n,
                 p=[0.10, 0.45, 0.35, 0.10]), "missing": 0.03},
            {"name": "attrition", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Yes", "No"], n, p=[0.16, 0.84]), "missing": 0.0},
        ],
    },
    {
        "name": "Industrial Sensor Readings",
        "description": "Time-series sensor data from a manufacturing plant",
        "rows_range": (2000, 10000),
        "columns": [
            {"name": "reading_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "temperature_c", "type": "numeric",
             "gen": lambda n: np.where(
                 np.random.random(n) > 0.95,
                 np.random.normal(150, 20, n),
                 np.random.normal(72, 5, n)).round(2), "missing": 0.03},
            {"name": "pressure_psi", "type": "numeric",
             "gen": lambda n: np.round(np.random.normal(45, 3, n).clip(30, 65), 2),
             "missing": 0.02},
            {"name": "vibration_hz", "type": "numeric",
             "gen": lambda n: np.round(np.abs(np.random.normal(0.5, 0.15, n)), 4),
             "missing": 0.01},
            {"name": "power_consumption_kw", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(3.5, 0.3, n), 2),
             "missing": 0.04},
            {"name": "machine_status", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Running", "Idle", "Maintenance", "Fault"], n,
                 p=[0.70, 0.15, 0.10, 0.05]), "missing": 0.0},
            {"name": "product_quality", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Pass", "Marginal", "Fail"], n,
                 p=[0.85, 0.10, 0.05]), "missing": 0.02},
        ],
    },
    {
        "name": "Student Academic Performance",
        "description": "University student records across multiple semesters",
        "rows_range": (400, 3000),
        "columns": [
            {"name": "student_id", "type": "numeric",
             "gen": lambda n: np.arange(20001, 20001 + n), "missing": 0.0},
            {"name": "gpa", "type": "numeric",
             "gen": lambda n: np.clip(np.random.beta(5, 2, n) * 4, 0, 4).round(2),
             "missing": 0.01},
            {"name": "study_hours_weekly", "type": "numeric",
             "gen": lambda n: np.clip(np.random.normal(20, 8, n), 0, 60).astype(int),
             "missing": 0.05},
            {"name": "attendance_pct", "type": "numeric",
             "gen": lambda n: np.clip(np.random.beta(8, 2, n) * 100, 0, 100).round(1),
             "missing": 0.03},
            {"name": "assignments_completed", "type": "numeric",
             "gen": lambda n: np.random.randint(5, 30, n), "missing": 0.0},
            {"name": "major", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["CS", "Engineering", "Business", "Science", "Arts", "Medicine"], n,
                 p=[0.22, 0.18, 0.20, 0.15, 0.13, 0.12]), "missing": 0.0},
            {"name": "scholarship", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Full", "Partial", "None"], n,
                 p=[0.10, 0.25, 0.65]), "missing": 0.02},
        ],
    },
    # ── Domain 7: Marketing/Advertising ──
    {
        "name": "Digital Marketing Campaign Data",
        "description": "Ad campaign performance metrics across channels",
        "rows_range": (500, 4000),
        "columns": [
            {"name": "campaign_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "impressions", "type": "numeric",
             "gen": lambda n: np.random.lognormal(10, 1.5, n).astype(int), "missing": 0.0},
            {"name": "clicks", "type": "numeric",
             "gen": lambda n: np.random.lognormal(6, 1.2, n).astype(int), "missing": 0.01},
            {"name": "ctr_pct", "type": "numeric",
             "gen": lambda n: np.round(np.random.beta(2, 50, n) * 100, 3), "missing": 0.02},
            {"name": "cost_usd", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(5, 1.0, n), 2), "missing": 0.0},
            {"name": "conversions", "type": "numeric",
             "gen": lambda n: np.random.poisson(lam=8, size=n), "missing": 0.03},
            {"name": "bounce_rate_pct", "type": "numeric",
             "gen": lambda n: np.clip(np.random.beta(3, 3, n) * 100, 5, 95).round(1), "missing": 0.04},
            {"name": "channel", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Google Ads", "Facebook", "Instagram", "TikTok", "LinkedIn", "Email"],
                 n, p=[0.25, 0.22, 0.18, 0.15, 0.10, 0.10]), "missing": 0.0},
            {"name": "campaign_type", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Brand", "Performance", "Retargeting", "Awareness"], n,
                 p=[0.20, 0.40, 0.25, 0.15]), "missing": 0.0},
        ],
    },
    # ── Domain 8: Real Estate ──
    {
        "name": "Property Listings Dataset",
        "description": "Residential property listings with pricing and features",
        "rows_range": (300, 5000),
        "columns": [
            {"name": "listing_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "price_usd", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(12.5, 0.6, n), -3), "missing": 0.01},
            {"name": "sqft", "type": "numeric",
             "gen": lambda n: np.random.lognormal(7.2, 0.4, n).astype(int), "missing": 0.02},
            {"name": "bedrooms", "type": "numeric",
             "gen": lambda n: np.random.choice([1, 2, 3, 4, 5, 6], n,
                 p=[0.10, 0.20, 0.35, 0.20, 0.10, 0.05]), "missing": 0.0},
            {"name": "bathrooms", "type": "numeric",
             "gen": lambda n: np.random.choice([1, 1.5, 2, 2.5, 3, 4], n,
                 p=[0.15, 0.15, 0.30, 0.20, 0.12, 0.08]), "missing": 0.01},
            {"name": "year_built", "type": "numeric",
             "gen": lambda n: np.random.randint(1950, 2025, n), "missing": 0.06},
            {"name": "days_on_market", "type": "numeric",
             "gen": lambda n: np.clip(np.random.exponential(30, n), 1, 365).astype(int),
             "missing": 0.03},
            {"name": "property_type", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["House", "Condo", "Townhouse", "Apartment"], n,
                 p=[0.40, 0.25, 0.20, 0.15]), "missing": 0.0},
            {"name": "neighborhood", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Downtown", "Suburbs", "Midtown", "Waterfront", "Rural"], n,
                 p=[0.22, 0.35, 0.18, 0.13, 0.12]), "missing": 0.02},
        ],
    },
    # ── Domain 9: Supply Chain/Logistics ──
    {
        "name": "Supply Chain Shipment Records",
        "description": "Logistics data tracking shipments and delivery performance",
        "rows_range": (1000, 8000),
        "columns": [
            {"name": "shipment_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "weight_kg", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(3.0, 0.8, n), 2), "missing": 0.01},
            {"name": "distance_km", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(5.5, 1.0, n), 1), "missing": 0.0},
            {"name": "shipping_cost_usd", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(3.5, 0.7, n), 2), "missing": 0.02},
            {"name": "delivery_days", "type": "numeric",
             "gen": lambda n: np.clip(np.random.poisson(5, n), 1, 30), "missing": 0.03},
            {"name": "delay_hours", "type": "numeric",
             "gen": lambda n: np.clip(np.random.exponential(8, n), 0, 120).round(1),
             "missing": 0.05},
            {"name": "carrier", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["FedEx", "UPS", "DHL", "USPS", "Regional"], n,
                 p=[0.25, 0.25, 0.20, 0.18, 0.12]), "missing": 0.0},
            {"name": "status", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Delivered", "In Transit", "Delayed", "Returned", "Lost"], n,
                 p=[0.72, 0.12, 0.10, 0.04, 0.02]), "missing": 0.0},
            {"name": "priority", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Express", "Standard", "Economy"], n,
                 p=[0.20, 0.55, 0.25]), "missing": 0.01},
        ],
    },
    # ── Domain 10: Social Media Analytics ──
    {
        "name": "Social Media Engagement Data",
        "description": "Post-level engagement metrics from a social platform",
        "rows_range": (1000, 10000),
        "columns": [
            {"name": "post_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "likes", "type": "numeric",
             "gen": lambda n: np.random.lognormal(4, 1.8, n).astype(int), "missing": 0.0},
            {"name": "comments", "type": "numeric",
             "gen": lambda n: np.random.lognormal(2, 1.5, n).astype(int), "missing": 0.01},
            {"name": "shares", "type": "numeric",
             "gen": lambda n: np.random.lognormal(1.5, 1.8, n).astype(int), "missing": 0.01},
            {"name": "reach", "type": "numeric",
             "gen": lambda n: np.random.lognormal(7, 1.5, n).astype(int), "missing": 0.02},
            {"name": "engagement_rate_pct", "type": "numeric",
             "gen": lambda n: np.round(np.random.beta(1.5, 30, n) * 100, 3), "missing": 0.03},
            {"name": "follower_count", "type": "numeric",
             "gen": lambda n: np.random.lognormal(8, 2, n).astype(int), "missing": 0.0},
            {"name": "content_type", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Image", "Video", "Reel", "Story", "Text", "Carousel"], n,
                 p=[0.25, 0.22, 0.20, 0.15, 0.08, 0.10]), "missing": 0.0},
            {"name": "platform", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Instagram", "TikTok", "Twitter", "LinkedIn", "YouTube"], n,
                 p=[0.28, 0.25, 0.18, 0.15, 0.14]), "missing": 0.0},
        ],
    },
    # ── Domain 11: Cybersecurity ──
    {
        "name": "Network Security Event Logs",
        "description": "Security events and threat detection from network monitoring",
        "rows_range": (2000, 15000),
        "columns": [
            {"name": "event_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "packet_size_bytes", "type": "numeric",
             "gen": lambda n: np.random.lognormal(6, 1.5, n).astype(int), "missing": 0.01},
            {"name": "duration_ms", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(4, 1.2, n), 2), "missing": 0.02},
            {"name": "src_port", "type": "numeric",
             "gen": lambda n: np.random.randint(1024, 65535, n), "missing": 0.0},
            {"name": "failed_logins", "type": "numeric",
             "gen": lambda n: np.random.poisson(lam=0.3, size=n), "missing": 0.0},
            {"name": "bytes_transferred", "type": "numeric",
             "gen": lambda n: np.random.lognormal(8, 2, n).astype(int), "missing": 0.03},
            {"name": "threat_score", "type": "numeric",
             "gen": lambda n: np.round(np.random.beta(1, 8, n) * 100, 1), "missing": 0.0},
            {"name": "protocol", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["TCP", "UDP", "HTTP", "HTTPS", "DNS", "SSH"], n,
                 p=[0.30, 0.15, 0.20, 0.18, 0.10, 0.07]), "missing": 0.0},
            {"name": "severity", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Low", "Medium", "High", "Critical"], n,
                 p=[0.55, 0.25, 0.13, 0.07]), "missing": 0.01},
        ],
    },
    # ── Domain 12: Retail Inventory ──
    {
        "name": "Retail Inventory Management",
        "description": "Product inventory levels and sales velocity data",
        "rows_range": (500, 5000),
        "columns": [
            {"name": "product_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "unit_price", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(3, 0.8, n), 2), "missing": 0.0},
            {"name": "units_sold_monthly", "type": "numeric",
             "gen": lambda n: np.random.lognormal(3.5, 1.2, n).astype(int), "missing": 0.02},
            {"name": "stock_quantity", "type": "numeric",
             "gen": lambda n: np.random.lognormal(4.5, 1.0, n).astype(int), "missing": 0.01},
            {"name": "reorder_lead_days", "type": "numeric",
             "gen": lambda n: np.clip(np.random.normal(14, 5, n), 1, 45).astype(int),
             "missing": 0.03},
            {"name": "return_rate_pct", "type": "numeric",
             "gen": lambda n: np.round(np.random.beta(1.5, 15, n) * 100, 2), "missing": 0.04},
            {"name": "discount_pct", "type": "numeric",
             "gen": lambda n: np.where(np.random.random(n) > 0.6,
                 np.random.choice([5, 10, 15, 20, 25, 30, 50], n), 0), "missing": 0.0},
            {"name": "category", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Electronics", "Clothing", "Food", "Home", "Beauty", "Sports"], n,
                 p=[0.20, 0.22, 0.18, 0.16, 0.12, 0.12]), "missing": 0.0},
            {"name": "supplier_rating", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["A", "B", "C", "D"], n,
                 p=[0.30, 0.35, 0.25, 0.10]), "missing": 0.02},
        ],
    },
    # ── Domain 13: Weather/Environmental ──
    {
        "name": "Weather Station Observations",
        "description": "Daily meteorological measurements from weather stations",
        "rows_range": (365, 3650),
        "columns": [
            {"name": "observation_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "temperature_avg_c", "type": "numeric",
             "gen": lambda n: np.round(15 + 12 * np.sin(np.linspace(0, 2*np.pi*(n/365), n))
                 + np.random.normal(0, 3, n), 1), "missing": 0.02},
            {"name": "humidity_pct", "type": "numeric",
             "gen": lambda n: np.clip(np.random.normal(65, 18, n), 5, 100).round(1),
             "missing": 0.03},
            {"name": "wind_speed_kmh", "type": "numeric",
             "gen": lambda n: np.round(np.random.weibull(2, n) * 15, 1), "missing": 0.02},
            {"name": "precipitation_mm", "type": "numeric",
             "gen": lambda n: np.where(np.random.random(n) > 0.65,
                 np.random.exponential(5, n), 0).round(1), "missing": 0.04},
            {"name": "pressure_hpa", "type": "numeric",
             "gen": lambda n: np.round(np.random.normal(1013, 10, n), 1), "missing": 0.01},
            {"name": "uv_index", "type": "numeric",
             "gen": lambda n: np.clip(np.random.gamma(3, 1.5, n), 0, 12).round(1),
             "missing": 0.05},
            {"name": "condition", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Clear", "Cloudy", "Rain", "Storm", "Fog", "Snow"], n,
                 p=[0.30, 0.28, 0.18, 0.08, 0.09, 0.07]), "missing": 0.0},
        ],
    },
    # ── Domain 14: Sports Analytics ──
    {
        "name": "Sports Player Performance Stats",
        "description": "Athlete performance and fitness tracking data",
        "rows_range": (200, 2000),
        "columns": [
            {"name": "player_id", "type": "numeric",
             "gen": lambda n: np.arange(1, n + 1), "missing": 0.0},
            {"name": "matches_played", "type": "numeric",
             "gen": lambda n: np.random.randint(1, 50, n), "missing": 0.0},
            {"name": "avg_score", "type": "numeric",
             "gen": lambda n: np.round(np.random.normal(15, 6, n).clip(0, 45), 1),
             "missing": 0.02},
            {"name": "sprint_speed_kmh", "type": "numeric",
             "gen": lambda n: np.round(np.random.normal(28, 3, n).clip(18, 38), 1),
             "missing": 0.03},
            {"name": "distance_covered_km", "type": "numeric",
             "gen": lambda n: np.round(np.random.normal(9.5, 1.5, n).clip(3, 14), 2),
             "missing": 0.02},
            {"name": "injury_days", "type": "numeric",
             "gen": lambda n: np.clip(np.random.exponential(10, n), 0, 180).astype(int),
             "missing": 0.04},
            {"name": "market_value_usd", "type": "numeric",
             "gen": lambda n: np.round(np.random.lognormal(14, 1.5, n), -3), "missing": 0.06},
            {"name": "position", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Forward", "Midfielder", "Defender", "Goalkeeper"], n,
                 p=[0.28, 0.30, 0.28, 0.14]), "missing": 0.0},
            {"name": "fitness_level", "type": "categorical",
             "gen": lambda n: np.random.choice(
                 ["Peak", "Good", "Average", "Recovering", "Injured"], n,
                 p=[0.20, 0.35, 0.25, 0.12, 0.08]), "missing": 0.01},
        ],
    },
]


# ── Dataset Generation ───────────────────────────────────────────

def generate_single_dataset(template: dict) -> pd.DataFrame:
    n = random.randint(*template["rows_range"])
    data = {}

    for col in template["columns"]:
        values = col["gen"](n)
        values = _safe_array(values, n)

        if col["missing"] > 0:
            mask = np.random.random(n) < col["missing"]
            if col["type"] == "numeric":
                values = values.astype(float)
                values[mask] = np.nan
            else:
                values = np.where(mask, None, values)

        data[col["name"]] = values

    return pd.DataFrame(data)


def add_correlations(df: pd.DataFrame, template: dict) -> pd.DataFrame:
    df = df.copy()
    numeric_cols = [
        c["name"] for c in template["columns"]
        if c["type"] == "numeric" and "id" not in c["name"].lower()
    ]

    if len(numeric_cols) < 2:
        return df

    num_pairs = random.randint(1, min(2, len(numeric_cols) // 2))
    shuffled = random.sample(numeric_cols, min(len(numeric_cols), num_pairs * 2))

    for i in range(0, len(shuffled) - 1, 2):
        c1, c2 = shuffled[i], shuffled[i + 1]
        df[c1] = df[c1].astype(float)
        df[c2] = df[c2].astype(float)

        valid = df[c1].notna() & df[c2].notna()
        if valid.sum() < 10:
            continue

        strength = random.uniform(0.3, 0.7)
        sign = random.choice([-1, 1])

        v1 = df.loc[valid, c1].values
        v2 = df.loc[valid, c2].values

        v1_z = (v1 - np.nanmean(v1)) / (np.nanstd(v1) + 1e-8)
        v2_z = (v2 - np.nanmean(v2)) / (np.nanstd(v2) + 1e-8)

        blended = sign * strength * v1_z + (1 - strength) * v2_z
        result = blended * np.nanstd(v2) + np.nanmean(v2)
        df.loc[valid, c2] = np.round(result, 4)

    return df


# ── Statistical Profiler ─────────────────────────────────────────

def profile_dataframe(df: pd.DataFrame) -> dict:
    profile = {
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "columns": {},
        "correlations": [],
        "quality_score": 0.0,
    }

    numeric_cols = []

    for col_name in df.columns:
        series = df[col_name]
        missing = int(series.isna().sum())
        missing_pct = round(missing / len(df) * 100, 2)

        cp = {
            "name": col_name,
            "missing": missing,
            "missing_pct": missing_pct,
            "unique_values": int(series.nunique()),
            "unique_ratio": round(series.nunique() / len(df), 4),
        }

        if pd.api.types.is_numeric_dtype(series):
            cp["type"] = "numeric"
            clean = series.dropna()
            if len(clean) > 0:
                q1, q3 = float(clean.quantile(0.25)), float(clean.quantile(0.75))
                iqr = q3 - q1
                outliers = int(((clean < q1 - 1.5 * iqr) | (clean > q3 + 1.5 * iqr)).sum())
                cp["stats"] = {
                    "mean": round(float(clean.mean()), 4),
                    "std": round(float(clean.std()), 4),
                    "min": round(float(clean.min()), 4),
                    "max": round(float(clean.max()), 4),
                    "median": round(float(clean.median()), 4),
                    "q25": round(q1, 4),
                    "q75": round(q3, 4),
                    "skewness": round(float(clean.skew()), 4),
                    "kurtosis": round(float(clean.kurtosis()), 4),
                    "outliers": outliers,
                    "outlier_pct": round(outliers / len(clean) * 100, 2),
                }
            numeric_cols.append(col_name)
        else:
            cp["type"] = "categorical"
            vc = series.value_counts()
            cp["top_values"] = {str(k): int(v) for k, v in vc.head(5).items()}
            if len(vc) > 1:
                cp["imbalance_ratio"] = round(float(vc.iloc[0] / vc.iloc[-1]), 2)

        profile["columns"][col_name] = cp

    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        for i, c1 in enumerate(numeric_cols):
            for j, c2 in enumerate(numeric_cols):
                if i < j:
                    r = round(float(corr.loc[c1, c2]), 4)
                    if abs(r) > 0.3:
                        profile["correlations"].append({
                            "col1": c1, "col2": c2, "r": r,
                            "strength": "strong" if abs(r) > 0.7 else "moderate" if abs(r) > 0.5 else "weak"
                        })

    total_missing = df.isna().sum().sum() / (len(df) * len(df.columns)) * 100
    profile["quality_score"] = round(max(0, 100 - total_missing * 2), 1)
    return profile


# ── Prompt Formatter ─────────────────────────────────────────────

def format_profile_as_prompt(profile: dict, domain_name: str) -> str:
    lines = [
        f"Dataset: {domain_name}",
        f"Rows: {profile['num_rows']:,} | Columns: {profile['num_columns']}",
        f"Quality Score: {profile['quality_score']}%",
        "",
        "=== Column Profiles ===",
    ]

    for col_name, col in profile["columns"].items():
        line = f"- {col_name} ({col['type']}): {col['unique_values']} unique"
        if col["missing_pct"] > 0:
            line += f", {col['missing_pct']}% missing"
        if col["type"] == "numeric" and "stats" in col:
            s = col["stats"]
            line += (f" | mean={s['mean']}, std={s['std']}, median={s['median']}, "
                     f"range=[{s['min']}, {s['max']}], skew={s['skewness']}, "
                     f"kurtosis={s['kurtosis']}")
            if s["outlier_pct"] > 0:
                line += f", outliers={s['outlier_pct']}%"
        elif col["type"] == "categorical" and "top_values" in col:
            top = ", ".join(f"{k}:{v}" for k, v in list(col["top_values"].items())[:4])
            line += f" | top: [{top}]"
            if "imbalance_ratio" in col:
                line += f", imbalance_ratio={col['imbalance_ratio']}"
        lines.append(line)

    if profile["correlations"]:
        lines.extend(["", "=== Notable Correlations ==="])
        for c in profile["correlations"]:
            lines.append(f"- {c['col1']} ↔ {c['col2']}: r={c['r']} ({c['strength']})")

    return "\n".join(lines)


# ── Thinking Generator ───────────────────────────────────────────

def generate_thinking(profile: dict, domain_name: str) -> str:
    thoughts = [
        f"Dataset: {domain_name}, {profile['num_rows']:,} rows, {profile['num_columns']} columns",
        f"Quality score: {profile['quality_score']}%",
    ]

    num_cols = [c for c in profile["columns"].values() if c["type"] == "numeric" and "id" not in c["name"].lower()]
    cat_cols = [c for c in profile["columns"].values() if c["type"] == "categorical"]
    thoughts.append(f"Features: {len(num_cols)} numeric, {len(cat_cols)} categorical")

    for col in num_cols:
        if "stats" not in col:
            continue
        s = col["stats"]
        notes = []
        skew = s.get("skewness", 0)
        if abs(skew) > 1.5:
            notes.append(f"heavily {'right' if skew > 0 else 'left'}-skewed")
        elif abs(skew) > 0.5:
            notes.append(f"moderately {'right' if skew > 0 else 'left'}-skewed")
        if s.get("outlier_pct", 0) > 3:
            notes.append(f"{s['outlier_pct']}% outliers")
        if s.get("kurtosis", 0) > 3:
            notes.append("heavy-tailed")
        if col["missing_pct"] > 5:
            notes.append(f"{col['missing_pct']}% missing")
        thoughts.append(f"{col['name']}: {', '.join(notes) if notes else 'normal, clean'}")

    for c in profile["correlations"][:3]:
        direction = "positive" if c["r"] > 0 else "negative"
        thoughts.append(f"Corr: {c['col1']} ↔ {c['col2']} r={c['r']} ({c['strength']} {direction})")

    for col in cat_cols:
        if col.get("imbalance_ratio", 1) > 5:
            thoughts.append(f"{col['name']}: imbalanced (ratio={col['imbalance_ratio']})")

    has_target = any(
        c["name"] in ("churn_risk", "attrition", "diagnosis", "product_quality", "target",
                       "conversions", "severity", "status", "fitness_level", "condition")
        for c in profile["columns"].values()
    )
    thoughts.append("Supervised target detected" if has_target else "No obvious target — consider unsupervised methods")

    return "\n".join(f"- {t}" for t in thoughts)


# ── Insight Generator ────────────────────────────────────────────

OPENERS = [
    "Looking at the overall structure of this dataset,",
    "This dataset presents several interesting characteristics.",
    "The data reveals some noteworthy patterns worth examining.",
    "Upon analyzing the statistical profile,",
    "Several key observations emerge from this data.",
]

DIST_PHRASES = {
    "normal": ["follows an approximately normal distribution",
               "shows a roughly bell-shaped distribution"],
    "right_skewed": ["is right-skewed with a long tail toward higher values",
                     "shows positive skewness, indicating concentration at lower values"],
    "left_skewed": ["is left-skewed, concentrated toward higher values",
                    "shows negative skewness with a tail toward lower values"],
    "uniform": ["is approximately uniformly distributed across its range",
                "shows no strong central tendency"],
}

CORR_PHRASES = {
    "strong_pos": ["are strongly positively correlated (r={r}), suggesting they move together",
                   "show a strong positive relationship (r={r})"],
    "mod_pos": ["show a moderate positive correlation (r={r})",
                "have a moderate positive relationship (r={r})"],
    "strong_neg": ["have a strong inverse relationship (r={r})",
                   "are strongly negatively correlated (r={r})"],
    "mod_neg": ["show a moderate negative correlation (r={r})",
                "have a moderate inverse relationship (r={r})"],
}

TECHNIQUES = {
    "skew": ["log transformation", "Box-Cox transformation", "quantile normalization"],
    "missing": ["KNN imputation", "iterative imputation (MICE)", "median/mode imputation"],
    "outliers": ["IQR-based capping", "Winsorization", "robust scaling"],
    "multicollinearity": ["VIF analysis + feature removal", "PCA", "L1 regularization"],
    "clustering": ["K-Means clustering", "DBSCAN", "Gaussian Mixture Models"],
}


def generate_insight(profile: dict, domain_name: str) -> str:
    paragraphs = []

    # Overview
    num_cols = [c for c in profile["columns"].values() if c["type"] == "numeric"]
    cat_cols = [c for c in profile["columns"].values() if c["type"] == "categorical"]
    overview = (f"{random.choice(OPENERS)} The {domain_name.lower()} contains "
                f"{profile['num_rows']:,} records across {profile['num_columns']} features. "
                f"It includes {len(num_cols)} numeric and {len(cat_cols)} categorical variables.")
    paragraphs.append(overview)

    # Distributions
    dist_notes = []
    for col in num_cols:
        if "stats" not in col or col["unique_ratio"] > 0.9 and "id" in col["name"].lower():
            continue
        skew = col["stats"].get("skewness", 0)
        if abs(skew) < 0.5:
            dtype = "normal"
        elif skew > 1:
            dtype = "right_skewed"
        elif skew < -1:
            dtype = "left_skewed"
        else:
            dtype = "normal"
        s = col["stats"]
        note = f"'{col['name']}' {random.choice(DIST_PHRASES[dtype])} (mean={s['mean']}, std={s['std']}, range=[{s['min']}, {s['max']}])"
        if s.get("outlier_pct", 0) > 3:
            note += f", with {s['outlier_pct']}% outliers detected"
        dist_notes.append(note)

    if dist_notes:
        selected = random.sample(dist_notes, min(len(dist_notes), random.randint(2, 4)))
        paragraphs.append("Distribution analysis: " + ". ".join(selected) + ".")

    # Correlations
    if profile["correlations"]:
        corr_notes = []
        for c in profile["correlations"][:3]:
            r = c["r"]
            key = ("strong_pos" if r > 0.7 else "mod_pos" if r > 0.3
                   else "strong_neg" if r < -0.7 else "mod_neg")
            phrase = random.choice(CORR_PHRASES[key]).format(r=r)
            corr_notes.append(f"'{c['col1']}' and '{c['col2']}' {phrase}")
        paragraphs.append("Correlation findings: " + ". ".join(corr_notes) + ".")

    # Quality
    q = profile["quality_score"]
    if q >= 95:
        qtext = "Data quality is excellent with minimal missing values."
    elif q >= 80:
        qtext = "Data quality is generally good, though some columns have notable gaps."
    else:
        qtext = "Data quality is concerning — several columns have significant missing values."
    bad_cols = sorted(
        [(c["name"], c["missing_pct"]) for c in profile["columns"].values() if c["missing_pct"] > 3],
        key=lambda x: -x[1])
    if bad_cols:
        worst = ", ".join(f"'{n}' ({p}%)" for n, p in bad_cols[:3])
        qtext += f" Columns with most missing data: {worst}."
    paragraphs.append(qtext)

    # Recommendations
    recs = []
    skewed = [c for c in num_cols if "stats" in c and abs(c["stats"].get("skewness", 0)) > 1.5]
    if skewed:
        names = ", ".join(f"'{c['name']}'" for c in skewed[:2])
        recs.append(f"Consider {random.choice(TECHNIQUES['skew'])} for skewed features {names}.")

    if any(c["missing_pct"] > 5 for c in profile["columns"].values()):
        recs.append(f"For missing values, {random.choice(TECHNIQUES['missing'])} would be a good approach.")

    outlier_cols = [c for c in num_cols if "stats" in c and c["stats"].get("outlier_pct", 0) > 5]
    if outlier_cols:
        recs.append(f"Address outliers with {random.choice(TECHNIQUES['outliers'])}.")

    if any(abs(c["r"]) > 0.7 for c in profile["correlations"]):
        recs.append(f"For multicollinearity, try {random.choice(TECHNIQUES['multicollinearity'])}.")

    if len(num_cols) >= 3:
        recs.append(f"With {len(num_cols)} numeric features, {random.choice(TECHNIQUES['clustering'])} could reveal hidden segments.")

    if recs:
        paragraphs.append("Recommendations: " + " ".join(recs))

    return "\n\n".join(paragraphs)


# ── .toon Formatter ──────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a senior data scientist. Analyze the following dataset profile "
    "and provide a comprehensive insight covering distribution analysis, "
    "correlation findings, data quality assessment, and actionable recommendations. "
    "Structure your response with clear sections."
)


def format_toon(instruction: str, input_text: str, thinking: str, answer: str) -> str:
    return (
        f"[system]\n{instruction}\n"
        f"[input]\n{input_text}\n"
        f"[output]\n{_combine_output(thinking, answer)}\n"
        f"<<<EOE>>>"
    )


def format_jsonl(instruction: str, input_text: str, thinking: str, answer: str) -> dict:
    return {
        "instruction": instruction,
        "input": input_text,
        "output": _combine_output(thinking, answer),
    }


def _combine_output(thinking: str, answer: str) -> str:
    """Merge thinking + answer into natural prose with markdown structure."""
    lines = ["## Initial Observations\n"]
    for thought in thinking.split("\n"):
        thought = thought.strip().lstrip("- ").strip()
        if thought:
            lines.append(f"- {thought}")
    lines.append("\n## Analysis\n")
    lines.append(answer)
    return "\n".join(lines)


# ── Pipeline ─────────────────────────────────────────────────────

def generate_training_example() -> tuple[str, dict]:
    template = random.choice(DOMAIN_TEMPLATES)
    df = generate_single_dataset(template)
    df = add_correlations(df, template)
    profile = profile_dataframe(df)

    input_text = format_profile_as_prompt(profile, template["name"])
    thinking = generate_thinking(profile, template["name"])
    answer = generate_insight(profile, template["name"])

    toon = format_toon(SYSTEM_PROMPT, input_text, thinking, answer)
    jsonl = format_jsonl(SYSTEM_PROMPT, input_text, thinking, answer)

    return toon, jsonl


# ── Main ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate training data for DataScope AI")
    parser.add_argument("--num_examples", type=int, default=3000)
    parser.add_argument("--output", type=str, default="../data/processed")
    parser.add_argument("--preview", type=int, default=0)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    toon_path = output_dir / "datascope_train.toon"
    jsonl_path = output_dir / "datascope_train.jsonl"

    print(f"╔{'═' * 58}╗")
    print(f"║  DataScope AI — Training Data Generator{' ' * 18}║")
    print(f"╠{'═' * 58}╣")
    print(f"║  Examples: {args.num_examples:<46}║")
    print(f"║  Output:   {str(toon_path):<46}║")
    print(f"║  Domains:  {len(DOMAIN_TEMPLATES):<46}║")
    print(f"╚{'═' * 58}╝\n")

    toon_entries = []
    jsonl_entries = []

    for i in range(args.num_examples):
        toon, jsonl = generate_training_example()
        toon_entries.append(toon)
        jsonl_entries.append(jsonl)

        if (i + 1) % 100 == 0 or i == 0:
            pct = (i + 1) / args.num_examples * 100
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            print(f"\r  [{bar}] {pct:.1f}% ({i + 1}/{args.num_examples})", end="", flush=True)

    print("\n")

    # Save .toon
    with open(toon_path, "w", encoding="utf-8") as f:
        f.write("\n".join(toon_entries))

    # Save .jsonl (for Unsloth compatibility)
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for entry in jsonl_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    avg_in = sum(len(e["input"]) for e in jsonl_entries) / len(jsonl_entries)
    avg_out = sum(len(e["output"]) for e in jsonl_entries) / len(jsonl_entries)

    print(f"  ✓ Saved {len(toon_entries)} examples")
    print(f"  ✓ .toon: {toon_path} ({toon_path.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"  ✓ .jsonl: {jsonl_path} ({jsonl_path.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"  ✓ Avg input: ~{avg_in / 4:.0f} tokens | Avg output: ~{avg_out / 4:.0f} tokens")

    if args.preview > 0:
        print(f"\n{'═' * 60}")
        for i, entry in enumerate(toon_entries[:args.preview]):
            print(f"\n{'─' * 20} Example {i + 1} {'─' * 20}")
            print(entry)


if __name__ == "__main__":
    main()