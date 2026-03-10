# Fresnel Handout Summary (Paraphrased)

The setup hint used in this analysis is:

1. Place a lens so the diffracting aperture itself forms a sharp magnified image on the screen.
2. Move that lens by a known distance `z` away from the aperture.
3. Under the bench conditions used in this lab, treat `z` as the distance from the aperture to the Fresnel diffraction pattern plane being imaged.

In the notebook, this is implemented as:

`z = track_position - track_focus_equivalent`

where `track_focus_equivalent` is the track coordinate corresponding to the focused imaging position.

`fresnel.pdf` is used only as a local reference and is not committed as a repo artifact.
