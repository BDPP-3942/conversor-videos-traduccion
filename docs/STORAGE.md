# Almacenamiento

El pipeline utiliza una abstracción común de almacenamiento para mantener la misma lógica de negocio en CLI y GUI.

## Backends

- `local`
- `google_drive` / `gdrive`
- `rclone`
- URL HTTP(S) como entrada de solo lectura

El origen y el destino pueden utilizar backends distintos.

Ejemplos:

```text
local://C:/Videos/curso.zip -> local://C:/Resultados
C:/Videos/curso.zip -> rclone://resultados
https://example.org/video.zip -> local://C:/Resultados
https://example.org/video.mp4 -> gdrive://CARPETA_ID
rclone://entrada -> local://C:/Resultados
```

Las URL HTTP(S) se materializan en un temporal aislado. Se validan las redirecciones, se rechazan credenciales incrustadas y se bloquean hosts locales o resoluciones a IP no públicas. El destino nunca puede ser HTTP(S).

No se implementa streaming HLS/DASH: el pipeline actual necesita un vídeo o ZIP materializado.

## Entrada local

La entrada puede ser una carpeta, un vídeo individual o un ZIP. El procesamiento directo reutiliza el pipeline de medios existente; no se duplica la lógica entre CLI y GUI.

## Transferencias

Para combinaciones de origen y destino distintos se utiliza un puente de almacenamiento. El origen se descarga a temporales privados y los resultados se suben mediante el backend de destino. El resultado final solo se considera entregado cuando el backend confirma la subida.

Las credenciales se mantienen en los mecanismos existentes y no deben aparecer en URL, logs ni artefactos.

## Rutas

Los vídeos y resultados predeterminados se mantienen separados de los temporales, logs, estado, modelos y secretos privados. La carpeta de instalación no se utiliza como área de trabajo.

## Limitaciones

La validación física de cada backend y arquitectura depende del runner o máquina disponible. Una matriz declarada en CI no constituye por sí sola una prueba de ejecución de todas las arquitecturas.
