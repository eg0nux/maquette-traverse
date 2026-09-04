# Maquette de la Manufacture des tabacs de Bergerac

Page de présentation de la maquette au 1/100 de l'ancienne Manufacture des tabacs
de Bergerac (vers 1950-1960), réalisée au FabLab de l'Atelier Partagé de La Traverse.

En ligne : <https://maquette.egonux.com>

## Structure

- `public/` — le site (HTML statique autonome, aucune dépendance de build)
- `public/img/` — photographies en deux tailles (1600 px et 800 px), logotypes
- `public/fonts/` — Cormorant Garamond réduite à l'esperluette de l'en-tête (licence SIL)
- `notes/` — notes de réalisation fournies par les auteurs de la maquette

## Publier

```sh
npx wrangler pages deploy public --project-name=maquette-egonux --branch=main
```

## Charte

Work Sans (titres et texte), Inconsolata (chiffres), cadres noirs épais à angles
arrondis. Palette : `#212121` `#edd1b0` `#eddd6e` `#f44336` `#f6ece0`.
