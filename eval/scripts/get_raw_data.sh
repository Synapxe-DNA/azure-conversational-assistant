#!/bin/bash

# Define parallel arrays for paths and their corresponding remotes
file_paths=("input/final_kws_for_qns_generation.xlsx.dvc")
remotes=("final_kws_for_qns_generation")

# Loop through each file and remote using indexed arrays
for i in "${!file_paths[@]}"; do
    file_path="${file_paths[$i]}"
    remote="${remotes[$i]}"
    echo "Pulling $file_path from remote $remote..."
    dvc pull "$file_path" --remote "$remote"
done
