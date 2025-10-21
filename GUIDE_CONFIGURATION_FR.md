# Guide de Configuration - Google Ads MCP Server

## 📖 Les Deux Méthodes de Configuration OAuth

Ce serveur MCP supporte **deux méthodes** pour configurer l'authentification OAuth 2.0 avec l'API Google Ads. Ce guide explique les deux options en détail.

---

## 🎯 OPTION 1 : Utiliser le fichier client_secret.json

### Avantages
- ✅ **Plus simple** - Un seul fichier à télécharger
- ✅ **Moins d'erreurs** - Pas de copier-coller manuel
- ✅ **Recommandé pour les débutants**

### Étapes de configuration

#### Étape 1 : Télécharger les credentials OAuth

1. Allez sur [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
2. Cliquez sur **"+ CREATE CREDENTIALS"** → **"OAuth 2.0 Client ID"**
3. Type d'application : **"Desktop application"**
4. Nom : `Google Ads MCP Client` (ou autre nom de votre choix)
5. Cliquez sur **"Create"**
6. Cliquez sur **"Download JSON"** (bouton de téléchargement)
7. Sauvegardez le fichier (il s'appellera quelque chose comme `client_secret_123456789.apps.googleusercontent.com.json`)

#### Étape 2 : Configurer le fichier .env

1. Copiez le fichier d'exemple :
```bash
cp env.example .env
```

2. Éditez le fichier `.env` et configurez :
```bash
# Token développeur Google Ads (obligatoire)
GOOGLE_ADS_DEVELOPER_TOKEN=votre_token_ici

# Chemin vers le fichier client_secret.json téléchargé
GOOGLE_ADS_CREDENTIALS_PATH=/chemin/complet/vers/client_secret_123456789.apps.googleusercontent.com.json
```

⚠️ **Important** : Utilisez le **chemin complet absolu** vers le fichier JSON.

**Exemple sur macOS/Linux :**
```bash
GOOGLE_ADS_CREDENTIALS_PATH=/Users/john/projects/google-ads-mcp/client_secret_123456.apps.googleusercontent.com.json
```

**Exemple sur Windows :**
```bash
GOOGLE_ADS_CREDENTIALS_PATH=C:/Users/John/projects/google-ads-mcp/client_secret_123456.apps.googleusercontent.com.json
```

#### Étape 3 : Premier lancement

Lors du premier lancement du serveur MCP, un navigateur s'ouvrira automatiquement pour l'authentification OAuth. Après autorisation, vos tokens seront sauvegardés dans un fichier `google_ads_token.json` créé automatiquement dans le même répertoire que votre `client_secret.json`.

---

## 🔧 OPTION 2 : Utiliser les variables d'environnement

### Avantages
- ✅ **Plus flexible** - Idéal pour les environnements de production
- ✅ **Meilleure sécurité** - Compatible avec les gestionnaires de secrets (Kubernetes, AWS Secrets Manager, etc.)
- ✅ **Pas de fichier JSON à gérer**

### Étapes de configuration

#### Étape 1 : Obtenir le Client ID et Client Secret

Vous devez quand même créer des credentials OAuth sur Google Cloud Console, mais vous allez extraire les valeurs manuellement :

1. Allez sur [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
2. Cliquez sur **"+ CREATE CREDENTIALS"** → **"OAuth 2.0 Client ID"**
3. Type d'application : **"Desktop application"**
4. Nom : `Google Ads MCP Client`
5. Cliquez sur **"Create"**
6. **Ne téléchargez PAS le fichier JSON** (ou téléchargez-le temporairement)
7. Vous verrez apparaître une fenêtre avec :
   - **Client ID** : `123456789.apps.googleusercontent.com`
   - **Client secret** : `GOCSPX-abc123def456xyz`
8. **Copiez ces deux valeurs**

**Alternative** : Si vous avez déjà téléchargé le fichier JSON :
1. Ouvrez le fichier `client_secret_xxxxx.json` avec un éditeur de texte
2. Cherchez les lignes :
```json
{
  "installed": {
    "client_id": "123456789.apps.googleusercontent.com",
    "client_secret": "GOCSPX-abc123def456xyz",
    ...
  }
}
```
3. Copiez les valeurs de `client_id` et `client_secret`

#### Étape 2 : Configurer le fichier .env

1. Copiez le fichier d'exemple :
```bash
cp env.example .env
```

2. Éditez le fichier `.env` et configurez :
```bash
# Token développeur Google Ads (obligatoire)
GOOGLE_ADS_DEVELOPER_TOKEN=votre_token_developpeur

# Client ID et Client Secret (extraits du fichier JSON ou de Google Cloud Console)
GOOGLE_ADS_CLIENT_ID=123456789.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=GOCSPX-abc123def456xyz

# Chemin où sauvegarder les tokens d'accès (sera créé automatiquement)
GOOGLE_ADS_CREDENTIALS_PATH=./google_ads_token.json
```

#### Étape 3 : Explication des paramètres

| Variable | Description | Exemple |
|----------|-------------|---------|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Token API Google Ads (obligatoire pour les deux options) | `ABcdEF12345678901234567890` |
| `GOOGLE_ADS_CLIENT_ID` | ID client OAuth (de Google Cloud Console) | `123456789.apps.googleusercontent.com` |
| `GOOGLE_ADS_CLIENT_SECRET` | Secret client OAuth (de Google Cloud Console) | `GOCSPX-abc123def456xyz` |
| `GOOGLE_ADS_CREDENTIALS_PATH` | Chemin où sauvegarder les tokens après authentification | `./google_ads_token.json` |

#### Étape 4 : Premier lancement

Lors du premier lancement :
1. Le serveur détectera que vous utilisez les variables d'environnement
2. Il construira automatiquement la configuration OAuth
3. Un navigateur s'ouvrira pour l'authentification
4. Après autorisation, vos tokens seront sauvegardés dans le fichier spécifié par `GOOGLE_ADS_CREDENTIALS_PATH`

---

## 🔑 Comment obtenir le Developer Token

**Le Developer Token est obligatoire pour les deux options !**

### Étapes pour obtenir votre Developer Token :

1. Connectez-vous à [Google Ads](https://ads.google.com)
2. Cliquez sur **"Tools & Settings"** (icône clé à molette en haut)
3. Sous **"Setup"**, cliquez sur **"API Center"**
4. Si c'est la première fois, acceptez les **Terms of Service**
5. Cliquez sur **"Apply for token"**
6. Remplissez le formulaire :
   - Décrivez votre cas d'utilisation (ex: "Intégration MCP pour analyse de campagnes")
   - Fournissez les détails techniques
7. Soumettez la demande et attendez l'approbation (1-3 jours ouvrables)

⚠️ **Note** : Vous recevrez d'abord un **token de test** avec des fonctionnalités limitées. Après vos tests, vous pourrez demander l'accès en production.

### Où trouver votre Developer Token :

Une fois approuvé :
1. Retournez dans **API Center** dans Google Ads
2. Copiez votre **Developer Token** (format : `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)

---

## ⚙️ Configuration avec Claude Desktop

### Fichier de configuration Claude Desktop

**macOS :**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows :**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

### Configuration du serveur MCP

Éditez `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "/chemin/complet/vers/.venv/bin/python",
      "args": [
        "/chemin/complet/vers/server.py"
      ]
    }
  }
}
```

**Exemple sur macOS :**
```json
{
  "mcpServers": {
    "google-ads": {
      "command": "/Users/john/projects/google-ads-mcp-server/.venv/bin/python",
      "args": [
        "/Users/john/projects/google-ads-mcp-server/server.py"
      ]
    }
  }
}
```

**Exemple sur Windows :**
```json
{
  "mcpServers": {
    "google-ads": {
      "command": "C:/Users/John/projects/google-ads-mcp-server/.venv/Scripts/python.exe",
      "args": [
        "C:/Users/John/projects/google-ads-mcp-server/server.py"
      ]
    }
  }
}
```

### Redémarrer Claude Desktop

Fermez complètement Claude Desktop et relancez-le pour charger la nouvelle configuration.

---

## 🧪 Tester la configuration

### Test 1 : Lister les comptes

Dans Claude Desktop, essayez :
```
Liste tous mes comptes Google Ads
```

### Test 2 : Vérifier les campagnes

```
Montre-moi la performance de mes campagnes pour le compte 1234567890
```

### Test 3 : Recherche de mots-clés

```
Génère des idées de mots-clés pour "marketing digital" avec le compte 1234567890
```

---

## 🔍 Dépannage

### Erreur : "GOOGLE_ADS_CLIENT_ID and GOOGLE_ADS_CLIENT_SECRET must be set"

**Cause** : Les variables d'environnement ne sont pas définies.

**Solution** :
1. Vérifiez que votre fichier `.env` contient bien :
```bash
GOOGLE_ADS_CLIENT_ID=votre_client_id
GOOGLE_ADS_CLIENT_SECRET=votre_client_secret
```
2. Vérifiez qu'il n'y a pas d'espaces avant ou après les valeurs
3. Redémarrez Claude Desktop

### Erreur : "OAuth config file not found"

**Cause** : Le chemin vers le fichier est incorrect (Option 1).

**Solution** :
1. Vérifiez que le chemin dans `GOOGLE_ADS_CREDENTIALS_PATH` est correct
2. Utilisez un chemin **absolu** (chemin complet)
3. Sur Windows, utilisez des slashes `/` au lieu de backslashes `\`

### Erreur : "Token refresh failed"

**Cause** : Les tokens ont expiré ou sont invalides.

**Solution** :
1. Supprimez le fichier `google_ads_token.json`
2. Relancez le serveur pour refaire l'authentification OAuth

### Le navigateur ne s'ouvre pas

**Cause** : Problème avec le serveur local OAuth.

**Solution** :
1. Vérifiez votre pare-feu
2. Essayez de relancer le serveur
3. Vérifiez les logs dans Claude Desktop

---

## 📊 Comparaison des deux options

| Critère | Option 1 (Fichier JSON) | Option 2 (Variables d'env) |
|---------|-------------------------|----------------------------|
| **Simplicité** | ⭐⭐⭐⭐⭐ Très simple | ⭐⭐⭐ Moyen |
| **Flexibilité** | ⭐⭐⭐ Moyen | ⭐⭐⭐⭐⭐ Très flexible |
| **Sécurité** | ⭐⭐⭐⭐ Bonne | ⭐⭐⭐⭐⭐ Excellente |
| **Production** | ⭐⭐⭐ OK | ⭐⭐⭐⭐⭐ Recommandé |
| **Débutants** | ⭐⭐⭐⭐⭐ Recommandé | ⭐⭐⭐ Possible |
| **CI/CD** | ⭐⭐ Limité | ⭐⭐⭐⭐⭐ Excellent |

---

## 💡 Conseils de sécurité

1. **Ne commitez JAMAIS vos credentials** dans Git
2. Le fichier `.env` est déjà dans `.gitignore`
3. Les fichiers `google_ads_token.json` et `client_secret_*.json` sont aussi ignorés
4. Pour la production, utilisez un gestionnaire de secrets (AWS Secrets Manager, Google Secret Manager, etc.)
5. Définissez des permissions restrictives sur vos fichiers :
```bash
chmod 600 .env
chmod 600 google_ads_token.json
chmod 600 client_secret_*.json
```

---

## 📝 Résumé : Quelle option choisir ?

### Choisissez **OPTION 1** si :
- ✅ Vous débutez avec l'API Google Ads
- ✅ Vous travaillez en développement local
- ✅ Vous voulez la solution la plus simple

### Choisissez **OPTION 2** si :
- ✅ Vous déployez en production
- ✅ Vous utilisez des systèmes de gestion de secrets
- ✅ Vous voulez plus de contrôle sur la configuration
- ✅ Vous travaillez avec Docker/Kubernetes
- ✅ Vous avez besoin de CI/CD

---

## ❓ Questions fréquentes

### Puis-je changer d'option après avoir configuré ?

Oui ! Le code détecte automatiquement quelle option vous utilisez. Vous pouvez passer de l'une à l'autre en modifiant simplement votre fichier `.env`.

### Dois-je refaire l'authentification OAuth si je change d'option ?

Non, tant que le fichier `google_ads_token.json` existe et est valide, il sera réutilisé.

### Que faire si j'ai plusieurs comptes Google Ads ?

Le serveur liste automatiquement tous les comptes accessibles avec vos credentials. Vous n'avez pas besoin de configuration spéciale.

### Dois-je configurer GOOGLE_ADS_LOGIN_CUSTOMER_ID ?

Seulement si vous utilisez un compte Manager (MCC) pour accéder à des sous-comptes. Pour la plupart des utilisateurs, ce n'est pas nécessaire.

---

## 📞 Support

Si vous rencontrez des problèmes :

1. Vérifiez les logs de Claude Desktop
2. Vérifiez que tous les chemins sont corrects (chemins absolus)
3. Vérifiez que votre Developer Token est valide
4. Consultez la documentation officielle de l'API Google Ads
5. Ouvrez une issue sur GitHub

---

**Bonne chance avec votre configuration ! 🚀**
