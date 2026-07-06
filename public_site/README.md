# Jupiter Lightning Detector Public Site

This folder contains the lightweight public site deployed on Vercel:

https://jupiter-lightning-detector-public.vercel.app

It is a public explanation and reviewer-entry page. It is not the full detector
engine. The full detector still runs from the main Python workbench because it
needs local OPUS image products, generated outputs, and label files.

Redeploy from this folder:

```powershell
npx vercel@latest --prod
```

Keep `.vercel/` local. It is ignored because it contains deployment metadata.
