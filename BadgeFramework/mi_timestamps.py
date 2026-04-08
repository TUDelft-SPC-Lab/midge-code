import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime


def make_timestamps_monotonically_increasing(timestamps, sensor_name, plotting=False):
    """
    Make timestamps monotonically increasing by fixing any timestamps that are in the future.

    Args:
        timestamps: List of timestamps
        sensor_name: Name of the sensor for error reporting

    Returns:
        List of datetime objects with future timestamps fixed
    """
    if len(timestamps) <= 2:
        return timestamps.copy()
    
    if "SCAN_" in sensor_name:
        return _remove_invalid_timestamps(timestamps, sensor_name)

    timestamps = timestamps.copy()
    if timestamps.ndim == 2 and timestamps.shape[1] == 1:
        timestamps = np.squeeze(timestamps, axis=1)

    timestamps = _remove_invalid_timestamps(timestamps, sensor_name)
    avg_diff = _get_median_timestamp_diff(timestamps, plotting=plotting)
    all_diffs = timestamps[1:] - timestamps[:-1]

    # Add the average difference at the beginning to align the indices for correction
    all_diffs = np.concatenate([[avg_diff], all_diffs], axis=0)

    first_valid_idx = _get_first_valid_timestamp_idx(timestamps, avg_diff)

    valid_diffs = all_diffs[first_valid_idx:]
    valid_timestamps = timestamps[first_valid_idx:]

    # Identify all the timestamps where there was a time correction.
    # Either a large jump or too small a difference
    correction_indices_large = np.nonzero(valid_diffs > (avg_diff * 2))[0]
    correction_indices_small = np.nonzero(valid_diffs < (avg_diff * 0.25))[0]

    if plotting:
        _print_debug_info(timestamps, valid_timestamps, correction_indices_large, correction_indices_small, avg_diff, valid_diffs, sensor_name)

    correction_indices = np.union1d(correction_indices_large, correction_indices_small)
    correction_indices = np.concatenate(
        [[0], correction_indices], axis=0
    )  # Add the first timestamp as a correction point

    for prev_idx, idx in zip(correction_indices[:-1], correction_indices[1:]):
        correction = _get_distributed_correction(valid_diffs, prev_idx, idx, avg_diff)
        if correction is not None:     
            valid_timestamps[prev_idx:idx] += correction

    timestamps[:first_valid_idx] = _fix_first_few_timestamps(
        timestamps, first_valid_idx, avg_diff
    )

    if plotting:
        _get_median_timestamp_diff(
            timestamps,
            plotting=True,
            plot_title="Fixed Consecutive Timestamp Differences",
        )

    return timestamps


def _print_debug_info(timestamps, valid_timestamps, correction_indices_large, correction_indices_small, avg_diff, valid_diffs, sensor_name):
    valid_dt = np.vectorize(lambda ts: datetime.fromtimestamp(float(ts) / 1000) if not np.isnan(ts) else None)(valid_timestamps)
    for idx in correction_indices_large:
        print(f"index, {idx}, time jump {valid_dt[idx] - valid_dt[idx - 1]}, time {valid_dt[idx]}")

    print("--------> Sensor: {}, Average timestamp diff: {:.2f} ms".format(sensor_name, avg_diff))
    print("--------> Sensor: {}, correction_indices_large: {}".format(sensor_name, correction_indices_large))
    print("--------> Sensor: {}, correction_indices_small: {}".format(sensor_name, correction_indices_small))
    
    print("--------> Sensor: {}, valid_diffs large: {}".format(sensor_name, valid_diffs[correction_indices_large]))
    print("--------> Sensor: {}, valid_diffs small: {}".format(sensor_name, valid_diffs[correction_indices_small]))
    print("--------> Sensor: {}, size: {}".format(sensor_name, len(timestamps)))

def _fix_first_few_timestamps(timestamps, first_valid_idx, avg_diff):
    return timestamps[first_valid_idx] - np.arange(first_valid_idx, 0, -1) * avg_diff


def _get_first_valid_timestamp_idx(timestamps, avg_diff):
    """
    Get the first valid timestamp from a ndarray of timestamps.

    Args:
        timestamps: ndarray of timestamps
        avg_diff: Average difference between consecutive timestamps
    Returns:
        The first valid timestamp or None if no valid timestamps are found
    """
    for i, ts in enumerate(timestamps):
        if i + 1 >= len(timestamps):
            break

        diff = np.abs(ts - timestamps[i + 1])
        if diff < avg_diff * 2 and diff < avg_diff / 0.25:
            return i

    raise RuntimeError("No valid timestamps found for sensor {}")


def _get_distributed_correction(diffs, prev_idx, idx, avg_diff):
    """
    Distribute the correction for a timestamp that was updated in the timestamps before it.

    Args:
        diffs: List of timestamp differences
        prev_idx: Index of the previous valid timestamp
        idx: Index of the current timestamp to be corrected
    """
    if idx - prev_idx <= 1:
        return  # No need to distribute if there are no intermediate timestamps

    diff_from_avg = diffs[idx] - avg_diff
    per_element_correction = np.linspace(0, diff_from_avg, idx - prev_idx + 1)
    if per_element_correction[1] < -avg_diff:
        error_msg = f"\tWarning: Large negative correction of {per_element_correction[1]:.2f} ms "
        error_msg += f" > than the average sample rate of {avg_diff:.2f} ms. "
        error_msg += "This will entail a jump backwards in time in the timestamps."
        print(error_msg)

    return per_element_correction[
        :-1
    ]  # Exclude the last element which has the updated timestamp already


def _remove_invalid_timestamps(timestamps, sensor_name):
    """
    Remove timestamps that are in the future or have conversion errors.

    Args:
        timestamps: ndarray of timestamps
        sensor_name: Name of the sensor for error reporting

    Returns:
        ndarray of valid timestamps, invalid are set to np.nan
    """

    class PrintOnce:
        def __init__(self):
            self.reported = False

        def report(self, message):
            if not self.reported:
                print(message)
                self.reported = True

    print_once = PrintOnce()

    def _filter_function(ts):
        try:
            datetime.fromtimestamp(float(ts) / 1000)
            return ts
        except Exception as e:
            print_once.report(
                "Error in timestamp conversion for sensor {}, ts {}: {}".format(
                    sensor_name, str(ts), str(e)
                )
            )
            return np.nan

    fixed_timestamps = np.vectorize(_filter_function)(timestamps)
    print(
        "Number of invalid timestamps for sensor {}: {}".format(
            sensor_name, np.sum(np.isnan(fixed_timestamps))
        )
    )
    return fixed_timestamps

def _get_median_timestamp_diff(
    timestamps, plotting=False, plot_title="Consecutive Timestamp Differences"
):
    """
    Calculate the median difference between consecutive timestamps.

    Args:
        timestamps: ndarray of datetime objects

    Returns:
        Median difference in seconds between consecutive timestamps
    """
    if timestamps.size < 2:
        raise RuntimeError("Not enough valid timestamps to calculate difference.")

    diffs_raw = timestamps[1:] - timestamps[:-1]
    diffs = np.abs(diffs_raw)

    valid_diffs = diffs[np.isfinite(diffs)]
    if valid_diffs.size == 0:
        raise RuntimeError("No valid timestamp differences found.")

    # The first few hundred timestamps can be very noisy, take the median instead of the average
    # for a more robust estimate
    avg_diff = np.nanmedian(valid_diffs)

    if plotting:
        plt.figure(figsize=(10, 4))

        # Subsample to avoid memory errors
        idx_to_plot = np.sort(
            np.random.choice(
                len(valid_diffs), size=min(len(valid_diffs), 1000), replace=False
            )
        )
        valid_diffs_to_plot = diffs_raw[idx_to_plot]

        plt.plot(valid_diffs_to_plot, label="Timestamp diffs", linewidth=1.5)
        plt.axhline(
            avg_diff, color="red", linestyle="--", label=f"Average: {avg_diff:.2f}"
        )
        plt.title(plot_title)
        plt.xlabel("Sample Index")
        plt.ylabel("Difference (ms)")
        plt.legend()
        plt.tight_layout()
        plt.show(block=False)

    return avg_diff


def _plot_bar(timestamps, title, fixed_indices):
    """ Plot the timestamps as a bar plot, with fixed_indices highlighted in red. """
    plt.figure(figsize=(10, 4))
    plt.bar(range(len(timestamps)), timestamps, width=0.8)
    for idx in fixed_indices:
        plt.bar(idx, timestamps[idx], width=0.8, color="red")
    plt.title(title)
    plt.xlabel("Sample Index")
    plt.ylabel("Timestamp (ms)")
    plt.tight_layout()
    plt.show(block=False)


if __name__ == "__main__":
    """
    Test and example usage of the make_timestamps_monotonically_increasing function with simulated timestamps.
    """
    import numpy.testing as npt

    now = 1775641284.420899  # time.time() # A timestamp in seconds
    np.set_printoptions(linewidth=np.inf)

    # Generate timestamps with a forward and a backwards jump
    timestamps = np.arange(0, 10, 1) * 18 + now * 1000
    print(str(timestamps - now * 1000))
    timestamps[3:] += 18 * 4  # Simulate a future timestamp, 72
    print(str(timestamps - now * 1000))
    timestamps[7:] -= 40  # Simulate a past timestamp

    fixed_timestamps = make_timestamps_monotonically_increasing(
        timestamps, "example_sensor", plotting=True
    )
    print(str(timestamps - now * 1000))
    print(fixed_timestamps - now * 1000)

    # fmt: off
    expected_timestamps = np.array([0, 0.04200006, 0.08400011, 0.12599993, 0.13400006,
                                    0.14199996, 0.1500001, 0.15799999, 0.17600012,
                                    0.19400001])
    # fmt: on
    npt.assert_allclose(fixed_timestamps / 1000 - now, expected_timestamps, rtol=1e-5)

    # Plot the increasing relative timestamps before and after correction, with the fixed indices highlighted
    _plot_bar(timestamps - now * 1000, "Original Timestamps", [3, 7])
    _plot_bar(fixed_timestamps - now * 1000, "Fixed Timestamps", [3, 7])

    plt.show()
