import subprocess
import sys

import pytest

FORBIDDEN_ROOTS = {"tkinter", "pystray", "pypresence"}

PROBE = """
import importlib
import pkgutil
import sys

package = importlib.import_module(sys.argv[1])
for module in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
    importlib.import_module(module.name)
print("\\n".join(sorted({name.split(".")[0] for name in sys.modules})))
"""


@pytest.mark.parametrize(
    "package",
    [
        pytest.param("discord_profile_studio.models", id="models"),
        pytest.param("discord_profile_studio.core", id="core"),
    ],
)
def test_importing_pure_layer_loads_no_gui_tray_or_discord_module(package: str):
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", PROBE, package],
        capture_output=True,
        text=True,
        check=True,
    )

    assert set(result.stdout.split()) & FORBIDDEN_ROOTS == set()
