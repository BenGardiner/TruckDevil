import os
import sys
import subprocess
import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TRUCKDEVIL_PY = os.path.join(_REPO_ROOT, "truckdevil", "truckdevil.py")

def test_cli_c_flag_ls():
    """Test 'python -m truckdevil -c ls' prints modules and exits."""
    result = subprocess.run(
        [sys.executable, _TRUCKDEVIL_PY, "-c", "ls"],
        capture_output=True, text=True, timeout=10,
        cwd=_REPO_ROOT
    )
    assert result.returncode == 0
    assert "read_messages" in result.stdout
    assert "send_messages" in result.stdout

def test_cli_c_flag_multiple_commands():
    """Test 'python -m truckdevil -c "add_device virtual vcan0 250000; list_device"'."""
    result = subprocess.run(
        [sys.executable, _TRUCKDEVIL_PY, "-c", "add_device virtual vcan0 250000; list_device"],
        capture_output=True, text=True, timeout=10,
        cwd=_REPO_ROOT
    )
    assert result.returncode == 0
    assert "virtual" in result.stdout
    assert "vcan0" in result.stdout

def test_cli_c_flag_quit():
    """Test 'python -m truckdevil -c quit' exits with non-zero (due to sys.exit message)."""
    result = subprocess.run(
        [sys.executable, _TRUCKDEVIL_PY, "-c", "quit"],
        capture_output=True, text=True, timeout=10,
        cwd=_REPO_ROOT
    )
    # sys.exit("Exiting TruckDevil") results in return code 1
    assert result.returncode == 1
    assert "Exiting TruckDevil" in result.stderr

def test_cli_c_flag_empty():
    """Test 'python -m truckdevil -c ""' exits normally."""
    result = subprocess.run(
        [sys.executable, _TRUCKDEVIL_PY, "-c", ""],
        capture_output=True, text=True, timeout=10,
        cwd=_REPO_ROOT
    )
    assert result.returncode == 0

def test_python_m_truckdevil_c_ls():
    """Test 'python -m truckdevil -c ls' works when truckdevil is in PYTHONPATH."""
    env = os.environ.copy()
    env["PYTHONPATH"] = _REPO_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-m", "truckdevil", "-c", "ls"],
        capture_output=True, text=True, timeout=10,
        env=env,
        cwd=_REPO_ROOT
    )
    assert result.returncode == 0
    assert "read_messages" in result.stdout
