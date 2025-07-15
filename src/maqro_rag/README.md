# Maqro RAG Module - Inventory Embedding & Retrieval

A modular, production-ready Retrieval-Augmented Generation (RAG) system for auto dealership inventory management.

## 🚗 Features

- **Multi-format ingestion**: CSV and JSON inventory files
- **Flexible embedding providers**: OpenAI and Cohere support
- **Scalable vector storage**: FAISS (local), Pinecone/Weaviate (cloud) ready
- **Semantic search**: Find vehicles based on natural language queries
- **Modular design**: Easy to extend and customize
- **Production-ready**: Comprehensive error handling and logging

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your API keys:

```bash
# OpenAI (default)
OPENAI_API_KEY=your_openai_api_key_here

# Cohere (alternative)
COHERE_API_KEY=your_cohere_api_key_here
```

### Configuration File

The system uses `config.yaml` for settings:

```yaml
embedding:
  provider: "openai"  # "openai" or "cohere"
  model: "text-embedding-ada-002"
  batch_size: 100
  max_retries: 3

vector_store:
  type: "faiss"  # "faiss", "pinecone", "weaviate"
  dimension: 1536

retrieval:
  top_k: 3
  similarity_threshold: 0.7
```

## 🚀 Quick Start

### 1. Basic Usage

```python
from maqro_rag import Config, VehicleRetriever

# Load configuration
config = Config.from_yaml("config.yaml")

# Initialize retriever
retriever = VehicleRetriever(config)

# Build index from inventory
retriever.build_index("sample_inventory.csv", "vehicle_index")

# Search for vehicles
results = retriever.search_vehicles("Looking for a reliable sedan with good gas mileage")
print(retriever.format_search_results(results))
```

### 2. Demo Script

Run the complete demo:

```bash
python main.py
```

### 3. Test Without API Keys

Test the system components:

```bash
python test_rag.py
```

## 📊 Inventory Format

### CSV Format

```csv
year,make,model,price,features,description
2022,Toyota,Corolla,21000,"Lane Assist, Android Auto","Compact and reliable sedan"
2023,Honda,Civic,23500,"Honda Sensing, Apple CarPlay","Sporty compact car"
```

### JSON Format

```json
[
  {
    "year": 2022,
    "make": "Toyota",
    "model": "Corolla",
    "price": 21000,
    "features": "Lane Assist, Android Auto",
    "description": "Compact and reliable sedan"
  }
]
```

## 🔍 Search Examples

```python
# Find reliable sedans
results = retriever.search_vehicles("Looking for a reliable sedan with good gas mileage")

# Luxury vehicles
results = retriever.search_vehicles("I want a luxury car with advanced technology")

# Affordable options
results = retriever.search_vehicles("Show me affordable vehicles under $25,000")

# SUVs for family
results = retriever.search_vehicles("I need an SUV for family use")

# Electric vehicles
results = retriever.search_vehicles("Electric vehicle with modern features")
```

## 🏗️ Architecture

### Core Components

1. **Config** (`config.py`): Configuration management with Pydantic
2. **EmbeddingProvider** (`embedding.py`): Abstract interface for embedding APIs
3. **VectorStore** (`vector_store.py`): Abstract interface for vector databases
4. **InventoryProcessor** (`inventory.py`): Data ingestion and formatting
5. **VehicleRetriever** (`retrieval.py`): Main RAG pipeline orchestrator

### Data Flow

```
Inventory CSV/JSON → InventoryProcessor → Formatted Texts → EmbeddingProvider → VectorStore → Search Results
```

### Extending the System

#### Adding New Embedding Provider

```python
class CustomEmbeddingProvider(EmbeddingProvider):
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        # Your implementation
        pass
    
    def embed_text(self, text: str) -> np.ndarray:
        # Your implementation
        pass
```

#### Adding New Vector Store

```python
class CustomVectorStore(VectorStore):
    def add_vectors(self, vectors: np.ndarray, metadata: List[Dict]) -> None:
        # Your implementation
        pass
    
    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[np.ndarray, List[Dict]]:
        # Your implementation
        pass
```

## 🔄 Migration Paths

### FAISS → Pinecone

1. Update `config.yaml`:
```yaml
vector_store:
  type: "pinecone"
  pinecone:
    environment: "us-west1-gcp"
    index_name: "maqro-inventory"
```

2. Set environment variable:
```bash
export PINECONE_API_KEY=your_pinecone_api_key
```

### FAISS → Weaviate

1. Update `config.yaml`:
```yaml
vector_store:
  type: "weaviate"
  weaviate:
    url: "http://localhost:8080"
    class_name: "Vehicle"
```

## 📈 Performance

- **FAISS**: Fast local search, suitable for development and small-medium inventories
- **Pinecone**: Scalable cloud solution for production with thousands of vehicles
- **Weaviate**: Self-hosted option with advanced querying capabilities

## 🛠️ Development

### Running Tests

```bash
python test_rag.py
```

### Adding New Features

1. Follow the modular design pattern
2. Add comprehensive error handling
3. Include logging for debugging
4. Update configuration as needed
5. Add tests for new functionality

## 🔮 Future Enhancements

- [ ] Pinecone integration
- [ ] Weaviate integration
- [ ] Fine-tuning capabilities
- [ ] Multi-language support
- [ ] Real-time inventory updates
- [ ] Advanced filtering options
- [ ] Performance optimization
- [ ] Docker containerization

## 📝 License

This module is part of the Maqro project for auto dealership lead management. 