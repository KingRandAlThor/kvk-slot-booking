import urllib.request

print("Envoi d'une requête GET à http://127.0.0.1:5000 pour déclencher la sélection...")

try:
    with urllib.request.urlopen('http://127.0.0.1:5000') as response:
        status = response.status
        print(f"✓ Requête réussie (HTTP {status})")
        print("✓ La sélection devrait maintenant être déclenchée!")
except Exception as e:
    print(f"❌ Erreur: {e}")
