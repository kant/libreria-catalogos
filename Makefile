# crear entorno virtual e instalar paquetes
# remover entorno virtual
# crear cronfile
# instalar cronfile
# correr rutina diaria

# Las dos recetas siguientes fueron tomadas de
# http://blog.bottlepy.org/2012/07/16/virtualenv-and-makefiles.html
download_python:
	wget https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz -P ~/
	tar -zxvf ~/Python-2.7.10.tgz
	cd ~/Python-2.7.10
	mkdir ~/.localpython
	./configure --prefix=$HOME/.localpython
	make
	make install

venv: venv/bin/activate

venv/bin/activate: requirements.txt
	test -d venv || virtualenv venv -p $HOME/.localpython/bin/python2.7
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

setup: download_python venv install_cron create_dir

setup_without_cron: download_python venv create_dir

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
