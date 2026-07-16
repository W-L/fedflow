library(tidyverse)
library(patchwork)
library(grid)
library(png)


tol_muted <- c(
  "darkgrey",   # centralized
  "#CC6677",    # rose
  "#332288",    # indigo
  "#DDCC77",    # sand
  "#117733",    # green
  "#88CCEE",    # cyan
  "#882255",    # wine  — federated (aggregate)
  "#44AA99",    # teal
  "#999933",    # olive
  "#AA4499"     # purple
)

FED_AGG_LABEL <- "federated (aggregate)"

args <- commandArgs(trailingOnly = TRUE)
svd_cent         <- args[1]
svd_fed          <- args[2]
rf_auc_long      <- args[3]
rf_paired_summary <- args[4]
rf_wilcoxon      <- args[5]
rf_roc_aggregate <- args[6]
rf_proba_all     <- args[7]
rf_ppscatter     <- args[8]
rulegraph        <- args[9]
out              <- args[10]


# setwd("/home/lweilguny/fedflow/analysis/workflow_comp")
# svd_cent         <- "results/biosphere/federated-svd/cent/000/federated.client+00@gmail.com/pca/localData.csv"
# svd_fed          <- "results/biosphere/federated-svd/fed/000/combined_svd.csv"
# rf_auc_long      <- "results/biosphere/random-forest/stats/auc_long.csv"
# rf_paired_summary <- "results/biosphere/random-forest/stats/paired_summary.csv"
# rf_wilcoxon      <- "results/biosphere/random-forest/stats/wilcoxon.csv"
# rf_roc_aggregate <- "results/biosphere/random-forest/stats/roc_aggregate.csv"
# rf_proba_all     <- "results/biosphere/random-forest/stats/proba_all.csv"
# rf_ppscatter     <- "results/biosphere/random-forest/stats/ppscatter.csv"
# rulegraph        <- "figs/rulegraph.png"
# out              <- "figs/fig_results_biosphere.png"


# shared colour palette
auc_long <- read_csv(rf_auc_long, col_names = TRUE, show_col_types = FALSE)
cohort_clients <- sort(unique(auc_long$client[
  !auc_long$client %in% c("centralized", FED_AGG_LABEL)
]))
client_order <- c("centralized", FED_AGG_LABEL, cohort_clients)
n_cohorts <- length(cohort_clients)
client_colors <- setNames(
  tol_muted[c(1L, n_cohorts + 2L, seq(2L, n_cohorts + 1L))],
  client_order
)


# panel A: rulegraph
rg <- rasterGrob(png::readPNG(rulegraph), interpolate = TRUE)

# panel B: federated SVD embedding
proj_cent <- read_delim(svd_cent, col_names = TRUE, show_col_types = FALSE)
proj_fed  <- read_delim(svd_fed,  col_names = TRUE, show_col_types = FALSE)
colnames(proj_cent) <- make.names(colnames(proj_cent))
colnames(proj_fed)  <- make.names(colnames(proj_fed))
proj_cent[["client"]] <- "centralized"
proj_cent[["facet"]]  <- "centralized"
proj_fed[["facet"]]   <- "federated"
proj <- bind_rows(proj_cent, proj_fed)

embedding <- ggplot(proj, aes(x = X0, y = X1, color = client)) +
  facet_wrap(~facet) +
  geom_point(alpha = 0.5) +
  scale_colour_manual(values = client_colors, na.value = "grey80") +
  labs(x = "PC1", y = "PC2") +
  theme_minimal() +
  theme(legend.position = "none", strip.text = element_blank())



# panel C: P-P scatter (cent vs fed, colour = cohort)
ppscatter_df <- read_csv(rf_ppscatter, col_names = TRUE, show_col_types = FALSE) |>
  mutate(client = factor(client, levels = client_order))

overall_cor  <- cor(ppscatter_df$prob_1_cent, ppscatter_df$prob_1_fed, method = "pearson")
overall_rmse <- sqrt(mean((ppscatter_df$prob_1_cent - ppscatter_df$prob_1_fed)^2))

ppscatter <- ggplot(ppscatter_df, aes(x = prob_1_cent, y = prob_1_fed, color = client)) +
  geom_point(alpha = 0.12, size = 0.5) +
  coord_equal() +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "darkgrey") +
  scale_colour_manual(values = client_colors) +
  labs(
    x = "p(cent. | class=1)",
    y = "p(fed. | class=1)",
    title = paste0("r = ", round(overall_cor, 3),
                   " | RMSE = ", round(overall_rmse, 3))
  ) +
  xlim(0, 1) +
  ylim(0, 1) +
  theme_minimal() +
  theme(plot.title = element_text(size = 9), legend.position = "none")


# panel D: aggregated ROC curves
roc_agg <- read_csv(rf_roc_aggregate, col_names = TRUE, show_col_types = FALSE) |>
  mutate(client = factor(client, levels = client_order))

rocs <- ggplot() +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "darkgrey") +
  geom_ribbon(
    data = roc_agg,
    aes(x = fpr, ymin = lower_tpr, ymax = upper_tpr, fill = client),
    alpha = 0.15, color = NA
  ) +
  geom_line(
    data = roc_agg,
    aes(x = fpr, y = mean_tpr, colour = client),
    linewidth = 0.8
  ) +
  # coord_equal() +
  scale_colour_manual(values = client_colors) +
  scale_fill_manual(values = client_colors) +
  labs(x = "False Positive Rate", y = "True Positive Rate") +
  theme_minimal() +
  theme(legend.position = "none")
# rocs

# panel E: probability boxplots
proba_all <- read_csv(rf_proba_all, col_names = TRUE, show_col_types = FALSE) |>
  mutate(client = factor(client, levels = client_order), prob_1 = as.numeric(prob_1))


dist_plot <- ggplot(proba_all, aes(x = factor(y_true), y = prob_1, color = client)) +
  geom_hline(yintercept = 0.5, linetype = "dashed", color = "darkgrey") +
  geom_violin(aes(fill=client), quantile.linetype = "solid", quantile.color="black") +
  labs(x = "True class", y = "p(class = 1)") +
  scale_colour_manual(values = client_colors) +
  scale_fill_manual(values = client_colors) +
  theme_minimal() +
  theme(legend.position = "bottom", legend.title = element_blank())
# dist_plot

# panel F: AUC boxplots
paired_summary <- read_csv(rf_paired_summary, col_names = TRUE, show_col_types = FALSE)
wilcoxon       <- read_csv(rf_wilcoxon,       col_names = TRUE, show_col_types = FALSE)

auc_subtitle <- paste0(
  "mean \u0394AUC = ", round(paired_summary$mean_delta_auc[1], 4),
  " \u00b1 ", round(paired_summary$sd_delta_auc[1], 4),
  "\n",
  "Wilcoxon p = ", signif(wilcoxon$p_value[1], 3)
)

auc_long_filtered <- auc_long |>
  filter(client %in% c("centralized", FED_AGG_LABEL)) |>
  mutate(client = factor(client, levels = c("centralized", FED_AGG_LABEL)))

auc_box <- ggplot(auc_long_filtered, aes(y = client, x = auc, color = client)) +
  geom_violin(aes(fill=client), quantile.linetype = "solid", quantile.color="black") +
  scale_colour_manual(values = client_colors[c("centralized", FED_AGG_LABEL)]) +
  scale_fill_manual(values = client_colors[c("centralized", FED_AGG_LABEL)]) +
  scale_y_discrete(guide = "none") +
  labs(y = "", x = "ROC-AUC", title = auc_subtitle) +
  theme_minimal() +
  theme(
    legend.position = "none",
    plot.title = element_text(size = 9)
  )
# auc_box




design <- "
AACD
AACD
AACD
AAEE
AAEE
AAEE
BBEE
BBEE
BBEE
GGFF
"


fig <- (wrap_elements(rg) + embedding + ppscatter + rocs + dist_plot + auc_box + guide_area()) +
  plot_annotation(tag_levels = "A") +
  plot_layout(design = design, guides = "collect")

ggsave(out, plot = fig, width = 12, height = 10, dpi = 400)

