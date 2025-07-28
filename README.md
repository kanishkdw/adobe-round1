# Adobe Challenge - PDF Processing System

This repository contains implementations for Adobe's PDF processing challenge with two rounds:

- **Round 1A**: PDF Outline Extraction - Extract hierarchical document outlines from PDF files
- **Round 1B**: Multi-PDF Relevance Extraction - Find relevant sections across multiple PDFs based on persona and job requirements

## 🏗️ Project Structure

```
adobe-round-1a/
├── 📁 round_1a/                    # Round 1A: PDF Outline Extraction
│   ├── 📁 src/
│   │   ├── extractor.py            # Main application logic
│   │   ├── pdf_utils.py            # PDF processing utilities
│   │   └── schema_validator.py     # JSON schema validation
│   ├── 📁 input/                   # Input PDF files
│   ├── 📁 output/                  # Generated outlines
│   ├── Dockerfile                  # Docker configuration
│   └── requirements.txt            # Python dependencies
│
├── 📁 round_1b/                    # Round 1B: Multi-PDF Relevance Extraction
│   ├── 📁 src/
│   │   ├── extractor.py            # Main application logic
│   │   ├── ranker.py               # Section ranking algorithms
│   │   ├── summarizer.py           # Text summarization
│   │   ├── persona_matcher.py      # Persona-job matching
│   │   └── utils.py                # Utility functions
│   ├── 📁 input/                   # Input PDF files and config
│   ├── 📁 output/                  # Generated relevance analysis
│   ├── Dockerfile                  # Docker configuration
│   └── requirements.txt            # Python dependencies
│
└── 📁 shared/                      # Shared utilities
    └── text_extractor.py           # PDF text extraction utilities
```

## 🚀 Quick Start

### Prerequisites

- Docker installed and running
- PDF files for processing

### Round 1A: PDF Outline Extraction

**Purpose**: Extract structured hierarchical outlines from PDF documents with titles and headings (H1, H2, H3).

#### Step 1: Prepare Input Files
Place your PDF files in the `round_1a/input/` directory:
```bash
# Copy your PDF files to the input directory
cp your_documents.pdf round_1a/input/
```

#### Step 2: Build Docker Image
```bash
docker build -t round-1a -f round_1a/Dockerfile .
```

#### Step 3: Run Round 1A
```bash
docker run --rm -v ${PWD}/round_1a/input:/app/input -v ${PWD}/round_1a/output:/app/output --network none round-1a
```

#### Step 4: Check Results
The system will process all PDF files in the input directory and generate individual outline files in `round_1a/output/`:
- `filename_outline.json` for each processed PDF

**Example Output Format**:
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

### Round 1B: Multi-PDF Relevance Extraction

**Purpose**: Analyze multiple PDFs to find the most relevant sections based on a specific persona and job requirements.

#### Step 1: Prepare Input Files
1. **Place PDF files** in `round_1b/input/`:
```bash
cp your_pdfs/*.pdf round_1b/input/
```

2. **Configure persona and job** in `round_1b/input/config.json`:
```json
{
  "persona": "Travel Planner",
  "job": "Plan a trip of 4 days for a group of 10 college friends"
}
```

#### Step 2: Build Docker Image
```bash
docker build -t round-1b -f round_1b/Dockerfile .
```

#### Step 3: Run Round 1B
```bash
docker run --rm -v ${PWD}/round_1b/input:/app/input -v ${PWD}/round_1b/output:/app/output --network none round-1b
```

#### Step 4: Check Results
The system generates `round_1b/output/relevant_sections.json` with:
- Top 5 most relevant sections ranked by importance
- Subsection analysis with refined text
- Metadata including processing timestamp

**Example Output Format**:
```json
{
  "metadata": {
    "input_documents": ["doc1.pdf", "doc2.pdf"],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a trip of 4 days for a group of 10 college friends",
    "processing_timestamp": "2025-07-28T14:43:28.874849"
  },
  "extracted_sections": [
    {
      "document": "doc1.pdf",
      "section_title": "Travel Tips",
      "importance_rank": 1,
      "page_number": 5
    }
  ],
  "subsection_analysis": [
    {
      "document": "doc1.pdf",
      "refined_text": "Essential travel information...",
      "page_number": 5
    }
  ]
}
```

## 🔧 Technical Details

### Round 1A Features
- **Offline processing**: No internet connection required
- **CPU-only**: No GPU dependencies
- **Fast processing**: < 10 seconds for 50-page documents
- **Lightweight**: < 200MB model size
- **Batch processing**: Handles multiple PDF files automatically
- **Smart heading detection**: Uses font size, boldness, position, and hierarchy heuristics
- **Title extraction**: Intelligently identifies document titles vs. headings

### Round 1B Features
- **Multi-document analysis**: Processes 3-10 PDFs simultaneously
- **Hybrid ranking**: Combines TF-IDF, semantic similarity, and composite scoring
- **Persona-job matching**: Context-aware relevance scoring
- **Extractive summarization**: Generates concise summaries of relevant sections
- **Quality filtering**: Removes low-quality or irrelevant content
- **Structured output**: JSON format with metadata and analysis

### Performance Constraints
- **Round 1A**: ≤ 10 seconds for 50 pages, ≤ 200MB model size
- **Round 1B**: ≤ 60 seconds for 10 PDFs, ≤ 1GB model size
- **Offline operation**: No external API calls
- **CPU-only processing**: No GPU requirements

## 🛠️ Troubleshooting

### Common Issues

1. **Docker build fails with "COPY" errors**:
   - Ensure you're running build commands from the project root directory
   - Use the exact Dockerfile paths: `-f round_1a/Dockerfile .` or `-f round_1b/Dockerfile .`

2. **ModuleNotFoundError**:
   - The Docker images are pre-configured with correct Python paths
   - Ensure you're using the latest built images

3. **No PDF files found**:
   - Check that PDF files are in the correct input directories
   - Verify file permissions and naming

4. **Empty outlines or low relevance scores**:
   - Ensure PDFs contain actual text content (not just images)
   - Check that persona and job descriptions are specific and relevant

### Debug Commands

```bash
# Check Docker images
docker images | grep round

# View container logs
docker logs <container_id>

# Inspect input/output directories
ls -la round_1a/input/
ls -la round_1a/output/
ls -la round_1b/input/
ls -la round_1b/output/
```

## 📋 Requirements

### System Requirements
- Docker Desktop or Docker Engine
- 4GB+ RAM recommended
- 2GB+ disk space for Docker images

### Supported PDF Formats
- Text-based PDFs (not scanned images)
- Up to 50 pages per document (Round 1A)
- Up to 10 documents per batch (Round 1B)

## 🎯 Use Cases

### Round 1A Use Cases
- Document structure analysis
- Table of contents generation
- Content organization assessment
- Legal document outline extraction
- Technical manual structure analysis

### Round 1B Use Cases
- Research document analysis
- Travel planning from multiple guides
- Academic literature review
- Business intelligence from reports
- Content recommendation systems

## 📝 License

This project is developed for the Adobe Challenge and follows the challenge specifications and constraints.

---

**Ready to process your PDFs?** Start with Round 1A for document structure analysis, then use Round 1B for multi-document relevance extraction! 