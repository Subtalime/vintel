#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#

from .stopwatch import StopWatch


class ViStopwatch(StopWatch):
    def get_report(self, extra_message: str = None):
        def format_report(aggregated_report):
            """returns a pretty printed string of reported values"""
            values = aggregated_report.aggregated_values
            root_tr_data = aggregated_report.root_timer_data

            # fetch all values only for main stopwatch, ignore all the tags
            log_names = sorted(log_name for log_name in values if "+" not in log_name)
            if not log_names:
                return ""

            root = log_names[0]
            root_time_ms, root_count, bucket = values[root]
            buf = [
                "   %.45s  %9.3fms (%3.f%%)"
                % (root.ljust(45), root_time_ms / root_count, 100),
            ]
            for log_name in log_names[1:]:
                delta_ms, count, bucket = values[log_name]
                depth = log_name[len(root) :].count("#")
                short_name = log_name[log_name.rfind("#") + 1 :]
                bucket_name = bucket.name if bucket else ""

                buf.append(
                    "%s%.12s  %.25s  %4d  %9.3fms (%3.f%%)"
                    % (
                        "   " * depth,
                        bucket_name.ljust(12),
                        short_name.ljust(25),
                        count,
                        delta_ms,
                        delta_ms / root_time_ms * 100.0,
                    )
                )

            annotations = sorted(ann.key for ann in root_tr_data.trace_annotations)
            if annotations:
                buf.append("Annotations: %s" % (", ".join(annotations)))
            return "\n".join(buf)

        time_msg = "Timing:\n"
        formatted = format_report(self.get_last_aggregated_report())
        if formatted:
            time_msg += format_report(self.get_last_aggregated_report())
            if extra_message:
                time_msg += "\n" + extra_message

        return time_msg

    def root_time(self) -> float:  # ms
        aggregated_report = self.get_last_aggregated_report()
        values = aggregated_report.aggregated_values

        log_names = sorted(log_name for log_name in values if "+" not in log_name)
        if not log_names:
            return 0.0

        root = log_names[0]
        root_time_ms, root_count, bucket = values[root]
        return root_time_ms / root_count
