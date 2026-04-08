#!/usr/bin/env python

from datetime import datetime as dt
from pathlib import Path
from mi_timestamps import make_timestamps_monotonically_increasing
import numpy as np

def _to_datetime(x):
    if np.isnan(x):
        return "Date error"
    return dt.fromtimestamp(float(x)/1000)


def parse_timestamps(timestamps, sensor_name):
    """
    Convert raw timestamps to datetime objects.
    
    Args:
        timestamps: ndarray of raw timestamp values
        sensor_name: Name of the sensor for error reporting
    
    Returns:
        ndarray of datetime objects or "Date error" strings for failed conversions
    """
    if len(timestamps) == 0:
        return timestamps
    fixed_timestamps = make_timestamps_monotonically_increasing(timestamps, Path(sensor_name).stem)
    return np.vectorize(_to_datetime)(fixed_timestamps)
