:: This .bat file runs create_grid_of_models.py. 
:: This script generate .mvs that contains grid of edm_models. 
:: It needs when you have several .blend files and you want to convert it to .emd format and watch it simultaneously.
:: Input:  json file with list of model names.
:: Output: view_all_models.mvs file. (Then you need to open ModelView.exe and load view_all_models.mvs)

set BLENDER_BASE=C:\Program Files\Blender Foundation\

set GLOBAL_PATH=e:\repos\trunk\Utils\EDMTools\io_scene_edm\Learning_Demo\

set VERSIONS=4.1 4.3 4.5 5.0

setlocal enabledelayedexpansion

for %%V in (%VERSIONS%) do (
    echo TEST BLENDER %%V
    python %~dp0create_grid_of_models.py "!BLENDER_BASE!Blender %%V\blender.exe" "%GLOBAL_PATH%list_of_models.json" "%GLOBAL_PATH%view_all_models_%%V.mvs"
    echo.
)

pause