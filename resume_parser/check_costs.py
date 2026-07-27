"""Quick check: how much have I spent so far this session/project?
Run with: python check_costs.py
"""
from cost_logger import get_session_total

totals = get_session_total()
print(f"Total calls:         {totals['total_calls']}")
print(f"Total input tokens:  {totals['total_input_tokens']}")
print(f"Total output tokens: {totals['total_output_tokens']}")
print(f"Total estimated cost: ${totals['total_cost_usd']:.6f}")