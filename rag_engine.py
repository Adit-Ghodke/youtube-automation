"""
RAG Engine for YouTube Automation
Uses ChromaDB for vector storage when available, with JSON fallback.
Retrieves relevant facts and context to enhance script generation.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
import json
import os

logger = logging.getLogger(__name__)

# Try to import ChromaDB + sentence-transformers
HAS_ADVANCED_RAG = False
try:
    # Suppress Pydantic V1 compatibility warning on Python 3.14+
    import warnings
    warnings.filterwarnings("ignore", message=".*Pydantic V1.*", category=UserWarning)
    
    import chromadb
    from chromadb.utils import embedding_functions
    from sentence_transformers import SentenceTransformer
    HAS_ADVANCED_RAG = True
except ImportError as e:
    logger.info(f"ChromaDB not available, using JSON fallback for RAG.")
except Exception as e:
    logger.info(f"ChromaDB not compatible with this Python version, using JSON fallback for RAG.")


class RAGEngine:
    """
    Retrieval-Augmented Generation engine.
    Uses ChromaDB when available, falls back to keyword-based JSON search.
    """
    
    def __init__(self, 
                 persist_directory: str = "./rag_data",
                 collection_name: str = "youtube_knowledge"):
        """
        Initialize the RAG engine.
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        self.collection_name = collection_name
        self.knowledge_file = self.persist_directory / "knowledge_base.json"
        
        self.knowledge_base = []
        self.use_vector_db = False
        self.enabled = True
        
        # Try ChromaDB first
        if HAS_ADVANCED_RAG:
            try:
                self._init_chromadb()
                self.use_vector_db = True
                logger.info("RAG Engine using ChromaDB (vector search)")
            except Exception as e:
                logger.warning(f"ChromaDB failed: {e}. Using JSON fallback.")
                self._init_json_fallback()
        else:
            self._init_json_fallback()
    
    def _init_chromadb(self):
        """Initialize ChromaDB backend."""
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function
        )
        
        if self.collection.count() == 0:
            self._populate_default_knowledge_chromadb()
    
    def _init_json_fallback(self):
        """Initialize JSON-based fallback (keyword search)."""
        logger.info("RAG Engine using JSON fallback (keyword search)")
        
        if self.knowledge_file.exists():
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
        else:
            self._populate_default_knowledge_json()
    
    def _get_default_facts(self) -> List[Dict]:
        """Get default knowledge base facts."""
        return [
            # Science & Space
            {"text": "A teaspoon of neutron star would weigh about 6 billion tons on Earth.", "category": "space", "tags": ["neutron star", "space", "physics", "weight"]},
            {"text": "Light takes 8 minutes and 20 seconds to travel from the Sun to Earth.", "category": "space", "tags": ["sun", "light", "earth", "speed"]},
            {"text": "There are more atoms in a single glass of water than there are glasses of water in all the oceans.", "category": "science", "tags": ["atoms", "water", "chemistry", "ocean"]},
            {"text": "The human brain can store approximately 2.5 petabytes of information, equivalent to 3 million hours of TV shows.", "category": "biology", "tags": ["brain", "memory", "human body", "storage"]},
            {"text": "Honey never spoils. Archaeologists have found 3000-year-old honey in Egyptian tombs that was still perfectly edible.", "category": "science", "tags": ["honey", "food", "archaeology", "egypt"]},
            {"text": "If you could fold a piece of paper 42 times, it would reach the Moon.", "category": "math", "tags": ["paper", "moon", "exponential", "math"]},
            {"text": "The shortest war in history lasted only 38 to 45 minutes between Britain and Zanzibar in 1896.", "category": "history", "tags": ["war", "history", "zanzibar", "britain"]},
            {"text": "Octopuses have three hearts and blue blood.", "category": "biology", "tags": ["octopus", "heart", "marine life", "animals"]},
            {"text": "A day on Venus is longer than its year. Venus takes 243 Earth days to rotate but only 225 days to orbit the Sun.", "category": "space", "tags": ["venus", "planet", "rotation", "orbit"]},
            {"text": "The Great Wall of China is not visible from space with the naked eye, but many highways are.", "category": "geography", "tags": ["china", "wall", "myth", "space"]},
            {"text": "Bananas are berries, but strawberries are not.", "category": "biology", "tags": ["banana", "strawberry", "botany", "fruit"]},
            {"text": "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid.", "category": "history", "tags": ["cleopatra", "egypt", "pyramid", "moon"]},
            {"text": "A single strand of spider silk is stronger than a steel thread of the same thickness.", "category": "biology", "tags": ["spider", "silk", "strength", "nature"]},
            {"text": "The deepest part of the ocean, the Mariana Trench, is deeper than Mount Everest is tall.", "category": "geography", "tags": ["ocean", "trench", "everest", "depth"]},
            {"text": "Your brain uses about 20% of your total energy despite being only 2% of your body weight.", "category": "biology", "tags": ["brain", "energy", "body", "metabolism"]},
            
            # Technology & AI
            {"text": "The first computer programmer was a woman named Ada Lovelace, who wrote algorithms for Charles Babbage's Analytical Engine in the 1840s.", "category": "technology", "tags": ["programming", "ada lovelace", "history", "computer"]},
            {"text": "The world's first website is still online at info.cern.ch, created by Tim Berners-Lee in 1991.", "category": "technology", "tags": ["internet", "website", "history", "web"]},
            {"text": "Google's original name was BackRub, and it ran on Stanford's servers using almost all their bandwidth.", "category": "technology", "tags": ["google", "search", "history", "stanford"]},
            {"text": "The first YouTube video was uploaded on April 23, 2005, titled 'Me at the zoo' by co-founder Jawed Karim.", "category": "technology", "tags": ["youtube", "video", "history", "social media"]},
            {"text": "AI can now generate images, write code, compose music, and even pass professional exams like the bar exam.", "category": "ai", "tags": ["artificial intelligence", "machine learning", "future", "technology"]},
            {"text": "The first email was sent in 1971 by Ray Tomlinson, and he doesn't remember what it said.", "category": "technology", "tags": ["email", "history", "internet", "communication"]},
            
            # Psychology & Human
            {"text": "The human attention span has dropped from 12 seconds in 2000 to just 8 seconds, less than a goldfish.", "category": "psychology", "tags": ["attention", "brain", "focus", "goldfish"]},
            {"text": "People are more likely to remember the first and last items in a list, known as the serial position effect.", "category": "psychology", "tags": ["memory", "learning", "brain", "recall"]},
            {"text": "Laughter is contagious because of mirror neurons in our brain that mimic the emotions of others.", "category": "psychology", "tags": ["laughter", "brain", "emotions", "social"]},
            {"text": "The fear of missing out (FOMO) triggers the same brain regions as physical pain.", "category": "psychology", "tags": ["fomo", "fear", "social media", "pain"]},
            {"text": "Humans are the only animals that blush, which Darwin called 'the most peculiar and most human of all expressions.'", "category": "psychology", "tags": ["blush", "emotions", "darwin", "human"]},
            {"text": "Your brain processes images 60,000 times faster than text, which is why visual content is so powerful.", "category": "psychology", "tags": ["brain", "visual", "images", "processing"]},
            {"text": "The average person has about 60,000 thoughts per day, and most of them are repetitive.", "category": "psychology", "tags": ["thoughts", "brain", "mind", "thinking"]},
            
            # Fun & Interesting
            {"text": "The inventor of the Pringles can is buried in one.", "category": "trivia", "tags": ["pringles", "inventor", "death", "quirky"]},
            {"text": "There are more possible iterations of a game of chess than there are atoms in the known universe.", "category": "science", "tags": ["chess", "atoms", "universe", "combinations"]},
        ]
    
    def _populate_default_knowledge_chromadb(self):
        """Populate ChromaDB with default facts."""
        facts = self._get_default_facts()
        
        self.collection.add(
            documents=[f["text"] for f in facts],
            metadatas=[{"category": f["category"], "tags": ",".join(f["tags"])} for f in facts],
            ids=[f"fact_{i}" for i in range(len(facts))]
        )
        logger.info(f"Added {len(facts)} facts to ChromaDB knowledge base.")
    
    def _populate_default_knowledge_json(self):
        """Populate JSON with default facts."""
        self.knowledge_base = self._get_default_facts()
        self._save_json()
        logger.info(f"Added {len(self.knowledge_base)} facts to JSON knowledge base.")
    
    def _save_json(self):
        """Save knowledge base to JSON file."""
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
    
    def add_knowledge(self, text: str, category: str = "general", tags: List[str] = None) -> bool:
        """Add new knowledge to the database."""
        if not self.enabled:
            return False
        
        try:
            fact = {"text": text, "category": category, "tags": tags or []}
            
            if self.use_vector_db:
                self.collection.add(
                    documents=[text],
                    metadatas=[{"category": category, "tags": ",".join(tags or [])}],
                    ids=[f"custom_{self.collection.count()}"]
                )
            else:
                self.knowledge_base.append(fact)
                self._save_json()
            
            logger.info(f"Added knowledge: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return False
    
    def retrieve(self, query: str, n_results: int = 5) -> List[Dict]:
        """Retrieve relevant knowledge for a query."""
        if not self.enabled:
            return []
        
        try:
            if self.use_vector_db:
                return self._retrieve_chromadb(query, n_results)
            else:
                return self._retrieve_json(query, n_results)
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def _retrieve_chromadb(self, query: str, n_results: int) -> List[Dict]:
        """Retrieve using ChromaDB vector search."""
        results = self.collection.query(query_texts=[query], n_results=n_results)
        
        retrieved = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                retrieved.append({
                    "text": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "score": 1 - (results['distances'][0][i] if results['distances'] else 0)
                })
        return retrieved
    
    def _retrieve_json(self, query: str, n_results: int) -> List[Dict]:
        """Retrieve using keyword matching (fallback)."""
        query_words = set(query.lower().split())
        
        scored_facts = []
        for fact in self.knowledge_base:
            # Score by matching keywords in text and tags
            fact_text = fact['text'].lower()
            fact_tags = set(tag.lower() for tag in fact.get('tags', []))
            
            # Calculate simple relevance score
            text_matches = sum(1 for word in query_words if word in fact_text)
            tag_matches = sum(2 for word in query_words if any(word in tag for tag in fact_tags))
            score = text_matches + tag_matches
            
            if score > 0:
                scored_facts.append({
                    "text": fact['text'],
                    "metadata": {"category": fact['category'], "tags": fact['tags']},
                    "score": score
                })
        
        # Sort by score and return top results
        scored_facts.sort(key=lambda x: x['score'], reverse=True)
        return scored_facts[:n_results]
    
    def get_context_for_topic(self, topic: str, max_facts: int = 7) -> str:
        """Get formatted context for a topic to inject into AI prompt."""
        if not self.enabled:
            return ""
        
        retrieved = self.retrieve(topic, n_results=max_facts)
        
        if not retrieved:
            return ""
        
        context_parts = ["RELEVANT FACTS FROM KNOWLEDGE BASE:"]
        for i, item in enumerate(retrieved, 1):
            context_parts.append(f"{i}. {item['text']}")
        
        return "\n".join(context_parts)
    
    def get_stats(self) -> Dict:
        """Get statistics about the knowledge base."""
        if self.use_vector_db:
            return {
                "enabled": True,
                "backend": "ChromaDB (vector search)",
                "count": self.collection.count()
            }
        else:
            return {
                "enabled": True,
                "backend": "JSON (keyword search)",
                "count": len(self.knowledge_base)
            }


# Quick access function
def get_rag_context(topic: str, max_facts: int = 5) -> str:
    """Quick function to get RAG context for a topic."""
    engine = RAGEngine()
    return engine.get_context_for_topic(topic, max_facts)
