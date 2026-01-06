library(tidyverse)
library(patchwork)


dir_cent = "results/fedsim_cent/federated.client+00@gmail.com/17306/pca/"
dir_fed = "results/fedsim_fed/"

proj_cent <- read_delim(paste0(dir_cent, "localData.csv"), col_names = TRUE)
proj_fed <- read_delim(paste0(dir_fed, "combined_localdata.csv"), col_names = TRUE)

colnames(proj_cent) <- make.names(colnames(proj_cent))
colnames(proj_fed) <- make.names(colnames(proj_fed))

# flip the axes for better comparison
proj_cent <- proj_cent %>%
  mutate(X0 = -X0)


embedding_cent <- ggplot(data=proj_cent, mapping=aes(x=X0, y=X1)) +
  geom_point(alpha = 0.7) +
  theme_minimal() 

embedding_fed <- ggplot(data=proj_fed, mapping=aes(x=X0, y=X1, color=client)) +
  geom_point(alpha = 0.7) +
  theme_minimal()

# patchwork to combine plots
embedding <- embedding_cent / embedding_fed + plot_annotation(tag_levels = "A")

ggsave("embedding_combo.png", plot = embedding, width = 8, height = 7)







# Load eigenvalues
# eigvals <- read_tsv("pca/eigenvalues.tsv", col_names = FALSE) |>
#   rename(eigenvalue = X1) |>
#   mutate(variance_explained = eigenvalue / sum(eigenvalue))

# Optional: load feature loadings (right singular vectors)
# loadings <- read_tsv("pca/right_eigenvectors.tsv")
# colnames(loadings) <- make.names(colnames(loadings))

# Optional: global feature means and stds
# means <- read_tsv("pca/mean.tsv", col_names = c("feature", "mean"))
# stds  <- read_tsv("pca/std.tsv",  col_names = c("feature", "std"))

# var_exp <- eigvals$variance_explained * 100
# xlab <- paste0("PC1 (", round(var_exp[1], 1), "%)")
# ylab <- paste0("PC2 (", round(var_exp[2], 1), "%)")


# Ensure sample IDs exist
# proj <- proj |>
  # mutate(sample = row_number()) |>
  # relocate(sample)


# Take top contributing features by loading magnitude
# top_features <- loadings |>
#   mutate(magnitude = sqrt(X0^2 + X1^2)) |>
#   slice_max(order_by = magnitude, n = 8)



# scree <- ggplot(eigvals,
#                 aes(
#                     x = seq_along(eigenvalue),
#                     y = variance_explained * 100)) +
#   geom_col(fill = "#4575B4") +
#   labs(x = "Component", y = "Variance Explained (%)", title = "Scree Plot") +
#   theme_minimal(base_size = 20)

# ggsave("viz_projections.png", plot = embedding, width = 8, height = 6)
# ggsave("viz_scree.png", plot = scree, width = 8, height = 6)
