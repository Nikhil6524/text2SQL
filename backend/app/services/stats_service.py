from __future__ import annotations

from typing import Any, Dict, List

from fastapi import HTTPException
from psycopg2.extras import RealDictCursor

from app.db.connection import get_connection
from app.db.schema import fetch_public_schema


NUMERIC_COLUMNS = ["cost", "rating", "depreciation_per_year"]


def _corr(values_x: List[float], values_y: List[float]) -> float:
    count = min(len(values_x), len(values_y))
    if count < 2:
        return 0.0

    mean_x = sum(values_x[:count]) / count
    mean_y = sum(values_y[:count]) / count

    numerator = 0.0
    sum_sq_x = 0.0
    sum_sq_y = 0.0

    for idx in range(count):
        dx = values_x[idx] - mean_x
        dy = values_y[idx] - mean_y
        numerator += dx * dy
        sum_sq_x += dx * dx
        sum_sq_y += dy * dy

    denominator = (sum_sq_x * sum_sq_y) ** 0.5
    if denominator == 0.0:
        return 0.0

    return numerator / denominator


def _fetch_column_values(column: str) -> List[float]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {column} FROM products WHERE {column} IS NOT NULL")
            return [float(row[0]) for row in cur.fetchall()]
    finally:
        conn.close()


def _build_histogram(values: List[float], bins: int = 12) -> Dict[str, List[float]]:
    if not values:
        return {"bins": [], "counts": []}

    min_val = min(values)
    max_val = max(values)

    if min_val == max_val:
        return {"bins": [min_val, max_val], "counts": [len(values)]}

    step = (max_val - min_val) / bins
    edges = [min_val + step * idx for idx in range(bins + 1)]
    counts = [0 for _ in range(bins)]

    for value in values:
        bucket = int((value - min_val) / step)
        if bucket == bins:
            bucket = bins - 1
        counts[bucket] += 1

    return {"bins": edges, "counts": counts}


def _fetch_summary() -> Dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS count,
                    MIN(cost) AS min_cost,
                    MAX(cost) AS max_cost,
                    AVG(cost) AS avg_cost,
                    MIN(rating) AS min_rating,
                    MAX(rating) AS max_rating,
                    AVG(rating) AS avg_rating,
                    MIN(depreciation_per_year) AS min_depreciation,
                    MAX(depreciation_per_year) AS max_depreciation,
                    AVG(depreciation_per_year) AS avg_depreciation
                FROM products
                """
            )
            return dict(cur.fetchone() or {})
    finally:
        conn.close()


def _fetch_heatmap() -> Dict[str, Any]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT cost, rating, depreciation_per_year
                FROM products
                WHERE cost IS NOT NULL
                  AND rating IS NOT NULL
                  AND depreciation_per_year IS NOT NULL
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return {"labels": NUMERIC_COLUMNS, "matrix": []}

    columns = list(zip(*rows))
    values = [[float(item) for item in column] for column in columns]

    matrix: List[List[float]] = []
    for idx_x in range(len(NUMERIC_COLUMNS)):
        row: List[float] = []
        for idx_y in range(len(NUMERIC_COLUMNS)):
            row.append(round(_corr(values[idx_x], values[idx_y]), 4))
        matrix.append(row)

    return {"labels": NUMERIC_COLUMNS, "matrix": matrix}


def get_product_stats() -> Dict[str, Any]:
    schema = fetch_public_schema()
    if "products" not in schema:
        raise HTTPException(status_code=400, detail="Products table not found in public schema")

    summary = _fetch_summary()
    cost_values = _fetch_column_values("cost")
    rating_values = _fetch_column_values("rating")
    depreciation_values = _fetch_column_values("depreciation_per_year")

    return {
        "summary": {
            "count": int(summary.get("count", 0) or 0),
            "cost": {
                "min": summary.get("min_cost"),
                "max": summary.get("max_cost"),
                "avg": summary.get("avg_cost"),
            },
            "rating": {
                "min": summary.get("min_rating"),
                "max": summary.get("max_rating"),
                "avg": summary.get("avg_rating"),
            },
            "depreciation_per_year": {
                "min": summary.get("min_depreciation"),
                "max": summary.get("max_depreciation"),
                "avg": summary.get("avg_depreciation"),
            },
        },
        "histograms": {
            "cost": _build_histogram(cost_values, bins=12),
            "rating": _build_histogram(rating_values, bins=8),
            "depreciation_per_year": _build_histogram(depreciation_values, bins=10),
        },
        "heatmap": _fetch_heatmap(),
    }
