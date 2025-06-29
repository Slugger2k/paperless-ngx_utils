# Paperless-ngx Docker Compose System Documentation

This repository contains a Docker Compose configuration for running Paperless-ngx, a document management system that helps you archive, search, and organize your digital documents.

## System Overview

This Docker Compose setup provides a complete Paperless-ngx environment with the following features:

- Document scanning and OCR (Optical Character Recognition)
- Document classification and tagging
- Full-text search
- AI-powered document analysis
- Web-based user interface
- API for automation and integration

## System Architecture

The system consists of the following services:

### Core Services

1. **webserver** - The main Paperless-ngx application
   - Provides the web interface and API
   - Handles document processing and management
   - Runs on port 8000

2. **postgres** - PostgreSQL database
   - Stores document metadata, user data, and system configuration
   - Runs on port 5432 (accessible only from localhost)

3. **broker** - Redis message broker
   - Handles task queuing and background processing
   - Used for communication between components

### Document Processing Services

4. **gotenberg** - PDF processing service
   - Converts various document formats to PDF
   - Handles document rendering

5. **tika** - Apache Tika for document parsing
   - Extracts text and metadata from various file formats
   - Enhances OCR capabilities

### Management and AI Services

6. **phppgadmin** - PostgreSQL administration interface
   - Web-based database management
   - Runs on port 7070

7. **paperless-gpt** - AI-powered document analysis
   - Uses LLMs (Large Language Models) for document understanding
   - Provides enhanced OCR capabilities
   - Runs on port 8081

8. **paperless-ai** - Additional AI capabilities
   - Provides RAG (Retrieval-Augmented Generation) services
   - Runs on port 3000

## Data Flow

1. Documents are placed in the `/share/ZFS19_DATA/Dokumente/import` directory
2. The system automatically processes new documents:
   - Converts documents to PDF if necessary (using Gotenberg)
   - Extracts text and metadata (using Tika)
   - Performs OCR on images and scanned documents
   - Analyzes content using AI services (paperless-gpt and paperless-ai)
3. Processed documents are stored in the media directory
4. Document metadata is stored in the PostgreSQL database
5. Users can access documents through the web interface or API

## Storage Configuration

The system uses the following volume mounts:

- **Redis data**: `/share/ZFS19_DATA/Dokumente/paperless2/redis/data`
- **PostgreSQL data**: `/share/ZFS19_DATA/Dokumente/postgres/data`
- **Application data**: `/share/ZFS19_DATA/Dokumente/paperless2/data`
- **Media files**: `/share/ZFS19_DATA/Dokumente/paperless2/media`
- **Export directory**: `/share/ZFS19_DATA/Dokumente/export`
- **Import directory**: `/share/ZFS19_DATA/Dokumente/import`
- **Scripts**: `/share/ZFS19_DATA/Dokumente/paperless2/scripts`
- **AI data**: 
  - `/share/ZFS19_DATA/Dokumente/paperless2/gpt/prompts`
  - `/share/ZFS19_DATA/Dokumente/paperless2/gpt/hocr`
  - `/share/ZFS19_DATA/Dokumente/paperless2/gpt/pdf`

## Configuration Options

### Main Application (webserver)

Key environment variables:
- `PAPERLESS_OCR_LANGUAGE`: OCR language settings (currently set to German and English)
- `PAPERLESS_PRE_CONSUME_SCRIPT`: Script to run before document processing
- Database configuration:
  - `PAPERLESS_DBHOST`, `PAPERLESS_DBENGINE`, `PAPERLESS_DBNAME`, `PAPERLESS_DBUSER`, `PAPERLESS_DBPASS`
- Integration settings:
  - `PAPERLESS_REDIS`, `PAPERLESS_TIKA_ENABLED`, `PAPERLESS_TIKA_GOTENBERG_ENDPOINT`, `PAPERLESS_TIKA_ENDPOINT`

### AI Services

#### paperless-gpt

- LLM Provider: Currently configured to use Ollama with the llama3.3 model
- OCR Provider: Using LLM-based OCR with the mistral-small3.2 model
- Language: Set to German
- OCR Processing: Image-based processing mode
- PDF Handling: Configured to upload enhanced PDFs to Paperless-ngx

#### paperless-ai

- RAG Service: Enabled for enhanced document retrieval and generation
- Port: Configurable via the `PAPERLESS_AI_PORT` environment variable (default: 3000)

## Setup Instructions

1. Ensure Docker and Docker Compose are installed on your system
2. Clone this repository
3. Configure the required environment variables:
   - Replace `<DB-PASS>` with a secure password for the PostgreSQL database
   - Replace `<PAPERLESS_API_TOKEN>` with your Paperless-ngx API token
4. Create the necessary directories for volume mounts
5. Start the system with:
   ```
   docker-compose up -d
   ```
6. Access the Paperless-ngx web interface at http://localhost:8000
7. Access phpPgAdmin at http://localhost:7070
8. Access paperless-gpt at http://localhost:8081
9. Access paperless-ai at http://localhost:3000

## Maintenance

- Database backups: The PostgreSQL data is stored in `/share/ZFS19_DATA/Dokumente/postgres/data`
- Document backups: All documents are stored in `/share/ZFS19_DATA/Dokumente/paperless2/media`
- Configuration: System scripts are in `/share/ZFS19_DATA/Dokumente/paperless2/scripts`

## Utility Scripts

This repository also includes several utility scripts for managing your Paperless-ngx installation:

- `paperless_remove_duplicated_corespondents.py/.sh`: Remove duplicate correspondents
- `find_duplicate_ocr_content.py`: Find documents with duplicate OCR content
- `delete_correspondets_without_doc.py`: Clean up correspondents without associated documents
