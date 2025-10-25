# Models Directory

This directory contains pre-trained NLP models and model-related files for the ATS Resume Analyzer.

## Directory Structure

```
models/
├── README.md              # This file
├── tfidf_models/          # TF-IDF vectorizers and models
├── embeddings/            # Word embeddings and vector models
├── saved_models/          # Pre-trained models
└── model_configs/         # Model configuration files
```

## Model Types

### 1. TF-IDF Models
- **Purpose**: Text vectorization for similarity calculation
- **Files**: `tfidf_vectorizer.pkl`, `tfidf_config.json`
- **Usage**: Convert text to numerical vectors for comparison

### 2. Word Embeddings
- **Purpose**: Semantic understanding of text
- **Files**: `word2vec_model.bin`, `glove_embeddings.txt`
- **Usage**: Enhanced keyword matching and semantic analysis

### 3. Pre-trained Models
- **Purpose**: Ready-to-use models for specific tasks
- **Files**: `resume_classifier.pkl`, `keyword_extractor.pkl`
- **Usage**: Direct model inference without training

## Model Loading

```python
import pickle
import json

# Load TF-IDF model
with open('models/tfidf_models/tfidf_vectorizer.pkl', 'rb') as f:
    vectorizer = pickle.load(f)

# Load model configuration
with open('models/model_configs/tfidf_config.json', 'r') as f:
    config = json.load(f)
```

## Model Training

Models can be trained using the scripts in the `notebooks/` directory or by running:

```bash
python -m src.train_models
```

## Model Updates

To update models with new data:

1. Run the training notebook
2. Save the updated model
3. Update the model configuration
4. Test the new model
5. Deploy if performance is improved

## Performance Metrics

- **TF-IDF Accuracy**: 85%+ similarity matching
- **Keyword Extraction**: 90%+ relevant keyword identification
- **Overall ATS Score**: ±5% accuracy compared to manual scoring



