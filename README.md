# Shade-aware Route Planning

![demo](demo.gif)

Our project runs on Python 3.11.11. Please refer to [requirements.txt](requirements.txt) for the dependencies.

Our default scenario is set in a part of Abeno Ward, Osaka.
The time interval is from 9:00 to 10:00 AM on December 5, 2024.
You can run `main.py` directly and adjust the shadow weight to control your preference for sunlight or shade.

If you wish to simulate other locations or time periods (within Osaka City), please load the corresponding data from the tran and bldg folders.

For areas outside Osaka, refer to the PLATEAU dataset.
Then run `precompute_shadow_ratios_offline.py` and `precompute_shadows_offline.py` to generate the corresponding offline shadow data, and proceed with `main.py`.




