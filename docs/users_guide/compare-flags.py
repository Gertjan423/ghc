#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Linter to verify that all flags reported by GHC's --show-options mode
are documented in the user's guide.
"""

import sys
import subprocess
from typing import Set
from pathlib import Path

# A list of known-undocumented flags. This should be considered to be a to-do
# list of flags that need to be documented.
EXPECTED_UNDOCUMENTED_PATH = \
    Path(__file__).parent / 'expected-undocumented-flags.txt'

EXPECTED_UNDOCUMENTED = \
    {line for line in open(EXPECTED_UNDOCUMENTED_PATH).read().split()}

def expected_undocumented(flag: str) -> bool:
    if flag in EXPECTED_UNDOCUMENTED:
        return True
    if flag.startswith('-Werror'):
        return True
    if flag.startswith('-Wno-') \
            or flag.startswith('-dno') \
            or flag.startswith('-fno') \
            or flag.startswith('-XNo'):
        return True
    if flag.startswith('-Wwarn=') \
            or flag.startswith('-Wno-warn='):
        return True

    return False

def read_documented_flags(doc_flags) -> Set[str]:
    # Map characters that mark the end of a flag
    # to whitespace.
    trans = str.maketrans({
        '=': ' ',
        '[': ' ',
        '⟨': ' ',
    })
    return {line.translate(trans).split()[0]
            for line in doc_flags.read().split('\n')
            if line != ''}

def read_ghc_flags(ghc_path: str) -> Set[str]:
    ghc_output = subprocess.check_output([ghc_path, '--show-options'],
                                         encoding='UTF-8')
    return {flag
            for flag in ghc_output.split('\n')
            if not expected_undocumented(flag)
            if flag != ''}

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ghc', type=argparse.FileType('r'),
                        help='path of GHC executable')
    parser.add_argument('--doc-flags', type=argparse.FileType('r'),
                        help='path of ghc-flags.txt output from Sphinx')
    args = parser.parse_args()

    doc_flags = read_documented_flags(args.doc_flags)
    ghc_flags = read_ghc_flags(args.ghc.name)

    failed = False

    undocumented = ghc_flags - doc_flags
    if len(undocumented) > 0:
        print(f'Found {len(undocumented)} flags not documented in the users guide:')
        print('\n'.join(f'  {flag}' for flag in sorted(undocumented)))
        print()
        failed = True

    now_documented = EXPECTED_UNDOCUMENTED.intersection(doc_flags)
    if len(now_documented) > 0:
        print(f'Found flags that are documented yet listed in {EXPECTED_UNDOCUMENTED_PATH}:')
        print('\n'.join(f'  {flag}' for flag in sorted(now_documented)))
        print()
        failed = True

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
