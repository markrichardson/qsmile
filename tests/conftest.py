"""Root conftest for the project test suite (tests/).

Security Notes:
- S101 (assert usage): Asserts are appropriate in test code for validating conditions
"""

import matplotlib as mpl

mpl.use("Agg")
