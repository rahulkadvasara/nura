"""
Nura - Router Agent
Production router determining target downstream execution agents for incoming user queries.
"""

import time
from typing import Any, Optional
from app.agents.base.base_agent import BaseAgent
from app.agents.base.context import AgentContext
from app.agents.router.schemas import RoutingDecision
from app.agents.router.intent_classifier import IntentClassifier
from app.agents.router.routing_rules import RoutingRulesEvaluator
from app.agents.router.telemetry import get_router_telemetry
from app.agents.router.fallback import FallbackManager


class RouterAgent(BaseAgent):
    """LangGraph execution entrypoint router directing queries based on classifications"""

    def __init__(self, name: str = "RouterAgent"):
        super().__init__(name=name)
        self.classifier = IntentClassifier()

    async def execute(self, input_data: Any, context: Optional[AgentContext] = None) -> RoutingDecision:
        """
        Primary execution node for the Router Agent.
        Analyzes query input string and resolves routing decisions.
        """
        # Validate query string format
        query = ""
        if isinstance(input_data, str):
            query = input_data
        elif isinstance(input_data, dict):
            query = input_data.get("query", "")
        
        # Safe execution call
        decision = await self.run_routing(query)
        return decision

    async def run_routing(self, query: str) -> RoutingDecision:
        """
        Synchronously run classification, evaluate thresholds rules, and log telemetry.
        Never throws exceptions; falls back to UnknownAgent if failures occur.
        """
        start_time = time.perf_counter()
        is_fallback = False
        is_failure = False
        
        try:
            # 1. Classify intent
            classification = self.classifier.classify(query)
            
            # 2. Evaluate routing rules
            decision = RoutingRulesEvaluator.evaluate_decision(classification)
            
            # Check if fallback agent was chosen
            if decision.detected_intent == "UNKNOWN":
                is_fallback = True
                
            return decision

        except Exception as e:
            self.logger.error(f"Router Agent encountered fatal error: {str(e)}", exc_info=True)
            is_failure = True
            is_fallback = True
            return FallbackManager.get_fallback_decision([f"error:exception_raised_{str(e)}"])

        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            # Update telemetry records
            telemetry = get_router_telemetry()
            if is_failure:
                telemetry.record_routing(
                    intent="UNKNOWN",
                    confidence=0.0,
                    latency_ms=latency_ms,
                    is_fallback=True,
                    is_failure=True
                )
            else:
                telemetry.record_routing(
                    intent=decision.detected_intent,
                    confidence=decision.confidence,
                    latency_ms=latency_ms,
                    is_fallback=is_fallback
                )
