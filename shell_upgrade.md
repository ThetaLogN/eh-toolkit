# Upgrade della Shell (Interactive TTY Upgrade)

Questa guida rapida mostra i comandi per effettuare l'upgrade di una shell limitata/non interattiva (es. netcat) a una shell TTY completamente interattiva (con supporto ad autocompletamento tab, cronologia dei comandi e scorciatoie da tastiera come Ctrl+C).

---

## Metodo 1: Con Python (Consigliato)

1. Avvia uno pseudoterminale (pty) tramite Python:
   ```bash
   python3 -c 'import pty; pty.spawn("/bin/bash")'
   ```
2. Sospendi la shell attuale e torna al terminale locale:
   * Premi la scorciatoia da tastiera: **`Ctrl + Z`**
3. Configura il terminale locale per passare l'input in modalità raw e riporta in primo piano (foreground) la shell remota:
   * Digita (sul tuo terminale locale):
     ```bash
     stty raw -echo; fg
     ```
   * Premi **`INVIO`** due volte per confermare e riattivare la visualizzazione.
4. Imposta la variabile d'ambiente del terminale per abilitare i colori e la compatibilità estesa:
   ```bash
   export TERM=xterm
   ```

---

## Metodo 2: Senza Python (Alternativo)

Se Python non è presente o utilizzabile sul sistema target, puoi usare l'utility di sistema `script`:

1. Avvia una sessione di shell tramite `script`:
   ```bash
   script /dev/null -qc bash
   ```
2. Sospendi la shell attuale e torna al terminale locale:
   * Premi la scorciatoia da tastiera: **`Ctrl + Z`**
3. Configura il terminale locale per passare l'input in modalità raw e riporta in primo piano (foreground) la shell remota:
   * Digita (sul tuo terminale locale):
     ```bash
     stty raw -echo; fg
     ```
   * Premi **`INVIO`** due volte per confermare e riattivare la visualizzazione.
4. Imposta la variabile d'ambiente del terminale per abilitare i colori e la compatibilità estesa:
   ```bash
   export TERM=xterm
   ```
