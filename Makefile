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

add_environ:
	@echo "ROOTDIR=$$PWD" >> ~/.bashrc
	@echo "PYTHON=$$PWD/venv/bin/python" >> ~/.bashrc

setup: venv install_cron add_environ
	test -d logs || mkdir logs
	test -d archivo || mkdir archivo

update_environment:
	git pull
	venv/bin/pip install -r requirements.txt --upgrade

main: update_environment
	$(PYTHON) main.py

clean:
	rm -rf venv/
	cat /dev/null | crontab
