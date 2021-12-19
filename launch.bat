@echo off

SET START_DIR=%CD%
cd %~dp0
python src\main.py %*
cd %START_DIR%
