#!/usr/bin/env python3
"""Verify axioms load correctly."""

import sys

# Clear any cached modules
for mod in list(sys.modules.keys()):
    if mod.startswith('al_furqan'):
        del sys.modules[mod]

from al_furqan.engine.axioms import AXIOM_VERSION, AXIOM_HASH, SEALED_AXIOM_HASH
print(f'Version: {AXIOM_VERSION}')
print(f'Hashes match: {AXIOM_HASH == SEALED_AXIOM_HASH}')
print(f'Runtime hash: {AXIOM_HASH}')
print(f'Sealed hash:  {SEALED_AXIOM_HASH}')
