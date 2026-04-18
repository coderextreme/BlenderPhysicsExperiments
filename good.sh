#!/bin/bash
npx sunrize@latest poncho_drop_animation.x3d hanim_poncho_loa4.x3d hanim_loa4_poncho.x3d hanim_loa4_skin_bend.x3d hanim_loa4_final.x3d hanim_classy_female.x3d

jar -cMf pseudosoftbodyphysics.zip ponchogen.py hanim_poncho_loa4.py hanim_loa4_poncho.py bendover4.py female.py poncho_drop_animation.x3d hanim_poncho_loa4.x3d hanim_loa4_poncho.x3d hanim_loa4_skin_bend.x3d hanim_loa4_final.x3d hanim_classy_female.x3d
