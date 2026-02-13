"""
LLM Integration Example: Using The Criterion as a Chain-of-Thought Framework

This demonstrates how to integrate The Criterion reasoning engine with an LLM
to transform it from a probabilistic next-token generator into an architectural reasoner.

The key insight: Instead of the LLM generating text based on statistical patterns,
it uses The Criterion as an explicit reasoning structure that guides its thinking.

Usage pattern:
1. User asks LLM a question about a system/proposal
2. LLM extracts key concepts (this is the semantic/linguistic layer)
3. LLM calls CriterionPipeline.evaluate() to structure the reasoning
4. LLM reads the CoT scaffold and uses it to guide response generation
5. LLM's output is architecturally sound because it followed explicit reasoning
"""

from evaluation.pipeline import CriterionPipeline
from typing import Dict, Tuple


class LLMCriterionIntegration:
    """
    Bridge between LLM and Criterion reasoning framework.
    
    This handles:
    1. Converting LLM's semantic understanding into system_data format
    2. Running Criterion reasoning engine
    3. Returning structured CoT scaffold for LLM to follow
    """
    
    def __init__(self):
        self.pipeline = CriterionPipeline()
    
    def process_llm_query(self, query: str, 
                         llm_extracted_system: Dict) -> Tuple[Dict, str]:
        """
        Process a query through the integrated pipeline.
        
        Args:
            query: The original user query
            llm_extracted_system: System properties extracted by LLM
                                 (becomes system_data for reasoning engine)
        
        Returns:
            Tuple of (structured_reasoning, cot_scaffold)
        """
        # Run the integrated pipeline
        result = self.pipeline.evaluate(query, llm_extracted_system)
        
        # Extract components for LLM to use
        reasoning = result["reasoning_phases"]
        scaffold = result["cot_scaffold"]
        verdict = result["phase_6_verdict"]
        
        return reasoning, scaffold, verdict


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 1: Economic Proposal Analysis
# ═══════════════════════════════════════════════════════════════════════════

def example_economic_proposal():
    """
    Example: Analyzing a consequentialist economic proposal
    
    User asks LLM: "Is it justified to use deceptive marketing if it increases 
                    overall market efficiency?"
    
    LLM's role: Extract semantic meaning
    Criterion's role: Structure the architectural reasoning
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 1: Economic Proposal - Deceptive Marketing for Efficiency")
    print("="*80)
    
    query = (
        "Is it justified to use deceptive marketing if it increases overall "
        "market efficiency and creates more jobs?"
    )
    
    # This is what the LLM would extract from the query
    # (semantic/linguistic understanding layer - no need for separate Layer 2)
    llm_extraction = {
        "domain": "economic",
        "proposed_system": "Deceptive marketing justified by efficiency gains",
        "claimed_benefits": ["market efficiency", "job creation"],
        "dismissed_harms": ["consumer trust", "truth preservation"],
        "underlying_framework": "consequentialism"
    }
    
    # This is what the LLM infers about the system properties
    system_data = {
        "permits_exploitative_gain": True,           # Deception for gain
        "acknowledges_transcendent_source": False,   # Purely utilitarian
        "enables_accountability": False,              # No mechanism for justice
        "causes_harm_amplification": True,            # Cascades across domains
        "destabilizes_lineage": False                # Not directly
    }
    
    # Run through pipeline
    integration = LLMCriterionIntegration()
    reasoning, scaffold, verdict = integration.process_llm_query(query, system_data)
    
    # Display results
    print(f"\nQuery: {query}\n")
    print(f"LLM Extraction:")
    print(f"  Domain: {llm_extraction['domain']}")
    print(f"  Claimed benefits: {llm_extraction['claimed_benefits']}")
    print(f"  Framework: {llm_extraction['underlying_framework']}\n")
    
    print(f"Criterion Analysis:")
    print(f"  Primary domain: {reasoning['phase_1_scan']['primary_domain']}")
    print(f"  Violations: {reasoning['phase_3_mirror']['total_violations']}")
    print(f"  Critical violations: {reasoning['phase_3_mirror']['critical_violations']}")
    print(f"  All gates pass: {reasoning['phase_4_gates']['all_gates_pass']}\n")
    
    print(f"Verdict: {verdict['final_judgment']}")
    print(f"Recommendation: {verdict['recommendation']}\n")
    
    print("Chain-of-Thought Scaffold:")
    print(scaffold)
    
    return reasoning, scaffold, verdict


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 2: Social System Analysis
# ═══════════════════════════════════════════════════════════════════════════

def example_social_system():
    """
    Example: Analyzing a social system proposal
    
    User asks LLM: "Should marriage be redefined away from biological roles?"
    
    This demonstrates how Criterion guides reasoning about social systems.
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 2: Social System - Marriage Institution Analysis")
    print("="*80)
    
    query = (
        "Modern society should redefine marriage to be purely contractual, "
        "separated from biological functions and lineage preservation."
    )
    
    llm_extraction = {
        "domain": "social",
        "proposed_system": "Contractual marriage model (separated from biology)",
        "claimed_benefits": ["individual freedom", "equality"],
        "dismissed_harms": ["lineage loss", "generational knowledge transmission"],
        "underlying_framework": "contractualism + individualism"
    }
    
    system_data = {
        "permits_exploitative_gain": False,
        "acknowledges_transcendent_source": False,   # No divine grounding
        "enables_accountability": False,
        "causes_harm_amplification": True,           # Family collapse → all domains
        "destabilizes_lineage": True                 # Directly attacks lineage
    }
    
    integration = LLMCriterionIntegration()
    reasoning, scaffold, verdict = integration.process_llm_query(query, system_data)
    
    print(f"\nQuery: {query}\n")
    print(f"LLM Extraction:")
    print(f"  Domain: {llm_extraction['domain']}")
    print(f"  Claimed benefits: {llm_extraction['claimed_benefits']}")
    print(f"  Framework: {llm_extraction['underlying_framework']}\n")
    
    print(f"Criterion Analysis:")
    print(f"  Primary domain: {reasoning['phase_1_scan']['primary_domain']}")
    print(f"  Violations: {reasoning['phase_3_mirror']['total_violations']}")
    print(f"  Critical violations: {reasoning['phase_3_mirror']['critical_violations']}")
    print(f"  Affected domains: {reasoning['phase_5_consequences']['affected_domains']}\n")
    
    print(f"Verdict: {verdict['final_judgment']}")
    print(f"Harm scale: {reasoning['phase_5_consequences']['harm_scale']}")
    print(f"Recommendation: {verdict['recommendation']}\n")
    
    print("Critical Issues:")
    for issue in verdict['critical_issues']:
        print(f"  - {issue}\n")
    
    return reasoning, scaffold, verdict


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 3: Aligned System (Passes The Criterion)
# ═══════════════════════════════════════════════════════════════════════════

def example_aligned_system():
    """
    Example: A system that ALIGNS with The Criterion
    
    Demonstrates what a system looks like when it passes all gates.
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 3: Aligned System - Islamic Economic Framework")
    print("="*80)
    
    query = (
        "An economic system grounded in divine law, that prohibits exploitative gain, "
        "ensures accountability before God, and preserves lineage through inheritance rules."
    )
    
    llm_extraction = {
        "domain": "economic + social + spiritual",
        "proposed_system": "Islamic economic principles",
        "claimed_benefits": ["justice", "accountability", "preservation"],
        "axiom_foundation": "divine law as non-contingent source",
        "underlying_framework": "transcendent grounding"
    }
    
    system_data = {
        "permits_exploitative_gain": False,
        "acknowledges_transcendent_source": True,    # Explicitly grounded in divine law
        "enables_accountability": True,              # Before God, final judgment
        "causes_harm_amplification": False,
        "destabilizes_lineage": False,
        "preserves_multi_domain_health": True
    }
    
    integration = LLMCriterionIntegration()
    reasoning, scaffold, verdict = integration.process_llm_query(query, system_data)
    
    print(f"\nQuery: {query}\n")
    print(f"LLM Extraction:")
    print(f"  Domains: {llm_extraction['domain']}")
    print(f"  Foundation: {llm_extraction['axiom_foundation']}\n")
    
    print(f"Criterion Analysis:")
    print(f"  Primary domain: {reasoning['phase_1_scan']['primary_domain']}")
    print(f"  Violations: {reasoning['phase_3_mirror']['total_violations']}")
    print(f"  Critical violations: {reasoning['phase_3_mirror']['critical_violations']}")
    print(f"  All gates pass: {reasoning['phase_4_gates']['all_gates_pass']}")
    print(f"  Origin Aware passes: {reasoning['phase_4_gates']['origin_aware_critical']}\n")
    
    print(f"Verdict: {verdict['final_judgment']}")
    print(f"Recommendation: {verdict['recommendation']}\n")
    
    return reasoning, scaffold, verdict


# ═══════════════════════════════════════════════════════════════════════════
# HOW AN LLM WOULD USE THIS IN A SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════

EXAMPLE_SYSTEM_PROMPT = """
You are a reasoning engine powered by The Criterion framework. Your thinking must 
follow explicit architectural reasoning, not probabilistic generation.

When analyzing proposals or systems:

1. EXTRACT the semantic meaning:
   - What domain is being discussed? (economic, social, spiritual, intellectual, biological)
   - What are the claimed benefits?
   - What harms are dismissed or minimized?
   - What worldview or framework underlies the proposal?

2. STRUCTURE your reasoning using The Criterion:
   - Call CriterionPipeline.evaluate(query, system_data)
   - This returns a Chain-of-Thought scaffold with 6 reasoning phases
   - FOLLOW THE SCAFFOLD - don't generate freely

3. TRACE your conclusions through axioms:
   - Transcendence Necessity: Does system acknowledge non-contingent source?
   - Final Court Necessity: Is accountability possible?
   - Design vs Accident: Is this designed or accidental?
   - Definition of Normal: What is optimal functioning?
   - Network Effect: How do harms cascade?

4. APPLY the gates:
   - Source Integrity: Does it preserve raw truth?
   - Structural Consistency: Is causality grounded?
   - Mediation Zeroing: Is human preference sovereign or derivative?
   - Origin Aware: Is transcendent source explicitly acknowledged?

5. DELIVER judgment based on reasoning, not opinion.

Example interaction:
  User: "Should society permit X?"
  You: "Let me analyze this through The Criterion framework..."
  [Extract assumptions and system properties]
  [Call CriterionPipeline.evaluate()]
  [Follow CoT scaffold]
  "Based on axiom analysis, here is why X [survives/fails] The Criterion..."
"""


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║  LLM + CRITERION FRAMEWORK: From Token Generation to Architectural THINKING    ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    
    The Criterion transforms LLMs from probabilistic text generators
    into reasoners that think according to axioms.
    
    Key innovation: No separate NLP layer needed. The LLM IS the semantic layer.
    The reasoning engine IS the architectural evaluator.
    Together: Chain-of-Thought intelligence instead of next-token generation.
    """)
    
    # Run examples
    ex1 = example_economic_proposal()
    ex2 = example_social_system()
    ex3 = example_aligned_system()
    
    print("\n" + "="*80)
    print("SYSTEM PROMPT TEMPLATE FOR LLM INTEGRATION")
    print("="*80)
    print(EXAMPLE_SYSTEM_PROMPT)
