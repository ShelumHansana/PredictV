# PredictV — Neon UI / Motion Showcase Update

This package retains the supplied full-stack code and changes only the frontend appearance and motorcycle visual presentation.

## Included changes
- Dark midnight/navy theme default (the existing light-mode toggle remains available).
- Violet and cyan atmospheric gradient background and subtle perspective grid.
- Rounded glass cards, updated inputs, chips, stepper, navigation and CTA hover states.
- New responsive motorcycle showcase on the Home and Check pages, using image assets derived from the reference visual supplied for this redesign.
- 3 motorcycle viewing angles, accessible previous/next buttons, clickable view markers, 8.5-second autoplay, hover/focus pause, pointer-responsive 2.5D tilt, slow floating/rim-light effects.
- Reduced-motion preference disables decorative movement and autoplay.
- Desktop and mobile page layouts updated; no backend/ML behavior was changed.

## Important technical disclosure
The showcase is an **animated 2.5D image-based visual**, not a downloadable or physically accurate 3D GLB model. It uses no external assets or third-party image services. The older procedural Three.js bike code remains in the source but is no longer mounted by BikeFigure.

## Local run
From `frontend/`:

    npm ci
    npm run dev
    npm run build

Frontend test/build was not executed successfully in the packaging environment because npm dependencies could not be installed from the network. Please run `npm ci && npm run build` locally and test before deployment.
