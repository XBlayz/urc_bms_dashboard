"""Shared heatmap color gradients used by cell voltage/temperature visualizations
(bar_chart matrix view and, optionally, bar coloring)."""

from PyQt6.QtGui import QColor


class HeatmapGradient:
    """Three-point color gradient (low -> optimal -> high) mapping a scalar to a QColor."""

    def __init__(self, min_val, opt_val, max_val, alpha=80, out_of_range_alpha=60):
        self.min_val = min_val
        self.opt_val = opt_val
        self.max_val = max_val
        self.alpha = alpha
        self.out_of_range_alpha = out_of_range_alpha

    def color_for(self, value):
        raise NotImplementedError


class VoltageHeatmap(HeatmapGradient):
    """Red at both extremes (under/over-voltage), green at the optimal voltage."""

    def color_for(self, value):
        if value is None:
            return None
        if value <= self.min_val or value >= self.max_val:
            return QColor(255, 0, 0, self.out_of_range_alpha)
        if value <= self.opt_val:
            ratio = (value - self.min_val) / (self.opt_val - self.min_val)
        else:
            ratio = 1.0 - (value - self.opt_val) / (self.max_val - self.opt_val)
        r = int((1 - ratio) * 255)
        g = int(ratio * 255)
        return QColor(r, g, 0, self.alpha)


class TemperatureHeatmap(HeatmapGradient):
    """Blue at low temperature, green at the optimal temperature, red at high temperature."""

    def color_for(self, value):
        if value is None:
            return None
        if value <= self.min_val:
            return QColor(0, 0, 255, self.out_of_range_alpha)
        if value >= self.max_val:
            return QColor(255, 0, 0, self.out_of_range_alpha)
        if value <= self.opt_val:
            ratio = (value - self.min_val) / (self.opt_val - self.min_val)
            b = int((1 - ratio) * 255)
            g = int(ratio * 255)
            return QColor(0, g, b, self.alpha)
        ratio = (value - self.opt_val) / (self.max_val - self.opt_val)
        r = int(ratio * 255)
        g = int((1 - ratio) * 255)
        return QColor(r, g, 0, self.alpha)
