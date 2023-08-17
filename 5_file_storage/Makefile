COMPOSE = docker-compose -f docker-compose.yml
BASE_COMMAND = ${COMPOSE} run --rm storage
COMMAND = ${BASE_COMMAND}  /bin/bash -c

build:
	${COMPOSE} up --build

install:
    ${COMMAND} 'pip install -r requirements.txt'

migrate:
	${COMMAND} 'alembic upgrade head'

run:
    ${COMMAND} 'python src/main.py'

test:
	${COMMAND} 'pytest'

clean:
    $(COMMAND) 'rm -rf __pycache__'
	$(COMMAND) 'rm -rf build'
	$(COMMAND) 'rm -rf dist'
	$(COMMAND) 'rm -rf file_storage.egg-info'
