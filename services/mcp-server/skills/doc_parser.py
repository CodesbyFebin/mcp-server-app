"""Document parser bridge for PDF/image OCR and structured parameter extraction.

Provides document parsing capabilities for the MCP system, enabling
OCR of PDFs/images, legal compliance checks, and structured parameter
extraction from legal/technical documents.
"""

import json
import time
from typing import Dict, Any, List, Optional, Literal


class DocumentParserBridge:
    """Bridge for document OCR, parsing, and structured extraction."""
    
    def __init__(self,
                 supported_formats: List[str] | None = None,
                 ocr_engine: Literal["tesseract", "paddle", "easyocr"] | None = None,
                 language: str = "en",
                 compliance_checks: bool = True):
        self.supported_formats = supported_formats or ["pdf", "jpg", "jpeg", "png", "tiff"]
        self.ocr_engine = ocr_engine or "tesseract"
        self.language = language
        self.compliance_checks = compliance_checks
        self._initialized = False
    
    def parse(self, 
             document_path: str,
             extract_fields: List[str] | None = None) -> Dict[str, Any]:
        """Parse a document and extract structured data.
        
        Args:
            path to the document file
            optional list of fields to extract (e.g., ["pan", "gstin", "date", "amount"])
            
        Returns:
            Dictionary with parsed data, metadata, and compliance status
        """
        if not self._initialized:
            self._initialize()
        
        start_time = time.time()
        
        # Validate format
        format_result = self._validate_format(document_path)
        if not format_result["valid"]:
            return format_result
        
        # Perform parsing
        parse_result = self._perform_parse(document_path, extract_fields)
        
        # Apply compliance checks if enabled
        compliance_result = {}
        if self.compliance_checks:
            compliance_result = self._apply_compliance_checks(parse_result)
        
        duration = time.time() - start_time
        
        return {
            "document_path": document_path,
            "format": format_result.get("format"),
            "parsed_data": parse_result,
            "compliance": compliance_result,
            "ocr_engine": self.ocr_engine,
            "language": self.language,
            "parse_duration_ms": round(duration * 1000),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    
    def _validate_format(self, document_path: str) -> Dict[str, Any]:
        """Validate document format and extract format info."""
        ext = document_path.rsplit(".", 1)[-1].lower() if "." in document_path else ""
        
        if ext in self.supported_formats:
            return {
                "valid": True,
                "format": ext,
                "file_path": document_path
            }
        
        return {
            "valid": False,
            "errors": [f"Unsupported format: {ext}. Supported: {', '.join(self.supported_formats)}"],
            "format": None,
            "file_path": document_path
        }
    
    def _perform_parse(self, document_path: str, extract_fields: List[str] | None) -> Dict[str, Any]:
        """Perform the actual document parsing. Meant to be overridden with real OCR."""
        # Mock parsed data structure
        mock_data = {
            "pan": None,
            "gstin": None,
            "date": None,
            "amount": None,
            "vendor": None,
            "total_text": "Mock OCR text from document",
            "confidence": 0.85
        }
        
        if extract_fields:
            # Only return requested fields
            result = {field: mock_data.get(field) for field in extract_fields}
            return result
        
        return mock_data
    
    def _apply_compliance_checks(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Apply compliance and PII redaction to parsed results."""
        compliance = {
            "compliant": True,
            "pii_masked": [],
            "redactions": [],
            "warnings": []
        }
        
        # Mask sensitive data patterns
        import re
        
        # PAN pattern: ABCDE1234F
        if parsed.get("pan"):
            masked = re.sub(r"([A-Z]{3})[A-Z]", r"\1****", parsed["pan"])
            compliance["pii_masked"].append("pan")
            compliance["redactions"].append(f"PAN masked: {parsed['pan']} -> {masked}")
        
        # GSTIN pattern: 15 chars
        if parsed.get("gstin"):
            masked = re.sub(r"([0-9]{2}[A-Z]{5})[0-9]{4}", r"\1****", parsed["gstin"])
            compliance["pii_masked"].append("gstin")
            compliance["redactions"].append(f"GSTIN masked: {parsed['gstin']} -> {masked}")
        
        # Email pattern
        if parsed.get("email") and "@" in str(parsed["email"]):
            parts = str(parsed["email"]).split("@")
            if len(parts) == 2 and len(parts[0]) > 2:
                masked = parts[0][:2] + "****" + "@" + parts[1]
                compliance["pii_masked"].append("email")
                compliance["redactions"].append(f"Email masked: {parsed['email']} -> {masked}")
        
        # Check for unmasked PII warnings
        for key, value in parsed.items():
            if isinstance(value, str) and len(value) > 8:
                # Simple heuristic for potential PII
                compliance["warnings"].append(f"Long value in {key}: {value[:20]}...")
        
        compliance["compliant"] = len(compliance["pii_masked"]) > 0 or not any(
            k in ["pan", "gstin", "email"] for k in parsed.keys()
        )
        
        return compliance
    
    def extract_structured_params(self, 
                                  document_text: str,
                                  param_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured parameters from document text using a schema.
        
        Args:
            raw text from document
            schema defining expected parameters with types and patterns
            
        Returns:
            Dictionary of extracted and typed parameters
        """
        result: Dict[str, Any] = {
            "extracted": {},
            "excluded": [],
            "pattern_matches": [],
            "compliance": {"pii_masked": [], "redactions": []}
        }
        
        # Process each schema field
        for param_name, param_config in param_schema.items():
            pattern = param_config.get("pattern")
            param_type = param_config.get("type", "string")
            
            if pattern and isinstance(document_text, str):
                match = re.search(pattern, document_text, re.IGNORECASE)
                if match:
                    value = match.group(0)
                    result["extracted"][param_name] = self._cast_type(value, param_type)
                    result["pattern_matches"].append({
                        "parameter": param_name,
                        "pattern": pattern,
                        "matched_value": value
                    })
                    
                    # Apply PII masking for known sensitive fields
                    if param_name.lower() in ["pan", "gstin", "account_number", "ssn"]:
                        masked = self._mask_sensitive(value, param_name.lower())
                        result["compliance"]["pii_masked"].append(param_name)
                        result["compliance"]["redactions"].append(f"{param_name}: {value} -> {masked}")
        
        return result
    
    def _cast_type(self, value: str, param_type: str) -> Any:
        """Cast a string value to the expected type."""
        if param_type == "integer":
            try:
                return int(value)
            except (ValueError, TypeError):
                return value
        elif param_type == "float" or param_type == "number":
            try:
                return float(value)
            except (ValueError, TypeError):
                return value
        elif param_type == "boolean":
            if value.lower() in ("true", "1", "yes"):
                return True
            if value.lower() in ("false", "0", "no"):
                return False
        return value
    
    def _mask_sensitive(self, value: str, field: str) -> str:
        """Mask sensitive field values."""
        import re
        
        if field == "pan":
            # ABCDE1234F -> AB**E1234F or similar
            return re.sub(r"([A-Z]{2})[A-Z]([A-Z])(\d{4})([A-Z])", r"\1****\3\4", value)
        elif field == "gstin":
            # 07AAAAA1234Z9 -> 07AAAAA*****9
            return re.sub(r"([0-9]{2}[A-Z]{5})[0-9]{4}", r"\1****", value)
        elif field == "account_number":
            # Last 4 digits visible
            return re.sub(r"(\d{4})$", r"****\1", value)
        elif field == "ssn":
            # XXX-XX-1234
            return re.sub(r"\d{3}-\d{2}-\d{4}", r"XXX-XX-1234", value)
        
        return value
    
    def _initialize(self):
        """Initialize the document parser bridge."""
        self._initialized = True


# Convenience function for quick parsing
def quick_parse(document_path: str, fields: List[str] | None = None) -> Dict[str, Any]:
    """Quick document parse with default settings."""
    bridge = DocumentParserBridge()
    return bridge.parse(document_path, fields)


# Example usage
if __name__ == "__main__":
    import sys
    
    print("=== Document Parser Bridge ===")
    if len(sys.argv) > 1:
        doc_path = sys.argv[1]
        result = quick_parse(doc_path, ["pan", "gstin", "date"])
        print(f"Document: {result['document_path']}")
        print(f"Format: {result['format']}")
        print(f"Parsed data: {json.dumps(result['parsed_data'], indent=2)}")
        print(f"Compliance: {json.dumps(result['compliance'], indent=2)}")
        print(f"Duration: {result['parse_duration_ms']}ms")
    else:
        # Demo with mock text
        import json
        demo_text = "PAN: ABCDE1234F, GSTIN: 07AAAAA1234Z9, Date: 2024-01-15, Amount: ₹50000"
        schema = {
            "pan": {"type": "string", "pattern": r"[A-Z]{5}\d{4}[A-Z]"},
            "gstin": {"type": "string", "pattern": r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}"},
            "date": {"type": "string", "pattern": r"\d{4}-\d{2}-\d{2}"},
            "amount": {"type": "float", "pattern": r"₹?\s?[\d,]+"}
        }
        result = quick_parse.__wrapped__.__call__(DocumentParserBridge, 
                                                   "",  # placeholder
                                                   schema) if hasattr(quick_parse, '__wrapped__') else {}
        
        # Demo extraction
        bridge = DocumentParserBridge()
        extracted = bridge.extract_structured_params(demo_text, schema)
        print(f"\nExtracted parameters: {json.dumps(extracted['extracted'], indent=2)}")
        print(f"Pattern matches: {len(extracted['pattern_matches'])}")
        print(f"Compliance: {json.dumps(extracted['compliance'], indent=2)}")