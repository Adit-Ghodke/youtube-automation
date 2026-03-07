"""Test RAG Engine initialization"""
try:
    import chromadb
    print("✅ chromadb imported")
except Exception as e:
    print(f"❌ chromadb import error: {e}")

try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence_transformers imported")
except Exception as e:
    print(f"❌ sentence_transformers import error: {e}")

try:
    from rag_engine import RAGEngine
    print("✅ RAGEngine imported")
    
    engine = RAGEngine()
    print(f"✅ RAGEngine initialized: {engine.get_stats()}")
    
    # Test retrieval
    results = engine.retrieve("brain facts", n_results=3)
    print(f"✅ Retrieved {len(results)} results")
    for r in results:
        print(f"   - {r['text'][:60]}...")
        
except Exception as e:
    import traceback
    print(f"❌ RAGEngine error: {e}")
    traceback.print_exc()
