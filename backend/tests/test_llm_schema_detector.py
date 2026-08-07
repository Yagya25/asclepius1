import pytest
import os
import json
from unittest.mock import patch, MagicMock
from app.services.llm_schema_detector import detect_schema_via_llm, SheetSchema

MOCK_SAMPLE = {
    "rows": [
        ["", "Opening", "", "Sales", ""],
        ["Item Code", "Qty", "Value", "Qty", "Value"],
        ["ITM01", 10, 100, 5, 50]
    ],
    "merged_cells": ["B1:C1", "D1:E1"]
}

MOCK_LLM_RESPONSE = {
    "header_row_index": 1,
    "data_start_row_index": 2,
    "metadata_rows": [{"row_index": 0, "content": "Opening, Sales"}],
    "columns": [
        {"excel_column_index": 0, "field_name": "item_code", "group": None, "data_type": "identifier"},
        {"excel_column_index": 1, "field_name": "qty", "group": "opening", "data_type": "number"},
        {"excel_column_index": 2, "field_name": "value", "group": "opening", "data_type": "number"},
        {"excel_column_index": 3, "field_name": "qty", "group": "sales", "data_type": "number"},
        {"excel_column_index": 4, "field_name": "value", "group": "sales", "data_type": "number"}
    ]
}

@patch("app.services.llm_schema_detector.Groq")
def test_detect_schema_via_llm_mocked(mock_groq):
    # Setup mock
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_message = MagicMock()
    mock_message.content = json.dumps(MOCK_LLM_RESPONSE)
    mock_completion.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_completion
    mock_groq.return_value = mock_client
    
    # Ensure env var is set
    os.environ["GROQ_API_KEY"] = "fake-key"
    
    schema = detect_schema_via_llm(MOCK_SAMPLE)
    
    assert isinstance(schema, SheetSchema)
    assert schema.header_row_index == 1
    assert schema.data_start_row_index == 2
    assert len(schema.columns) == 5
    assert schema.columns[1].group == "opening"
    assert schema.columns[1].field_name == "qty"
    assert schema.columns[3].group == "sales"
    assert schema.columns[4].data_type == "number"

@pytest.mark.skip(reason="Requires real GROQ_API_KEY network call")
def test_detect_schema_via_llm_integration():
    """Integration test against Groq API with real Brinton sample."""
    sample_json = {
        "rows": [
            ["BRINTON PHARMACEUTICALS LIMITED-KOLKATA", "", "", ""],
            ["Stock Statement (Batch Wise) From 01/04/2026 To 24/04/2026", "", "", ""],
            ["", "", "", "Opening", "", "Total In", "", "Total Out", "", "Balance", ""],
            ["Item Category", "Item Name", "HSN Code", "Qty.", "Value", "Total In", "Opening Total", "Sales Qty", "Sales Value", "Total Out", "Qty.", "Value"]
        ],
        "merged_cells": ["A1:P1", "A2:P2", "D3:E3", "F3:G3", "H3:I3", "J3:K3"]
    }
    
    # Should throw ValueError if key not set
    schema = detect_schema_via_llm(sample_json)
    assert schema.header_row_index == 3
    assert len(schema.columns) == 12
