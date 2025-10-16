#!/usr/bin/env python3
"""Measure LM Studio baseline performance for test timeout calibration.

This script runs a series of standardized tests against the local LM Studio
instance to establish performance baselines for different query complexities.

Usage:
    uv run python scripts/measure_llm_baselines.py

Output:
    Prints baseline measurements and recommended timeouts to stdout.
    Saves JSON results to baseline/logs/llm_baseline_TIMESTAMP.json
"""

import json
import os
import platform
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any, Dict, List

try:
    import requests
except ImportError:
    print("Error: requests library not found. Run: uv pip install requests")
    sys.exit(1)


def get_system_info() -> Dict[str, str]:
    """Gather system information for baseline documentation."""
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "timestamp": datetime.now().isoformat(),
    }
    
    # Try to get more detailed hardware info on macOS
    if platform.system() == "Darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.splitlines():
                if "Model Name:" in line:
                    info["model_name"] = line.split(":", 1)[1].strip()
                elif "Chip:" in line:
                    info["chip"] = line.split(":", 1)[1].strip()
                elif "Total Number of Cores:" in line:
                    info["cpu_cores"] = line.split(":", 1)[1].strip()
                elif "Memory:" in line:
                    info["memory"] = line.split(":", 1)[1].strip()
        except Exception:
            pass
    
    return info


def check_lmstudio_available(url: str = "http://localhost:1234/v1/models") -> bool:
    """Check if LM Studio is running and accessible."""
    try:
        resp = requests.get(url, timeout=5)
        return resp.status_code == 200
    except Exception as e:
        print(f"Error: Cannot connect to LM Studio at {url}")
        print(f"Details: {e}")
        return False


def measure_query(
    url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    attempts: int = 3,
    description: str = ""
) -> Dict[str, Any]:
    """Measure response time for a query."""
    print(f"\n{description}")
    print(f"  Prompt length: {len(prompt)} chars, Max tokens: {max_tokens}")
    
    timings: List[float] = []
    for attempt in range(attempts):
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        
        try:
            start = time.time()
            response = requests.post(url, json=payload, timeout=120)
            duration = time.time() - start
            
            if response.status_code == 200:
                timings.append(duration)
                print(f"  Attempt {attempt + 1}: {duration:.2f}s")
            else:
                print(f"  Attempt {attempt + 1}: ERROR {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"  Attempt {attempt + 1}: TIMEOUT (>120s)")
        except Exception as e:
            print(f"  Attempt {attempt + 1}: ERROR - {str(e)[:50]}")
        
        time.sleep(1)  # Brief pause between attempts
    
    if timings:
        return {
            "description": description,
            "prompt_length": len(prompt),
            "max_tokens": max_tokens,
            "attempts": len(timings),
            "mean": mean(timings),
            "median": median(timings),
            "min": min(timings),
            "max": max(timings),
            "stdev": stdev(timings) if len(timings) > 1 else 0.0,
            "recommended_timeout_3x": max(timings) * 3,
        }
    return {}


def main() -> int:
    """Run baseline measurements."""
    print("=" * 70)
    print("LM Studio Baseline Performance Measurement")
    print("=" * 70)
    
    # Check LM Studio availability
    if not check_lmstudio_available():
        return 1
    
    # Get system info
    system_info = get_system_info()
    print("\nSystem Information:")
    for key, value in system_info.items():
        print(f"  {key}: {value}")
    
    # Get model from LM Studio
    try:
        resp = requests.get("http://localhost:1234/v1/models", timeout=5)
        models = resp.json().get("data", [])
        if not models:
            print("\nError: No models available in LM Studio")
            return 1
        model = models[0]["id"]
        print(f"\nUsing model: {model}")
    except Exception as e:
        print(f"\nError getting models: {e}")
        return 1
    
    url = "http://localhost:1234/v1/chat/completions"
    
    # Define test scenarios
    scenarios = [
        {
            "name": "simple_query",
            "prompt": "What is Python?",
            "max_tokens": 100,
            "description": "Simple query (llm_simple tier)",
        },
        {
            "name": "medium_research",
            "prompt": """Based on these sources, synthesize an answer:
Source 1: Python is a high-level programming language.
Source 2: It emphasizes code readability.
Source 3: Python supports multiple paradigms.

Question: What are Python's key characteristics?""",
            "max_tokens": 300,
            "description": "Medium research synthesis (llm_medium tier)",
        },
        {
            "name": "large_context",
            "prompt": f"""You are analyzing research documents. Here are summaries:

Document 1 (1500 words): {'Deep learning overview. ' * 50}
Document 2 (1200 words): {'Healthcare ML applications. ' * 40}
Document 3 (1800 words): {'Programming language evolution. ' * 60}

Question: Synthesize insights about computational efficiency.""",
            "max_tokens": 500,
            "description": "Large context analysis (llm_complex tier)",
        },
        {
            "name": "dialectical_reasoning",
            "prompt": """Perform dialectical analysis:
Claim: AI systems should be regulated like pharmaceuticals.

Thesis: Present strongest arguments for.
Antithesis: Present strongest arguments against.
Synthesis: Develop nuanced position.

Provide evidence-based reasoning with examples.""",
            "max_tokens": 600,
            "description": "Complex dialectical reasoning (llm_complex tier)",
        },
    ]
    
    print("\n" + "=" * 70)
    print("Running Baseline Measurements")
    print("=" * 70)
    
    results = {}
    for scenario in scenarios:
        result = measure_query(
            url=url,
            model=model,
            prompt=scenario["prompt"],
            max_tokens=scenario["max_tokens"],
            description=scenario["description"],
        )
        if result:
            results[scenario["name"]] = result
    
    # Print summary
    print("\n" + "=" * 70)
    print("BASELINE SUMMARY")
    print("=" * 70)
    
    for name, stats in results.items():
        print(f"\n{name}:")
        print(f"  Mean: {stats['mean']:.2f}s, Median: {stats['median']:.2f}s")
        print(f"  Range: {stats['min']:.2f}s - {stats['max']:.2f}s")
        if stats['stdev'] > 0:
            variance_pct = (stats['stdev'] / stats['mean']) * 100
            print(f"  Std Dev: {stats['stdev']:.2f}s ({variance_pct:.1f}% variance)")
        print(f"  Recommended timeout: {stats['recommended_timeout_3x']:.1f}s (3x max)")
    
    # Save results to JSON
    output_dir = Path("baseline/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    output_file = output_dir / f"llm_baseline_{timestamp}.json"
    
    output_data = {
        "system_info": system_info,
        "model": model,
        "results": results,
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

