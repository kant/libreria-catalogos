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

install_cron: cron_jobs
	@echo "ROOTDIR=$$PWD" >> .cronfile
	@echo "PYTHON=$$PWD/venv/bin/python" >> .cronfile
	cat cron_jobs >> .cronfile
	crontab .cronfile
	rm .cronfile
	touch cron_jobs

rutina_diaria: venv
	$(PYTHON) main.py rutina_diaria
