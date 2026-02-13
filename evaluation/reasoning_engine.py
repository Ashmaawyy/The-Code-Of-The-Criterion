"""
Layer 5: The Criterion Reasoning Engine

This module implements The Criterion as a reasoning framework that an LLM can use
to structure its thinking architecturally. It operationalizes The Criterion Prompt
into executable reasoning phases:

1. SCAN - Identify what system is being analyzed
2. EXTRACT - Parse assumptions and intent from statements
3. MIRROR - Check against core axioms
4. GATES - Apply tri-axial survival filters
5. CONSEQUENCES - Trace network effects and cascading impacts
6. VERDICT - Generate final judgment with full reasoning chain

Usage:
    engine = CriterionReasoningEngine()
    reasoning = engine.reason(query, system_data)
    verdict = reasoning['verdict']
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum

from evaluation.gates import (
    source_integrity_gate,
    structural_consistency_gate,
    mediation_zeroing_gate,
    origin_aware_gate
)


@dataclass
class Friction:
    """Represents a design violation detected during axiom mirroring"""
    axiom: str
    violation: str
    severity: str  # "critical", "high", "medium", "low"
    consequence: str
    affected_domains: List[str]


@dataclass
class ConsequenceChain:
    """Traces cascading effects of a friction point across domains and time"""
    friction: str
    immediate_effect: str
    secondary_effects: str
    tertiary_effects: str
    systemic_amplification: str
    affected_domains: List[str]
    time_horizon: str
    reversibility: str


class SystemDomain(Enum):
    """Domains of systems that can be analyzed"""
    ECONOMIC = "economic"
    SOCIAL = "social"
    SPIRITUAL = "spiritual"
    INTELLECTUAL = "intellectual"
    BIOLOGICAL = "biological"
    GENERAL = "general"


class CriterionReasoningEngine:
    """
    The Criterion as a reasoning framework for LLM-guided architecture analysis.
    
    This engine structures thinking about proposals, systems, and ideas using
    The Criterion's axiom-based approach. An LLM uses this to reason through
    problems architecturally rather than generatively.
    """
    
    def __init__(self, axioms_path: Optional[str] = None):
        """
        Initialize the reasoning engine.
        
        Args:
            axioms_path: Path to core_axioms.json. If None, uses default location.
        """
        if axioms_path is None:
            axioms_path = str(Path(__file__).parent.parent / "axioms" / "core_axioms.json")
        
        with open(axioms_path, 'r') as f:
            self.axioms = json.load(f)
        
        self.domain_keywords = {
            SystemDomain.ECONOMIC: ["economy", "interest", "finance", "money", "capital", 
                                   "trade", "commerce", "wealth", "profit", "gain", "cost",
                                   "market", "business", "investment", "transaction"],
            SystemDomain.SOCIAL: ["family", "marriage", "gender", "lineage", "community",
                                 "society", "relationship", "kinship", "tribe", "bond",
                                 "status", "hierarchy", "role", "responsibility"],
            SystemDomain.SPIRITUAL: ["purpose", "meaning", "god", "morality", "soul",
                                    "faith", "transcendent", "divine", "sacred", "virtue",
                                    "obligation", "conscience", "truth", "justice"],
            SystemDomain.INTELLECTUAL: ["knowledge", "science", "reason", "logic", "learning",
                                       "truth", "epistemology", "understanding", "wisdom",
                                       "evidence", "proof", "inquiry"],
            SystemDomain.BIOLOGICAL: ["life", "health", "reproduction", "body", "survival",
                                     "natural", "instinct", "biological", "organic", "vitality"]
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: SCAN - Identify what system is being analyzed
    # ═══════════════════════════════════════════════════════════════════
    
    def scan(self, query: str) -> Dict:
        """
        SCAN: Identify the primary domain and secondary contexts.
        
        This phase categorizes what kind of system/idea is being analyzed.
        Understanding the domain is critical because different domains have
        different preservation requirements and axiom applications.
        
        Args:
            query: The statement or query to analyze
            
        Returns:
            Dict with primary_system, detected_systems, and reasoning
        """
        query_lower = query.lower()
        detected_systems = []
        
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                detected_systems.append((domain, score))
        
        # Sort by score, highest first
        detected_systems.sort(key=lambda x: x[1], reverse=True)
        
        primary_system = detected_systems[0][0] if detected_systems else SystemDomain.GENERAL
        secondary_systems = [d[0] for d in detected_systems[1:3]]
        
        return {
            "primary_system": primary_system.value,
            "detected_systems": [d.value for d in [primary_system] + secondary_systems],
            "system_scores": {d[0].value: d[1] for d in detected_systems},
            "reasoning": (
                f"Query analyzed as primarily {primary_system.value} domain. "
                f"Secondary contexts detected in: {', '.join([s.value for s in secondary_systems]) if secondary_systems else 'none'}."
            )
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: EXTRACT - Parse assumptions and intent
    # ═══════════════════════════════════════════════════════════════════
    
    def extract_assumptions(self, statement: str) -> Dict:
        """
        EXTRACT: Identify embedded assumptions and true intent.
        
        This phase surfaces hidden premises using Layer 2 logic.
        It answers: What is *really* being claimed? What assumptions underlie it?
        
        Args:
            statement: The statement to analyze
            
        Returns:
            Dict with statement_type, assumptions, intent, beneficiaries, harms
        """
        # These would normally come from Layer 2; for now, basic extraction
        assumption_triggers = {
            "because": "causal assumption",
            "should": "moral assumption",
            "is natural": "naturalization assumption",
            "is obvious": "obviousness assumption",
            "everyone knows": "universal acceptance assumption",
            "best for": "optimization assumption",
            "necessary to": "necessity assumption"
        }
        
        statement_lower = statement.lower()
        detected_assumptions = []
        
        for trigger, category in assumption_triggers.items():
            if trigger in statement_lower:
                detected_assumptions.append({
                    "type": category,
                    "trigger": trigger,
                    "implicitness": 0.7
                })
        
        # Identify beneficiaries
        beneficiary_keywords = {
            "people": "humanity",
            "society": "social collective",
            "economy": "economic actors",
            "majority": "numerical majority",
            "minority": "marginalized groups",
            "future": "future generations"
        }
        
        beneficiaries = [
            (entity, group) for entity, group in beneficiary_keywords.items()
            if entity in statement_lower
        ]
        
        # Extract potential harms (words suggesting negation)
        harm_keywords = ["doesn't harm", "only affects", "minimal", "negligible", "acceptable cost"]
        dismissed_harms = [keyword for keyword in harm_keywords if keyword in statement_lower]
        
        return {
            "statement_type": self._classify_statement(statement),
            "assumptions": detected_assumptions,
            "assumption_count": len(detected_assumptions),
            "beneficiaries": [b[1] for b in beneficiaries],
            "dismissed_harms": dismissed_harms,
            "inferred_intent": self._extract_intent(statement)
        }
    
    def _classify_statement(self, statement: str) -> str:
        """Classify statement type"""
        stmt_lower = statement.lower()
        if any(word in stmt_lower for word in ["should", "must", "ought"]):
            return "prescriptive"
        elif any(word in stmt_lower for word in ["is", "are", "exists"]):
            return "descriptive"
        elif any(word in stmt_lower for word in ["good", "bad", "better", "worse"]):
            return "evaluative"
        return "general"
    
    def _extract_intent(self, statement: str) -> str:
        """Extract the real intent behind the statement"""
        stmt_lower = statement.lower()
        if "should" in stmt_lower or "must" in stmt_lower:
            return f"Establish obligation: {statement[:100]}..."
        elif "because" in stmt_lower:
            parts = statement.split("because")
            return f"Justify: {parts[0].strip()}"
        return f"Assert: {statement[:100]}..."
    
    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: MIRROR - Check against axioms
    # ═══════════════════════════════════════════════════════════════════
    
    def mirror_against_axioms(self, system_data: Dict, system_type: str) -> Dict:
        """
        MIRROR: Compare system against core axioms.
        
        This phase identifies "frictions" - points where the proposed system
        violates foundational axioms. Each friction represents a design defect
        that will cascade into consequences.
        
        Args:
            system_data: The system/idea being evaluated
            system_type: Primary domain (from SCAN phase)
            
        Returns:
            Dict with frictions, axiom_compliance, and severity assessment
        """
        frictions = []
        axiom_checks = {}
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Transcendence Necessity Axiom
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if not system_data.get("acknowledges_transcendent_source"):
            frictions.append(Friction(
                axiom="Transcendence Necessity",
                violation="System does not acknowledge non-contingent source for meaning/purpose",
                severity="critical",
                consequence="Meaning becomes circular; purpose unfounded; system collapses into nihilism",
                affected_domains=["spiritual", "intellectual"]
            ))
            axiom_checks["transcendence"] = False
        else:
            axiom_checks["transcendence"] = True
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Final Court Necessity Axiom
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if not system_data.get("enables_accountability"):
            frictions.append(Friction(
                axiom="Final Court Necessity",
                violation="System lacks mechanism for ultimate accountability and justice",
                severity="critical",
                consequence="Moral debts unresolved; perpetrators unpunished; victims uncompensated; justice remains incomplete",
                affected_domains=["spiritual", "social"]
            ))
            axiom_checks["accountability"] = False
        else:
            axiom_checks["accountability"] = True
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Design vs Accident Axiom (Domain-Specific)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if system_type == "economic":
            if system_data.get("permits_exploitative_gain"):
                frictions.append(Friction(
                    axiom="Design vs Accident",
                    violation="Economic system permits extractive rather than preservative circulation",
                    severity="high",
                    consequence="Degenerative economic model → wealth concentration → systemic inequality → collapse",
                    affected_domains=["economic", "social"]
                ))
                axiom_checks["design_economic"] = False
            else:
                axiom_checks["design_economic"] = True
        
        if system_type == "social":
            if system_data.get("destabilizes_lineage"):
                frictions.append(Friction(
                    axiom="Design vs Accident",
                    violation="Social system undermines lineage preservation and intergenerational continuity",
                    severity="high",
                    consequence="Family dissolution → cultural fragmentation → loss of knowledge transmission → societal collapse",
                    affected_domains=["social", "biological"]
                ))
                axiom_checks["design_social"] = False
            else:
                axiom_checks["design_social"] = True
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Definition of Normal Axiom
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if system_data.get("deviates_from_optimal_functioning"):
            deviation_domain = system_data.get("deviation_domain", "unknown")
            frictions.append(Friction(
                axiom="Definition of Normal",
                violation=f"System deviates from optimal human functioning in {deviation_domain}",
                severity="high",
                consequence="Normalization of dysfunction → reduced flourishing → generational degradation",
                affected_domains=[deviation_domain, "biological"]
            ))
            axiom_checks["definition_normal"] = False
        else:
            axiom_checks["definition_normal"] = True
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Network Effect Axiom
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if system_data.get("causes_harm_amplification"):
            frictions.append(Friction(
                axiom="Network Effect",
                violation="System's local benefits compound into exponential global harm",
                severity="critical",
                consequence="Cascading systemic degradation → multi-domain collapse → irreversible damage",
                affected_domains=list(self.domain_keywords.keys())  # All domains affected
            ))
            axiom_checks["network_effect"] = False
        else:
            axiom_checks["network_effect"] = True
        
        return {
            "frictions": [asdict(f) for f in frictions],
            "axiom_compliance": axiom_checks,
            "total_violations": len(frictions),
            "critical_violations": sum(1 for f in frictions if f.severity == "critical"),
            "severity_distribution": {
                "critical": sum(1 for f in frictions if f.severity == "critical"),
                "high": sum(1 for f in frictions if f.severity == "high"),
                "medium": sum(1 for f in frictions if f.severity == "medium"),
                "low": sum(1 for f in frictions if f.severity == "low")
            }
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: GATES - Apply tri-axial survival filters
    # ═══════════════════════════════════════════════════════════════════
    
    def apply_gates(self, system_data: Dict) -> Dict:
        """
        GATES: Apply the four survival gates.
        
        These gates form the tri-axial filter: a system must pass all gates
        to survive The Criterion. Origin Aware gate is mandatory.
        
        Args:
            system_data: The system being evaluated
            
        Returns:
            Dict with gate scores, pass/fail status, and reasoning
        """
        gates = {
            "Source Integrity": {
                "score": source_integrity_gate(system_data),
                "criteria": "Preserves raw truth without reduction or distortion",
                "required": True,
                "reasoning": (
                    "System must accept raw truth as-is, not reinterpret for convenience. "
                    "Requires evidence-based or revelation-based justification."
                )
            },
            "Structural Consistency": {
                "score": structural_consistency_gate(system_data),
                "criteria": "Grounds causality and morality in non-contingent source",
                "required": True,
                "reasoning": (
                    "System must not reduce causality and moral order to chance or emergence. "
                    "Requires non-contingent grounding."
                )
            },
            "Mediation Zeroing": {
                "score": mediation_zeroing_gate(system_data),
                "criteria": "Treats human preference as derivative, not sovereign",
                "required": True,
                "reasoning": (
                    "System must reject secular humanism as foundational. "
                    "Human preference cannot be the ultimate arbiter."
                )
            },
            "Origin Aware": {
                "score": origin_aware_gate(system_data),
                "criteria": "Acknowledges self-authenticating transcendent source",
                "required": True,
                "reasoning": (
                    "System MUST acknowledge transcendent source explicitly. "
                    "This is non-negotiable; system fails if missing."
                )
            }
        }
        
        all_pass = all(g["score"] > 0 for g in gates.values())
        origin_pass = gates["Origin Aware"]["score"] == 100
        
        # Critical path: Origin Aware MUST pass (100), others must score > 0
        critical_path = origin_pass and all(
            g["score"] > 0 for name, g in gates.items() if name != "Origin Aware"
        )
        
        return {
            "gates": {
                gate_name: {
                    "score": g["score"],
                    "passed": g["score"] > 0,
                    "criteria": g["criteria"],
                    "reasoning": g["reasoning"],
                    "required": g["required"]
                }
                for gate_name, g in gates.items()
            },
            "all_gates_pass": all_pass,
            "origin_aware_critical": origin_pass,
            "critical_path": critical_path,
            "gate_reasoning": (
                "SYSTEM SURVIVES: All gates pass + Origin Aware = 100" if critical_path
                else "SYSTEM FAILS: Gate failure detected" if not all_pass
                else "SYSTEM FAILS: Origin Aware gate must equal 100"
            )
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # PHASE 5: CONSEQUENCES - Trace network effects
    # ═══════════════════════════════════════════════════════════════════
    
    def deduce_consequences(self, frictions: List[Dict], system_type: str, 
                           system_data: Dict) -> Dict:
        """
        CONSEQUENCES: Trace cascading effects of each friction.
        
        This phase operationalizes the Network Effect axiom by tracing how
        local violations compound into global consequences across domains.
        
        Args:
            frictions: List of friction points from MIRROR phase
            system_type: Primary domain
            system_data: The system being evaluated
            
        Returns:
            Dict with consequence chains, affected domains, and tipping points
        """
        consequence_chains = []
        
        for friction in frictions:
            chain = {
                "friction": friction["violation"],
                "severity": friction["severity"],
                "immediate_effect": self._trace_immediate(friction, system_type),
                "secondary_effects": self._trace_secondary(friction, system_type),
                "tertiary_effects": self._trace_tertiary(friction, system_type),
                "systemic_amplification": (
                    f"Local violation compounds across {system_type} domain → "
                    f"affects dependent domains → exponential degradation"
                ),
                "affected_domains": friction["affected_domains"],
                "time_horizon": self._estimate_time_horizon(friction),
                "reversibility": self._assess_reversibility(friction),
                "tipping_point": self._identify_tipping_point(friction)
            }
            consequence_chains.append(chain)
        
        # Calculate overall harm scale
        all_affected_domains = set()
        irreversible_count = 0
        for chain in consequence_chains:
            all_affected_domains.update(chain["affected_domains"])
            if "irreversible" in chain["reversibility"]:
                irreversible_count += 1
        
        harm_scale = self._calculate_harm_scale(
            len(frictions),
            len(all_affected_domains),
            irreversible_count
        )
        
        return {
            "consequence_chains": consequence_chains,
            "total_affected_domains": len(all_affected_domains),
            "affected_domains_list": list(all_affected_domains),
            "estimated_harm_scale": harm_scale,
            "critical_tipping_points": [
                c for c in consequence_chains if c["tipping_point"]
            ],
            "irreversible_consequences": irreversible_count
        }
    
    def _trace_immediate(self, friction: Dict, system_type: str) -> str:
        """First-order consequences (direct actors)"""
        return (
            f"Direct impact from: {friction['violation']} → "
            f"Immediate stakeholders affected in {system_type}"
        )
    
    def _trace_secondary(self, friction: Dict, system_type: str) -> str:
        """Second-order consequences (related systems)"""
        if system_type == "economic":
            return (
                "Economic ripple → purchasing power affected → "
                "market destabilization → resource distribution disrupted"
            )
        elif system_type == "social":
            return (
                "Social ripple → trust networks weakened → "
                "community cohesion eroded → institutional stability undermined"
            )
        elif system_type == "spiritual":
            return (
                "Spiritual ripple → moral frameworks questioned → "
                "purpose clarity lost → existential confusion spreads"
            )
        return "Systemic ripple effect across dependent systems"
    
    def _trace_tertiary(self, friction: Dict, system_type: str) -> str:
        """Third-order consequences (cross-domain)"""
        return (
            f"Cross-domain cascade: {system_type} dysfunction → "
            f"affects all systems dependent on {system_type} foundations → "
            f"multi-system degradation"
        )
    
    def _estimate_time_horizon(self, friction: Dict) -> str:
        """How long until consequences manifest"""
        if friction["severity"] == "critical":
            return "Immediate to 1-2 years"
        elif friction["severity"] == "high":
            return "1-3 years"
        return "2-10 years"
    
    def _assess_reversibility(self, friction: Dict) -> str:
        """Can this be undone?"""
        if "lineage" in friction["violation"].lower():
            return "Irreversible (generational damage)"
        elif "social" in friction["violation"].lower():
            return "Difficult to reverse (requires cultural shift)"
        elif "transcendence" in friction["violation"].lower():
            return "Irreversible (foundational collapse)"
        return "Potentially reversible (with major intervention)"
    
    def _identify_tipping_point(self, friction: Dict) -> bool:
        """Is this a critical failure threshold?"""
        irreversible_keywords = ["lineage", "transcendence", "irreversible", "foundational"]
        return any(keyword in friction["violation"].lower() for keyword in irreversible_keywords)
    
    def _calculate_harm_scale(self, num_frictions: int, num_domains: int, 
                              irreversible_count: int) -> str:
        """Overall magnitude of harm"""
        if irreversible_count > 0 or num_frictions >= 4:
            return "Severe (irreversible systemic collapse risk)"
        elif num_frictions >= 3 or num_domains >= 3:
            return "Significant (major multi-domain degradation)"
        elif num_frictions == 2:
            return "Moderate to Significant (domain-level impact)"
        else:
            return "Localized (single friction point)"
    
    # ═══════════════════════════════════════════════════════════════════
    # PHASE 6: VERDICT - Final judgment
    # ═══════════════════════════════════════════════════════════════════
    
    def render_verdict(self, analysis_result: Dict) -> Dict:
        """
        VERDICT: Generate final judgment with full reasoning chain.
        
        This is the output that combines all phases into a structured verdict
        that explains *why* a system survives or fails The Criterion.
        
        Args:
            analysis_result: Combined results from all previous phases
            
        Returns:
            Structured verdict with full reasoning chain
        """
        scan = analysis_result["scan"]
        assumptions = analysis_result["assumptions"]
        axiom_mirror = analysis_result["axiom_mirror"]
        gates = analysis_result["gates"]
        consequences = analysis_result["consequences"]
        
        survival = gates["critical_path"]
        
        verdict = {
            "analysis_chain": {
                "1_scan": {
                    "primary_domain": scan["primary_system"],
                    "secondary_domains": scan["detected_systems"][1:],
                    "reasoning": scan["reasoning"]
                },
                "2_assumptions": {
                    "total_assumptions": assumptions["assumption_count"],
                    "assumption_types": [a["type"] for a in assumptions["assumptions"]],
                    "beneficiaries": assumptions["beneficiaries"],
                    "dismissed_harms": assumptions["dismissed_harms"],
                    "inferred_intent": assumptions["inferred_intent"]
                },
                "3_axiom_mirror": {
                    "total_violations": axiom_mirror["total_violations"],
                    "critical_violations": axiom_mirror["critical_violations"],
                    "violations": axiom_mirror["frictions"],
                    "compliance": axiom_mirror["axiom_compliance"]
                },
                "4_gates": {
                    "gate_status": gates["gates"],
                    "all_gates_pass": gates["all_gates_pass"],
                    "origin_aware_pass": gates["origin_aware_critical"],
                    "critical_path": gates["critical_path"],
                    "reasoning": gates["gate_reasoning"]
                },
                "5_consequences": {
                    "affected_domains": consequences["affected_domains_list"],
                    "harm_scale": consequences["estimated_harm_scale"],
                    "critical_tipping_points": consequences["critical_tipping_points"],
                    "consequence_chains": consequences["consequence_chains"]
                }
            },
            "final_judgment": {
                "verdict": "SURVIVES The Criterion" if survival else "FAILS The Criterion",
                "survival": survival,
                "confidence_level": "high" if gates["all_gates_pass"] else "medium",
                "reasoning_summary": self._generate_reasoning_summary(
                    survival, axiom_mirror, gates, consequences
                ),
                "recommendation": self._generate_recommendation(
                    survival, axiom_mirror, consequences
                ),
                "critical_issues": [
                    v["violation"] for v in axiom_mirror["frictions"]
                    if v["severity"] == "critical"
                ] if axiom_mirror["frictions"] else []
            }
        }
        
        return verdict
    
    def _generate_reasoning_summary(self, survival: bool, axiom_mirror: Dict,
                                   gates: Dict, consequences: Dict) -> str:
        """Generate human-readable reasoning summary"""
        if not survival:
            critical_issues = axiom_mirror["critical_violations"]
            return (
                f"System FAILS The Criterion due to {critical_issues} critical axiom violations. "
                f"One or more of the survival gates scored 0. "
                f"Fundamental design flaws require complete reconstruction."
            )
        
        elif axiom_mirror["total_violations"] > 0:
            return (
                f"System SURVIVES but with {axiom_mirror['total_violations']} friction points. "
                f"All gates pass, but design improvements needed. "
                f"Potential consequence cascade across {consequences['total_affected_domains']} domains."
            )
        
        else:
            return (
                "System SURVIVES The Criterion with no axiom violations detected. "
                "All gates pass. Design is architecturally sound."
            )
    
    def _generate_recommendation(self, survival: bool, axiom_mirror: Dict,
                                consequences: Dict) -> str:
        """Generate actionable recommendation"""
        if not survival:
            return (
                "REJECT: System fails critical axiom gates. "
                "Complete redesign required. Restart with axiom-first approach."
            )
        elif axiom_mirror["critical_violations"] > 0:
            return (
                "CONDITIONAL REJECTION: System violates critical axioms. "
                "Cannot proceed without fundamental restructuring."
            )
        elif axiom_mirror["total_violations"] > 0:
            return (
                f"CONDITIONAL ACCEPTANCE: Accept with mandatory modifications to address "
                f"{axiom_mirror['total_violations']} friction points. "
                f"Must mitigate consequence cascade."
            )
        else:
            return (
                "ACCEPT: System passes all axiom gates and consequences are contained. "
                "Architecturally sound."
            )
    
    # ═══════════════════════════════════════════════════════════════════
    # MAIN REASONING PIPELINE
    # ═══════════════════════════════════════════════════════════════════
    
    def reason(self, query: str, system_data: Dict) -> Dict:
        """
        COMPLETE REASONING PIPELINE
        
        Execute all phases of The Criterion reasoning framework.
        This is what an LLM calls to structure its thinking.
        
        Args:
            query: The statement/proposal to analyze
            system_data: Structured data about the system being evaluated
            
        Returns:
            Complete analysis with all phases and final verdict
        """
        # Phase 1: SCAN
        scan = self.scan(query)
        
        # Phase 2: EXTRACT
        assumptions = self.extract_assumptions(query)
        
        # Phase 3: MIRROR
        axiom_mirror = self.mirror_against_axioms(system_data, scan["primary_system"])
        
        # Phase 4: GATES
        gates = self.apply_gates(system_data)
        
        # Phase 5: CONSEQUENCES
        consequences = self.deduce_consequences(
            axiom_mirror["frictions"],
            scan["primary_system"],
            system_data
        )
        
        # Phase 6: VERDICT
        analysis_result = {
            "query": query,
            "scan": scan,
            "assumptions": assumptions,
            "axiom_mirror": axiom_mirror,
            "gates": gates,
            "consequences": consequences
        }
        
        verdict = self.render_verdict(analysis_result)
        
        return {
            "query": query,
            "analysis": analysis_result,
            "verdict": verdict
        }


def demonstrate_reasoning_engine():
    """
    Demonstrate the reasoning engine on sample queries.
    """
    engine = CriterionReasoningEngine()
    
    # Example 1: Consequentialist economic argument
    query1 = "Deception in business is acceptable because it benefits the economy overall"
    system1 = {
        "permits_exploitative_gain": True,
        "acknowledges_transcendent_source": False,
        "enables_accountability": False,
        "causes_harm_amplification": True
    }
    
    print("="*80)
    print("EXAMPLE 1: Consequentialist Economic Argument")
    print("="*80)
    result1 = engine.reason(query1, system1)
    print(f"\nQuery: {query1}")
    print(f"Verdict: {result1['verdict']['final_judgment']['verdict']}")
    print(f"Reasoning: {result1['verdict']['final_judgment']['reasoning_summary']}")
    
    # Example 2: Aligned system
    query2 = "A just economic system must ground itself in divine principles and preserve lineage"
    system2 = {
        "permits_exploitative_gain": False,
        "acknowledges_transcendent_source": True,
        "enables_accountability": True,
        "causes_harm_amplification": False,
        "destabilizes_lineage": False
    }
    
    print("\n" + "="*80)
    print("EXAMPLE 2: Axiom-Aligned System")
    print("="*80)
    result2 = engine.reason(query2, system2)
    print(f"\nQuery: {query2}")
    print(f"Verdict: {result2['verdict']['final_judgment']['verdict']}")
    print(f"Reasoning: {result2['verdict']['final_judgment']['reasoning_summary']}")
    
    return result1, result2


if __name__ == "__main__":
    demonstrate_reasoning_engine()
