# API AML fictive pour Salesforce Financial Services Cloud

API REST Python 3.10+, sans dépendance externe. Les trois identités de `mock_watchlist.json` sont entièrement fictives. Cette démonstration ne consulte aucun fournisseur AML et ne constitue pas une décision de conformité.

## Contrat

`POST /v1/aml/screen` avec `Content-Type: application/json` et `X-API-Key`.

```json
{"firstName":"Alex","lastName":"TestAlerte","dateOfBirth":"1980-01-15"}
```

Réponse HTTP 200 :

```json
{"isFlagged":true}
```

`true` = correspondance dans la liste fictive, à examiner. `false` = aucune correspondance selon les règles de cette démo, pas une certification de conformité. Le nom, le prénom et la date de naissance doivent tous correspondre. La casse, les accents et les espaces superflus sont ignorés dans les noms. Aucun rapprochement phonétique ou approximatif. Les sociétés ne sont pas prises en charge dans cette première version.

| Prénom | Nom | Naissance | isFlagged |
|---|---|---|---|
| Alex | TestAlerte | 1980-01-15 | true |
| Camille | DemoVigilance | 1990-06-20 | true |
| Émile | ExempleFictif | 1975-12-03 | true |
| Alex | TestClair | 1980-01-15 | false |

Les erreurs renvoient un objet `error`, sans `isFlagged` : 400 requête invalide, 401 clé absente/invalide, 404 route inconnue, 408 délai de lecture dépassé, 413 corps trop volumineux, 415 type de contenu invalide. Une panne réseau ou un HTTP non-200 doit déclencher le chemin d'erreur dans Salesforce.

## Démarrage local — PowerShell

Depuis ce dossier :

```powershell
$env:AML_API_KEY = [guid]::NewGuid().ToString('N')
# Conserver cette valeur pour le client de test et la configuration Salesforce.
python app.py
```

Écoute par défaut sur `http://127.0.0.1:8000`. `HOST` et `PORT` sont configurables. La clé est obligatoire (16 caractères minimum) et n'est jamais écrite dans les fichiers du projet.

Dans un deuxième terminal, renseigner la même clé :

```powershell
$key = Read-Host 'Cle API utilisee au demarrage'
$body = @{ firstName = 'Alex'; lastName = 'TestAlerte'; dateOfBirth = '1980-01-15' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/v1/aml/screen' -Headers @{ 'X-API-Key' = $key } -ContentType 'application/json' -Body $body
```

Santé du service : `GET /health`. Tests HTTP locaux : `python -m unittest -v test_api.py`.

## Connexion Salesforce

1. Héberger cette démo derrière une URL HTTPS accessible depuis Salesforce. `localhost` sur votre PC n'est pas accessible depuis l'organisation Salesforce. Le serveur HTTP fourni est destiné à la démonstration locale ; l'hébergement et TLS restent à configurer.
2. Dans Setup, créer une External Credential avec protocole **Custom**, un principal **Named Principal**, et un paramètre d'authentification `ApiKey` contenant la même clé que `AML_API_KEY`.
3. Ajouter un en-tête personnalisé `X-API-Key` référençant ce paramètre via le sélecteur de formule Salesforce, par exemple `{!$Credential.AML_Mock_External.ApiKey}` si l'External Credential est nommée `AML_Mock_External`. Activer l'évaluation des formules d'en-têtes si nécessaire.
4. Créer la Named Credential **AML_Mock**, avec l'URL HTTPS de base sans `/v1/aml/screen`, et l'associer à cette External Credential. Ne pas générer d'en-tête Authorization pour cette authentification par `X-API-Key`.
5. Attribuer à l'utilisateur exécutant l'appel un Permission Set donnant accès au principal de l'External Credential et, pour Apex, à la classe fournie.
6. Ajouter les deux classes du dossier `salesforce` à votre projet/org et exécuter `AmlScreeningServiceTest`. Aucun accès à une org Salesforce n'a été utilisé pour compiler ou tester ces classes ici.

Exemple dans Execute Anonymous, après configuration :

```apex
Boolean isFlagged = AmlScreeningService.screen(
    'Alex', 'TestAlerte', Date.newInstance(1980, 1, 15)
);
System.debug(isFlagged); // true
```

Pour un Person Account, mapper `FirstName`, `LastName`, `PersonBirthdate`. Pour un Contact, mapper `FirstName`, `LastName`, `Birthdate`. Si votre modèle FSC utilise d'autres champs, adapter ce mapping. L'API ne lit ni ne modifie Salesforce : le consommateur transmet ces trois valeurs.

### Utilisation dans Flow sans Apex

Créer une action **HTTP Callout**, choisir la Named Credential `AML_Mock`, la méthode POST et le chemin `/v1/aml/screen`. Utiliser la requête et la réponse JSON ci-dessus comme exemples pour définir les structures. Transmettre les champs du client et utiliser `isFlagged` dans un élément Decision. Lier le connecteur Fault à un traitement explicite « vérification indisponible ». Dans un Flow déclenché par enregistrement, placer l'appel dans un chemin asynchrone après la sauvegarde pour éviter un appel après des modifications non validées. La classe Apex fournie est un service appelable en Apex, pas une action invocable Flow.

Vous pouvez créer des champs personnalisés pour stocker le résultat, la date du contrôle et un statut distinct (`Non vérifié`, `Vérifié`, `Erreur`) : une case à cocher seule ne distingue pas un résultat négatif d'un contrôle jamais exécuté. Ces champs ne sont pas créés par ce projet. Ne pas appeler le service Apex dans une boucle de traitement massif sans concevoir le traitement asynchrone et respecter les limites d'appels de l'org.

## Documentation de référence

- [Salesforce : Named Credentials](https://developer.salesforce.com/docs/platform/named-credentials/guide/get-started.html)
- [Salesforce : clés API et en-têtes personnalisés](https://help.salesforce.com/s/articleView?id=sf.nc_custom_headers_and_api_keys.htm&language=en_US&type=5)

Le contrat détaillé figure dans `openapi.json`. Aucun déploiement public ni aucune configuration de votre organisation Salesforce n'a été effectué.
"# DAAM-AML" 
