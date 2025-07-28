# Round 1B: Multi-PDF Relevance Extraction

This module extracts the most relevant sections from multiple PDF documents based on a user persona and specific job requirements, then provides ranked results with detailed subsection analysis.

## Features

- **Multi-Document Processing**: Handles 3-10 PDF files simultaneously
- **Persona-Job Matching**: Advanced context analysis for relevance scoring
- **Hybrid Ranking**: Combines TF-IDF, semantic similarity, and positional scoring
- **Extractive Summarization**: Multiple summarization techniques (TextRank, frequency-based, positional)
- **Intelligent Filtering**: Quality-based section filtering with relevance thresholds
- **Structured Output**: JSON format with metadata, ranked sections, and subsection analysis

## Technical Approach

### Document Processing
- **Section Extraction**: Identifies document sections using heading detection
- **Content Normalization**: Cleans and standardizes text content
- **Fallback Handling**: Page-based sections when structure detection fails

### Relevance Scoring
- **TF-IDF Analysis**: Term frequency-inverse document frequency scoring
- **Semantic Similarity**: Keyword overlap and context matching
- **Persona Analysis**: Extracts profession, domain, and specialization characteristics
- **Job Analysis**: Identifies action verbs, requirements, and deliverables
- **Composite Scoring**: Weighted combination of multiple relevance factors

### Ranking and Filtering
- **Hybrid Ranker**: Combines multiple ranking strategies with configurable weights
- **Quality Filters**: Removes low-quality content (headers, page numbers, etc.)
- **Relevance Thresholds**: Configurable minimum relevance scores
- **Top-K Selection**: Returns top 5 most relevant sections

### Summarization
- **TextRank**: Graph-based sentence ranking algorithm
- **Frequency-Based**: Word frequency scoring for sentence selection
- **Positional**: Considers sentence position importance
- **Hybrid Approach**: Combines multiple methods for optimal results

## Libraries Used

- **PyMuPDF**: Primary PDF parsing and text extraction
- **nltk**: Natural language processing utilities
- **scikit-learn**: Machine learning algorithms and utilities
- **numpy**: Numerical computing for scoring algorithms
- **jsonschema**: Output validation

## Usage

### Docker Command
```bash
docker build -t round-1b .
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none round-1b
```

### Input Requirements
- **PDF Files**: Place 3-10 PDF files in `input/` directory
- **Configuration**: One of the following:
  - Environment variables: `PERSONA` and `JOB`
  - Config file: `input/config.json`
  - Individual files: `input/persona.txt` and `input/job.txt`

### Configuration Examples

**Environment Variables:**
```bash
docker run --rm \
  -e PERSONA="Food Contractor" \
  -e JOB="Create a vegetarian dinner buffet plan with gluten-free items" \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none round-1b
```

**Config File (config.json):**
```json
{
  "persona": "Food Contractor",
  "job": "Create a vegetarian dinner buffet plan with gluten-free items"
}
```

### Output Format
```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "Food Contractor",
    "job_to_be_done": "Create a vegetarian dinner buffet plan with gluten-free items",
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
      "refined_text": "Vegetarian menu planning requires careful consideration of protein sources...",
      "page_number": 15
    }
  ]
}
```

## Architecture

```
src/
├── main.py              # Docker entry point
├── extractor.py         # Main extraction pipeline
├── ranker.py           # Section ranking algorithms
├── summarizer.py       # Text summarization techniques
├── persona_matcher.py  # Persona-job context analysis
└── utils.py            # Common utilities and data structures

../shared/
└── text_extractor.py   # Common PDF processing utilities
```

## Performance

- **Speed**: <60 seconds for 10 documents
- **Memory**: Optimized for processing multiple large PDFs
- **Model Size**: <1GB total including all dependencies
- **CPU Only**: No GPU requirements

## Scoring Algorithm

The relevance score is calculated as:

```
score = w1 * tfidf_score + w2 * semantic_score + w3 * composite_score

where:
- tfidf_score: TF-IDF based term matching
- semantic_score: Keyword overlap and context similarity  
- composite_score: Combined content, title, and position scoring
- w1, w2, w3: Configurable weights (default: 0.3, 0.3, 0.4)
```

## Error Handling

- **Missing Configuration**: Falls back to default persona/job for testing
- **No PDFs Found**: Graceful error with clear messaging
- **Parsing Failures**: Individual document failures don't stop processing
- **Low Relevance**: Returns best available sections even if scores are low
- **Empty Sections**: Filters out meaningless content automatically

## Customization

- **Ranking Weights**: Modify weights in `HybridRanker`
- **Filter Thresholds**: Adjust relevance and quality thresholds
- **Summarization**: Choose between different summarization methods
- **Section Limits**: Configure maximum sections returned (default: 5)
- **Persona Patterns**: Extend persona recognition patterns 