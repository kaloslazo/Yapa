# Iteración 24 · Alta de vecinos y reinicio del PIN

## Requisito

Como administrador de Yapa, quiero dar de alta a un vecino nuevo desde la web, con su consentimiento para usar sus datos, y reiniciarle el PIN si lo olvida, para que el piloto pueda sumar vecinos sin tocar código.

## Por qué

- S-65 (iteración 10) dice que el PIN inicial lo asigna el administrador **al dar de alta al vecino**, pero no hay pantalla para dar de alta. Hoy los vecinos solo existen si están en `seed.py`.
- Si un vecino olvida su PIN, no hay cómo recuperarlo: solo puede cambiarlo quien conoce el actual.
- **Ley 29733 (protección de datos personales):** para guardar el nombre y el celular de una persona hace falta su **consentimiento**, y hay que poder demostrar cuándo se dio.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-133 | El alta la hace el admin con nombre, celular y zona. El vecino da su consentimiento (por ejemplo, por WhatsApp) y el admin lo marca. Se guarda la fecha y hora del consentimiento. Sin consentimiento, no hay alta. | — |
| S-134 | El celular es de Perú: 9 dígitos que empiezan con 9. No se repite entre vecinos. Sirve para que el admin le mande el PIN. | — |
| S-135 | El número de cliente nuevo es el siguiente al más alto que ya existe. | — |
| S-136 | El sistema **genera** el PIN inicial al azar (no lo elige el admin), cumpliendo S-66. Se muestra **una sola vez** para que el admin se lo envíe, y solo se guarda su hash. | — |
| S-137 | Si el vecino olvida su PIN, el admin genera uno nuevo con las mismas reglas. Esto también desbloquea la cuenta si estaba bloqueada por intentos fallidos. | — |
| S-138 | Se da de alta en una zona que ya existe. Si su edificio todavía no tiene zona, el vecino la crea después desde "Mi zona" (iteración 5). | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AV-01 | Solo el admin da de alta y reinicia PIN. | `NOT_AUTHORIZED` (403 en la web) |
| AV-02 | El nombre no está vacío. | `NAME_REQUIRED` |
| AV-03 | El celular tiene 9 dígitos y empieza con 9 (S-134), y no está registrado. | `INVALID_PHONE`, `PHONE_ALREADY_REGISTERED` |
| AV-04 | La zona existe (S-138). | `ZONE_NOT_FOUND` |
| AV-05 | Hay consentimiento; se guarda la fecha y hora (S-133). | `CONSENT_REQUIRED` |
| AV-06 | Se crea el cliente con el siguiente número (S-135) y un PIN generado que cumple S-66 (S-136). | — |
| AV-07 | Reiniciar el PIN de un cliente que existe genera uno nuevo y desbloquea la cuenta (S-137). | `CUSTOMER_NOT_FOUND` |
| AV-08 | `/admin/vecinos` lista a los vecinos (número, nombre, celular, zona, consentimiento) con los formularios de alta y reinicio. El PIN nuevo solo aparece en la respuesta del alta o del reinicio. | — |

## Criterios de aceptación

Base del piloto: clientes 101 a 105. Hora: miércoles 16/09/2026, 10:00.

- **AV-A · Alta.** El admin da de alta a "Lucía Ramos", celular 987654321, zona Z-LINCE-01, con consentimiento → cliente **106**, con celular y hora del consentimiento guardados, y un PIN de 6 dígitos que cumple S-66. Con ese PIN, Lucía entra a la web. → AV-06
- **AV-B · Datos inválidos.** Nombre vacío → `NAME_REQUIRED`; celular `98765432` (8 dígitos) o `887654321` (no empieza con 9) → `INVALID_PHONE`; zona `Z-NO-EXISTE` → `ZONE_NOT_FOUND`; sin consentimiento → `CONSENT_REQUIRED`. En ningún caso se crea el cliente. → AV-02..AV-05
- **AV-C · Celular repetido.** Otro alta con 987654321 → `PHONE_ALREADY_REGISTERED`. → AV-03
- **AV-D · El PIN no queda guardado.** Lo guardado es un hash distinto del PIN, y la lista de `/admin/vecinos` no muestra el PIN. → S-136
- **AV-E · Reiniciar el PIN.** Lucía se equivoca 5 veces y su cuenta se bloquea. El admin reinicia su PIN → con el nuevo entra enseguida, y con el anterior ya no. Reiniciar el PIN del cliente 999 → `CUSTOMER_NOT_FOUND`. → AV-07, S-137
- **AV-F · Solo el admin.** Un vecino que abre `/admin/vecinos` o envía el alta recibe 403. → AV-01
- **AV-G · Web.** Desde `/admin/vecinos`, el alta responde con "Cliente 106" y el PIN para enviar, y la lista muestra a Lucía con su celular. → AV-08
