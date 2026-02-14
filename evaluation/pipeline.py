"""
Integrated Pipeline: The Criterion as Chain-of-Thought Framework for LLM Reasoning

This pipeline operationalizes The Criterion as a structured thinking framework that 
guides LLMs beyond simple next-token generation into principled reasoning.

Architecture:
- LLM uses The Criterion as internal reasoning structure
- Reasoning engine breaks thinking into 6 phases (SCAN → EXTRACT → MIRROR → GATES → CONSEQUENCES → VERDICT)
- Every conclusion is traceable through explicit axiom-based reasoning
- Output serves as CoT (Chain-of-Thought) scaffold for LLM generation

The LLM becomes the EXTRACT layer (semantic understanding + assumption identification)
The Reasoning Engine operationalizes SCAN, MIRROR, GATES, CONSEQUENCES, VERDICT
Together they create architectural reasoning, not probabilistic generation
"""

from evaluation.reasoning_engine import CriterionReasoningEngine
from evaluation.gates import (
    source_integrity_gate,
    structural_consistency_gate,
    mediation_zeroing_gate,
    origin_aware_gate
)
from typing import Dict, Any, List, Optional
import json


class CriterionPipeline:
    """
    Integrated reasoning pipeline that combines:
    1. LLM as semantic/linguistic layer (Layer 2)
    2. Reasoning Engine as architectural evaluator (Layer 5)
    
    This transforms an LLM from a next-token generator into a chain-of-thought reasoner
    that thinks according to axioms rather than probability distributions.
    """
    
    def __init__(self, axioms_path: Optional[str] = None):
        """Initialize the pipeline with reasoning engine"""
        self.reasoning_engine = CriterionReasoningEngine(axioms_path)
    
    def evaluate(self, query: str, system_data: Dict[str, Any], 
                 llm_extraction: Optional[Dict] = None) -> Dict:
        """
        INTEGRATED PIPELINE EVALUATION
        
        This is what an LLM system prompt calls to structure its reasoning.
        
        Flow:
        1. LLM provides initial extraction (assumptions, intent) - OR engine infers it
        2. Engine runs full reasoning pipeline
        3. Return structured CoT scaffold for LLM to use in generation
        
        Args:
            query: The statement/proposal to evaluate
            system_data: System properties and attributes
            llm_extraction: Optional extraction from LLM (assumptions, intent, etc.)
                          If provided, enriches the analysis with LLM understanding
        
        Returns:
            Structured reasoning output for LLM to use in chain-of-thought generation
        """
        
        # Run complete reasoning pipeline
        full_analysis = self.reasoning_engine.reason(query, system_data)
        
        # Enrich with LLM extraction if provided
        if llm_extraction:
            full_analysis["analysis"]["llm_semantic_layer"] = llm_extraction
        
        # Extract key components for CoT scaffold
        verdict_data = full_analysis["verdict"]
        
        return {
            "query": query,
            "reasoning_phases": {
                "phase_1_scan": {
                    "primary_domain": verdict_data["analysis_chain"]["1_scan"]["primary_domain"],
                    "detected_contexts": verdict_data["analysis_chain"]["1_scan"]["secondary_domains"],
                    "reasoning": verdict_data["analysis_chain"]["1_scan"]["reasoning"]
                },
                "phase_2_extract": {
                    "assumption_count": verdict_data["analysis_chain"]["2_assumptions"]["total_assumptions"],
                    "assumption_types": verdict_data["analysis_chain"]["2_assumptions"]["assumption_types"],
                    "beneficiaries_claimed": verdict_data["analysis_chain"]["2_assumptions"]["beneficiaries"],
                    "dismissed_harms": verdict_data["analysis_chain"]["2_assumptions"]["dismissed_harms"],
                    "inferred_intent": verdict_data["analysis_chain"]["2_assumptions"]["inferred_intent"],
                    "llm_semantic_enrichment": llm_extraction if llm_extraction else None
                },
                "phase_3_mirror": {
                    "total_violations": verdict_data["analysis_chain"]["3_axiom_mirror"]["total_violations"],
                    "critical_violations": verdict_data["analysis_chain"]["3_axiom_mirror"]["critical_violations"],
                    "violations": verdict_data["analysis_chain"]["3_axiom_mirror"]["violations"],
                    "compliance_status": verdict_data["analysis_chain"]["3_axiom_mirror"]["compliance"],
                    "severity_distribution": {
                        "critical": verdict_data["analysis_chain"]["3_axiom_mirror"]["critical_violations"],
                        "high": sum(1 for v in verdict_data["analysis_chain"]["3_axiom_mirror"]["violations"]
                                   if v.get("severity") == "high")
                    }
                },
                "phase_4_gates": {
                    "gate_scores": {
                        name: gate["score"]
                        for name, gate in verdict_data["analysis_chain"]["4_gates"]["gate_status"].items()
                    },
                    "gate_details": verdict_data["analysis_chain"]["4_gates"]["gate_status"],
                    "all_gates_pass": verdict_data["analysis_chain"]["4_gates"]["all_gates_pass"],
                    "origin_aware_critical": verdict_data["analysis_chain"]["4_gates"]["origin_aware_pass"],
                    "critical_path": verdict_data["analysis_chain"]["4_gates"]["critical_path"]
                },
                "phase_5_consequences": {
                    "affected_domains": verdict_data["analysis_chain"]["5_consequences"]["affected_domains"],
                    "harm_scale": verdict_data["analysis_chain"]["5_consequences"]["harm_scale"],
                    "critical_tipping_points": [
                        {
                            "friction": c.get("friction"),
                            "time_horizon": c.get("time_horizon"),
                            "reversibility": c.get("reversibility")
                        }
                        for c in verdict_data["analysis_chain"]["5_consequences"]["critical_tipping_points"]
                    ],
                    "total_affected_domains": len(verdict_data["analysis_chain"]["5_consequences"]["affected_domains"])
                }
            },
            "phase_6_verdict": {
                "final_judgment": verdict_data["final_judgment"]["verdict"],
                "survival": verdict_data["final_judgment"]["survival"],
                "confidence": verdict_data["final_judgment"]["confidence_level"],
                "reasoning_summary": verdict_data["final_judgment"]["reasoning_summary"],
                "recommendation": verdict_data["final_judgment"]["recommendation"],
                "critical_issues": verdict_data["final_judgment"]["critical_issues"]
            },
            "cot_scaffold": self._generate_cot_scaffold(verdict_data),
            "structured_output": full_analysis
        }
    
    def _generate_cot_scaffold(self, verdict_data: Dict) -> str:
        """
        Generate a Chain-of-Thought scaffold that guides LLM reasoning.
        
        This is the concrete thinking structure the LLM uses internally
        instead of relying on probabilistic next-token generation.
        """
        scaffold = f"""
═══════════════════════════════════════════════════════════════════════════════
CHAIN-OF-THOUGHT REASONING SCAFFOLD
═══════════════════════════════════════════════════════════════════════════════

THINKING STRUCTURE (Use this to reason architecturally, not generatively):

PHASE 1 - SCAN (Domain Identification):
  Primary system: {verdict_data["analysis_chain"]["1_scan"]["primary_domain"]}
  Context domains: {verdict_data["analysis_chain"]["1_scan"]["secondary_domains"]}
  → Therefore, we must evaluate using {verdict_data["analysis_chain"]["1_scan"]["primary_domain"]}-specific axioms

PHASE 2 - EXTRACT (Assumption Parsing):
  Total assumptions embedded: {verdict_data["analysis_chain"]["2_assumptions"]["total_assumptions"]}
  Assumption types: {verdict_data["analysis_chain"]["2_assumptions"]["assumption_types"]}
  Claimed beneficiaries: {verdict_data["analysis_chain"]["2_assumptions"]["beneficiaries"]}
  Dismissed harms: {verdict_data["analysis_chain"]["2_assumptions"]["dismissed_harms"] or 'none listed'}
  True intent: {verdict_data["analysis_chain"]["2_assumptions"]["inferred_intent"]}
  → Therefore, the proposal attempts to: [hidden premises here]

PHASE 3 - MIRROR (Axiom Compliance):
  Violations detected: {verdict_data["analysis_chain"]["3_axiom_mirror"]["total_violations"]}
  Critical violations: {verdict_data["analysis_chain"]["3_axiom_mirror"]["critical_violations"]}
  Axiom compliance:
"""
        for axiom, compliant in verdict_data["analysis_chain"]["3_axiom_mirror"]["compliance"].items():
            status = "✓ Compliant" if compliant else "✗ Violated"
            scaffold += f"    - {axiom}: {status}\n"
        
        scaffold += f"""
  → Therefore, system has {verdict_data["analysis_chain"]["3_axiom_mirror"]["total_violations"]} design flaws

PHASE 4 - GATES (Survival Filter):
  Gate evaluation:
"""
        for gate_name, gate_data in verdict_data["analysis_chain"]["4_gates"]["gate_status"].items():
            score = gate_data["score"]
            status = "PASS" if gate_data["passed"] else "FAIL"
            scaffold += f"    - {gate_name}: {score}/100 [{status}]\n"
        
        scaffold += f"""
  Origin-Aware gate (mandatory): {verdict_data["analysis_chain"]["4_gates"]["origin_aware_pass"]}
  All gates pass: {verdict_data["analysis_chain"]["4_gates"]["all_gates_pass"]}
  → Therefore, system {"SURVIVES" if verdict_data["analysis_chain"]["4_gates"]["critical_path"] else "FAILS"} survival gates

PHASE 5 - CONSEQUENCES (Network Effect Tracing):
  Affected domains: {verdict_data["analysis_chain"]["5_consequences"]["affected_domains"]}
  Overall harm scale: {verdict_data["analysis_chain"]["5_consequences"]["harm_scale"]}
  Critical tipping points: {len(verdict_data["analysis_chain"]["5_consequences"]["critical_tipping_points"])}
  → Therefore, consequences compound across {len(verdict_data["analysis_chain"]["5_consequences"]["affected_domains"])} domains

PHASE 6 - VERDICT (Structured Judgment):
  Final judgment: {verdict_data["final_judgment"]["verdict"]}
  Confidence: {verdict_data["final_judgment"]["confidence_level"]}
  
  Reasoning: {verdict_data["final_judgment"]["reasoning_summary"]}
  
  Recommendation: {verdict_data["final_judgment"]["recommendation"]}
  
  Critical issues requiring attention:
"""
        if verdict_data["final_judgment"]["critical_issues"]:
            for issue in verdict_data["final_judgment"]["critical_issues"]:
                scaffold += f"    - {issue}\n"
        else:
            scaffold += "    - None detected\n"
        
        scaffold += f"""
═══════════════════════════════════════════════════════════════════════════════
CONCLUSION:
This reasoning chain shows WHY the system {"survives" if verdict_data["final_judgment"]["survival"] else "fails"}, 
not just that it does. Each judgment is traceable to axiom-based reasoning.
═══════════════════════════════════════════════════════════════════════════════
"""
        return scaffold
    
    def evaluate_legacy(self, query: str, system: Dict, axioms: Optional[Dict] = None) -> Dict:
        """
        Legacy interface for backward compatibility.
        Calls the new integrated pipeline but returns legacy format.
        """
        result = self.evaluate(query, system, axioms)
        
        return {
            "Query": query,
            "Primary System": result["reasoning_phases"]["phase_1_scan"]["primary_domain"],
            "Friction Points": [
                v["violation"] for v in result["reasoning_phases"]["phase_3_mirror"]["violations"]
            ],
            "Consequences": [
                f"{v['violation']} → {v['consequence']}"
                for v in result["reasoning_phases"]["phase_3_mirror"]["violations"]
            ],
            "Tri-Axial Gate Scores": result["reasoning_phases"]["phase_4_gates"]["gate_scores"],
            "Origin-Aware Gate": "Survive" if result["reasoning_phases"]["phase_4_gates"]["origin_aware_critical"] else "Fail",
            "Total Score": sum(result["reasoning_phases"]["phase_4_gates"]["gate_scores"].values()),
            "Final Judgment": result["phase_6_verdict"]["final_judgment"],
            "Chain-of-Thought": result["cot_scaffold"]
        }
    
    def evaluate_with_deepseek(self, query: str, verbose: bool = False) -> Dict:
        """
        Full integration: deepseek-r1:8b → Criterion reasoning → verdict
        
        Automatically extracts semantic meaning using deepseek-r1:8b from Ollama,
        then runs through the complete reasoning pipeline.
        
        Args:
            query: User query or proposal to analyze
            verbose: Print intermediate steps
            
        Returns:
            Complete analysis with LLM semantic layer integrated
            
        Raises:
            ConnectionError: If Ollama is not running or model not found
        """
        from evaluation.llm_integration import OllamaLLMBridge
        
        # Initialize LLM bridge (will verify Ollama connection)
        bridge = OllamaLLMBridge()
        
        # Extract semantic meaning using deepseek-r1:8b
        if verbose:
            print(f"\n📡 Extracting semantic meaning with deepseek-r1:8b...")
        system_data = bridge.extract_semantic_meaning(query)
        
        if verbose:
            print(f"   Domain: {system_data['domain']}")
            print(f"   Intent: {system_data['intent']}")
            print(f"   Assumptions identified: {len(system_data['assumptions'])}")
        
        # Run reasoning pipeline with LLM extraction
        if verbose:
            print(f"\n🧠 Running Criterion reasoning engine...")
        result = self.evaluate(query, system_data, llm_extraction=system_data)
        
        if verbose:
            print(f"   Axiom violations: {result['reasoning_phases']['phase_3_mirror']['total_violations']}")
            print(f"   Gates status: {'PASS' if result['reasoning_phases']['phase_4_gates']['all_gates_pass'] else 'FAIL'}")
            print(f"   Verdict: {result['phase_6_verdict']['final_judgment']}")
        
        return result


# Standalone functions for direct use (simple interface)

def evaluate(query: str, system: Dict, axioms: Optional[Dict] = None) -> Dict:
    """
    Simple standalone evaluation function.
    
    Args:
        query: Statement/proposal to evaluate
        system: System properties
        axioms: Optional axioms dict (for legacy compatibility)
    
    Returns:
        Integrated reasoning output with CoT scaffold
    """
    pipeline = CriterionPipeline()
    return pipeline.evaluate(query, system, axioms)
