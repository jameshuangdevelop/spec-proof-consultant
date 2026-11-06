from pathlib import Path

import pytest

from spec_consultant.matcher import assess
from spec_consultant.profiler import profile

EXAMPLE = Path(__file__).parents[1] / "examples" / "rust-buffer"
FIXTURES = Path(__file__).parent / "fixtures"


def pytest_addoption(parser):
    parser.addoption(
        "--evaluation-dir", help="Read-only retained customer-evaluation bundle for pinned integration cases"
    )


@pytest.fixture
def evaluation_dir(request):
    value = request.config.getoption("--evaluation-dir")
    if not value:
        pytest.skip("Pass --evaluation-dir to exercise retained public corpus and all nine semantic conclusions")
    base = Path(value).expanduser().resolve(strict=True)
    assert (base / "REPORT.md").is_file() and (base / "product-arm/recommendations.json").is_file()
    return base


@pytest.fixture
def assessment():
    return assess(profile([str(EXAMPLE)]))
