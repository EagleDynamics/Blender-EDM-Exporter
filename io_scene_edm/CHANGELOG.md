20.02.2025
* Added per vertex damage to deck material.

Release 26.11.2024:
* Fixed bug preventing export of aircraft registration numbers on machines with non english locale.
* Fixed bug in blender plugin: after updating edm materials, the values ​​in the drop-down lists were set to default values. 
* Fixed blender warning: 'WARN (bpy.rna): \intern\bpy_rna.cc:1366 pyrna_enum_to_py: current value '0' matches no enum in '.

Release 10.11.2024:
* Added support of rgba damage mask.

Release 31.08.2025
* Added support of multiple animation of bones through nla-editor

Release 02.09.2025
* Added `optimizeVertexCache` checkbox in dev mode
* Check Action name - it should start with integer (argument).

Release 03.10.2025
* Remove asterisk from Damage Visibility sockets in Glass and Default material.

Release 23.10.2025
* Return hash check of materials;
* Fix reference .blend glass material (default version was 5 while min = 6, max = 6, instance = 6).

Release 24.11.2025
* Added ability to set path for EDM Fast Export;
* Check Blender Plugin Version. If it's 5.0 and later - you can't use the plugin.

Release 16.12.2025
* Update materials works now for Blender version 5.0.

Release 17.12.2025
* Fix bug with fcurves in Blender 5.0

Release 19.12.2025
* Remove support of Blender 3.

Release 23.12.2025
* Fix the bug with extracting animation from non-armature objects.

Release 29.01.2026
* Fix the bug with bones: texture distortions after exporting.