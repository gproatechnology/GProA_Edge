#!/usr/bin/env python3
"""
Test script to verify the LLM provider architecture works correctly.
This version uses mocks to avoid dependency on Ollama/Gemini availability during testing.
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch

# Add the backend directory to the path so we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__)))

async def test_llm_router():
    """Test the LLM router."""
    print("\nTesting LLM Router...")
    
    try:
        from app.services.llm.routing import LLMRouter, TaskType, FallbackProvider
        
        router = LLMRouter()
        
        # Test routing classification to Ollama (with Gemini fallback)
        classification_provider = router.route(TaskType.CLASSIFICATION)
        print(f"Classification routed to: {type(classification_provider).__name__}")
        assert isinstance(classification_provider, FallbackProvider)
        assert classification_provider.primary_name == "Ollama"
        assert classification_provider.secondary_name == "Gemini"
        
        # Test routing summary to Ollama (with Gemini fallback)
        summary_provider = router.route(TaskType.SUMMARY)
        print(f"Summary routed to: {type(summary_provider).__name__}")
        assert isinstance(summary_provider, FallbackProvider)
        assert summary_provider.primary_name == "Ollama"
        assert summary_provider.secondary_name == "Gemini"
        
        # Test routing relationship to Gemini (with Ollama fallback)
        relationship_provider = router.route(TaskType.RELATIONSHIP)
        print(f"Relationship routed to: {type(relationship_provider).__name__}")
        assert isinstance(relationship_provider, FallbackProvider)
        assert relationship_provider.primary_name == "Gemini"
        assert relationship_provider.secondary_name == "Ollama"
        
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

async def test_ollama_provider_mocked():
    """Test the Ollama provider with mocked responses."""
    print("\nTesting Ollama Provider (with mocks)...")
    
    try:
        from app.services.llm.ollama_provider import OllamaProvider
        
        provider = OllamaProvider()
        
        # Mock the generate method to return predictable responses
        with patch.object(provider, 'generate', new_callable=AsyncMock) as mock_generate, \
             patch.object(provider, 'generate_json', new_callable=AsyncMock) as mock_generate_json:
            
            # Configure mocks for different call types
            def generate_side_effect(prompt):
                if "summary" in prompt.lower() or "technical summary" in prompt.lower():
                    return "This is a test summary."
                elif "relationship" in prompt.lower() or "infer" in prompt.lower():
                    return '{"related_entities": ["entity1", "entity2"], "relationship_type": "similar", "confidence": 0.9}'
                else:  # classification or other
                    return '{"category_edge": "ENERGY", "measure_edge": "EEM22", "confidence": 0.95}'
            
            def generate_json_side_effect(prompt):
                if "relationship" in prompt.lower() or "infer" in prompt.lower():
                    return {"related_entities": ["entity1", "entity2"], "relationship_type": "similar", "confidence": 0.9}
                else:  # classification
                    return {"category_edge": "ENERGY", "measure_edge": "EEM22", "doc_type": "ficha_tecnica", "confidence": 0.95}
            
            mock_generate.side_effect = generate_side_effect
            mock_generate_json.side_effect = generate_json_side_effect
            
            # Test classification
            test_text = "This is a technical specification for an LED lighting fixture with 18 watts and 2000 lumens."
            result = await provider.classify(test_text)
            print(f"Classification result: {result}")
            assert result["category_edge"] == "ENERGY"
            assert result["measure_edge"] == "EEM22"
            assert result["doc_type"] == "ficha_tecnica"
            assert result["confidence"] == 0.95
            
            # Test summarization
            summary = await provider.summarize(test_text)
            print(f"Summary result: {summary}")
            assert summary == "This is a test summary."
            
            # Test relationship inference
            context = {
                "entity1": "LED_Light_Fixture_A",
                "entity2": "LED_Light_Fixture_B",
                "properties": {
                    "entity1": {"watts": 18, "lumens": 2000},
                    "entity2": {"watts": 18, "lumens": 2000}
                }
            }
            relationship = await provider.infer_relationship(context)
            print(f"Relationship result: {relationship}")
            assert "related_entities" in relationship
            assert relationship["relationship_type"] == "similar"
            assert relationship["confidence"] == 0.9
            
        print("Ollama Provider test passed!")
        return True
        
    except Exception as e:
        print(f"Ollama Provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("Testing LLM Provider Architecture for EOSIS\n")
    
    tests = [
        test_llm_router,
        test_llm_result_model,
        test_ollama_provider_mocked
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