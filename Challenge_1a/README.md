To run: 
docker build --platform=linux/amd64 -t adobe_round1 .

docker run --rm -v "${PWD}\sample_dataset\pdfs:/app/input:ro" -v "${PWD}\sample_dataset\outputs:/app/output" --network none adobe_round1