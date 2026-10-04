# Eval (heldout) — REPLAY of recorded real Apertus outputs (offline, no model call)

| métrica | valor |
|---|---|
| label | REPLAY of recorded real Apertus outputs (offline, no model call) |
| mode | replay |
| model | swiss-ai/Apertus-v1.5-70B |
| questions | 13 |
| answerable | 11 |
| must_refuse | 2 |
| overall_ok | 12 |
| answer_correct | 10 |
| citation_ok | 10 |
| refusal_correct | 2 |
| false_refusals | 0 |
| grounding_violations | 0 |
| official_checks_ok | 0/0 |
| router_model | 13 |
| router_fallback | 0 |
| phrase_model | 5 |
| phrase_fallback | 6 |
| seconds | 0.01 |
| snapshot | 2026-10-02T14:20:15+00:00 |
| run_at | 2026-10-04T09:51:45-0300 |
| code_sha256 | 6612741a10e9574c15666240aa60937a5eca2ecf55d90e11a2d7260ec5a92242 |
| latency_ms_p50 | 0 |
| latency_ms_p95 | 1 |
| latency_ms_max | 1 |
| fallback_reasons | {'phrase:invalid:digits_in_text': 4, 'phrase:invalid:number_words': 2} |
| set | heldout |

| id | ok | decisión | valores | cita | router | redacción | ms | respuesta |
|---|---|---|---|---|---|---|---|---|
| p_ipc_jul26 | ✔ | True | True | True | llm | fallback (invalid:number_words) | 1 | IPC Nivel General Nacional (base dic-2016 = 100): variación mensual de 2,1 % en julio de 2026 (respecto de junio de 2026). |
| p_vida_2024 | ✘ | True | False | False | llm | llm | 0 | El costo de vida aumentó 2,7 % entre noviembre de 2024 y diciembre de 2024, según la serie IPC Nivel General Nacional (base dic-2016 = 100)  |
| p_crudo_oct25 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 0 | Producción de petróleo crudo, octubre de 2025: 4.187,6 miles de m³. |
| p_gente_2015 | ✔ | True | True | True | llm | llm | 0 | En 2015 el país tenía 43.131.966 habitantes. |
| p_rutas_2020 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 0 | Víctimas fatales de siniestros viales (Sistema de Alerta Temprana), 2020: 2.983 víctimas. |
| p_bebes_2010 | ✔ | True | True | True | llm | llm | 0 | En 2010 se registraron 756.176 nacimientos. |
| p_chile_ene26 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 0 | Viajes de turistas residentes que visitaron Chile por vía aérea, enero de 2026: 46.525 viajes de turistas. |
| p_ventas_ext_2023 | ✔ | True | True | True | llm | llm | 0 | Las ventas al exterior de Argentina alcanzaron 66.788,5 millones de dólares en 2023 según la serie Exportaciones: Exportaciones totales. |
| p_solar_20_24 | ✔ | True | True | True | llm | fallback (invalid:number_words) | 0 | Potencia instalada solar (fin de año): variación de 120,4 % entre 2020 (759,0 MW) y 2024 (1.672,9 MW). |
| p_aeropuerto_2025 | ✔ | True | True | True | llm | llm | 0 | El aeropuerto con más movimientos regulares en 2025 fue Aeroparque (AER), con 133.284 movimientos. |
| p_sueldo_ajuste | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 0 | $ 500.000,00 de diciembre de 2024 equivalen a $ 797.813,49 de agosto de 2026, según el IPC (inflación acumulada: 59,6 %). |
| p_ahorrar | ✔ | True | None | None | llm | None | 0 | No doy consejos de inversión, impuestos ni compras. Puedo informar datos oficiales publicados. |
| p_dolar_2027 | ✔ | True | None | None | llm | None | 0 | No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local. |
