"""
JSON schema validation for Round 1A output.
Ensures the extracted outline matches the required format.
"""

import json
import jsonschema
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# JSON Schema for Round 1A output
OUTLINE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "minLength": 1
        },
        "outline": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "enum": ["H1", "H2", "H3"]
                    },
                    "text": {
                        "type": "string",
                        "minLength": 1
                    },
                    "page": {
                        "type": "integer",
                        "minimum": 1
                    }
                },
                "required": ["level", "text", "page"],
                "additionalProperties": False
            }
        }
    },
    "required": ["title", "outline"],
    "additionalProperties": False
}

class OutlineValidator:
    """Validates the outline extraction results against the required schema."""
    
    def __init__(self):
        self.schema = OUTLINE_SCHEMA
        
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate the outline data against the schema.
        
        Args:
            data: The outline data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            jsonschema.validate(data, self.schema)
            logger.info("Schema validation passed")
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"Schema validation failed: {e.message}")
            return False
        except jsonschema.SchemaError as e:
            logger.error(f"Schema error: {e.message}")
            return False
            
    def validate_and_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean the outline data.
        
        Args:
            data: The outline data to validate and clean
            
        Returns:
            Dict: Cleaned data if valid, None if invalid
        """
        if not self.validate(data):
            return None
            
        # Clean up the data
        cleaned = {
            "title": str(data["title"]).strip(),
            "outline": []
        }
        
        for item in data["outline"]:
            cleaned_item = {
                "level": str(item["level"]).upper(),
                "text": str(item["text"]).strip(),
                "page": int(item["page"])
            }
            cleaned["outline"].append(cleaned_item)
            
        return cleaned
        
    def validate_heading_hierarchy(self, outline: List[Dict[str, Any]]) -> bool:
        """
        Validate that the heading hierarchy makes logical sense.
        
        Args:
            outline: List of heading items
            
        Returns:
            bool: True if hierarchy is valid
        """
        if not outline:
            return True
            
        level_order = {"H1": 1, "H2": 2, "H3": 3}
        prev_level = 0
        
        for item in outline:
            current_level = level_order[item["level"]]
            
            # First item can be any level
            if prev_level == 0:
                prev_level = current_level
                continue
                
            # Level can stay same, go down one level, or jump to any higher level
            if current_level > prev_level + 1:
                logger.warning(f"Heading hierarchy jump from {prev_level} to {current_level}")
                # Allow it but warn - some documents have inconsistent hierarchies
                
            prev_level = current_level
            
        return True
        
    def get_validation_errors(self, data: Dict[str, Any]) -> List[str]:
        """
        Get detailed validation errors.
        
        Args:
            data: The data to validate
            
        Returns:
            List[str]: List of validation error messages
        """
        errors = []
        
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation: {e.message}")
            
        # Additional semantic validation
        if "outline" in data and isinstance(data["outline"], list):
            if not self.validate_heading_hierarchy(data["outline"]):
                errors.append("Invalid heading hierarchy")
                
            # Check for duplicate headings on same page
            seen = set()
            for item in data["outline"]:
                if isinstance(item, dict) and "text" in item and "page" in item:
                    key = (item["text"], item["page"])
                    if key in seen:
                        errors.append(f"Duplicate heading '{item['text']}' on page {item['page']}")
                    seen.add(key)
                    
        return errors 