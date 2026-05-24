#!/usr/bin/env python3
"""
Test script to verify the LLM provider architecture works correctly with real Ollama connection.
"""

import asyncio
import sys
import os

# Add the backend directory to the path so we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__)))

async def test_ollama_provider():
    """Test the Ollama provider directly with real connection."""
    print("Testing Ollama Provider (real connection)...")
    
    try:
        from app.services.llm.ollama_provider import OllamaProvider
        
        # Use a reasonable timeout for real Ollama connection
        provider = OllamaProvider(timeout=60.0)
        
        # Test classification
        print("  Testing classification...")
        test_text = "This is a technical specification for an LED lighting fixture with 18 watts and 2000 lumens."
        result = await provider.classify(test_text)
        print(f"  Classification result: {result}")
        
        # Validate classification result has expected structure
        assert "category_edge" in result
        assert "measure_edge" in result
        assert "confidence" in result
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0
        
        # Test summarization
        print("  Testing summarization...")
        summary = await provider.summarize(test_text)
        print(f"  Summary result: {summary[:100]}..." if len(summary) > 100 else f"  Summary result: {summary}")
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        # Test relationship inference
        print("  Testing relationship inference...")
        context = {
            "entity1": "LED_Light_Fixture_A",
            "entity2": "LED_Light_Fixture_B",
            "properties": {
                "entity1": {"watts": 18, "lumens": 2000},
                "entity2": {"watts": 18, "lumens": 2000}
            }
        }
        relationship = await provider.infer_relationship(context)
        print(f"  Relationship result: {relationship}")
        assert isinstance(relationship, dict)
        # Basic validation - should have some relationship data
        
        print("Ollama Provider test passed!")
        return True
        
    except Exception as e:
        print(f"Ollama Provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_llm_router():
    """Test the LLM router."""
    print("\nTesting LLM Router...")
    
    try:
        from app.services.llm.routing import LLMRouter, TaskType
        
        router = LLMRouter()
        
        # Test routing classification to Ollama
        classification_provider = router.route(TaskType.CLASSIFICATION)
        print(f"Classification routed to: {type(classification_provider).__name__}")
        
        # Test routing summary to Ollama
        summary_provider = router.route(TaskType.SUMMARY)
        print(f"Summary routed to: {type(summary_provider).__name__}")
        
        # Test routing relationship to Gemini (default)
        relationship_provider = router.route(TaskType.RELATIONSHIP)
        print(f"Relationship routed to: {type(relationship_provider).__name__}")
        
        print("LLM Router test passed!")
        return True
        
    except Exception as e:
        print(f"LLM Router test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_llm_result_model():
    """Test the LLMResult model."""
    print("\nTesting LLMResult Model...")
    
    try:
        from app.services.llm.models import LLMResult
        
        # Create a sample result
        result = LLMResult.create(
            provider="ollama",
            model="llama3.2",
            prompt="Test prompt",
            response={"category_edge": "ENERGY", "measure_edge": "EEM22", "confidence": 0.95},
            confidence=0.95,
            latency_ms=150
        )
        
        print(f"LLMResult created: {result}")
        print(f"Prompt hash: {result.prompt_hash}")
        
        print("LLMResult Model test passed!")
        return True
        
    except Exception as e:
        print(f"LLMResult Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("Testing LLM Provider Architecture for EOSIS with REAL Ollama connection\n")
    
    tests = [
        test_ollama_provider,
        test_llm_router,
        test_llm_result_model
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print(f"\nTest Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("All tests passed! The LLM architecture is ready for integration.")
        return 0
    else:
        print("Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)