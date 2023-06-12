all: deps

# install dependencies, mac
deps:
	brew install ffmpeg
	brew install portaudio
	brew install poetry
	brew install postgresql@14 
	brew install pgvector
	brew services run postgresql@14

# install packages
install:
	poetry install
	pip install tiktoken==0.3.2

# fix package issues
fix:
	pip install tiktoken==0.3.2

# create database
database:
	createdb gptva && psql -d gptva < schema.sql
	psql -d gptva -c "\dt"

# run project
run:
	python -m app