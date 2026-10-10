# AUDIT MCP CLAUDE — Pont « westofmonday-file-bridge »

- Date : 2026-10-10
- Mode : lecture seule (aucune installation, modification, suppression, publication ni appel d'API payante)
- Auditeur : Claude Code, **session cloud** (conteneur Linux éphémère, hors du PC Windows)

---

## 0. Limite majeure de cet audit (à lire en premier)

Cet audit a été exécuté depuis un **conteneur cloud Linux**, et non sur le PC Windows.
Cette session n'a **aucun accès** au PC : pas de shell Windows, pas d'outil computer-use ou
remote-devices relié, pas de nœud Tailscale. Les points 1, 3 et 4 de la mission (processus,
ports, tunnel, Tailscale, n8n) **n'ont donc pas pu être observés directement**.

Ce rapport distingue donc :
- **[VÉRIFIÉ]** : constaté avec une preuve dans cette session ;
- **[HYPOTHÈSE]** : déduction technique, à confirmer sur le PC avec les commandes de la section 8, qui sont toutes en lecture seule.

---

## 1. Éléments vérifiés, avec preuves

| # | Vérification | Résultat | Preuve |
|---|---|---|---|
| V1 | Présence de `bridge/server.mjs` dans l'environnement d'audit | **Absent** | Recherche disque complète (`find / -path "*bridge/server.mjs"`) : aucun résultat |
| V2 | Références à `westofmonday`, `file-bridge`, `tailscale`, `n8n` ou `server.mjs` dans le dépôt `fabrice47-ui/OpenHands` | **Aucune** (sauf un faux positif dans `frontend/package-lock.json`) | `grep -rIil` sur le dépôt |
| V3 | Existence d'un dépôt GitHub « WestOfMonday » ou d'un dépôt du pont | **Aucun** | Dépôts accessibles : OpenHands, idea-radar, etsy-decider-app, arena-product-intelligence, phoenix-next-private |
| V4 | Processus Node, Tailscale ou n8n, et ports en écoute | **Aucun** (normal, car il s'agit du conteneur cloud, pas du PC) | `ps aux`, `ss -ltnp` ; seul `node` est installé, sans `tailscale` ni `n8n` |
| V5 | Projet WestOfMonday dans Google Drive | **Présent** : dossier `WestOfMonday`, archives produits, tableurs QA, `WestOfMonday_PRE_OPUS_POUR_CLAUDE.zip` | Recherche Drive (lecture seule) |
| V6 | Test de pont Windows ↔ Google | Document « WestOfMonday Bridge Test 2026-09-27 », objet : *« verify operational Google side »* | Contenu du document Drive |
| V7 | Documentation, configuration ou code du serveur MCP WestOfMonday dans Drive | **Aucun** document sur `server.mjs`, MCP, Tailscale ou n8n | Recherche plein texte dans Drive |

---

## 2. Éléments fonctionnels

- **Côté Google (Drive)** : un test de pont a réussi le 2026-09-27 (V6). Le PC a donc déjà
  pu déposer des fichiers dans Drive, probablement par synchronisation ou par un script.
- **Les fichiers WestOfMonday sont accessibles via Drive** (V5). Pour la lecture de fichiers,
  Drive constitue déjà un canal opérationnel, sans aucune exposition réseau du PC.

## 3. Éléments défaillants ou non prouvés

- **Aucun serveur MCP WestOfMonday n'est prouvé** (V1, V3, V7). Aucune trace n'existe d'un code
  qui implémente le protocole MCP : `initialize`, `tools/list`, `tools/call` via JSON-RPC, en
  transport *Streamable HTTP* ou SSE. Le nom « file-bridge » et le fichier `bridge/server.mjs` évoquent
  plutôt un **petit serveur HTTP/REST local**, ce qui n'est pas la même chose.
- **Le raccordement au « tunnel MCP OpenAI » n'est pas vérifiable** depuis cette session.
- **Les états de Tailscale, n8n et du pont local ne sont pas vérifiables** depuis cette session.

---

## 4. Cause probable du blocage [HYPOTHÈSE, classée par probabilité]

1. **Joignabilité réseau (cause la plus probable).** Un connecteur MCP personnalisé dans ChatGPT
   est appelé **depuis les serveurs d'OpenAI**, et non depuis le navigateur du PC. Il faut donc une URL
   **HTTPS joignable publiquement**. Or :
   - `localhost:<port>` est injoignable depuis OpenAI ;
   - une adresse Tailscale `100.x.y.z` ou `*.ts.net` diffusée via `tailscale serve` n'est
     joignable **que depuis le tailnet**, ce qui exclut les serveurs d'OpenAI ;
   - seul `tailscale funnel` (ou un tunnel équivalent) expose le service sur Internet, ce que la
     mission **interdit**. Si le « tunnel MCP OpenAI déjà configuré » pointe vers une adresse du tailnet
     ou vers `localhost`, ChatGPT ne peut pas l'atteindre : c'est un blocage par conception, pas une panne.

2. **Protocole.** Si `bridge/server.mjs` expose une API REST, par exemple `GET /files`, et non le
   protocole MCP (JSON-RPC `initialize` / `tools/list` sur `/mcp` ou `/sse`), ChatGPT
   refusera le connecteur ou n'y verra aucun outil, même si le réseau fonctionne.

3. **Décalage de port ou de chemin.** Le tunnel peut pointer vers un port ou un chemin différent de
   celui où écoute `server.mjs` (exemple : le tunnel vise `:3000/mcp` alors que le serveur écoute sur `:8787/`).

4. **Processus arrêté.** Le pont n'est pas lancé de façon persistante : il s'arrête à la fermeture
   du terminal et ne démarre pas en service.

5. **Authentification.** Le pont exige un jeton ou un en-tête que le connecteur ChatGPT n'envoie pas.
   Un connecteur personnalisé ChatGPT prend en charge OAuth ou l'absence d'authentification, mais pas un en-tête arbitraire.

6. **Protections volontaires.** Le Pare-feu Windows, les ACL Tailscale ou la liste des dossiers autorisés du pont
   bloquent la requête. Ces protections ne doivent **pas** être contournées.

> **Point d'architecture.** ChatGPT n'a jamais d'accès « direct » au PC. Pour l'atteindre, il faut
> soit un serveur MCP public (exposition Internet, interdite ici), soit passer par un service tiers déjà
> connecté, comme Google Drive.

---

## 5. Solution recommandée (correction minimale, sans nouvelle infrastructure)

**Étape A — Diagnostic local (5 minutes, lecture seule).** Lancer les commandes de la section 8
sur le PC et noter les résultats. Elles permettent de trancher entre les hypothèses 1 à 5.

**Étape B — Choisir selon le résultat :**

- **Recommandé : utiliser Google Drive comme pont de fichiers.** Le test du 2026-09-27 montre
  que ce canal fonctionne déjà. Il suffit d'y déposer les fichiers à partager et d'activer le connecteur
  Google Drive natif de ChatGPT. Cette option n'ouvre aucun port, ne crée aucune infrastructure et ne
  nécessite aucune modification du PC. Elle couvre l'**accès aux fichiers**, mais **pas le pilotage des agents**.
- **Si le pilotage d'agents est indispensable :** il faut un serveur MCP réel et une URL HTTPS
  publique, donc soit `tailscale funnel`, soit un tunnel public. Cela **contredit l'interdiction
  d'exposer des ports sur Internet** et demande une **décision explicite** (voir la section 7). Dans ce cas,
  il faut au minimum : l'authentification OAuth, une liste blanche de dossiers, des outils en lecture seule
  par défaut et une journalisation des appels.
- **Si le blocage vient du protocole (hypothèse 2) :** `server.mjs` doit être enveloppé dans un vrai serveur MCP,
  par exemple avec le SDK officiel `@modelcontextprotocol/sdk` en transport Streamable HTTP. C'est une
  modification de code, qui demande donc une validation.
- **Si le blocage vient d'un décalage de port (3) ou d'un processus arrêté (4) :** il faut aligner le port
  ou le chemin du tunnel sur celui du serveur, ou relancer le pont. C'est la correction la plus petite,
  mais elle reste inutile si l'hypothèse 1 est confirmée.

---

## 6. Risques et dépendances

| Risque | Gravité | Commentaire |
|---|---|---|
| Exposition d'un serveur de fichiers sur Internet (Funnel ou tunnel public) | **Élevée** | Un pont mal protégé donne accès au disque du PC à n'importe qui ; c'est un risque d'injection de prompt via les fichiers lus |
| Pilotage d'agents locaux par un service distant | **Élevée** | Exécution d'actions sur le PC déclenchée depuis le cloud |
| Fuite de secrets (jetons dans `.env` ou dans les journaux) | Moyenne | Ne jamais coller de jetons dans ChatGPT ni dans ce rapport |
| Dépendance à Tailscale ou n8n | Moyenne | Si ces services sont arrêtés, le pont tombe |
| Option Drive | Faible | Dépend seulement du compte Google, qui fonctionne déjà |

## 7. Actions nécessitant validation (non exécutées)

1. Lancer les commandes de diagnostic de la section 8 **sur le PC**, par l'utilisateur ou par une session Claude
   reliée au PC avec computer-use ou Remote Control.
2. Activer le connecteur Google Drive dans ChatGPT (solution recommandée).
3. Toute exposition publique (`tailscale funnel`, tunnel public) : **décision explicite requise**,
   car elle contredit les interdictions de la mission.
4. Toute modification de `bridge/server.mjs`, de la configuration du tunnel, des ACL Tailscale ou de n8n.
5. Copier ce rapport dans le dossier local du projet WestOfMonday sur le PC et/ou dans le dossier Drive `WestOfMonday`.

---

## 8. Commandes de diagnostic en lecture seule (PowerShell, à lancer sur le PC)

> Aucune de ces commandes ne modifie quoi que ce soit. **Masquer tout jeton ou clé** avant de partager une sortie.

```powershell
# 1. Processus server.mjs : PID, dossier, ligne de commande
Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
  Where-Object CommandLine -match 'server\.mjs' |
  Select-Object ProcessId, ExecutablePath, CommandLine

# 2. Ports en écoute de ce processus (remplacer <PID>)
Get-NetTCPConnection -State Listen -OwningProcess <PID> |
  Select-Object LocalAddress, LocalPort

# 3. Est-ce un vrai serveur MCP ? (remplacer <PORT> et le chemin /mcp si besoin)
$body = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"audit","version":"0"}}}'
Invoke-WebRequest -Uri "http://127.0.0.1:<PORT>/mcp" -Method Post -Body $body `
  -ContentType "application/json" -Headers @{Accept="application/json, text/event-stream"} -UseBasicParsing |
  Select-Object StatusCode, Content
#   Une réponse avec "serverInfo" et "capabilities" indique un serveur MCP. Une erreur 404 ou du HTML indique une API REST ou un mauvais chemin.

# 4. Recherche de dépendances MCP dans le dossier du pont
Select-String -Path "<DOSSIER_DU_PONT>\package.json" -Pattern "modelcontextprotocol"

# 5. Tailscale
tailscale status
tailscale serve status
tailscale funnel status     # « No serve config » ou aucune ligne Funnel signifie que rien n'est public

# 6. n8n
Get-CimInstance Win32_Process | Where-Object CommandLine -match 'n8n' | Select-Object ProcessId, CommandLine
Get-NetTCPConnection -State Listen -LocalPort 5678 -ErrorAction SilentlyContinue

# 7. Tunnels éventuels (cloudflared, ngrok, etc.)
Get-Process cloudflared, ngrok -ErrorAction SilentlyContinue | Select-Object Id, Path
```

**Lecture des résultats :**
- (3) ne répond pas au protocole MCP : la cause est le **protocole** (hypothèse 2).
- (5) montre seulement `serve`, sans `funnel`, et aucun tunnel public n'apparaît en (7) : la cause
  est la **joignabilité** (hypothèse 1). ChatGPT ne peut pas atteindre le pont, par conception.
- (1) est vide : le **pont est arrêté** (hypothèse 4).
- Le port de (2) diffère de la cible du tunnel : il s'agit d'un **décalage** (hypothèse 3).

---

## 9. Conformité aux interdictions

- Aucun crédit d'API payante consommé ; aucune publication Etsy.
- Aucune configuration modifiée ; aucun port ouvert ou exposé.
- Aucun secret lu ni divulgué : le seul document Drive lu contenait un jeton de test non sensible, qui n'est pas reproduit ici.
- Seule écriture : création de ce fichier de rapport.
