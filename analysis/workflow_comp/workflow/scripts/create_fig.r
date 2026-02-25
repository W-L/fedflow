library(tidyverse)
library(patchwork)
library(plotROC)
library(grid)
library(png)



tol_muted <- c(
  "darkgrey",   # for control
  "#CC6677",  # rose
  "#332288",  # indigo
  "#DDCC77",  # sand
  "#117733",  # green
  "#88CCEE",  # cyan
  "#882255",  # wine
  "#44AA99",  # teal
  "#999933",  # olive
  "#AA4499"   # purple
)


args <- commandArgs(trailingOnly = TRUE)
svd_cent <- args[1]
svd_fed <- args[2]
rf_cent_pred <- args[3]
rf_cent_proba <- args[4]
rf_cent_test <- args[5]  
rf_fed_in <- args[6]
rulegraph <- args[7]
out <- args[8]


# setwd("/home/lweilguny/fedflow/analysis/workflow_comp")
# svd_cent <- "results/biosphere/federated-svd/cent/federated.client+00@gmail.com/pca/localData.csv"
# svd_fed <- "results/biosphere/federated-svd/fed/combined_svd.csv"
# rf_cent_pred <- "results/biosphere/random-forest/cent/federated.client+00@gmail.com/pred.csv"
# rf_cent_proba <- "results/biosphere/random-forest/cent/federated.client+00@gmail.com/proba.csv"
# rf_cent_test <- "results/biosphere/random-forest/cent/federated.client+00@gmail.com/test.csv"
# rf_fed_in <- "results/biosphere/random-forest/fed/combined_randfor.csv"
# out <- "fig2.png"


proj_cent <- read_delim(svd_cent, col_names = TRUE)
proj_fed <- read_delim(svd_fed, col_names = TRUE)

colnames(proj_cent) <- make.names(colnames(proj_cent))
colnames(proj_fed) <- make.names(colnames(proj_fed))

# flip the axes for better comparison
proj_cent <- proj_cent %>%
  mutate(X1 = -X1)


# combine the two datasets for plotting
proj_cent["client"] <- "centralized"
proj_cent["facet"] <- "centralized"
proj_fed["facet"] <- "federated"
proj <- bind_rows(proj_cent, proj_fed)


embedding <- ggplot(data=proj, mapping=aes(x=X0, y=X1, color=client)) +
  facet_wrap(~facet) +
  geom_point(alpha = 0.5) +
  scale_colour_manual(values = tol_muted) +
  labs(x = "PC1", y = "PC2") +  
  theme_minimal() +
  theme(legend.position = "none", strip.text = element_blank()) 


##################################################


prob_cent <- read_csv(rf_cent_proba, col_names = TRUE)
pred_cent <- read_csv(rf_cent_pred, col_names = TRUE)
test_cent <- read_csv(rf_cent_test, col_names = TRUE)
# combine
rf_cent <- test_cent |>
  bind_cols(prob_cent) |>
  bind_cols(pred_cent)
rf_cent["client"] <- "centralized"


rf_fed <- read_csv(rf_fed_in, col_names = TRUE)
names(rf_fed) <- c("y_true_fed", "prob_0_fed", "prob_1_fed", "pred_fed", "client_fed") 
rf <- rf_cent |> bind_cols(rf_fed)

# calc correlation of probabilities - this works because the samples are in the same order
correlation <- cor(rf$prob_1, rf$prob_1_fed, method = "pearson")
rmse <- sqrt(mean((rf$prob_1 - rf$prob_1_fed)^2))

# P-P scatter plot
ppscatter <- ggplot(data = rf, mapping = aes(x = prob_1, y = prob_1_fed, color = client_fed)) +
  geom_point(alpha = 0.5) +
  coord_equal() +
  scale_colour_manual(values = tol_muted[2:length(tol_muted)]) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "darkgrey") +
  labs(x = "p(cent. | class=1)", y = "p(fed. | class=1)") +
  ggtitle(paste0("r = ", round(correlation, 3), 
                 " | RMSE = ", round(rmse, 3))) +
  ylim(0, 1) +
  xlim(0, 1) +
  theme_minimal() +
  theme(plot.title = element_text(size = 10), legend.position = "none") 


# concatenate rf_cent and rf_fed 
rf_fed2 <- read_csv(rf_fed_in, col_names = TRUE)
rf_combo <- bind_rows(rf_cent, rf_fed2)


# distribution of predicted probabilities by true class and client
dist_plot <- ggplot(rf_combo, aes(x = factor(y_true), y = prob_1, color = client)) +
  geom_hline(yintercept = 0.5, linetype = "dashed", color = "darkgrey") +
  geom_boxplot(position = position_dodge(width = 0.85)) +
  geom_point(alpha = 0.5, size = 1, position = position_jitterdodge(jitter.width = 0.25, dodge.width  = 0.85)) +
  labs(x = "True class", y = "p(class = 1)") +
  scale_colour_manual(values = tol_muted) +
  theme_minimal() + 
  theme(legend.position = "bottom", legend.title = element_blank())



############################# ROC curves


rocs <- ggplot(rf_combo, aes(d = y_true, m = prob_1, colour = client)) + 
    geom_abline(slope = 1, intercept = 0, linetype = "dashed", color="darkgrey") +
    geom_roc(labels=FALSE, n.cuts=0) +
    coord_equal() +
    scale_colour_manual(values = tol_muted) +
    labs(
      x = "False Positive Rate",
      y = "True Positive Rate",
    ) +
    theme_minimal() +
    theme(legend.position = "none") 


# Load rulegraph
rg <- rasterGrob(png::readPNG(rulegraph), interpolate = TRUE)

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
FFFF
"

fig <- (wrap_elements(rg) + embedding + ppscatter + rocs + dist_plot + guide_area()) +
    plot_annotation(tag_levels = "A") +
    plot_layout(design = design, guides = "collect") 


ggsave(out, plot = fig, width = 12, height = 9)
