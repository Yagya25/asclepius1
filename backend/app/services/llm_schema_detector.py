import os
import json
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ValidationError
from groq import Groq

class MetadataRow(BaseModel):
    row_index: int
    content: str

class ColumnSchema(BaseModel):
    excel_column_index: int
    field_name: str
    group: Optional[str] = None
    data_type: Literal["string", "number", "date_month_year", "date_day_month_year", "identifier"]

class SheetSchema(BaseModel):
    header_row_index: int
    data_start_row_index: int
    metadata_rows: List[MetadataRow]
    columns: List[ColumnSchema]

def detect_schema_via_llm(sample_json: dict) -> SheetSchema:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set.")
    
    client = Groq(api_key=api_key)
    
    system_prompt = """You are a spreadsheet structure analyzer. 
You will be provided with a JSON representation of the first 15 rows of an Excel file, including merged cell ranges.
Your task is to analyze the structure and determine the exact schema.

Rules:
1. Return ONLY valid JSON matching the exact schema requested, no markdown blocks, no conversational text.
2. The schema format:
{
  "header_row_index": <int>,
  "data_start_row_index": <int>,
  "metadata_rows": [{"row_index": int, "content": str}],
  "columns": [
    {
      "excel_column_index": int, 
      "field_name": str, 
      "group": str|null, 
      "data_type": "string"|"number"|"date_month_year"|"date_day_month_year"|"identifier"
    }
  ]
}
3. `header_row_index` is the row (0-indexed) that contains the main column headers. If there are merged headers spanning multiple rows, pick the bottom-most row that contains the specific column names.
4. `data_start_row_index` is the row (0-indexed) where actual tabular data records begin.
5. `columns` should list all detected columns. `excel_column_index` must match the 0-indexed column position.
6. `field_name` must be snake_case. 
7. If a column falls under a merged group header (e.g. "Opening Balance", "Sales"), include the group name in `group`. Prefix the `field_name` with the group to deduplicate if necessary (e.g. `opening_qty`, `sales_qty`).
8. `data_type`: use "identifier" for item codes, batch numbers, HSN, MRN, SKU, etc. Use "number" for quantities, values, revenue, prices. Use "string" for names, categories, descriptions.
"""

    prompt = f"Here is the sample sheet data:\n{json.dumps(sample_json, indent=2)}\n\nReturn the strict JSON output."
    
    def call_llm(messages: list) -> str:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        response_text = call_llm(messages)
        schema_dict = json.loads(response_text)
        return SheetSchema(**schema_dict)
    except (json.JSONDecodeError, ValidationError) as e:
        # Retry once
        messages.append({"role": "assistant", "content": response_text if 'response_text' in locals() else "{}"})
        messages.append({"role": "user", "content": f"Your previous response failed validation: {str(e)}. Please correct it and return ONLY valid JSON matching the schema."})
        try:
            response_text = call_llm(messages)
            schema_dict = json.loads(response_text)
            return SheetSchema(**schema_dict)
        except Exception as retry_e:
            raise RuntimeError(f"Failed to detect schema via LLM after retry: {retry_e}")
