"""Fixed-size high/low resolution ring buffer with automatic decimation.

Shared by every plot widget that keeps a scrolling time history: appending
past the high-res capacity decimates the oldest samples into a much larger
low-res buffer instead of dropping them, so long sessions stay bounded in
memory while still allowing 'fit to full history' operations.
"""

import numpy as np


class TimeSeriesRingBuffer:
    def __init__(self, series_count, hr_max=1200, lr_max=10000, ds_rate=20):
        self.series_count = series_count
        self.hr_max = hr_max
        self.lr_max = lr_max
        self.ds_rate = ds_rate
        self.reset()

    def reset(self):
        self.hr_x = np.empty(self.hr_max, dtype=np.float64)
        self.hr_y = np.empty((self.hr_max, self.series_count), dtype=np.float64)
        self.hr_ptr = 0
        self.hr_count = 0

        self.lr_x = np.empty(self.lr_max, dtype=np.float64)
        self.lr_y = np.empty((self.lr_max, self.series_count), dtype=np.float64)
        self.lr_ptr = 0
        self.lr_count = 0

        self.ds_counter = 0

    def append(self, timestamp, values):
        if self.hr_count == self.hr_max:
            self.ds_counter += 1
            if self.ds_counter >= self.ds_rate:
                self.ds_counter = 0
                oldest_ptr = self.hr_ptr
                self.lr_x[self.lr_ptr] = self.hr_x[oldest_ptr]
                self.lr_y[self.lr_ptr, :] = self.hr_y[oldest_ptr, :]
                self.lr_ptr = (self.lr_ptr + 1) % self.lr_max
                if self.lr_count < self.lr_max:
                    self.lr_count += 1

        self.hr_x[self.hr_ptr] = timestamp
        self.hr_y[self.hr_ptr, :] = values
        self.hr_ptr = (self.hr_ptr + 1) % self.hr_max
        if self.hr_count < self.hr_max:
            self.hr_count += 1

    def snapshot(self):
        """Returns (x, y) arrays: low-res history followed by high-res recent data, oldest first."""
        if self.lr_count == 0:
            lr_x_out = np.array([], dtype=np.float64)
            lr_y_out = np.empty((0, self.series_count), dtype=np.float64)
        elif self.lr_count < self.lr_max:
            lr_x_out = self.lr_x[:self.lr_count]
            lr_y_out = self.lr_y[:self.lr_count]
        else:
            lr_x_out = np.concatenate((self.lr_x[self.lr_ptr:], self.lr_x[:self.lr_ptr]))
            lr_y_out = np.concatenate((self.lr_y[self.lr_ptr:], self.lr_y[:self.lr_ptr]))

        if self.hr_count < self.hr_max:
            hr_x_out = self.hr_x[:self.hr_count]
            hr_y_out = self.hr_y[:self.hr_count]
        else:
            hr_x_out = np.concatenate((self.hr_x[self.hr_ptr:], self.hr_x[:self.hr_ptr]))
            hr_y_out = np.concatenate((self.hr_y[self.hr_ptr:], self.hr_y[:self.hr_ptr]))

        if self.lr_count > 0:
            return np.concatenate((lr_x_out, hr_x_out)), np.concatenate((lr_y_out, hr_y_out))
        return hr_x_out, hr_y_out
