library(ggplot2)
library(patchwork)

# setwd('analysis/workflow_benchmarks/metrics')

# Read CSV files
df <- read.csv("metrics_long.csv", stringsAsFactors = FALSE)
phase_df <- read.csv("metrics_phase_long.csv", stringsAsFactors = FALSE)

df$data_size_cat <- as.factor(df$data_size)
phase_df$data_size_cat <- as.factor(phase_df$data_size)
df$nclients_cat <- as.factor(df$nclients)
df$rep <- as.factor(df$rep)


tol_muted <- c(
  "#CC6677", # rose
  "#332288", # indigo
  "#DDCC77", # sand
  "#117733", # green
  "#88CCEE", # cyan
  "#882255", # wine
  "#44AA99", # teal
  "#999933", # olive
  "#AA4499"  # purple
)

n_dodge <- 3


# Plot 1A: Runtime vs number of clients
plot_runtime_vs_clients <- ggplot(df, aes(x = nclients, y = wall_clock_seconds, color = data_size_cat)) +
  scale_color_manual(values = tol_muted) +
  geom_smooth(method = "lm", se = TRUE, color = "darkgrey", alpha = 0.7) +
  geom_point(position = position_jitter(width = 0.5, height = 0), alpha = 0.7) +
  scale_x_continuous(breaks = sort(unique(df$nclients)), guide = guide_axis(n.dodge = n_dodge)) +
  labs(
    x = "number of clients",
    y = "wall-clock time (s)",
    color = "data size",
  ) +
  theme_minimal() +
  theme(legend.position = "none")

# Plot 1B: CPU vs number of clients
plot_cpu_vs_clients <- ggplot(df, aes(x = nclients, y = process_cpu_seconds, color = data_size_cat)) +
  scale_color_manual(values = tol_muted) +
  geom_smooth(method = "lm", se = TRUE, color = "darkgrey", alpha = 0.7) +
  geom_point(size = 1, position = position_jitter(width = 0.5, height = 0), alpha = 0.7) +
  scale_x_continuous(breaks = sort(unique(df$nclients)), guide = guide_axis(n.dodge = n_dodge)) +
  labs(
    x = "number of clients",
    y = "total CPU time (s)",
    color = "data size",
  ) +
  theme_minimal() +
  theme(legend.position = "right")


# Plot 2D: Runtime vs data size
plot_runtime_vs_datasize <- ggplot(df, aes(x = data_size, y = wall_clock_seconds, color = nclients_cat)) +
  scale_color_manual(values = tol_muted) +
  geom_smooth(aes(group = nclients_cat), method = "lm", se = TRUE, alpha = 0.7, show.legend = FALSE) +
  geom_point(size = 1, position = position_jitter(width = 0.05, height = 0), alpha = 0.7) +
  scale_x_log10() +
  labs(
    x = "input data size per client",
    y = "wall-clock time (s)",
    color = "clients",
  ) +
  theme_minimal() +
  theme(legend.position = "right",
)


# Plot 3C: Memory usage vs number of clients
plot_memory <- ggplot(df, aes(x = nclients, y = peak_rss_mib, color = data_size_cat)) +
  scale_color_manual(values = tol_muted) +
  geom_smooth(method = "lm", se = TRUE, color = "darkgrey", alpha = 0.7) +
  geom_point(size = 2, position = position_jitter(width = 0.5, height = 0), alpha = 0.7) +
  scale_x_continuous(breaks = sort(unique(df$nclients)), guide = guide_axis(n.dodge = n_dodge)) +
  labs(
    x = "number of clients",
    y = "peak RSS (MiB)",
    color = "data size",
  ) +
  theme_minimal() +
  theme(legend.position = "none")


# Plot phase breakdown 
phase_df$phase[phase_df$phase == "provision_clients"] <- "dependency_check"
phase_df$phase[phase_df$phase == "post_run_settle_sleep"] <- "settle_sleep"
phase_df$phase[phase_df$phase == "start_featurecloud_controllers"] <- "start_featurecloud"
phase_df$phase[phase_df$phase == "create_and_join_project"] <- "join_project"
phase_df$phase[phase_df$phase == "contribute_data_to_project"] <- "contribute_data"
phase_df <- phase_df[phase_df$phase != "distribute_credentials", ]

ordered_phases <- c(
  "connect_clients",
  "dependency_check",
  "install_package",
  "reset_clients",
  "start_featurecloud",
  "distribute_data",
  "join_project",
  "contribute_data",
  "monitor_project_run",
  "settle_sleep",
  "fetch_results",
  "cleanup"
)

phase_df$phase <- factor(phase_df$phase, levels = ordered_phases, ordered = TRUE)


# Plot 3E: Faceted phase duration vs number of clients
plot_phase_breakdown <- ggplot(phase_df, aes(x = nclients, y = duration_seconds)) +
  geom_smooth(method = "lm", se = TRUE, color = "darkgrey", alpha = 0.7) +
  geom_point(size = 1, position = position_jitter(width = 0.8, height = 0), color = tol_muted[2], alpha = 0.5) +
  scale_x_continuous(breaks = sort(unique(df$nclients)), guide = guide_axis(n.dodge = n_dodge)) +
  facet_wrap(~ phase, ncol = 2, scales = "free_y") +
  labs(
    x = "number of clients",
    y = "phase duration (s)",
  ) +
  theme_minimal()

# Example run for 64 clients, data_size=10000, rep=0
phase_df_64_10000_0 <- phase_df[
  phase_df$nclients == 64 &
    phase_df$data_size == 10000 &
    phase_df$rep == 0,
]

phase_df_64_10000_0$phase <- factor(
  phase_df_64_10000_0$phase,
  levels = rev(ordered_phases),
  ordered = TRUE
)

# Plot 3F: Example phase bar chart
plot_phase_example <- ggplot(phase_df_64_10000_0, aes(x = phase, y = duration_seconds, fill = phase)) +
  geom_col(width = 1) +
  coord_flip() +
  labs(
    y = "duration (s)",
    x = ""
  ) +
  theme_minimal() +
  theme(legend.position = "none")


# Compose all plots into a single figure

design <- "
ABEEE
CDEEE
FFEEE
"

fig <- (
    plot_runtime_vs_clients + 
    plot_cpu_vs_clients + 
    plot_memory + 
    plot_runtime_vs_datasize + 
    plot_phase_breakdown + 
    free(plot_phase_example)
) + plot_annotation(tag_levels = "A") + plot_layout(design = design)


ggsave("metrics_summary.png", plot = fig, width = 12, height = 9, dpi = 400)

