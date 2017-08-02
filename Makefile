# crear entorno virtual e instalar paquetes
# remover entorno virtual
# crear cronfile
# instalar cronfile
# correr rutina diaria

# Las dos recetas siguientes fueron tomadas de
# http://blog.bottlepy.org/2012/07/16/virtualenv-and-makefiles.html
venv: venv/bin/activate

venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv
	venv/bin/pip install -r requirements.txt
	touch venv/bin/activate

# Las siguientes recetas son especÃficas a nuestro repositorio
install_cron: cron_jobs
	@echo "ROOTDIR=$$PWD" >> .cronfile
	@echo "PYTHON=$$PWD/venv/bin/python" >> .cronfile
	cat cron_jobs >> .cronfile
	crontab .cronfile
	rm .cronfile
	touch cron_jobs

create_dir:
	mkdir -p logs
	mkdir -p archivo

setup: venv install_cron create_dir

setup_without_cron: venv create_dir

update_environment:
	git pull
	venv/bin/pip install -r requirements.txt --upgrade

all: update_environment
	$$PWD/venv/bin/python main.py

all_local:
	git pull
	python main.py

clean:
	rm -rf venv/
	cat /dev/null | crontab
