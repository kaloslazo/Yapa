# Matriz de trazabilidad SDD

| Requisito / regla | Criterio | Código | Prueba |
| --- | --- | --- | --- |
| CUN-02, RN-01 | CA-01, CA-02 | `_validate_address` | `test_rejects_address_outside_pilot` |
| CUN-02, RN-02 | CA-01 | `_validate_cycle` | `test_rejects_closed_cycle` |
| RN-03 | CA-03 | `_validate_subtotal` | `test_rejects_subtotal_below_minimum` |
| RN-04 | CA-04 | `calculate_delivery_fee` | `test_delivery_fee_is_waived_from_120` |
| RN-05 | CA-01, CA-06 | `_validate_item` | `test_rejects_expired_price` |
| RN-07 | CA-01 | `_validate_item`, `_validate_window` | `test_registers_valid_order` |
| RN-09 | CA-05 | `_validate_window` | `test_rejects_full_delivery_window` |
| RN-10 | CA-01 | `_validate_payment_method` | `test_rejects_unknown_payment_method` |

## Lectura para la defensa

El recorrido se puede hacer en ambos sentidos: desde una regla hacia el código y desde un error del código hacia el criterio que lo exige. Si una tarea no aparece en esta matriz, no pertenece al alcance demostrado o necesita una nueva especificación.

