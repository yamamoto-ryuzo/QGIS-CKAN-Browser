@echo off
setlocal
set LRELEASE="C:\Qt\linguist_6.9.1\lrelease.exe"
set I18NDIR=CKAN-Browser\i18n

for %%f in (%I18NDIR%\CKANBrowser_*.ts) do (
    echo Converting %%f ...
    %LRELEASE% %%f
)
echo All .ts files converted to .qm.
pause
