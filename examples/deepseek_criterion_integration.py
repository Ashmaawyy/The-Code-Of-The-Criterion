"""
Complete Example: Using deepseek-r1:8b with The Criterion Framework

This script demonstrates the full integration:
1. Query deepseek-r1:8b for semantic extraction
2. Run Criterion reasoning engine
3. Get complete verdict with chain-of-thought

Prerequisites:
    pip install requests  # For Ollama API calls
    
Then start Ollama:
    ollama pull deepseek-r1:8b
    ollama serve
"""

from evaluation.llm_integration import OllamaLLMBridge, analyze_with_deepseek
from evaluation.pipeline import CriterionPipeline
import json


def example_1_economic_proposal():
    """
    Example 1: Analyzing an economic proposal
    Tests deepseek-r1:8b's semantic extraction on a complex business proposal
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Economic Proposal with Deepseek-R1:8b Integration")
    print("="*80)
    
    query = """
    We propose a new business model where we charge customers an upfront fee of $100,
    which gives them access to our platform. However, their usage data will be sold to
    third parties for targeted marketing. The customers won't be told about the data
    selling. We justify this by saying the upfront fee makes our service cheap and
    accessible to low-income customers, so the data trade-off creates net social good.
    """
    
    print(f"\nPROPOSAL:\n{query}")
    
    try:
        # Use the high-level interface for full analysis
        result = analyze_with_deepseek(query, verbose=True)
        
        # Extract key findings
        print("\n" + "-"*80)
        print("ANALYSIS SUMMARY")
        print("-"*80)
        
        verdict = result['phase_6_verdict']
        print(f"\n✓ Survival: {verdict['final_judgment']}")
        print(f"✓ Recommendation: {verdict['recommendation']}")
        
        violations = result['reasoning_phases']['phase_3_mirror']['violations']
        print(f"\n⚠️  Axiom Violations Found: {len(violations)}")
        for v in violations[:3]:  # Show first 3
            print(f"   - {v['violation']}: {v['consequence']}")
        
        gates = result['reasoning_phases']['phase_4_gates']
        print(f"\n🚪 Gate Status:")
        for gate_name, gate_info in gates['gate_details'].items():
            status = "✓ PASS" if gate_info['pass'] else "✗ FAIL"
            print(f"   {status} - {gate_name}")
        
        return result
        
    except ConnectionError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure Ollama is running:")
        print("  1. ollama pull deepseek-r1:8b")
        print("  2. ollama serve")
        return None


def example_2_social_system():
    """
    Example 2: Analyzing a social/institutional proposal
    Tests deepseek-r1:8b on institutional-level changes
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Social System Proposal with Deepseek-R1:8b Integration")
    print("="*80)
    
    query = """
    We propose redefining 'family' to include any group of people who live together
    and care for each other, regardless of biological relationships or legal marriage.
    This will make society more inclusive and reduce the stigma on alternative
    household arrangements. We'll update all legal, financial, and educational
    systems to recognize this new definition. This change is simply about being more
    accepting and shouldn't cause any friction with existing institutions.
    """
    
    print(f"\nPROPOSAL:\n{query}")
    
    try:
        result = analyze_with_deepseek(query, verbose=True)
        
        print("\n" + "-"*80)
        print("ANALYSIS SUMMARY")
        print("-"*80)
        
        verdict = result['phase_6_verdict']
        print(f"\n✓ Survival: {verdict['final_judgment']}")
        print(f"✓ Critical Issues: {len(verdict['critical_issues'])} identified")
        for issue in verdict['critical_issues'][:2]:
            print(f"   - {issue}")
        
        # Check for axiom violations
        violations = result['reasoning_phases']['phase_3_mirror']['violations']
        print(f"\n⚠️  Axiom Violations: {len(violations)}")
        
        # Check for network effects
        consequences = result['reasoning_phases']['phase_5_consequences']
        print(f"\n🌐 Network Effects:")
        print(f"   - Affected domains: {', '.join(consequences['affected_domains'])}")
        print(f"   - Harm scale: {consequences['harm_scale']}")
        
        return result
        
    except ConnectionError as e:
        print(f"\n❌ Error: {e}")
        return None


def example_3_direct_bridge_usage():
    """
    Example 3: Direct bridge usage for more control
    Shows how to use the OllamaLLMBridge directly
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Direct OllamaLLMBridge Usage")
    print("="*80)
    
    query = """
    Should we implement a social credit system that tracks citizens' financial,
    legal, and social compliance, with real-time access by employers, schools,
    and government agencies? Benefits: Better risk assessment, reduced fraud,
    faster decision-making.
    """
    
    print(f"\nQUERY:\n{query}\n")
    
    try:
        # Initialize bridge directly
        print("🔗 Connecting to Ollama...")
        bridge = OllamaLLMBridge()
        
        # Step 1: Extract semantic meaning
        print("📡 Extracting semantic meaning...")
        system_data = bridge.extract_semantic_meaning(query)
        
        print(f"\n   Domain: {system_data['domain']}")
        print(f"   Intent: {system_data['intent']}")
        print(f"   Assumptions: {system_data['assumptions']}")
        print(f"   Beneficiaries: {system_data['beneficiaries']}")
        print(f"   Dismissed harms: {system_data['dismissed_harms']}")
        
        # Step 2: Run through pipeline
        print("\n🧠 Running reasoning engine...")
        pipeline = CriterionPipeline()
        result = pipeline.evaluate(query, system_data)
        
        # Step 3: Display verdict
        print("\n" + "-"*80)
        print("VERDICT")
        print("-"*80)
        verdict = result['phase_6_verdict']
        print(f"\nFinal Judgment: {verdict['final_judgment']}")
        print(f"Recommendation: {verdict['recommendation']}")
        
        # Show reasoning for critical violations
        if verdict['critical_issues']:
            print(f"\n🚨 Critical Issues Requiring Attention:")
            for issue in verdict['critical_issues']:
                print(f"   • {issue}")
        
        return result
        
    except ConnectionError as e:
        print(f"\n❌ Error: {e}")
        print("\nSetup Ollama:")
        print("  1. Install Ollama from https://ollama.ai")
        print("  2. Run: ollama pull deepseek-r1:8b")
        print("  3. Run: ollama serve")
        return None


def example_4_batch_analysis():
    """
    Example 4: Batch analysis of multiple proposals
    Shows how to analyze multiple queries in sequence
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Batch Analysis")
    print("="*80)
    
    queries = [
        "Should we eliminate all regulations on cryptocurrency to maximize innovation?",
        "Can we replace human teachers with AI tutors to reduce educational costs?",
        "Should social media platforms be allowed to use any algorithm without oversight?"
    ]
    
    results = []
    
    try:
        bridge = OllamaLLMBridge()
        pipeline = CriterionPipeline()
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Analyzing...")
            print(f"Query: {query[:60]}...")
            
            # Extract semantic meaning
            system_data = bridge.extract_semantic_meaning(query)
            
            # Run reasoning
            result = pipeline.evaluate(query, system_data)
            
            # Store result
            results.append({
                'query': query,
                'verdict': result['phase_6_verdict']['final_judgment'],
                'violations': len(result['reasoning_phases']['phase_3_mirror']['violations'])
            })
            
            print(f"   → {result['phase_6_verdict']['final_judgment']}")
            print(f"   → {result['reasoning_phases']['phase_3_mirror']['total_violations']} violations")
        
        # Summary
        print("\n" + "="*80)
        print("BATCH SUMMARY")
        print("="*80)
        
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r['query'][:70]}...")
            print(f"   Verdict: {r['verdict']}")
            print(f"   Violations: {r['violations']}")
        
        pass_count = sum(1 for r in results if "SURVIVE" in r['verdict'])
        print(f"\n📊 Summary: {pass_count}/{len(results)} proposals survive Criterion evaluation")
        
        return results
        
    except ConnectionError as e:
        print(f"\n❌ Error: {e}")
        return None


def example_5_detailed_reasoning_trace():
    """
    Example 5: Detailed reasoning trace through all 6 phases
    Shows the complete thinking process for transparency
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: Detailed 6-Phase Reasoning Trace")
    print("="*80)
    
    query = """
    We propose using personalized medical treatments based on genetic testing.
    Patients would submit their DNA, and we'd design treatments optimized for
    their individual biology. This eliminates the one-size-fits-all approach
    of traditional medicine.
    """
    
    print(f"\nQUERY:\n{query}\n")
    
    try:
        result = analyze_with_deepseek(query, verbose=False)
        
        # Show all 6 phases with details
        phases = result['reasoning_phases']
        
        print("PHASE 1: SCAN (Domain Identification)")
        print("-" * 60)
        scan = phases['phase_1_scan']
        print(f"Primary Domain: {scan['primary_domain']}")
        print(f"Secondary Domains: {', '.join(scan['detected_contexts'])}")
        print(f"Reasoning: {scan['reasoning']}\n")
        
        print("PHASE 2: EXTRACT (Assumptions & Intent)")
        print("-" * 60)
        extract = phases['phase_2_extract']
        print(f"Assumption Count: {extract['assumption_count']}")
        print(f"Beneficiaries Claimed: {extract['beneficiaries_claimed']}")
        print(f"Dismissed Harms: {extract['dismissed_harms']}")
        print(f"Inferred Intent: {extract['inferred_intent']}\n")
        
        print("PHASE 3: MIRROR (Axiom Compliance)")
        print("-" * 60)
        mirror = phases['phase_3_mirror']
        print(f"Total Violations: {mirror['total_violations']}")
        print(f"Critical Violations: {mirror['critical_violations']}")
        print(f"Compliance Status: {mirror['compliance_status']}")
        if mirror['violations']:
            print("Violations:")
            for v in mirror['violations'][:3]:
                print(f"  • {v['violation']}: {v['consequence']}\n")
        
        print("PHASE 4: GATES (Survival Filters)")
        print("-" * 60)
        gates = phases['phase_4_gates']
        for gate_name, score in gates['gate_scores'].items():
            print(f"{gate_name}: {score:.1f}/10")
        print(f"All Gates Pass: {gates['all_gates_pass']}\n")
        
        print("PHASE 5: CONSEQUENCES (Network Effects)")
        print("-" * 60)
        consequences = phases['phase_5_consequences']
        print(f"Affected Domains: {', '.join(consequences['affected_domains'])}")
        print(f"Harm Scale: {consequences['harm_scale']}\n")
        
        print("PHASE 6: VERDICT (Final Judgment)")
        print("-" * 60)
        verdict = result['phase_6_verdict']
        print(f"Final Judgment: {verdict['final_judgment']}")
        print(f"Recommendation: {verdict['recommendation']}")
        if verdict['critical_issues']:
            print("Critical Issues:")
            for issue in verdict['critical_issues']:
                print(f"  • {issue}\n")
        
        return result
        
    except ConnectionError as e:
        print(f"\n❌ Error: {e}")
        return None


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("DEEPSEEK-R1:8B + THE CRITERION FRAMEWORK")
    print("Complete Integration Examples")
    print("="*80)
    
    print("\n⚠️  Prerequisites:")
    print("   1. pip install requests")
    print("   2. ollama pull deepseek-r1:8b")
    print("   3. ollama serve (in another terminal)")
    
    # Run examples (catching connection errors gracefully)
    try:
        # Uncomment to run individual examples:
        # example_1_economic_proposal()
        # example_2_social_system()
        # example_3_direct_bridge_usage()
        # example_4_batch_analysis()
        # example_5_detailed_reasoning_trace()
        
        # Run just the direct bridge example (simplest test)
        print("\n\nStarting example 3 (simplest test)...\n")
        example_3_direct_bridge_usage()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
