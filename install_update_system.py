#!/usr/bin/env python3
"""
Script d'installation du système de notification de mise à jour
Modifie automatiquement webapp.py et index.html
Repo: https://github.com/F1SMV/Spot-Watcher-DX
"""

import os
import re
import sys

# ============================================
# CONFIGURATIONS
# ============================================

GITHUB_USER = "F1SMV"
GITHUB_REPO = "Spot-Watcher-DX"

VERSION_JSON_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.json"

# ============================================
# CODE À AJOUTER DANS webapp.py
# ============================================

WEBAPP_CODE = f'''
@app.route('/api/check_update')
def check_update():
    """Vérifie si une nouvelle version est disponible sur GitHub."""
    GITHUB_VERSION_URL = "{VERSION_JSON_URL}"
   
    try:
        req = urllib.request.Request(GITHUB_VERSION_URL, headers={{'User-Agent': 'Mozilla/5.0'}})
        with urllib.request.urlopen(req, timeout=10) as r:
            remote_data = json.loads(r.read().decode('utf-8'))
       
        remote_version = remote_data.get("version", "0.0.0")
        current_version = APP_VERSION.split()[-1]  # Extrait "6.2" de "NEURAL v6.2"
       
        update_available = (remote_version != current_version)
       
        return jsonify({{
            "update_available": update_available,
            "current_version": current_version,
            "latest_version": remote_version,
            "release_date": remote_data.get("release_date"),
            "changelog_url": remote_data.get("changelog_url"),
            "download_url": remote_data.get("download_url")
        }})
    except Exception as e:
        logger.warning(f"Impossible de vérifier les mises à jour: {{e}}")
        return jsonify({{"update_available": False, "error": str(e)}})
'''

# ============================================
# CODE À AJOUTER DANS index.html
# ============================================

HTML_BANNER = '''
<!-- BANDEAU DE MISE À JOUR -->
<div id="update-banner" style="display:none; position:fixed; top:0; left:0; width:100%; background:#ff9800; color:#fff; text-align:center; padding:10px; z-index:9999; font-weight:bold;">
    🚀 Une nouvelle version (<span id="new-version"></span>) est disponible !
    <a href="#" id="changelog-link" style="color:#fff; text-decoration:underline;">Voir les nouveautés</a>
    <button onclick="document.getElementById('update-banner').style.display='none'" style="float:right; background:#fff; color:#ff9800; border:none; padding:5px 10px; cursor:pointer; border-radius:3px;">Fermer</button>
</div>
'''

HTML_SCRIPT = '''
<script>
// Vérifie les mises à jour au chargement de la page
fetch('/api/check_update')
    .then(res => res.json())
    .then(data => {
        if (data.update_available) {
            document.getElementById('update-banner').style.display = 'block';
            document.getElementById('new-version').textContent = data.latest_version;
            document.getElementById('changelog-link').href = data.changelog_url;
        }
    })
    .catch(err => console.warn('Erreur lors de la vérification des mises à jour:', err));
</script>
'''

# ============================================
# FONCTIONS DE MODIFICATION
# ============================================

def modify_webapp():
    """Ajoute la route /api/check_update dans webapp.py"""
    filepath = "webapp.py"
   
    if not os.path.exists(filepath):
        print(f"❌ Erreur: {filepath} introuvable")
        return False
   
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
   
    # Vérifie si déjà installé
    if '/api/check_update' in content:
        print(f"✅ {filepath} déjà modifié (route existante)")
        return True
   
    # Trouve la ligne "if __name__ == '__main__':"
    pattern = r"(if __name__ == ['\"]__main__['\"]:\s*)"
   
    if not re.search(pattern, content):
        print(f"❌ Impossible de trouver 'if __name__ == \"__main__\":' dans {filepath}")
        return False
   
    # Insère le code avant cette ligne
    modified = re.sub(pattern, f"{WEBAPP_CODE}\n\n\\1", content)
   
    # Sauvegarde
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(modified)
   
    print(f"✅ {filepath} modifié avec succès")
    return True

def modify_index_html():
    """Ajoute le bandeau et le script dans index.html"""
    filepath = "templates/index.html"
   
    if not os.path.exists(filepath):
        print(f"❌ Erreur: {filepath} introuvable")
        return False
   
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
   
    # Vérifie si déjà installé
    if 'update-banner' in content:
        print(f"✅ {filepath} déjà modifié (bandeau existant)")
        return True
   
    # Insère le bandeau juste après <body>
    if '<body>' not in content:
        print(f"❌ Balise <body> introuvable dans {filepath}")
        return False
   
    content = content.replace('<body>', f'<body>\n{HTML_BANNER}')
   
    # Insère le script juste avant </body>
    if '</body>' not in content:
        print(f"❌ Balise </body> introuvable dans {filepath}")
        return False
   
    content = content.replace('</body>', f'{HTML_SCRIPT}\n</body>')
   
    # Sauvegarde
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
   
    print(f"✅ {filepath} modifié avec succès")
    return True

def create_version_json():
    """Crée le fichier version.json s'il n'existe pas"""
    filepath = "version.json"
   
    if os.path.exists(filepath):
        print(f"✅ {filepath} existe déjà")
        return True
   
    import json
    version_data = {
        "version": "6.2.1",
        "release_date": "2026-02-24",
        "changelog_url": f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases",
        "download_url": f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/archive/refs/heads/main.zip"
    }
   
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, indent=2)
   
    print(f"✅ {filepath} créé avec succès")
    return True

# ============================================
# FONCTION PRINCIPALE
# ============================================

def main():
    print("=" * 60)
    print("🚀 Installation du système de notification de mise à jour")
    print(f"📦 Repo: https://github.com/{GITHUB_USER}/{GITHUB_REPO}")
    print("=" * 60)
    print()
   
    success = True
   
    success &= modify_webapp()
    success &= modify_index_html()
    success &= create_version_json()
   
    print()
    print("=" * 60)
    if success:
        print("✅ Installation terminée avec succès !")
        print()
        print("📋 Prochaines étapes:")
        print("1. Commit et push version.json sur GitHub:")
        print("   git add version.json")
        print("   git commit -m 'Ajout du système de notification de mise à jour'")
        print("   git push origin main")
        print()
        print("2. Redémarre webapp.py")
        print("3. Recharge la page web")
        print()
        print("🔗 URL de version.json:")
        print(f"   {VERSION_JSON_URL}")
    else:
        print("❌ Certaines modifications ont échoué")
        print("Vérifie les messages d'erreur ci-dessus")
    print("=" * 60)
   
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())