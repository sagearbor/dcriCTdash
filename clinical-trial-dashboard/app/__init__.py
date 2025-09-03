"""
DCRI Clinical Trial Analytics Dashboard

FDA-compliant web application for real-time monitoring and analysis 
of clinical trial data at Duke Clinical Research Institute.
"""

__version__ = "0.1.0"
__author__ = "Duke Clinical Research Institute"
__email__ = "dcri@duke.edu"

# Core application imports
from . import core, data, components

__all__ = ["core", "data", "components"]