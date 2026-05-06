close all
clear all
clc

% timing = readtable("timing_log_1_untrimmed.csv");
% timing = readtable("timing_log_2_untrimmed.csv");
timing = readtable("timing_log_3_untrimmed.csv");

end_time_margin_remove_s = 5;
duration_to_consider_from_end_s = 30;

end_time = timing.x1_sdk_update_loop_start(end) - end_time_margin_remove_s;
toConsiderEndIndex = find(timing.x1_sdk_update_loop_start > end_time);
toConsiderEndIndex = toConsiderEndIndex(1);
toConsiderStartIndex = find(timing.x1_sdk_update_loop_start < end_time - duration_to_consider_from_end_s);
toConsiderStartIndex = toConsiderStartIndex(end);

timing = timing(toConsiderStartIndex:toConsiderEndIndex, :);


t = timing.x1_sdk_update_loop_start - timing.x1_sdk_update_loop_start(1);



dt_start_to_start = diff(timing.x1_sdk_update_loop_start);
dt_frame_waiting = timing.x2_sdk_update_loop_got_frame - timing.x1_sdk_update_loop_start;
dt_sdk_device_data_fetch = timing.x4_sdk_update_loop_update_devices_end - timing.x3_sdk_update_loop_update_devices_start;
dt_sdk_labeled_markers_fetch = timing.x6_sdk_update_loop_update_labeled_markers_end - timing.x5_sdk_update_loop_update_labeled_markers_start;
dt_sdk_unlabeled_markers_fetch = timing.x8_sdk_update_loop_update_unlabeled_markers_end - timing.x7_sdk_update_loop_update_unlabeled_markers_start;
dt_sdk_update_subject_fetchNcompute = timing.x10_sdk_update_loop_update_subjects_end- timing.x9_sdk_update_loop_update_subjects_start;

dt_clean_plot_save_to_csv_get_active_subject = timing.x12_plot_clean_saving_to_csv_get_active_subject_end - timing.x11_plot_clean_saving_to_csv_get_active_subject_start;
dt_update_plotting = timing.x14_update_plotting_end - timing.x13_update_plotting_start;
dt_update_exporting = timing.x16_update_exporting_end - timing.x15_update_exporting_start;
dt_update_streaming = timing.x18_update_streaming_end - timing.x17_update_streaming_start;
dt_update_feedback = timing.x19_update_feedback_end - timing.x19_update_feedback_start;

dt_start_to_start_minus_frame_waiting = dt_start_to_start - dt_frame_waiting(1:end-1);
dt_elements_summned_minus_frame_waiting = dt_sdk_device_data_fetch + dt_sdk_labeled_markers_fetch + dt_sdk_unlabeled_markers_fetch + ...
    dt_sdk_update_subject_fetchNcompute + dt_clean_plot_save_to_csv_get_active_subject + dt_update_plotting + ...
    dt_update_exporting + dt_update_streaming + dt_update_feedback;

fps = 1./diff(timing.x1_sdk_update_loop_start);
plot(fps)
hold on 
plot(100./diff(timing.frameNumber))
plot(timing.frameNumber)
figure
hold on
plot(t(1:end-1), dt_start_to_start*1000, 'k')
plot(t, dt_frame_waiting*1000)
plot(t, dt_sdk_device_data_fetch*1000)
plot(t, dt_sdk_labeled_markers_fetch*1000)
plot(t, dt_sdk_unlabeled_markers_fetch*1000)
plot(t, dt_sdk_update_subject_fetchNcompute*1000)

plot(t, dt_clean_plot_save_to_csv_get_active_subject * 1000, '--')
plot(t, dt_update_plotting * 1000, '--')
plot(t, dt_update_exporting * 1000, '--')
plot(t, dt_update_streaming * 1000, '--')
plot(t, dt_update_feedback * 1000, '--')

plot(t(1:end-1), dt_start_to_start_minus_frame_waiting*1000, ':')
plot(t, dt_elements_summned_minus_frame_waiting * 1000, ':')

legend('dt_start_to_start', ...
        'dt_frame_waiting', ...
        'dt_sdk_device_data_fetch', ...
        'dt_sdk_labeled_markers_fetch', ...
        'dt_sdk_unlabeled_markers_fetch', ...
        'dt_sdk_update_subject_fetchNcompute', ...
        'dt_clean_plot_save_to_csv_get_active_subject', ...
        'dt_update_plotting', ...
        'dt_update_exporting', ...
        'dt_update_streaming', ...
        'dt_update_feedback', ...
        'dt_start_to_start_minus_frame_waiting', ...
        'dt_elements_summned_minus_frame_waiting(gui_even_processing)', ...
        'Interpreter', 'none')

xlabel('time (sec)')
ylabel('ms')
grid


print_statistics_row_ms("S1: dt_sdk_frame_waiting_ms                        ", dt_frame_waiting*1000)
print_statistics_row_ms("S2: dt_sdk_device_data_fetch_ms                    ", dt_sdk_device_data_fetch*1000)
print_statistics_row_ms("S3: dt_sdk_labeled_markers_fetch_ms                ", dt_sdk_labeled_markers_fetch*1000)
print_statistics_row_ms("S4: dt_sdk_unlabeled_markers_fetch_ms              ", dt_sdk_unlabeled_markers_fetch*1000)
print_statistics_row_ms("S5: dt_sdk_update_subject_fetchNcompute_ms         ", dt_sdk_update_subject_fetchNcompute*1000)
disp(' ')
print_statistics_row_ms("P1: dt_clean_plot_save_to_csv_get_active_subject_ms" ,dt_clean_plot_save_to_csv_get_active_subject * 1000)
print_statistics_row_ms("P2: dt_update_plotting_ms                          ", dt_update_plotting * 1000)
print_statistics_row_ms("P3: dt_update_exporting_ms                         ", dt_update_exporting * 1000)
print_statistics_row_ms("P4: dt_update_streaming_ms                         ", dt_update_streaming * 1000)
print_statistics_row_ms("P5: dt_update_feedback_ms                          ", dt_update_feedback * 1000)
disp(' ')
print_statistics_row_ms("S2+S3+S4+S5 + P1+P2+P3+P4+P5 ms", dt_elements_summned_minus_frame_waiting*1000)
print_statistics_row_ms("(GUI overhead + OS) ms         ", dt_start_to_start*1000 - dt_elements_summned_minus_frame_waiting(1:end-1)*1000 - dt_frame_waiting(1:end-1)*1000)
disp(' ')
print_statistics_row_ms("S1+S2+S3+S4+S5 + P1+P2+P3+P4+P5 + (GUI overhead + OS): dt_start_to_start_ms", dt_start_to_start*1000)
print_statistics_row_ms("dt_start_to_start_FPS                                                      ", fps)




function print_statistics_row_ms(Name, x)
    % Calculate the core metrics
    minV = min(x);
    maxV = max(x);
    medianV = median(x);
    meanV = mean(x);
    stdV = std(x);
    p99V = prctile(x, 99);

    % Formatted Output
    % %-20s: Left-aligns the name in a 20-character block
    % %7.4f: 7 total characters, 4 after the decimal (crucial for ms precision)
    fprintf('%-20s | min: %7.4f | med: %7.4f | max: %8.4f | mean: %7.4f | std: %7.4f | p99: %7.4f\n', ...
            Name, minV, medianV, maxV, meanV, stdV, p99V);
end


% plot(dt_update_loop_devices*1000)