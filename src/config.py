"""
config.py — Shared configuration loader.

Loads config.json and expands ~ and environment variables in path values
so a single config can work across different users' machines.

Examples that get expanded at load time:
  "~\\Desktop\\PP29\\output"            (Windows + Linux)
  "%USERPROFILE%\\Desktop\\PP29"        (Windows)
  "$HOME/PP29/output"                   (Linux/Mac)

Search order for config.json when no explicit path is given:
  1. Path passed via --config CLI argument
  2. Project root (parent of src/)
  3. Current working directory
"""

import json
import os
import sys


# Keys whose values are file/directory paths and should get ~/env expansion.
PATH_KEYS = (
    'sap_input_path',
    'access_excel_path',
    'daily_output_path',
    'consolidated_output_path',
    'db_path',
    'log_path',
)


def expand_path(path: str) -> str:
    """Expand ~ and %VAR% / $VAR in a path string. No-op for plain paths."""
    if not isinstance(path, str):
        return path
    return os.path.expandvars(os.path.expanduser(path))


def load_config(config_path: str = None) -> dict:
    """
    Load config.json and expand ~ / env vars in every known path key.

    Args:
        config_path: explicit path to a config file (from --config CLI arg).
                     If not given or missing, search project root then cwd.

    Returns:
        Parsed config dict with path values already expanded.
    """
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            cfg = json.load(f)
    else:
        search = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json'),
            os.path.join(os.getcwd(), 'config.json'),
        ]
        cfg = None
        for p in search:
            if os.path.exists(p):
                with open(p, 'r') as f:
                    cfg = json.load(f)
                break
        if cfg is None:
            print("ERROR: config.json not found.")
            print("Copy config.example.json to config.json and edit the paths.")
            sys.exit(1)

    for k in PATH_KEYS:
        if k in cfg:
            cfg[k] = expand_path(cfg[k])
    return cfg
