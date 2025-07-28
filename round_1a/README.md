# Round 1A: PDF Outline Extraction

This module extracts structured, hierarchical outlines from PDF files with document titles and heading levels (H1, H2, H3).

## Features

- **Offline Processing**: Works completely offline without network access
- **Fast Performance**: Processes up to 50 pages in under 10 seconds
- **Hierarchical Detection**: Automatically classifies headings into H1, H2, H3 levels
- **Layout-Aware**: Uses font size, boldness, and position heuristics
- **Schema Validation**: Ensures output matches the required JSON structure
- **Robust Parsing**: Handles various PDF layouts and formats

## Technical Approach

### Heading Detection
- **Font Analysis**: Uses font size ratios and boldness to identify headings
- **Position Heuristics**: Considers text positioning and layout
- **Pattern Recognition**: Detects numbered sections (1., 1.1, 1.1.1), chapters, etc.
- **Hierarchy Validation**: Ensures logical heading structure

### Libraries Used
- **PyMuPDF**: Primary PDF parsing and text extraction
- **jsonschema**: Output validation
- **pdfplumber**: Fallback PDF processing

## Usage

### Docker Command
```bash
docker build -t round-1a .
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none round-1a
```

### Input/Output
- **Input**: Place PDF file in `input/` directory
- **Output**: JSON file saved to `output/outline.json`

### Output Format
```json
{
  "title": "Document Title",
  "outline": [
    { "level": "H1", "text": "Main Heading", "page": 1 },
    { "level": "H2", "text": "Subsection", "page": 2 },
    { "level": "H3", "text": "Sub-subsection", "page": 3 }
  ]
}
```

## Architecture

```
src/
├── main.py              # Docker entry point
├── extractor.py         # Main extraction pipeline
├── pdf_utils.py         # Heading detection and classification
└── schema_validator.py  # JSON schema validation

../shared/
└── text_extractor.py    # Common PDF processing utilities
```

## Performance

- **Speed**: <10 seconds for 50-page documents
- **Memory**: Optimized for minimal memory usage
- **Model Size**: No ML models >200MB
- **CPU Only**: Works without GPU acceleration

## Error Handling

- Validates PDF file existence and readability
- Handles malformed PDFs gracefully
- Provides detailed logging for debugging
- Returns structured error messages

## Validation

- **Schema Compliance**: Strict JSON schema validation
- **Hierarchy Logic**: Ensures proper heading level progression
- **Data Integrity**: Validates page numbers and text content
- **Duplicate Detection**: Identifies and handles duplicate headings 