# Load required libraries
library(seriation)
library(tools)  # For file path manipulation
library(R.utils)  # for timeout

# Function to process a single CSV file
process_file <- function(file_path, output_folder, time_out, repetitions, method_number) {
  cat("\nProcessing:", basename(file_path), "\n")

  # Read the dissimilarity matrix from the CSV file
  diss_matrix <- as.matrix(read.csv(file_path, header = TRUE, row.names = 1))

  # Convert to dist object
  diss_dist <- as.dist(diss_matrix)

  # List available seriation methods
  methods_list <- list_seriation_methods("dist")
  stopifnot(length(methods_list) == method_number)

  # Manually define available evaluation criteria
  criteria_list <- c("AR_events", "AR_deviations", "BAR", "Gradient_raw", "Gradient_weighted",
                     "Path_length", "Inertia", "Least_squares", "LS", "2SUM", "ME", "Moore_stress", "Neumann_stress")

  # Initialize dataframe to store evaluation results
  me_results <- data.frame(matrix(NA, nrow=length(methods_list)*repetitions+1, ncol=2+length(criteria_list)))
  colnames(me_results) <- c("Name", "Method", criteria_list)

  # Function to compute all criteria for a given dist object
  compute_criteria <- function(dist_obj, order_obj) {
    sapply(criteria_list, function(crit) {
      tryCatch(criterion(dist_obj, method = crit, order=order_obj), error = function(e) NA)
    })
  }

  # Compute metrics for the original matrix (WITHOUT applying seriation methods)
  original_criteria <- compute_criteria(diss_dist, NULL)
  me_results[1,] <- c("Original", "None", as.list(original_criteria))

  # Set seed for reproducibility
  set.seed(123)

  # Total number of iterations (for progress bar)
  total_steps <- repetitions * length(methods_list)

  # Generate random permutations and apply all methods
  for (i in 1:repetitions) {
    # Random permutation of object order
    perm_order <- sample(nrow(diss_matrix))

    # Apply permutation correctly to both rows & columns
    permuted_dist <- as.dist(diss_matrix[perm_order, perm_order])


    # Loop through each seriation method
    j <- 0
    for (method in methods_list) {
      # increase the counter variable
      j <- j + 1

      # Try to apply the method (some may fail)
      start_time = Sys.time()
      seriation_result <- tryCatch({
          withTimeout({
                seriate(permuted_dist, method = method)
            }, onTimeout="warning", timeout=time_out)
      }, error = function(e) -1)
      end_time = Sys.time()
      print(paste0("Time for method", method))
      print(start_time)
      print(end_time)
      print("-----------")

      # If seriation was successful, compute evaluation metrics
      if (is.null(seriation_result)) {
        # fill in that the method timed out
        print(paste0("Method ", method, " timed out."))
        me_results[(i-1)*length(methods_list)+j+1,] <- c(paste0("Permutation_", i), method, rep(c(Inf), length(criteria_list)))
      }
      else if (is.list(seriation_result)) {
        # permute the dist matrix
        reordered_dist <- permute(permuted_dist, seriation_result)

        # Compute all criteria
        criteria_values <- compute_criteria(permuted_dist, seriation_result)

        # Store results
        me_results[(i-1)*length(methods_list)+j+1,] <- c(paste0("Permutation_", i), method, as.list(criteria_values))
      }
      else {
        # Store results with NA values
        print(paste0("Method ", method, " reported an error."))
        me_results[(i-1)*length(methods_list)+j+1,] <- c(paste0("Permutation_", i), method, rep(c(NA), length(criteria_list)))
      }
      print("")
    }
  }

  # Convert all numeric columns to proper data types
  me_results[, 3:ncol(me_results)] <- lapply(me_results[, 3:ncol(me_results)], as.numeric)

  # Construct output filename
  file_name <- file_path_sans_ext(basename(file_path))  # Get filename without extension
  output_file <- file.path(output_folder, paste0(file_name, "_reordering_results.csv"))

  # Save evaluation results to a CSV file
  write.csv(me_results, output_file, row.names = FALSE)
  cat("✔ Saved results to:", output_file, "\n")
}

# ------------------- MAIN SCRIPT -------------------

# Get command-line arguments
args <- commandArgs(trailingOnly = TRUE)
# we expect [foldername, time out in seconds, number of repetitions, expected number of methods, OPTIONAL: filename]

# Check if the user provided a folder path
if (length(args) == 0) {
  stop("❌ Please provide a folder path as an argument.\nUsage: Rscript script.R /path/to/folder")
}
if (length(args) == 1) {
  stop("❌ Please provide a timeout in seconds for each of the methods.")
}
if (length(args) == 2) {
  stop("❌ Please provide a number of repetitions.")
}
if (length(args) == 3) {
  stop("❌ Please provide a number of methods you expect.")
}

# Get folder path from argument
input_folder <- args[1]

# Check if the folder exists
if (!dir.exists(input_folder)) {
  stop("❌ The specified folder does not exist.")
}

# get the time out per method
time_out <- as.integer(args[2])

# get the repetitions per method
repetitions <- as.integer(args[3])

# get the repetitions per method
method_number <- as.integer(args[4])

# Get all CSV files in the folder
csv_files <- list.files(input_folder, pattern = "\\.csv$", full.names = TRUE)
csv_files <- grep("_reordering_results", csv_files, invert=TRUE, value = TRUE)
if (length(args) == 5) {
    csv_files <- grep(args[5], csv_files, value = TRUE)
}

# Check if there are CSV files
if (length(csv_files) == 0) {
  stop("❌ No CSV files found in the specified folder.")
}

cat("\n📂 Found", length(csv_files), "CSV files. Processing...\n")

# Process each file
for (file in csv_files) {
  process_file(file, input_folder, time_out, repetitions, method_number)
}

# show the warnings
warnings()
cat("\n✅ All files processed successfully!\n")
