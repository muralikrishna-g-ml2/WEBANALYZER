"""
Performance Monitor

Tracks and analyzes execution performance across the AQM workflow,
with focus on measuring TTLX reduction through parallelization.
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PhaseMetrics:
    """Metrics for a single workflow phase"""
    phase_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    agent_timings: Dict[str, float] = field(default_factory=dict)
    parallel_execution: bool = False
    
    def complete(self):
        """Mark phase as complete and calculate duration"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution"""
    agent_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tokens_used: Optional[int] = None
    
    def complete(self, tokens: Optional[int] = None):
        """Mark agent execution as complete"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.tokens_used = tokens


class PerformanceMonitor:
    """
    Monitors and analyzes performance across the AQM workflow.
    
    Key focus: Measuring Time to Last Token (TTLX) reduction
    achieved through parallel agent execution.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.phase_metrics: List[PhaseMetrics] = []
        self.agent_metrics: List[AgentMetrics] = []
        self.current_phase: Optional[PhaseMetrics] = None
        self.session_start = time.time()
    
    def start_phase(self, phase_name: str, parallel: bool = False):
        """Start tracking a new phase"""
        if self.current_phase and not self.current_phase.end_time:
            self.current_phase.complete()
        
        self.current_phase = PhaseMetrics(
            phase_name=phase_name,
            start_time=time.time(),
            parallel_execution=parallel
        )
        self.phase_metrics.append(self.current_phase)
    
    def end_phase(self):
        """End tracking current phase"""
        if self.current_phase:
            self.current_phase.complete()
    
    def start_agent(self, agent_name: str) -> AgentMetrics:
        """
        Start tracking an agent execution.
        
        Returns:
            AgentMetrics object to be completed when agent finishes
        """
        metrics = AgentMetrics(
            agent_name=agent_name,
            start_time=time.time()
        )
        self.agent_metrics.append(metrics)
        
        return metrics
    
    def record_agent_timing(self, agent_name: str, duration: float):
        """Record timing for an agent in current phase"""
        if self.current_phase:
            self.current_phase.agent_timings[agent_name] = duration
    
    def calculate_ttlx_reduction(self) -> Dict[str, float]:
        """
        Calculate TTLX reduction from parallel execution.
        
        Compares actual parallel execution time vs theoretical
        sequential execution time.
        
        Returns:
            Dict with actual_time, sequential_time, reduction_pct
        """
        # Find parallel discovery phase (P1)
        p1_phase = next(
            (p for p in self.phase_metrics if p.phase_name == "P1"),
            None
        )
        
        if not p1_phase or not p1_phase.parallel_execution:
            return {
                "actual_time": 0.0,
                "sequential_time": 0.0,
                "reduction_pct": 0.0,
                "note": "No parallel phase found"
            }
        
        # Actual parallel execution time
        actual_time = p1_phase.duration or 0.0
        
        # Theoretical sequential time (sum of all agent times)
        sequential_time = sum(p1_phase.agent_timings.values())
        
        # Calculate reduction
        if sequential_time > 0:
            reduction_pct = ((sequential_time - actual_time) / sequential_time) * 100
        else:
            reduction_pct = 0.0
        
        return {
            "actual_time": actual_time,
            "sequential_time": sequential_time,
            "reduction_pct": reduction_pct,
            "time_saved": sequential_time - actual_time
        }
    
    def get_phase_summary(self) -> List[Dict]:
        """Get summary of all phase timings"""
        return [
            {
                "phase": p.phase_name,
                "duration": p.duration,
                "parallel": p.parallel_execution,
                "agent_count": len(p.agent_timings),
                "agents": p.agent_timings
            }
            for p in self.phase_metrics
            if p.duration is not None
        ]
    
    def get_agent_summary(self) -> List[Dict]:
        """Get summary of all agent executions"""
        return [
            {
                "agent": a.agent_name,
                "duration": a.duration,
                "tokens": a.tokens_used,
            }
            for a in self.agent_metrics
            if a.duration is not None
        ]
    
    def export_report(self) -> str:
        """
        Export performance report in Markdown format.
        
        Returns:
            Markdown-formatted performance report
        """
        total_time = time.time() - self.session_start
        ttlx_data = self.calculate_ttlx_reduction()
        
        report = f"""# Performance Report - {self.session_id}

**Total Session Time**: {total_time:.2f}s
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## TTLX Reduction Analysis

"""
        if ttlx_data['reduction_pct'] > 0:
            report += f"""- **Parallel Execution Time**: {ttlx_data['actual_time']:.2f}s
- **Theoretical Sequential Time**: {ttlx_data['sequential_time']:.2f}s
- **Time Saved**: {ttlx_data['time_saved']:.2f}s
- **Reduction**: {ttlx_data['reduction_pct']:.1f}%

✅ **Target Met**: {'Yes' if ttlx_data['reduction_pct'] >= 50 else 'No'} (Target: >50% reduction)
"""
        else:
            report += f"_{ttlx_data.get('note', 'No data available')}_\n"
        
        report += "\n## Phase Timings\n\n"
        for phase in self.get_phase_summary():
            report += f"### {phase['phase']}\n"
            report += f"- **Duration**: {phase['duration']:.2f}s\n"
            report += f"- **Parallel Execution**: {phase['parallel']}\n"
            
            if phase['agents']:
                report += f"- **Agents** ({phase['agent_count']}):\n"
                for agent, timing in phase['agents'].items():
                    report += f"  - {agent}: {timing:.2f}s\n"
            report += "\n"
        
        report += "## Agent Execution Summary\n\n"
        report += "| Agent | Duration | Tokens |\n"
        report += "|-------|----------|--------|\n"
        
        for agent in self.get_agent_summary():
            tokens = agent['tokens'] if agent['tokens'] else 'N/A'
            report += f"| {agent['agent']} | {agent['duration']:.2f}s | {tokens} |\n"
        
        return report
    
    def check_performance_targets(self) -> Dict[str, bool]:
        """
        Check if performance targets are met.
        
        Returns:
            Dict of target_name -> met (bool)
        """
        ttlx_data = self.calculate_ttlx_reduction()
        
        return {
            "ttlx_reduction_50pct": ttlx_data['reduction_pct'] >= 50.0,
            "user_interaction_delay_30s": self._check_user_delay_target(),
        }
    
    def _check_user_delay_target(self) -> bool:
        """Check if user interaction delay is under 30s"""
        # Find P1 and P2 phases (before user interaction in P3)
        p1_p2_time = sum(
            p.duration for p in self.phase_metrics
            if p.phase_name in ["P1", "P2"] and p.duration is not None
        )
        
        return p1_p2_time < 30.0
