# prereq: install.packages("lidR")
library(lidR)

# simple workflow: read, classify ground, normalize
las <- readLAS("path/to/input.laz")
opt_output_files("path/to/processed/{ORIGINALBASENAME}_norm.laz")
# classify ground with csf
las = classify_ground(las, csf())
# normalize
las_norm = normalize_height(las, knnidw(k = 10L, p = 2))
writeLAS(las_norm, "path/to/output_norm.laz")
