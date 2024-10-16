# Define arrays for file paths and their corresponding remotes
$filePaths = @("input/final_kws_for_qns_generation.xlsx.dvc")
$remotes = @("final_kws_for_qns_generation")

# Loop through each file and remote using their indices
for ($i = 0; $i -lt $filePaths.Length; $i++) {
    $filePath = $filePaths[$i]
    $remote = $remotes[$i]
    Write-Host "Pulling $filePath from remote $remote..."
    & dvc pull $filePath --remote $remote
}
