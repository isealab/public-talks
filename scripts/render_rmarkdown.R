#!/usr/bin/env Rscript

files <- sort(list.files(pattern = "\\.Rmd$", recursive = TRUE, ignore.case = TRUE))

if (length(files) == 0) {
  stop("No R Markdown files found.", call. = FALSE)
}

for (file in files) {
  message("Rendering ", file)
  rmarkdown::render(
    input = file,
    envir = new.env(parent = globalenv()),
    quiet = FALSE
  )
}
