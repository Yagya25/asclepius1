"""Shared test fixtures for Asclepius tests."""
import os

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal, engine
from app.main import app
from app.models import Base


@pytest.fixture(autouse=True)
def setup_db():
    """Create fresh tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    os.makedirs("uploads", exist_ok=True)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session for direct DB operations in tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_pharma_df() -> pd.DataFrame:
    """Minimal pharma sales DataFrame for unit testing."""
    return pd.DataFrame({
        "invoice_date": pd.to_datetime([
            "2026-01-15", "2026-02-10", "2026-03-05",
            "2026-04-20", "2026-05-15", "2026-06-10",
            "2026-01-20", "2026-02-15", "2026-03-10",
            "2026-01-25",
        ]),
        "product_name": [
            "Paracetamol 500mg", "Paracetamol 500mg", "Paracetamol 500mg",
            "Crocin 650mg", "Crocin 650mg", "Crocin 650mg",
            "Amoxicillin 250mg", "Amoxicillin 250mg", "Amoxicillin 250mg",
            "Dead Stock Medicine",  # only sold in Jan
        ],
        "qty": [50, 60, 70, 30, 25, 20, 40, 45, 50, 10],
        "amount": [1250, 1500, 1750, 900, 750, 600, 3400, 3825, 4250, 500],
        "customer_name": [
            "Apollo Pharmacy", "MedPlus", "Apollo Pharmacy",
            "City Medical", "MedPlus", "Apollo Pharmacy",
            "Health First", "City Medical", "MedPlus",
            "Apollo Pharmacy",
        ],
        "expiry_date": pd.to_datetime([
            "2027-06-01", "2027-06-01", "2027-06-01",
            "2026-09-15", "2026-09-15", "2026-09-15",  # near-expiry
            "2027-12-01", "2027-12-01", "2027-12-01",
            "2026-07-01",  # expired
        ]),
        "batch_no": ["B1001", "B1001", "B1001", "B2001", "B2001", "B2001",
                      "B3001", "B3001", "B3001", "B4001"],
    })


@pytest.fixture
def sample_columns() -> dict[str, str]:
    """Column mapping for the sample pharma DataFrame."""
    return {
        "date": "invoice_date",
        "product": "product_name",
        "quantity": "qty",
        "revenue": "amount",
        "customer": "customer_name",
        "expiry": "expiry_date",
        "batch": "batch_no",
    }


@pytest.fixture
def sample_csv_path(tmp_path, sample_pharma_df) -> str:
    """Write sample data to a CSV file and return the path."""
    path = str(tmp_path / "test_pharma.csv")
    sample_pharma_df.to_csv(path, index=False)
    return path
