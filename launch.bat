@echo off

pushd %~dp0
python src\main.py %*
popd
