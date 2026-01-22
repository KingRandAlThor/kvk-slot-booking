# 🚀 Déploiement sur PythonAnywhere

## Commande de déploiement rapide

Pour mettre à jour l'application sur PythonAnywhere après un push GitHub :

```bash
cd ~/kvk-slot-booking && git pull origin main && touch /var/www/randalthor_pythonanywhere_com_wsgi.py
```

⚠️ **IMPORTANT** : Le nom du fichier WSGI est `randalthor_pythonanywhere_com_wsgi.py` (tout en minuscules)

## Étapes détaillées

### 1. Se connecter à PythonAnywhere
- Aller sur https://www.pythonanywhere.com
- Se connecter avec le compte **RandAlThor**
- Ouvrir un **Bash console**

### 2. Mettre à jour le code
```bash
cd ~/kvk-slot-booking
git pull origin main
```

### 3. Recharger l'application
```bash
touch /var/www/randalthor_pythonanywhere_com_wsgi.py
```

Ou via le dashboard :
- Aller sur https://www.pythonanywhere.com/user/RandAlThor/webapps/
- Cliquer sur le bouton **"Reload"**

## ⚠️ IMPORTANT - Configuration initiale

### Vérifier le fichier WSGI

Le fichier `/var/www/randalthor_pythonanywhere_com_wsgi.py` doit contenir :

```python
import sys
import os
project_home = '/home/RandAlThor/kvk-slot-booking'
if project_home not in sys.path:
    sys.path.insert(0, project_home)
os.chdir(project_home)
from app import app as application
```

⚠️ Le path doit pointer vers `kvk-slot-booking` et PAS vers `kvk` !

### Réinitialiser la base de données (si nécessaire)

Si le site ne fonctionne pas après un pull :

```bash
cd ~/kvk-slot-booking && python3 init_db.py
```

Puis configurer les dates via l'admin :
- Aller sur https://randalthor.pythonanywhere.com/admin
- Mot de passe : `AidxRand2026Love`
- Onglet "📆 Configure KVK Week"
- Sélectionner le lundi de la semaine KVK
- Cliquer sur "Configure Week"

## Structure sur PythonAnywhere

- **Projet actif** : `~/kvk-slot-booking/` ✅
- **Ancien projet** : `~/kvk/` (ne plus utiliser)
- **WSGI file** : `/var/www/randalthor_pythonanywhere_com_wsgi.py` (minuscules)
- **Base de données** : `~/kvk-slot-booking/kvk.db`

## Notes

- Le `touch` sur le fichier WSGI force le rechargement automatique de l'application
- Pensez à vérifier les logs en cas d'erreur : **Error log** dans le dashboard
