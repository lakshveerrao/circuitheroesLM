"""Native circuitheroesLM host reference package."""

PROJECT_NAME = "circuitheroesLM"
FORMAT_MAGIC = b"CHLM"

from .model import ESRConfig, EngineeringStateRouterLM

__all__ = ["PROJECT_NAME", "FORMAT_MAGIC", "ESRConfig", "EngineeringStateRouterLM"]

