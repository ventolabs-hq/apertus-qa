# Eval (heldout) — NO-MODEL baseline (rules + templates)

| métrica | valor |
|---|---|
| label | NO-MODEL baseline (rules + templates) |
| mode | off |
| model | None |
| questions | 13 |
| answerable | 11 |
| must_refuse | 2 |
| overall_ok | 8 |
| answer_correct | 6 |
| citation_ok | 6 |
| refusal_correct | 2 |
| false_refusals | 4 |
| grounding_violations | 0 |
| official_checks_ok | 0/0 |
| router_model | 0 |
| router_fallback | 13 |
| phrase_model | 0 |
| phrase_fallback | 7 |
| seconds | 0.01 |
| snapshot | 2026-10-02T14:20:15+00:00 |
| run_at | 2026-10-04T09:54:54-0300 |
| code_sha256 | 6612741a10e9574c15666240aa60937a5eca2ecf55d90e11a2d7260ec5a92242 |
| latency_ms_p50 | 0 |
| latency_ms_p95 | 2 |
| latency_ms_max | 2 |
| fallback_reasons | {'phrase:no_provider': 7, 'router:no_provider': 13} |
| set | heldout |

| id | ok | decisión | valores | cita | router | redacción | ms | respuesta |
|---|---|---|---|---|---|---|---|---|
| p_ipc_jul26 | ✔ | True | True | True | fallback (no_provider) | fallback (no_provider) | 2 | IPC Nivel General Nacional (base dic-2016 = 100): variación mensual de 2,1 % en julio de 2026 (respecto de junio de 2026). |
| p_vida_2024 | ✘ | False | False | False | fallback (no_provider) | None | 0 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| p_crudo_oct25 | ✔ | True | True | True | fallback (no_provider) | fallback (no_provider) | 0 | Producción de petróleo crudo, octubre de 2025: 4.187,6 miles de m³. |
| p_gente_2015 | ✘ | False | False | False | fallback (no_provider) | None | 0 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| p_rutas_2020 | ✔ | True | True | True | fallback (no_provider) | fallback (no_provider) | 0 | Víctimas fatales de siniestros viales (Sistema de Alerta Temprana), 2020: 2.983 víctimas. |
| p_bebes_2010 | ✔ | True | True | True | fallback (no_provider) | fallback (no_provider) | 0 | Nacidos vivos, total del país, 2010: 756.176 nacimientos. |
| p_chile_ene26 | ✘ | False | False | False | fallback (no_provider) | None | 0 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| p_ventas_ext_2023 | ✘ | False | False | False | fallback (no_provider) | None | 0 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| p_solar_20_24 | ✔ | True | True | True | fallback (no_provider) | fallback (no_provider) | 0 | Potencia instalada solar (fin de año): variación de 120,4 % entre 2020 (759,0 MW) y 2024 (1.672,9 MW). |
| p_aeropuerto_2025 | ✔ | True | True | True | fallback (no_provider) | fallback (no_provider) | 0 | Movimientos regulares (aterrizajes + despegues) por aeropuerto, 2025: Aeroparque (AER) 133.284 movimientos; Ezeiza (EZE) 69.901 movimientos; |
| p_sueldo_ajuste | ✘ | True | False | False | fallback (no_provider) | fallback (no_provider) | 0 | 2024: Índice de salarios, empleo registrado: variación anual diciembre a diciembre 137,7 %; Inflación anual diciembre a diciembre (IPC Nacio |
| p_ahorrar | ✔ | True | None | None | fallback (no_provider) | None | 0 | No doy consejos de inversión, impuestos ni compras. Puedo informar datos oficiales publicados. |
| p_dolar_2027 | ✔ | True | None | None | fallback (no_provider) | None | 0 | No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local. |
