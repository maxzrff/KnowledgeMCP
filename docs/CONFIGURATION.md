# Configuration Guide

Complete guide to configuring the MCP Knowledge Server.

## Overview

The server supports three configuration sources (in priority order):

1. **Environment Variables** (highest priority) - `KNOWLEDGE_<SECTION>__<KEY>`
2. **Custom Config File** - `config.yaml.local`
3. **Default Config** - `config.yaml`

## Configuration Files

### Location

- `config.yaml` - Default configuration (tracked in git)
- `config.yaml.local` - Custom configuration (gitignored)
- `config.yaml.template` - Template for custom config

### Creating Custom Configuration

```bash
# Option 1: Copy default config
cp config.yaml config.yaml.local

# Option 2: Use template
cp config.yaml.template config.yaml.local

# Edit your settings
nano config.yaml.local
```

The server automatically loads `config.yaml.local` if it exists, otherwise falls back to `config.yaml`.

## Configuration Sections

### Storage Configuration

Controls where files and data are stored.

```yaml
storage:
  # Where uploaded documents are stored
  documents_path: ./data/documents
  
  # ChromaDB vector database location
  vector_db_path: ./data/chromadb
  
  # HuggingFace model cache
  model_cache_path: ~/.cache/huggingface
```

**Environment Variables:**
```bash
export KNOWLEDGE_STORAGE__DOCUMENTS_PATH=/custom/docs
export KNOWLEDGE_STORAGE__VECTOR_DB_PATH=/custom/db
export KNOWLEDGE_STORAGE__MODEL_CACHE_PATH=/custom/cache
```

### Embedding Configuration

Controls the embedding model and generation.

```yaml
embedding:
  # Model from HuggingFace
  model_name: sentence-transformers/all-MiniLM-L6-v2
  
  # Batch size for embedding generation
  batch_size: 32
  
  # Device: cpu, cuda, or mps (Apple Silicon)
  device: cpu
```

**Model Options:**

| Model | Dimensions | Speed | Quality | Use Case |
|-------|------------|-------|---------|----------|
| all-MiniLM-L6-v2 | 384 | Fast | Good | Default, balanced |
| all-mpnet-base-v2 | 768 | Medium | Better | Higher quality |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | Medium | Good | Multi-language |

**Performance Tips:**
- Increase `batch_size` for faster processing (needs more RAM)
- Use `device: cuda` if you have an NVIDIA GPU
- Use `device: mps` for Apple Silicon Macs (M1/M2)

**Environment Variables:**
```bash
export KNOWLEDGE_EMBEDDING__MODEL_NAME=all-mpnet-base-v2
export KNOWLEDGE_EMBEDDING__BATCH_SIZE=64
export KNOWLEDGE_EMBEDDING__DEVICE=cuda
```

### Chunking Configuration

Controls how documents are split into chunks.

```yaml
chunking:
  # Target chunk size in characters
  chunk_size: 500
  
  # Overlap between chunks
  chunk_overlap: 50
  
  # Strategy: sentence, paragraph, fixed
  strategy: sentence
```

**Chunking Strategies:**

- **sentence** (recommended): Splits on sentence boundaries, maintains readability
- **paragraph**: Splits on paragraph breaks, larger chunks
- **fixed**: Fixed character length, simple but may break mid-sentence

**Guidelines:**
- **Small chunks (200-300)**: More precise search, more chunks
- **Medium chunks (500-800)**: Balanced, recommended
- **Large chunks (1000+)**: More context, fewer chunks, slower search

**Overlap**: Maintains context across chunk boundaries
- Recommended: 10-20% of chunk size
- Too small: May lose context
- Too large: Redundant data

**Environment Variables:**
```bash
export KNOWLEDGE_CHUNKING__CHUNK_SIZE=800
export KNOWLEDGE_CHUNKING__CHUNK_OVERLAP=80
export KNOWLEDGE_CHUNKING__STRATEGY=paragraph
```

### Processing Configuration

Controls document processing behavior.

```yaml
processing:
  # Maximum concurrent processing tasks
  max_concurrent_tasks: 3
  
  # OCR confidence threshold (0.0-1.0)
  ocr_confidence_threshold: 0.6
  
  # Maximum file size in MB
  max_file_size_mb: 100
```

**Performance Tips:**
- Set `max_concurrent_tasks` to your CPU core count
- Increase `max_file_size_mb` for large documents
- Lower `ocr_confidence_threshold` if OCR quality is poor

**Environment Variables:**
```bash
export KNOWLEDGE_PROCESSING__MAX_CONCURRENT_TASKS=8
export KNOWLEDGE_PROCESSING__MAX_FILE_SIZE_MB=500
```

### Logging Configuration

Controls logging behavior.

```yaml
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: INFO
  
  # Log format: text or json
  format: text
  
  # Optional log file path
  # file: ./mcp_server.log
  
  # Enable debug mode
  debug: false
```

**Log Levels:**
- **DEBUG**: Verbose, shows everything
- **INFO**: Normal operation (recommended)
- **WARNING**: Only warnings and errors
- **ERROR**: Only errors
- **CRITICAL**: Only critical errors

**Environment Variables:**
```bash
export KNOWLEDGE_LOGGING__LEVEL=DEBUG
export KNOWLEDGE_LOGGING__FORMAT=json
```

### Search Configuration

Controls search behavior.

```yaml
search:
  # Default number of results
  default_top_k: 10
  
  # Maximum allowed results
  max_top_k: 50
  
  # Default minimum relevance (0.0-1.0)
  default_min_relevance: 0.0
  
  # Enable result highlighting
  enable_highlighting: true
```

**Environment Variables:**
```bash
export KNOWLEDGE_SEARCH__DEFAULT_TOP_K=20
export KNOWLEDGE_SEARCH__MAX_TOP_K=100
```

### Performance Configuration

Controls caching and optimization.

```yaml
performance:
  # Cache embeddings for faster queries
  cache_embeddings: true
  
  # Number of embeddings to cache
  cache_size: 1000
  
  # Load models on demand
  lazy_load_models: true
  
  # Database connection pool size
  db_pool_size: 5
```

**Environment Variables:**
```bash
export KNOWLEDGE_PERFORMANCE__CACHE_SIZE=5000
export KNOWLEDGE_PERFORMANCE__DB_POOL_SIZE=10
```

### Feature Flags

Enable or disable features.

```yaml
features:
  enable_ocr: true                # OCR for scanned documents
  enable_image_analysis: false    # Image analysis (experimental)
  enable_async: true              # Async processing
  enable_progress: true           # Progress tracking
  enable_metadata: true           # Metadata extraction
```

**Environment Variables:**
```bash
export KNOWLEDGE_FEATURES__ENABLE_OCR=false
export KNOWLEDGE_FEATURES__ENABLE_ASYNC=true
```

## Environment Variables Reference

Format: `KNOWLEDGE_<SECTION>__<KEY>=value`

**Examples:**

```bash
# Storage
export KNOWLEDGE_STORAGE__DOCUMENTS_PATH=/data/docs
export KNOWLEDGE_STORAGE__VECTOR_DB_PATH=/data/chromadb

# Embedding
export KNOWLEDGE_EMBEDDING__MODEL_NAME=all-mpnet-base-v2
export KNOWLEDGE_EMBEDDING__BATCH_SIZE=64
export KNOWLEDGE_EMBEDDING__DEVICE=cuda

# Chunking
export KNOWLEDGE_CHUNKING__CHUNK_SIZE=800
export KNOWLEDGE_CHUNKING__CHUNK_OVERLAP=80

# Processing
export KNOWLEDGE_PROCESSING__MAX_CONCURRENT_TASKS=8
export KNOWLEDGE_PROCESSING__MAX_FILE_SIZE_MB=500

# Logging
export KNOWLEDGE_LOGGING__LEVEL=DEBUG
export KNOWLEDGE_LOGGING__FORMAT=json

# Search
export KNOWLEDGE_SEARCH__DEFAULT_TOP_K=20
export KNOWLEDGE_SEARCH__MAX_TOP_K=100
```

## Common Configurations

### Development Setup

```yaml
logging:
  level: DEBUG
  debug: true

development:
  debug_mode: true
  hot_reload: true
  profiling: true
```

Or:
```bash
export KNOWLEDGE_LOGGING__LEVEL=DEBUG
export KNOWLEDGE_DEVELOPMENT__DEBUG_MODE=true
```

### Production Setup

```yaml
logging:
  level: INFO
  format: json
  file: /var/log/knowledge-mcp/server.log

performance:
  cache_embeddings: true
  cache_size: 5000
  db_pool_size: 10

processing:
  max_concurrent_tasks: 8
```

### High-Performance Setup

```yaml
embedding:
  batch_size: 128
  device: cuda

chunking:
  chunk_size: 1000
  chunk_overlap: 100

processing:
  max_concurrent_tasks: 16

performance:
  cache_embeddings: true
  cache_size: 10000
  db_pool_size: 20
```

### Low-Resource Setup

```yaml
embedding:
  batch_size: 8
  device: cpu

chunking:
  chunk_size: 300
  chunk_overlap: 30

processing:
  max_concurrent_tasks: 1
  max_file_size_mb: 50

performance:
  cache_embeddings: false
  lazy_load_models: true
```

## Validation

Check your configuration:

```bash
# Verify syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Test configuration loading
python -c "from src.config.settings import get_settings; print(get_settings())"
```

## Troubleshooting

### Configuration not loading

```bash
# Check file exists
ls -la config.yaml config.yaml.local

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check permissions
chmod 644 config.yaml
```

### Environment variables not working

```bash
# Check variable is set
echo $KNOWLEDGE_STORAGE__DOCUMENTS_PATH

# Export in current session
export KNOWLEDGE_STORAGE__DOCUMENTS_PATH=/custom/path

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export KNOWLEDGE_STORAGE__DOCUMENTS_PATH=/custom/path' >> ~/.bashrc
```

### Performance issues

```bash
# Increase batch size
export KNOWLEDGE_EMBEDDING__BATCH_SIZE=64

# Use GPU if available
export KNOWLEDGE_EMBEDDING__DEVICE=cuda

# Increase concurrent tasks
export KNOWLEDGE_PROCESSING__MAX_CONCURRENT_TASKS=8
```

## Best Practices

1. **Use custom config file for local changes**
   - Don't edit `config.yaml` directly
   - Use `config.yaml.local` for customization

2. **Use environment variables for secrets**
   - API keys, passwords, etc.
   - Never commit secrets to config files

3. **Start with defaults**
   - Default configuration works well for most cases
   - Adjust only what you need

4. **Test configuration changes**
   - Restart server after config changes
   - Check logs for errors
   - Verify with status command

5. **Document custom settings**
   - Add comments in config file
   - Keep track of why you changed settings

## See Also

- [README.md](../README.md) - Main documentation
- [SERVER_MANAGEMENT.md](SERVER_MANAGEMENT.md) - Server management
- [src/config/settings.py](../src/config/settings.py) - Configuration implementation
