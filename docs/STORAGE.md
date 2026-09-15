# Almacenamiento

El pipeline de procesamiento utiliza una abstracción de almacenamiento para compartir la lógica de procesamiento entre los distintos backends.

## Backends compatibles

- `local`
- `google_drive` / `gdrive`
- `rclone`

El proveedor debe utilizar esquemas URI coincidentes para origen y destino. Los valores locales predeterminados son `local://storage/input` y `local://storage/output`.

## Estructura local

```text
storage/
├── input/
├── work/
├── output/
│   └── _manifests/
├── archive/
├── failures/
├── logs/
└── state/
```

La aplicación también utiliza `secrets/` para credenciales/perfiles y `tools/` para recursos de runtime gestionados/externos.

## Procesamiento en la nube

Las ejecuciones respaldadas por la nube utilizan el mismo pipeline común. Las entradas se acceden mediante el adaptador seleccionado y las salidas se validan antes de completar las acciones de finalización/archivado. La autenticación en la nube debe prepararse antes de la ejecución programada.

No elimines la salida local simplemente porque se haya iniciado una subida; debe confirmarse la transferencia.
