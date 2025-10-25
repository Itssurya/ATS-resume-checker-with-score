"""
Model Manager for ATS Resume Analyzer

This module handles saving, loading, and managing ML models for the ATS system.
It provides model persistence, versioning, and efficient model loading.
"""

import os
import pickle
import joblib
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import nltk
from nltk.corpus import stopwords

# Ensure NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class ModelManager:
    """
    Manages ML models for the ATS Resume Analyzer.
    
    Features:
    - Model persistence and versioning
    - Efficient model loading and caching
    - Model performance tracking
    - Automatic model retraining
    """
    
    def __init__(self, models_dir: str = "models"):
        """Initialize the ModelManager."""
        self.models_dir = models_dir
        self.embeddings_dir = os.path.join(models_dir, "embeddings")
        self.tfidf_dir = os.path.join(models_dir, "tfidf_models")
        self.saved_models_dir = os.path.join(models_dir, "saved_models")
        self.configs_dir = os.path.join(models_dir, "model_configs")
        
        # Create directories if they don't exist
        self._create_directories()
        
        # Model cache
        self._model_cache = {}
        
        # Default model configuration
        self.default_config = {
            "tfidf": {
                "stop_words": "english",
                "ngram_range": (1, 2),
                "max_features": 1000,
                "lowercase": True,
                "min_df": 1,
                "max_df": 0.95
            },
            "similarity": {
                "metric": "cosine",
                "normalize": True
            },
            "keywords": {
                "max_keywords": 50,
                "min_score": 0.1
            }
        }
    
    def _create_directories(self):
        """Create necessary directories for model storage."""
        directories = [
            self.models_dir,
            self.embeddings_dir,
            self.tfidf_dir,
            self.saved_models_dir,
            self.configs_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def save_tfidf_model(self, vectorizer: TfidfVectorizer, model_name: str = "default") -> str:
        """
        Save a TF-IDF vectorizer model.
        
        Args:
            vectorizer: The trained TF-IDF vectorizer
            model_name: Name for the model
            
        Returns:
            Path to the saved model
        """
        model_path = os.path.join(self.tfidf_dir, f"{model_name}_tfidf.pkl")
        config_path = os.path.join(self.configs_dir, f"{model_name}_tfidf_config.json")
        
        # Save the model
        joblib.dump(vectorizer, model_path)
        
        # Save configuration
        config = {
            "model_name": model_name,
            "created_at": datetime.now().isoformat(),
            "type": "tfidf",
            "parameters": {
                "stop_words": vectorizer.stop_words,
                "ngram_range": vectorizer.ngram_range,
                "max_features": vectorizer.max_features,
                "lowercase": vectorizer.lowercase,
                "min_df": vectorizer.min_df,
                "max_df": vectorizer.max_df,
                "vocabulary_size": len(vectorizer.vocabulary_) if hasattr(vectorizer, 'vocabulary_') else 0
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return model_path
    
    def load_tfidf_model(self, model_name: str = "default") -> Optional[TfidfVectorizer]:
        """
        Load a TF-IDF vectorizer model.
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            Loaded TF-IDF vectorizer or None if not found
        """
        model_path = os.path.join(self.tfidf_dir, f"{model_name}_tfidf.pkl")
        
        if not os.path.exists(model_path):
            return None
        
        try:
            vectorizer = joblib.load(model_path)
            self._model_cache[f"tfidf_{model_name}"] = vectorizer
            return vectorizer
        except Exception as e:
            print(f"Error loading TF-IDF model {model_name}: {e}")
            return None
    
    def save_embeddings(self, embeddings: np.ndarray, metadata: Dict[str, Any], 
                       model_name: str = "default") -> str:
        """
        Save word embeddings.
        
        Args:
            embeddings: The embeddings array
            metadata: Metadata about the embeddings
            model_name: Name for the model
            
        Returns:
            Path to the saved embeddings
        """
        embeddings_path = os.path.join(self.embeddings_dir, f"{model_name}_embeddings.npy")
        metadata_path = os.path.join(self.configs_dir, f"{model_name}_embeddings_metadata.json")
        
        # Save embeddings
        np.save(embeddings_path, embeddings)
        
        # Save metadata
        metadata.update({
            "model_name": model_name,
            "created_at": datetime.now().isoformat(),
            "type": "embeddings",
            "shape": embeddings.shape
        })
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return embeddings_path
    
    def load_embeddings(self, model_name: str = "default") -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """
        Load word embeddings.
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            Tuple of (embeddings, metadata) or (None, None) if not found
        """
        embeddings_path = os.path.join(self.embeddings_dir, f"{model_name}_embeddings.npy")
        metadata_path = os.path.join(self.configs_dir, f"{model_name}_embeddings_metadata.json")
        
        if not os.path.exists(embeddings_path):
            return None, None
        
        try:
            embeddings = np.load(embeddings_path)
            
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            return embeddings, metadata
        except Exception as e:
            print(f"Error loading embeddings {model_name}: {e}")
            return None, None
    
    def save_analysis_model(self, model_data: Dict[str, Any], model_name: str = "default") -> str:
        """
        Save a complete analysis model (TF-IDF + configuration).
        
        Args:
            model_data: Dictionary containing model components
            model_name: Name for the model
            
        Returns:
            Path to the saved model
        """
        model_path = os.path.join(self.saved_models_dir, f"{model_name}_analysis.pkl")
        
        # Add metadata
        model_data.update({
            "model_name": model_name,
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        })
        
        # Save the complete model
        joblib.dump(model_data, model_path)
        
        return model_path
    
    def load_analysis_model(self, model_name: str = "default") -> Optional[Dict[str, Any]]:
        """
        Load a complete analysis model.
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            Loaded model data or None if not found
        """
        model_path = os.path.join(self.saved_models_dir, f"{model_name}_analysis.pkl")
        
        if not os.path.exists(model_path):
            return None
        
        try:
            model_data = joblib.load(model_path)
            self._model_cache[f"analysis_{model_name}"] = model_data
            return model_data
        except Exception as e:
            print(f"Error loading analysis model {model_name}: {e}")
            return None
    
    def create_default_models(self):
        """Create and save default models for the ATS system."""
        print("Creating default models...")
        
        # Create default TF-IDF model
        vectorizer = TfidfVectorizer(
            stop_words=self.default_config["tfidf"]["stop_words"],
            ngram_range=self.default_config["tfidf"]["ngram_range"],
            max_features=self.default_config["tfidf"]["max_features"],
            lowercase=self.default_config["tfidf"]["lowercase"],
            min_df=self.default_config["tfidf"]["min_df"],
            max_df=self.default_config["tfidf"]["max_df"]
        )
        
        # Fit with sample data to initialize
        sample_texts = [
            "software engineer python javascript react",
            "data scientist machine learning python sql",
            "product manager agile scrum project management",
            "marketing manager digital marketing social media",
            "sales representative customer service communication"
        ]
        
        vectorizer.fit(sample_texts)
        
        # Save the model
        self.save_tfidf_model(vectorizer, "default")
        print(f"✅ Created default TF-IDF model")
        
        # Create default analysis model
        analysis_model = {
            "vectorizer": vectorizer,
            "config": self.default_config,
            "stop_words": set(stopwords.words('english')),
            "created_at": datetime.now().isoformat()
        }
        
        self.save_analysis_model(analysis_model, "default")
        print(f"✅ Created default analysis model")
        
        # Create model index
        self._create_model_index()
        
        print("✅ Default models created successfully!")
    
    def _create_model_index(self):
        """Create an index of all available models."""
        index = {
            "created_at": datetime.now().isoformat(),
            "models": {}
        }
        
        # Index TF-IDF models
        for file in os.listdir(self.tfidf_dir):
            if file.endswith('.pkl'):
                model_name = file.replace('_tfidf.pkl', '')
                index["models"][f"tfidf_{model_name}"] = {
                    "type": "tfidf",
                    "path": os.path.join(self.tfidf_dir, file),
                    "config_path": os.path.join(self.configs_dir, f"{model_name}_tfidf_config.json")
                }
        
        # Index embeddings
        for file in os.listdir(self.embeddings_dir):
            if file.endswith('.npy'):
                model_name = file.replace('_embeddings.npy', '')
                index["models"][f"embeddings_{model_name}"] = {
                    "type": "embeddings",
                    "path": os.path.join(self.embeddings_dir, file),
                    "metadata_path": os.path.join(self.configs_dir, f"{model_name}_embeddings_metadata.json")
                }
        
        # Index analysis models
        for file in os.listdir(self.saved_models_dir):
            if file.endswith('.pkl'):
                model_name = file.replace('_analysis.pkl', '')
                index["models"][f"analysis_{model_name}"] = {
                    "type": "analysis",
                    "path": os.path.join(self.saved_models_dir, file)
                }
        
        # Save index
        index_path = os.path.join(self.models_dir, "model_index.json")
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about all available models."""
        index_path = os.path.join(self.models_dir, "model_index.json")
        
        if not os.path.exists(index_path):
            return {"models": {}, "error": "No model index found"}
        
        with open(index_path, 'r') as f:
            return json.load(f)
    
    def clear_cache(self):
        """Clear the model cache."""
        self._model_cache.clear()
        print("Model cache cleared.")


# Global model manager instance
model_manager = ModelManager()








