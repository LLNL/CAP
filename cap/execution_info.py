"""Contains the execution info for the current CAP execution

See the README.md, 'Configuration Files' subsection for more info
"""
from bincfg import X86HPCDataNormalizer, X86BaseNormalizer, JavaBaseNormalizer

# The unique identifier for this CAP execution
EXECUTION_UID = 'acme'

# Postprocessing methods to apply
POSTPROCESSING = ['cfg', 'memcfg']

# The columns to drop
DROP_COLUMNS = []

# The normalizer(s) to use
NORMALIZERS = [X86BaseNormalizer()]

# The analyzer(s) to use, should exist inside the container_info file
ANALYZERS = ['rose']

# The compile methods to use. See the README.md, 'Compile Method' section for more info
COMPILE_METHODS = []

# Whether or not to have each process on the same machine wait for previous processes to load their data before loading
#   theirs to save memory
AWAIT_LOAD = False
