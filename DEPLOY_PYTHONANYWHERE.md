# Déploiement sur PythonAnywhere

## Mise à jour rapide

Après un push sur GitHub, depuis une console Bash de PythonAnywhere :

```bash
cd ~/kvk-slot-booking && git pull origin main && touch /var/www/randalthor_pythonanywhere_com_wsgi.py
```

Le nom du fichier WSGI est `randalthor_pythonanywhere_com_wsgi.py`, en minuscules. Le `touch` force le rechargement de l'application ; le bouton **Reload** de l'onglet Web fait la même chose.

## Première installation

1. Cloner le dépôt : `git clone https://github.com/KingRandAlThor/kvk-slot-booking.git ~/kvk-slot-booking`
2. Installer les dépendances : `pip install --user -r requirements.txt`
3. Créer la base : `cd ~/kvk-slot-booking && python3 init_db.py`
4. Créer la web app (Flask, Python 3.x) dans l'onglet **Web**.

## Fichier WSGI

Le fichier `/var/www/randalthor_pythonanywhere_com_wsgi.py` doit contenir, en plus des variables d'environnement :

```python
import sys
import os

os.environ['ADMIN_PASSWORD'] = 'choisis-un-mot-de-passe-solide'
os.environ['SECRET_KEY'] = 'une-longue-chaine-aleatoire'

project_home = '/home/RandAlThor/kvk-slot-booking'
if project_home not in sys.path:
    sys.path.insert(0, project_home)
os.chdir(project_home)

from app import app as application
```

Le chemin doit pointer vers `kvk-slot-booking` (l'ancien projet `~/kvk/` n'est plus utilisé). Le mot de passe et la clé ne doivent jamais être publiés dans le dépôt.

## Configurer une semaine d'événement

1. Ouvrir la page `/admin` du site et saisir le mot de passe administrateur.
2. Onglet « Configure KVK Week », choisir le lundi de la semaine, puis « Configure Week ».

## Dépannage

- Si le site ne répond plus après un `git pull`, relancer `python3 init_db.py` puis recharger l'application.
- Les erreurs sont visibles dans **Error log**, sur le tableau de bord de PythonAnywhere.
- La base de données se trouve dans `~/kvk-slot-booking/kvk.db` ; elle n'est pas versionnée.
