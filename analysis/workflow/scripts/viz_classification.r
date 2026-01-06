library(tidyverse)
library(patchwork)
library(pROC)

tol_muted <- c(
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


dir_cent <- "results/fedsim_cent/federated.client+00@gmail.com/17307/"
dir_fed <- "results/fedsim_fed/"

prob_cent <- read_csv(paste0(dir_cent, "proba.csv"), col_names = TRUE)
pred_cent <- read_csv(paste0(dir_cent, "pred.csv"), col_names = TRUE)
test_cent <- read_csv(paste0(dir_cent, "test.csv"), col_names = TRUE)
# combine
rf_cent <- test_cent |>
  bind_cols(prob_cent) |>
  bind_cols(pred_cent)
rf_cent["client"] <- "centralized"


rf_fed <- read_csv(paste0(dir_fed, "combined_randfor.csv"), col_names = TRUE)
names(rf_fed) <- c("y_true_fed", "prob_0_fed", "prob_1_fed", "pred_fed", "client_fed") 

rf <- rf_cent |> bind_cols(rf_fed)

# calc correlation of probabilities
correlation <- cor(rf$prob_1, rf$prob_1_fed, method = "pearson")
rmse <- sqrt(mean((rf$prob_1 - rf$prob_1_fed)^2))


# P-P scatter plot
ppscatter <- ggplot(data = rf, mapping = aes(x = prob_1, y = prob_1_fed, color = client_fed)) +
  geom_point(alpha = 0.5) +
  scale_colour_manual(values = tol_muted) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "darkred") +
  labs(x = "p(centralized | y=1)", y = "p(federated | y=1)") +
  ggtitle(paste0("corr (Pearson): ", round(correlation, 4), 
                 " | RMSE: ", round(rmse, 4))) +
  ylim(0, 1) +
  xlim(0, 1) +
  theme_minimal() +
  theme(plot.title = element_text(size = 10), legend.title = element_blank()) 



# ggsave("figs/rf_ppscatter.png", plot = ppscatter, width = 8, height = 7)



#################################### 

# concatenate rf_cent and rf_fed for plotting
rf_fed2 <- read_csv(paste0(dir_fed, "combined_randfor.csv"), col_names = TRUE)
rf_combo <- bind_rows(rf_cent, rf_fed2)


# Distribution plot
dist_plot <- ggplot(data = rf_combo) +
  geom_density(aes(x = prob_1, color = client, fill = client), alpha = 0.3) +
  facet_wrap(y_true ~ client, nrow=2) +# , labeller = as_labeller(c(`0` = "True Class = 0", `1` = "True Class = 1"))) +
  labs(x = "p(y=1)", y = "density") +
  scale_colour_manual(values = c('darkgrey', tol_muted)) +
  scale_fill_manual(values = c('darkgrey', tol_muted)) +
  theme_minimal() +
  theme(legend.position = "none", strip.text = element_text(size = 8), axis.text.x = element_text(angle = 45, hjust = 1))


# ggsave("figs/rf_distplot.png", plot = dist_plot, width = 14, height = 6)


############################# ROC curves

roc_cent <- roc(rf_cent$y_true, rf_cent$prob_1)
roc_fed <- roc(rf_fed$y_true_fed, rf_fed$prob_1_fed)
# add auc and delta AUC as annotation to plot
delta_auc <- auc(roc_cent) - auc(roc_fed)
auc_annotation <- paste0("AUC(cent.) = ", round(auc(roc_cent), 4), 
                         "\nAUC(fed.) = ", round(auc(roc_fed), 4),
                         "\nΔAUC = ", round(delta_auc, 4))

roc_plot <- ggroc(list(cent = roc_cent, fed = roc_fed)) +
  scale_colour_manual(values = c("darkred", "darkblue")) +
  labs(x = "FP", y = "TPR") +
  annotate("text", x = 0.8, y = 0.2, label = auc_annotation, size = 3, hjust = 0) +
  theme_minimal() +
  theme(legend.title = element_blank()) 



randfor_fig <- ((ppscatter | roc_plot) / dist_plot) + plot_annotation(tag_levels = "A")
ggsave("randfor.png", plot = randfor_fig, width = 10, height = 8)
