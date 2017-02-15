# Pasos seguidos para configurar un usuario de git con clave SSH propia

1. Generar un par de claves publica/privada propias del usuario/bot, y guardarlas en `~/.ssh/config`:
```bash
ssh-keygen -t rsa -C "github-datosargentina" -f "github-datosargentina"
mv github-datosargentina* ~/.ssh/
```

2. Generar un alias de ssh (en `~/.ssh/config`) para utilizar expl√citamente la clave nueva:
```
Host github.com-datosargentina-bot
    HostName github.com
    User git
    IdentityFile ~/.ssh/github-datosargentina
```
N√tese que "IdentityFile" apunta a la clave generada en el paso 1.

3. Modificar la configuraci√n de git del repositorio (`.git/config` en la ra√z del repositorio) para usar el alias generado:
```
[user]
	email = datos@modernizacion.gob.ar
	name = datosgobar-bot
(...)
[remote "origin"]
	url = git@github.com-datosargentina-bot:datosgobar/libreria-catalogos.git
	fetch = +refs/heads/*:refs/remotes/origin/*
	merge = refs/heads/master
(...)
```
N√≥tese que la `url` del remote "origin" usa el host "github.com-datosargentina-bot" que generamos en el paso 2.

4. Agregar la clave p√blica `~/.ssh/github-datosargentina.pub` a la lista de claves permitidas en GitHub para el usuario del paso 3, `datosgorbar-bot`.
