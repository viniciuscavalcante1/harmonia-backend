git clone https://github.com/viniciuscavalcante1/harmonia-backend # Clone o repositório

cd harmonia-backend # Acesse o repositório

docker build -t harmonia-api . # Construa a imagem do docker

docker run -p 8000:8080 --env-file .env --name harmonia-app harmonia-api # Execute o contêiner com a imagem construída