"""SICA runner: the trusted harness the agent cannot edit.

Contains the ledger, config/pins, model client, sandbox + broker (the four
guardrails), the benchmark layer, and the evolution machinery (proposer, gate,
memory, archive, engine, report). The self-modifiable scaffold lives in
sica/scaffold/ and is executed only through broker.py.
"""
