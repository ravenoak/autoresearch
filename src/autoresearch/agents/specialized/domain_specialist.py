"""
DomainSpecialistAgent for providing expert knowledge in specific domains.

This agent is responsible for providing deep, domain-specific expertise
on particular subjects, offering specialized insights, and applying
domain-specific methodologies to analyze problems.
"""

from typing import Dict, Any, List

from ...agents.base import Agent, AgentRole
from ...config import ConfigModel
from ...orchestration.phases import DialoguePhase
from ...orchestration.state import QueryState
from ...logging_utils import get_logger
from ...search import Search

log = get_logger(__name__)


class DomainSpecialistAgent(Agent):
    """Provides expert knowledge and analysis in specific domains."""

    role: AgentRole = AgentRole.SPECIALIST
    name: str = "DomainSpecialist"
    domain: str = "general"  # Default domain, can be overridden in config

    def execute(self, state: QueryState, config: ConfigModel) -> Dict[str, Any]:
        """Provide domain-specific expertise and analysis."""
        log.info(f"DomainSpecialistAgent ({self.domain}) executing (cycle {state.cycle})")

        adapter = self.get_adapter(config)
        model = self.get_model(config)

        # Determine the domain if not already set
        if self.domain == "general":
            self.domain = self._determine_domain(state.query)
            log.info(f"Determined domain: {self.domain}")

        # Get domain-specific context from search or knowledge base
        domain_context = self._get_domain_context(state.query, self.domain)
        
        # Extract relevant claims from the state
        relevant_claims = self._get_relevant_claims(state, self.domain)
        claims_text = self._format_claims(relevant_claims)

        # Generate domain-specific analysis using the prompt template
        prompt = self.generate_prompt(
            "specialist.analysis",
            query=state.query,
            domain=self.domain,
            domain_context=domain_context,
            claims=claims_text,
            cycle=state.cycle
        )
        
        analysis = adapter.generate(prompt, model=model)

        # Generate domain-specific recommendations
        recommendations_prompt = self.generate_prompt(
            "specialist.recommendations",
            query=state.query,
            domain=self.domain,
            analysis=analysis,
            cycle=state.cycle
        )
        
        recommendations = adapter.generate(recommendations_prompt, model=model)

        # Create and return the result
        analysis_claim = self.create_claim(analysis, "domain_analysis")
        recommendations_claim = self.create_claim(recommendations, "domain_recommendations")
        
        return self.create_result(
            claims=[analysis_claim, recommendations_claim],
            metadata={
                "phase": DialoguePhase.ANALYSIS,
                "domain": self.domain,
                "analyzed_claims": [c.get("id") for c in relevant_claims],
            },
            results={
                "domain_analysis": analysis,
                "domain_recommendations": recommendations,
                "domain": self.domain
            },
        )

    def can_execute(self, state: QueryState, config: ConfigModel) -> bool:
        """Determine if this specialist should execute based on the query domain."""
        # Always execute if explicitly configured
        if hasattr(config, "specialist_domains") and self.domain in config.specialist_domains:
            return super().can_execute(state, config)
            
        # Otherwise, only execute if the query is relevant to this domain
        domain_relevance = self._check_domain_relevance(state.query, self.domain)
        return super().can_execute(state, config) and domain_relevance > 0.7  # Threshold for relevance
    
    def _determine_domain(self, query: str) -> str:
        """Determine the most relevant domain for the query."""
        # This is a simplified implementation
        # In a real system, this would use a classifier or embedding model
        
        domains = {
            "medicine": ["health", "disease", "medical", "doctor", "patient", "treatment"],
            "technology": ["computer", "software", "hardware", "tech", "digital", "internet"],
            "finance": ["money", "investment", "stock", "financial", "economy", "market"],
            "science": ["scientific", "experiment", "research", "physics", "chemistry", "biology"],
            "law": ["legal", "law", "court", "justice", "regulation", "compliance"],
            "education": ["learning", "teaching", "school", "education", "student", "academic"]
        }
        
        query_lower = query.lower()
        domain_scores = {}
        
        for domain, keywords in domains.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            domain_scores[domain] = score
        
        # Get the domain with the highest score
        if max(domain_scores.values()) > 0:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        
        return "general"  # Default if no specific domain is detected
    
    def _check_domain_relevance(self, query: str, domain: str) -> float:
        """Check how relevant the query is to the specified domain."""
        # This is a simplified implementation
        # In a real system, this would use a more sophisticated relevance model
        
        if domain == "general":
            return 1.0  # General domain is always relevant
            
        domain_keywords = {
            "medicine": ["health", "disease", "medical", "doctor", "patient", "treatment"],
            "technology": ["computer", "software", "hardware", "tech", "digital", "internet"],
            "finance": ["money", "investment", "stock", "financial", "economy", "market"],
            "science": ["scientific", "experiment", "research", "physics", "chemistry", "biology"],
            "law": ["legal", "law", "court", "justice", "regulation", "compliance"],
            "education": ["learning", "teaching", "school", "education", "student", "academic"]
        }
        
        if domain not in domain_keywords:
            return 0.5  # Unknown domain, moderate relevance
            
        query_lower = query.lower()
        keywords = domain_keywords[domain]
        
        # Count how many domain keywords appear in the query
        matches = sum(1 for keyword in keywords if keyword in query_lower)
        
        # Calculate relevance score (0.0 to 1.0)
        if len(keywords) > 0:
            return min(1.0, matches / len(keywords) * 2)  # Scale up to reach 1.0 more easily
        
        return 0.5  # Default moderate relevance
    
    def _get_domain_context(self, query: str, domain: str) -> str:
        """Get domain-specific context for the query."""
        try:
            # Try to get domain-specific information from search
            search_query = f"{query} {domain} expert knowledge"
            search_results = Search.external_lookup(search_query, max_results=3)
            
            if search_results:
                # Format search results as context
                context_parts = []
                for i, result in enumerate(search_results, 1):
                    title = result.get("title", "Untitled")
                    content = result.get("content", "No content")
                    source = result.get("url", "Unknown source")
                    
                    context_parts.append(f"Source {i}: {title}\n{content}\nReference: {source}")
                
                return "\n\n".join(context_parts)
        except Exception as e:
            log.warning(f"Error getting domain context: {str(e)}")
        
        # Fallback: return generic domain description
        domain_descriptions = {
            "medicine": "Medicine is the science and practice of caring for patients, managing health conditions, and preventing disease.",
            "technology": "Technology encompasses the tools, systems, and methods used to solve problems and improve efficiency.",
            "finance": "Finance deals with the management of money, investments, and other financial assets.",
            "science": "Science is the systematic study of the structure and behavior of the physical and natural world through observation and experiment.",
            "law": "Law is a system of rules created and enforced through social or governmental institutions to regulate behavior.",
            "education": "Education is the process of facilitating learning, or the acquisition of knowledge, skills, values, beliefs, and habits."
        }
        
        return domain_descriptions.get(domain, f"The domain of {domain} involves specialized knowledge and methodologies specific to this field.")
    
    def _get_relevant_claims(self, state: QueryState, domain: str) -> List[Dict[str, Any]]:
        """Get claims from the state that are relevant to the specified domain."""
        # This is a simplified implementation
        # In a real system, this would use more sophisticated relevance matching
        
        relevant_claims = []
        domain_keywords = {
            "medicine": ["health", "disease", "medical", "doctor", "patient", "treatment"],
            "technology": ["computer", "software", "hardware", "tech", "digital", "internet"],
            "finance": ["money", "investment", "stock", "financial", "economy", "market"],
            "science": ["scientific", "experiment", "research", "physics", "chemistry", "biology"],
            "law": ["legal", "law", "court", "justice", "regulation", "compliance"],
            "education": ["learning", "teaching", "school", "education", "student", "academic"]
        }
        
        keywords = domain_keywords.get(domain, [])
        
        if not keywords:
            # If no specific keywords for this domain, return all claims
            return state.claims
            
        for claim in state.claims:
            content = claim.get("content", "").lower()
            
            # Check if any domain keyword appears in the claim
            if any(keyword in content for keyword in keywords):
                relevant_claims.append(claim)
                
        # If no relevant claims found, return the most recent claims
        if not relevant_claims and state.claims:
            return state.claims[-3:]  # Return the 3 most recent claims
            
        return relevant_claims
    
    def _format_claims(self, claims: List[Dict[str, Any]]) -> str:
        """Format claims for inclusion in the prompt."""
        formatted_claims = []
        
        for i, claim in enumerate(claims, 1):
            agent = claim.get("agent", "Unknown Agent")
            content = claim.get("content", "No content")
            claim_type = claim.get("type", "statement")
            
            formatted_claims.append(f"Claim {i} ({agent}, {claim_type}):\n{content}")
        
        if not formatted_claims:
            return "No relevant claims available."
            
        return "\n\n".join(formatted_claims)
