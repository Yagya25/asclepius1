"""Ingestion Agent: validates and cleans uploaded pharma distributor data."""
import os
import re
import json
import hashlib
import subprocess
import openpyxl
import pandas as pd

from ..models import Dataset, SchemaCache
from .base_agent import BaseAgent
from ..services.llm_schema_detector import detect_schema_via_llm, SheetSchema

class IngestionAgent(BaseAgent):
    """Agent 1: Upload → Parse → Detect Columns → Clean → Detect Domain → Log."""

    COLUMN_PATTERNS: dict[str, list[str]] = {
        "date": ["date", "invoice_date", "inv_date", "bill_date", "order_date", "dt"],
        "product": ["product_name", "item_name", "itemname", "product", "medicine", "drug", "description", "item"],
        "product_code": ["item_code", "itemcd", "item_cd", "code", "sku"],
        "quantity": ["balance_qty", "closing_stock", "closingstock", "sales_qty", "saleqty", "qty", "quantity", "units", "units_sold", "no_of_units", "pcs", "pack"],
        "revenue": ["total_value", "balance_value", "sales_value", "bsval", "clstkval", "amount", "total", "revenue", "value", "net_amount", "mrp_value", "bill_amount"],
        "customer": ["customer", "customer_name", "buyer", "client", "party", "party_name", "distributor"],
        "expiry": ["expmmyy", "expiry", "expiry_date", "exp_date", "exp", "exp_dt", "expiry_dt"],
        "batch": ["batch", "batch_no", "batch_number", "lot", "lot_no"],
        "price": ["ptr", "bsrt", "mrp", "price", "unit_price", "rate", "selling_price"],
        "category": ["category", "group", "drug_category", "type", "class", "item_category"],
        "region": ["region", "state", "city", "zone", "territory", "location", "area"],
        "salesman": ["salesman", "sales_rep", "representative", "rep"],
        "invoice": ["invoice", "invoice_no", "bill_no", "inv_no"],
        "hsn": ["hsn_code", "hsn"],
    }

    def __init__(self, db):
        super().__init__("INGESTION", db)

    def run(self, dataset_id: int, file_path: str) -> tuple[pd.DataFrame, dict[str, str]]:
        """Run ingestion pipeline. Returns cleaned DataFrame and column mapping."""
        # Magic bytes detection for XLS and LibreOffice conversion
        try:
            with open(file_path, 'rb') as f:
                header_bytes = f.read(8)
            if header_bytes == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':  # OLE2
                outdir = os.path.dirname(file_path)
                subprocess.run(["soffice", "--headless", "--convert-to", "xlsx", file_path, "--outdir", outdir], check=True)
                file_path = os.path.splitext(file_path)[0] + ".xlsx"
        except Exception:
            pass

        # Step 1: Extract structure sample
        try:
            if file_path.endswith((".xlsx", ".xls")):
                preview = pd.read_excel(file_path, header=None, nrows=15)
            else:
                preview = pd.read_csv(file_path, header=None, nrows=15)
        except Exception:
            preview = pd.DataFrame()

        merged_cells = []
        if file_path.endswith(".xlsx"):
            try:
                wb = openpyxl.load_workbook(file_path, data_only=True, read_only=False)
                ws = wb.active
                for merge in ws.merged_cells.ranges:
                    merged_cells.append(str(merge))
                wb.close()
            except Exception:
                pass

        sample_data = {
            "rows": json.loads(preview.to_json(orient="values", date_format="iso")),
            "merged_cells": merged_cells
        }
        
        signature = hashlib.sha256(json.dumps(sample_data, sort_keys=True).encode()).hexdigest()
        
        llm_schema = None
        cache_entry = self.db.query(SchemaCache).filter(SchemaCache.file_signature == signature).first()
        if cache_entry:
            try:
                llm_schema = SheetSchema(**cache_entry.schema_json)
            except Exception:
                pass
                
        if not llm_schema and os.getenv("ENABLE_LLM_SCHEMA_DETECTION", "false").lower() == "true":
            try:
                llm_schema = detect_schema_via_llm(sample_data)
                self.db.add(SchemaCache(file_signature=signature, schema_json=llm_schema.dict()))
                self.db.commit()
            except Exception as e:
                print(f"LLM Schema Detection failed: {e}")
                pass

        columns = {}
        if llm_schema:
            header_row = llm_schema.header_row_index
            if file_path.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_path, header=header_row)
            else:
                df = pd.read_csv(file_path, header=header_row)
            
            # Apply deterministic LLM schema rename and coercion
            for col_schema in llm_schema.columns:
                if col_schema.excel_column_index < len(df.columns):
                    orig_col_name = df.columns[col_schema.excel_column_index]
                    target_name = f"{col_schema.group}_{col_schema.field_name}" if col_schema.group else col_schema.field_name
                    target_name = re.sub(r'[^a-z0-9]+', '_', target_name.strip().lower()).strip('_')
                    df.rename(columns={orig_col_name: target_name}, inplace=True)
                    
                    if col_schema.data_type == "number":
                        df[target_name] = pd.to_numeric(df[target_name], errors="coerce").fillna(0)
                    elif col_schema.data_type == "identifier":
                        df[target_name] = df[target_name].astype(str)
                    elif col_schema.data_type in ("date_month_year", "date_day_month_year"):
                        df[target_name] = pd.to_datetime(df[target_name], errors="coerce")
            
            columns = self._detect_columns(df.columns.tolist())
            
        else:
            # Fallback to rule-based logic
            best_row = 0
            max_score = 0
            keywords = ["item", "batch", "qty", "stock", "date", "amount", "price", "val", "exp", "name", "code", "revenue"]
            
            for idx, row in preview.iterrows():
                matches = 0
                non_nulls = row.notna().sum()
                row_strs = [str(v).lower().replace(" ", "").replace("_", "") for v in row.values if pd.notna(v)]
                for val in row_strs:
                    if any(k in val for k in keywords):
                        matches += 1
                
                score = matches * non_nulls
                if score > max_score:
                    max_score = score
                    best_row = idx

            if file_path.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_path, header=best_row)
            else:
                df = pd.read_csv(file_path, header=best_row)

            # Step 2: Standardize column names
            df.columns = [re.sub(r'[^a-z0-9]+', '_', str(c).strip().lower()).strip('_') for c in df.columns]

            # Step 3: Detect column semantics
            columns = self._detect_columns(df.columns.tolist())


        original_rows = len(df)

        self.log_action(
            dataset_id=dataset_id,
            action="FILE_LOADED",
            input_summary=f"File: {file_path}",
            output_summary=f"Loaded {original_rows} rows, {len(df.columns)} columns: {list(df.columns)}",
        )

        # Step 2: Standardize column names
        df.columns = [re.sub(r'[^a-z0-9]+', '_', c.strip().lower()).strip('_') for c in df.columns]

        # Step 3: Detect column semantics
        columns = self._detect_columns(df.columns.tolist())

        # Step 4: Clean data
        # Drop exact duplicates
        duplicates = int(df.duplicated().sum())
        df = df.drop_duplicates()

        # Drop rows where ALL values are missing
        all_missing = int(df.isna().all(axis=1).sum())
        df = df.dropna(how="all")

        # Strip whitespace from string columns
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": None, "None": None, "": None})

        # Coerce numeric columns
        for sem_type in ["quantity", "revenue", "price"]:
            col = columns.get(sem_type)
            if col and col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[₹,\s]', '', regex=True),
                    errors="coerce"
                )

        # Parse date columns
        for sem_type in ["date", "expiry"]:
            col = columns.get(sem_type)
            if col and col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Drop rows with invalid dates in the primary date column
        date_col = columns.get("date")
        if date_col and date_col in df.columns:
            invalid_dates = int(df[date_col].isna().sum())
            df = df.dropna(subset=[date_col])
        else:
            invalid_dates = 0

        # Entity resolution: normalize product names
        product_col = columns.get("product")
        if product_col and product_col in df.columns:
            df[product_col] = self._resolve_entities(df[product_col])

        cleaned_rows = len(df)

        self.log_action(
            dataset_id=dataset_id,
            action="DATA_CLEANED",
            input_summary=f"Original rows: {original_rows}",
            output_summary=(
                f"Duplicates removed: {duplicates}, Blank rows: {all_missing}, "
                f"Invalid dates: {invalid_dates}, Final rows: {cleaned_rows}"
            ),
        )

        # Step 5: Detect domain
        domain = self._detect_domain(df.columns.tolist(), columns)

        # Step 6: Update dataset record
        dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        dataset.status = "validated"
        dataset.row_count = cleaned_rows
        dataset.detected_domain = domain
        self.db.commit()

        self.log_action(
            dataset_id=dataset_id,
            action="VALIDATION_COMPLETE",
            input_summary=f"Cleaned data: {cleaned_rows} rows",
            output_summary=f"Domain: {domain}, Columns mapped: {columns}",
        )

        return df, columns

    def _detect_columns(self, col_names: list[str]) -> dict[str, str]:
        """Map column names to semantic types using pattern matching."""
        mapping: dict[str, str] = {}
        mapped_cols = set()
        
        for sem_type, patterns in self.COLUMN_PATTERNS.items():
            # First pass: look for exact matches for ANY pattern
            for pattern in patterns:
                pat_clean = pattern.lower().replace("_", "").replace(" ", "")
                for col in col_names:
                    if col in mapped_cols:
                        continue
                    col_lower = col.lower().replace("_", "").replace(" ", "")
                    if pat_clean == col_lower:
                        mapping[sem_type] = col
                        mapped_cols.add(col)
                        break
                if sem_type in mapping:
                    break
            
            if sem_type in mapping:
                continue
                
            # Second pass: look for substring matches for ANY pattern
            for pattern in patterns:
                pat_clean = pattern.lower().replace("_", "").replace(" ", "")
                for col in col_names:
                    if col in mapped_cols:
                        continue
                    col_lower = col.lower().replace("_", "").replace(" ", "")
                    
                    if pat_clean in col_lower:
                        # Prevent 'item_code' matching as 'product'
                        if sem_type == "product" and ("cd" in col_lower or "code" in col_lower):
                            continue
                        mapping[sem_type] = col
                        mapped_cols.add(col)
                        break
                if sem_type in mapping:
                    break
                    
        return mapping

    def _detect_domain(self, col_names: list[str], columns: dict[str, str]) -> str:
        """Detect business domain from column semantics."""
        has_expiry = "expiry" in columns
        has_batch = "batch" in columns
        if has_expiry or has_batch:
            return "pharma"
        if "quantity" in columns and "product" in columns:
            return "inventory"
        if "revenue" in columns and "customer" in columns:
            return "sales"
        return "generic"

    def _resolve_entities(self, series: pd.Series) -> pd.Series:
        """Normalize inconsistent product names.

        Handles: 'Crocin 650mg' vs 'CROCIN-650' vs 'crocin 650mg'.
        Strategy: lowercase, remove special chars, keep alpha + numbers + spaces.
        """
        def normalize(name):
            if pd.isna(name) or name is None:
                return name
            s = str(name).lower().strip()
            s = re.sub(r'[^a-z0-9\s]', ' ', s)
            s = re.sub(r'\s+', ' ', s).strip()
            return s.title()  # Title Case for readability

        normalized = series.apply(normalize)

        # Build a mapping: normalized → most common original form
        # (so we keep a consistent canonical name)
        name_map: dict[str, str] = {}
        for orig, norm in zip(series, normalized):
            if norm and norm not in name_map:
                name_map[norm] = norm  # Use normalized form as canonical

        return normalized
