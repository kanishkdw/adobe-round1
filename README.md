# Adobe Challenge: PDF Processing Solutions

This repository contains comprehensive solutions for both Round 1A (PDF Outline Extraction) and Round 1B (Multi-PDF Relevance Extraction) of the Adobe coding challenge.

## Project Structure

```
adobe_challenge/
├── round_1a/                    # PDF Outline Extraction
│   ├── src/
│   │   ├── extractor.py        # Main extraction pipeline
│   │   ├── pdf_utils.py        # Heading detection and classification
│   │   ├── schema_validator.py # JSON schema validation
│   │   └── main.py            # Docker entry point
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── round_1b/                    # Multi-PDF Relevance Extraction
│   ├── src/
│   │   ├── extractor.py        # Main processing pipeline
│   │   ├── ranker.py           # Section ranking algorithms
│   │   ├── summarizer.py       # Text summarization
│   │   ├── persona_matcher.py  # Context analysis
│   │   ├── utils.py            # Common utilities
│   │   └── main.py            # Docker entry point
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── approach_explanation.md
│   └── README.md
│
└── shared/
    └── text_extractor.py       # Common PDF processing utilities
```

## Round 1A: PDF Outline Extraction

### Overview
Extracts structured, hierarchical outlines from PDF files with document titles and heading levels (H1, H2, H3).

### Key Features
- **Fast Processing**: <10 seconds for 50-page documents
- **Layout-Aware**: Uses font size, boldness, and position heuristics
- **Hierarchical Detection**: Automatically classifies headings into H1, H2, H3 levels
- **Schema Validation**: Ensures output matches required JSON structure
- **Offline Processing**: Works completely offline without network access

### Usage
```bash
cd round_1a
docker build -t round-1a .
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none round-1a
```

**Input**: Place PDF file in `input/` directory  
**Output**: JSON file saved to `output/outline.json`

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

## Round 1B: Multi-PDF Relevance Extraction

### Overview
Extracts the most relevant sections from multiple PDF documents based on a user persona and specific job requirements.

### Key Features
- **Multi-Document Processing**: Handles 3-10 PDF files simultaneously
- **Persona-Job Matching**: Advanced context analysis for relevance scoring
- **Hybrid Ranking**: Combines TF-IDF, semantic similarity, and positional scoring
- **Extractive Summarization**: Multiple summarization techniques
- **Structured Output**: JSON format with metadata and ranked sections

### Usage
```bash
cd round_1b
docker build -t round-1b .

# Using environment variables
docker run --rm \
  -e PERSONA="Food Contractor" \
  -e JOB="Create a vegetarian dinner buffet plan with gluten-free items" \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none round-1b
```

**Input**: 
- PDF files in `input/` directory
- Configuration via environment variables, config.json, or individual text files

**Output**: JSON file saved to `output/relevant_sections.json`

### Output Format
```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "Food Contractor",
    "job_to_be_done": "Create a vegetarian dinner buffet plan",
    "processing_timestamp": "2023-12-07T10:30:00"
  },
  "extracted_sections": [
    {
      "document": "catering_guide.pdf",
      "section_title": "Vegetarian Menu Planning",
      "importance_rank": 1,
      "page_number": 15
    }
  ],
  "subsection_analysis": [
    {
      "document": "catering_guide.pdf",
      "refined_text": "Menu planning summary...",
      "page_number": 15
    }
  ]
}
```

## Technical Architecture

### Shared Components
- **`shared/text_extractor.py`**: Common PDF processing utilities using PyMuPDF
- Provides text extraction, heading detection, and document analysis functions
- Used by both rounds for consistent PDF handling

### Round 1A Architecture
- **Heading Detection**: Font size and formatting analysis
- **Hierarchy Classification**: Smart level assignment with validation
- **Schema Validation**: Strict JSON structure compliance

### Round 1B Architecture
- **Document Processing**: Section extraction and content normalization
- **Relevance Scoring**: Multi-factor ranking with TF-IDF, semantic similarity
- **Persona Analysis**: Professional context and requirement extraction
- **Summarization**: TextRank, frequency-based, and positional methods

## Performance Specifications

### Round 1A
- **Speed**: <10 seconds for 50-page documents
- **Model Size**: No models >200MB
- **CPU Only**: No GPU requirements
- **Memory**: Optimized for minimal usage

### Round 1B  
- **Speed**: <60 seconds for 10 documents
- **Model Size**: <1GB total including dependencies
- **CPU Only**: No GPU requirements
- **Memory**: Handles multiple large PDFs efficiently

## Dependencies

### Round 1A
- PyMuPDF (PDF processing)
- jsonschema (validation)
- pdfplumber (fallback processing)

### Round 1B
- PyMuPDF (PDF processing)
- nltk (NLP utilities)
- scikit-learn (ML algorithms)
- numpy (numerical computing)
- jsonschema (validation)

## Development Approach

### Design Principles
1. **Modularity**: Clear separation of concerns with focused modules
2. **Reusability**: Shared components for common functionality
3. **Robustness**: Graceful error handling and fallback mechanisms
4. **Performance**: Optimized for speed and memory efficiency
5. **Maintainability**: Clean code with comprehensive documentation

### Quality Assurance
- **Schema Validation**: Strict output format compliance
- **Error Handling**: Comprehensive error catching and logging
- **Performance Monitoring**: Built-in timing and progress tracking
- **Content Quality**: Filtering of low-quality or irrelevant content

## Testing and Validation

### Round 1A Testing
1. Place test PDF in `round_1a/input/`
2. Run Docker command
3. Verify `round_1a/output/outline.json` format and content

### Round 1B Testing
1. Place multiple PDFs in `round_1b/input/`
2. Create configuration (environment variables or config files)
3. Run Docker command
4. Verify `round_1b/output/relevant_sections.json` format and relevance

## Future Enhancements

### Potential Improvements
- **Advanced NLP**: Transformer models for better semantic understanding
- **Visual Elements**: Process images, tables, and charts
- **Multi-language**: Support for non-English documents
- **Real-time Processing**: Stream processing capabilities
- **API Interface**: REST API for programmatic access

### Scalability Features
- **Distributed Processing**: Handle larger document collections
- **Database Integration**: Persistent storage and indexing
- **Caching**: Improved performance for repeat processing
- **Batch Processing**: Handle multiple jobs simultaneously

This implementation provides a solid foundation for PDF processing tasks while maintaining flexibility for future enhancements and different use cases. 