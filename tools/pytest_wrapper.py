# https://stackoverflow.com/a/67389568

import sys
import pytest  # type: ignore[import-not-found,import-untyped]

# if using 'bazel test ...'
if __name__ == "__main__":
    sys.exit(pytest.main(sys.argv[1:]))
