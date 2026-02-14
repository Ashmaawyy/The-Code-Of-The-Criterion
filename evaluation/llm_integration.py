"""
LLM Integration: Deepseek-R1 via Ollama

Integrates deepseek-r1:8b from Ollama as the semantic extraction layer (Layer 2).
The LLM extracts domain, assumptions, and intent from user queries.
Output becomes system_data input for the reasoning engine.

Setup:
    1. Install Ollama from https://ollama.ai
    2. Run: ollama pull deepseek-r1:8b
    3. Start Ollama server (default: localhost:11434)

Usage:
    from evaluation.llm_integration import OllamaLLMBridge
    
    bridge = OllamaLLMBridge()
    system_data = bridge.extract_semantic_meaning(query)
    
    # Then use with reasoning engine:
    from evaluation.pipeline import CriterionPipeline
    pipeline = CriterionPipeline()
    result = pipeline.evaluate(query, system_data)
"""

import json
import requests
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Result of semantic extraction from LLM"""
    domain: str
    assumptions: list
    intent: str
    beneficiaries: list
    dismissed_harms: list
    system_data: Dict


class OllamaLLMBridge:
    """
    Bridge between Ollama's deepseek-r1:8b and The Criterion reasoning engine.
    
    Role: Extract semantic meaning from natural language queries into structured system_data
    """
    
    def __init__(self, model: str = "deepseek-r1:8b", base_url: str = "http://localhost:11434"):
        """
        Initialize connection to Ollama.
        
        Args:
            model: Model name (default: deepseek-r1:8b)
            base_url: Ollama server URL (default: localhost:11434)
        """
        self.model = model
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/api/generate"
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if self.model not in model_names:
                    print(f"⚠️  Warning: {self.model} not found in Ollama")
                    print(f"Available models: {model_names}")
                    print(f"Run: ollama pull {self.model}")
            else:
                raise ConnectionError(f"Ollama returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}\n"
                "Make sure Ollama is running. Start with: ollama serve"
            )
    
    def extract_semantic_meaning(self, query: str) -> Dict:
        """
        Extract semantic meaning from a query using deepseek-r1:8b.
        
        Args:
            query: User query or proposal to analyze
            
        Returns:
            system_data dict ready for reasoning engine
        """
        # Build extraction prompt
        extraction_prompt = self._build_extraction_prompt(query)
        
        # Call LLM
        try:
            response = self._call_ollama(extraction_prompt)
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            # Return default system_data if LLM fails
            return self._default_system_data()
        
        # Parse response into system_data
        system_data = self._parse_extraction_response(response, query)
        
        return system_data
    
    def _build_extraction_prompt(self, query: str) -> str:
        """Build extraction prompt for the LLM"""
        return f"""You are a semantic analysis engine for The Criterion reasoning framework.

Your task: Extract semantic properties from the following query.

Return ONLY valid JSON (no markdown, no extra text) with this exact structure:
{{
    "domain": "economic|social|spiritual|intellectual|biological|general",
    "assumptions": ["assumption 1", "assumption 2", ...],
    "intent": "brief description of true intent",
    "beneficiaries": ["group 1", "group 2", ...],
    "dismissed_harms": ["harm 1", "harm 2", ...],
    "permits_exploitative_gain": true|false,
    "acknowledges_transcendent_source": true|false,
    "enables_accountability": true|false,
    "causes_harm_amplification": true|false,
    "destabilizes_lineage": true|false,
    "deviates_from_optimal_functioning": true|false
}}

QUERY: {query}

Return ONLY the JSON object, nothing else."""
    
    def _call_ollama(self, prompt: str, timeout: int = 300) -> str:
        """
        Call Ollama API with deepseek-r1:8b.
        
        Args:
            prompt: The prompt to send
            timeout: Timeout in seconds (deepseek-r1 can be slow)
            
        Returns:
            Model response text
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.1,  # Low temperature for deterministic extraction
        }
        
        response = requests.post(
            self.api_endpoint,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result.get("response", "")
    
    def _parse_extraction_response(self, response_text: str, query: str) -> Dict:
        """
        Parse LLM response into system_data.
        
        Args:
            response_text: Raw response from LLM
            query: Original query (for fallback)
            
        Returns:
            Structured system_data dict
        """
        try:
            # Try to extract JSON from response
            # Sometimes model includes extra text, so look for JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                extracted = json.loads(json_str)
                
                # Validate and build system_data
                return {
                    "domain": extracted.get("domain", "general"),
                    "assumptions": extracted.get("assumptions", []),
                    "intent": extracted.get("intent", f"Analyze: {query[:100]}"),
                    "beneficiaries": extracted.get("beneficiaries", []),
                    "dismissed_harms": extracted.get("dismissed_harms", []),
                    "permits_exploitative_gain": extracted.get("permits_exploitative_gain", False),
                    "acknowledges_transcendent_source": extracted.get("acknowledges_transcendent_source", False),
                    "enables_accountability": extracted.get("enables_accountability", False),
                    "causes_harm_amplification": extracted.get("causes_harm_amplification", False),
                    "destabilizes_lineage": extracted.get("destabilizes_lineage", False),
                    "deviates_from_optimal_functioning": extracted.get("deviates_from_optimal_functioning", False),
                }
        except json.JSONDecodeError:
            print(f"Failed to parse LLM response as JSON. Raw: {response_text[:200]}")
        
        # Fallback to default if parsing fails
        return self._default_system_data()
    
    def _default_system_data(self) -> Dict:
        """Return default conservative system_data"""
        return {
            "domain": "general",
            "assumptions": [],
            "intent": "Unknown intent",
            "beneficiaries": [],
            "dismissed_harms": [],
            "permits_exploitative_gain": False,
            "acknowledges_transcendent_source": False,
            "enables_accountability": False,
            "causes_harm_amplification": False,
            "destabilizes_lineage": False,
            "deviates_from_optimal_functioning": False,
        }
    
    def extract_with_reasoning(self, query: str, verbose: bool = False):
        """
        Full pipeline: Extract semantics → Run reasoning engine → Return verdict.
        
        Args:
            query: User query
            verbose: Print intermediate steps
            
        Returns:
            Complete reasoning result with verdict
        """
        from evaluation.pipeline import CriterionPipeline
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"QUERY: {query}")
            print(f"{'='*80}")
        
        # Step 1: Extract semantic meaning
        if verbose:
            print("\n[STEP 1] Extracting semantic meaning with deepseek-r1:8b...")
        system_data = self.extract_semantic_meaning(query)
        
        if verbose:
            print(f"Domain: {system_data['domain']}")
            print(f"Assumptions: {len(system_data['assumptions'])} identified")
            print(f"Intent: {system_data['intent']}")
        
        # Step 2: Run reasoning engine
        if verbose:
            print("\n[STEP 2] Running Criterion reasoning engine...")
        pipeline = CriterionPipeline()
        result = pipeline.evaluate(query, system_data)
        
        if verbose:
            print(f"Violations: {result['reasoning_phases']['phase_3_mirror']['total_violations']}")
            print(f"Gates pass: {result['reasoning_phases']['phase_4_gates']['all_gates_pass']}")
            print(f"\n[VERDICT] {result['phase_6_verdict']['final_judgment']}")
            print(f"Recommendation: {result['phase_6_verdict']['recommendation']}")
            print(f"\n{'='*80}\n")
        
        return result


# Convenience function for quick integration
def analyze_with_deepseek(query: str, verbose: bool = True) -> Dict:
    """
    Quick function to analyze a query with deepseek-r1:8b + Criterion reasoning.
    
    Args:
        query: Query to analyze
        verbose: Print detailed output
        
    Returns:
        Complete analysis result
    """
    try:
        bridge = OllamaLLMBridge()
        return bridge.extract_with_reasoning(query, verbose=verbose)
    except ConnectionError as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    # Test the integration
    print("Testing deepseek-r1:8b integration with The Criterion...\n")
    
    # Test query 1: Economic
    query1 = "Can deception in business be justified if it increases overall market efficiency?"
    print(f"Query 1: {query1}\n")
    result1 = analyze_with_deepseek(query1, verbose=True)
    
    # Test query 2: Social
    query2 = "Should we redefine traditional family structures to maximize individual freedom?"
    print(f"\nQuery 2: {query2}\n")
    result2 = analyze_with_deepseek(query2, verbose=True)
