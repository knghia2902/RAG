# Docker storage on this development machine

The user authorized relocation on 2026-10-05 after C: filled during Docker image builds.

- Physical Docker WSL storage: `D:\DockerData\wsl`.
- Original path: `C:\Users\O5A00001315\AppData\Local\Docker\wsl`.
- The original path is a Windows directory junction pointing to the physical location. Docker settings and WSL paths retain their existing values.
- Docker/WSL were stopped before moving the files. Both VHD lengths were checked after moving. The source directory was removed only after it contained no files, then replaced by the junction.
- Linux Docker daemon 29.8.1 restarted successfully. Existing project images and the operational/test PostgreSQL volumes were present after relocation.

This is a machine-specific development arrangement, not required by the portable Compose deployment. Keep D: available when Docker runs. Do not delete the junction target to reclaim C: space; deleting D: storage would delete images, containers and volumes. Do not manually relocate mounted VHD files.

Quick inspection in PowerShell:

```powershell
Get-Item -LiteralPath "$env:LOCALAPPDATA\Docker\wsl" | Select-Object FullName,LinkType,Target
& 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' info --format '{{.OSType}} {{.ServerVersion}}'
& 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' volume ls
```

Docker also provides a Disk image location setting under Settings → Resources → Advanced for managed relocation. See the [official WSL storage documentation](https://docs.docker.com/desktop/features/wsl/).
