# TsukiBrain

Embodied affective avatar driven by Drosophila connectome topology.

## Project Structure

TSUKIBRAIN/
├── bridge/
│   ├── feed_gui.py
│   ├── feed_listener.py
│   ├── flybrain_topology.py
│   └── inspect_data.py
├── data/
├── output/
│   ├── feed_signal.json
│   └── flybrain_output.json
└── repos/
    └── fly-brain/ (cloned Drosophila brain neural project)
        ├── code/
        ├── data/
        ├── scripts/
        ├── environment.yml
        ├── main.py
        └── README.md

## How it works

Feed signals (sugar, water, shock, bitter) → connectome topology mapping → bone-driven ear/tail + shape-key isolation (`びっくり` excluded) → 3D avatar motion.

## Character Model

- Model: BlueGua VRChat Avatar (Phys Bone edition)
- Source: https://bluegua.booth.pm/items/3919107
- Author: BlueGua
- Terms: Personal use; modification allowed; no redistribution to unpurchased users.
- Modifications: Custom retexture applied. Bone-driven mapping & connectome driver added.
- Redistribution: Model files NOT included. Must purchase/obtain from BOOTH.

## Fly-Brain Clone

`repos/fly-brain/` is a cloned external repository for Drosophila brain neural data/topology. Independent environment (`environment.yml`). Not modified by this project.

## Third-Party

- Poiyomi Toon Shader (MIT)
- Janelia FlyEM connectome data (public)

## Author

tsutokiteo — high school student, self-directed research

## License

Code: MIT License.
[Third-party assets retain respective licenses; character model not redistributed.](THIRD_PARTY.md)
