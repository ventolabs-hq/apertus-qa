# Eval (heldout) — REAL model

| métrica | valor |
|---|---|
| label | REAL model |
| mode | real |
| model | swiss-ai/Apertus-v1.5-8B |
| questions | 13 |
| answerable | 11 |
| must_refuse | 2 |
| overall_ok | 9 |
| answer_correct | 7 |
| citation_ok | 7 |
| refusal_correct | 2 |
| false_refusals | 4 |
| grounding_violations | 0 |
| official_checks_ok | 0/0 |
| router_model | 11 |
| router_fallback | 2 |
| phrase_model | 5 |
| phrase_fallback | 2 |
| seconds | 29.59 |
| snapshot | 2026-10-02T14:20:15+00:00 |
| run_at | 2026-10-04T09:53:07-0300 |
| code_sha256 | 6612741a10e9574c15666240aa60937a5eca2ecf55d90e11a2d7260ec5a92242 |
| latency_ms_p50 | 2006 |
| latency_ms_p95 | 4141 |
| latency_ms_max | 4141 |
| fallback_reasons | {'phrase:invalid:digits_in_text': 1, 'phrase:invalid:missing_required': 1, 'router:invalid:bad_period_format': 2} |
| model_calls | 20 |
| http_attempts | 20 |
| retries | 0 |
| transport_errors | {} |
| prompt_tokens | 70109 |
| completion_tokens | 632 |
| total_tokens | 70741 |
| set | heldout |

| id | ok | decisión | valores | cita | router | redacción | ms | respuesta |
|---|---|---|---|---|---|---|---|---|
| p_ipc_jul26 | ✘ | False | False | False | llm | None | 939 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| p_vida_2024 | ✘ | False | False | False | fallback (invalid:bad_period_format) | None | 1100 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| p_crudo_oct25 | ✔ | True | True | True | llm | llm | 1855 | La producción de crudo en octubre del octubre de 2025 fue de 4.187,6 miles de m³. |
| p_gente_2015 | ✔ | True | True | True | llm | llm | 2006 | En 2015 la población del país fue de 43.131.966 habitantes. |
| p_rutas_2020 | ✔ | True | True | True | llm | llm | 2082 | En 2020 se registraron 2.983 víctimas en siniestros de tránsito. |
| p_bebes_2010 | ✔ | True | True | True | llm | llm | 1787 | En 2010 se registraron 756.176 nacimientos |
| p_chile_ene26 | ✘ | False | False | False | llm | None | 2018 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| p_ventas_ext_2023 | ✘ | False | False | False | llm | None | 2533 | No tengo ese dato en el snapshot local (la serie no admite suma anual). No invento cifras. |
| p_solar_20_24 | ✔ | True | True | True | fallback (invalid:bad_period_format) | llm | 4032 | La variación entre 759,0 MW y 1.672,9 MW en el 2024 fue 120,4 %. |
| p_aeropuerto_2025 | ✔ | True | True | True | llm | fallback (invalid:missing_required) | 4120 | Movimientos regulares (aterrizajes + despegues) por aeropuerto, 2025: Aeroparque (AER) 133.284 movimientos; Ezeiza (EZE) 69.901 movimientos; |
| p_sueldo_ajuste | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 4141 | $ 500.000,00 de diciembre de 2024 equivalen a $ 797.813,49 de agosto de 2026, según el IPC (inflación acumulada: 59,6 %). |
| p_ahorrar | ✔ | True | None | None | llm | None | 1363 | No doy consejos de inversión, impuestos ni compras. Puedo informar datos oficiales publicados. |
| p_dolar_2027 | ✔ | True | None | None | llm | None | 1611 | No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local. |
