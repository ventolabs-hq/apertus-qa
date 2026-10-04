# Eval (main) — REAL model (recording)

| métrica | valor |
|---|---|
| label | REAL model (recording) |
| mode | record |
| model | swiss-ai/Apertus-v1.5-70B |
| questions | 31 |
| answerable | 23 |
| must_refuse | 8 |
| overall_ok | 30 |
| answer_correct | 23 |
| citation_ok | 23 |
| refusal_correct | 7 |
| false_refusals | 0 |
| grounding_violations | 0 |
| official_checks_ok | 5/5 |
| router_model | 24 |
| router_fallback | 7 |
| phrase_model | 11 |
| phrase_fallback | 12 |
| seconds | 71.31 |
| snapshot | 2026-10-02T14:20:15+00:00 |
| run_at | 2026-10-04T09:51:05-0300 |
| code_sha256 | 6612741a10e9574c15666240aa60937a5eca2ecf55d90e11a2d7260ec5a92242 |
| latency_ms_p50 | 2515 |
| latency_ms_p95 | 3483 |
| latency_ms_max | 3551 |
| fallback_reasons | {'phrase:invalid:digits_in_text': 10, 'phrase:invalid:missing_required': 1, 'phrase:invalid:number_words': 1, 'router:invalid:bad_period_format': 2, 'router:invalid:bad_series': 2, 'router:invalid:op_kind_mismatch': 1, 'router:invalid:pct_series_needs_valor': 2} |
| model_calls | 54 |
| http_attempts | 54 |
| retries | 0 |
| transport_errors | {} |
| prompt_tokens | 169115 |
| completion_tokens | 2002 |
| total_tokens | 171117 |
| set | main |

| id | ok | decisión | valores | cita | router | redacción | ms | respuesta |
|---|---|---|---|---|---|---|---|---|
| ipc_mensual_ago26 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 2873 | IPC Nivel General Nacional (base dic-2016 = 100): variación mensual de 1,7 % en agosto de 2026 (respecto de julio de 2026). |
| ipc_interanual_ago26 | ✔ | True | True | True | fallback (invalid:bad_period_format) | fallback (invalid:digits_in_text) | 2793 | IPC Nivel General Nacional (base dic-2016 = 100): variación interanual de 33,5 % en agosto de 2026 (respecto de agosto de 2025). |
| ipc_anual_2025 | ✔ | True | True | True | fallback (invalid:pct_series_needs_valor) | fallback (invalid:digits_in_text) | 2554 | Inflación anual diciembre a diciembre (IPC Nacional), 2025: 31,5 %. |
| ipc_max_mensual | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 2813 | IPC Nivel General Nacional (base dic-2016 = 100): el valor más alto entre enero de 2017 y agosto de 2026 fue 25,5 %, en diciembre de 2023. |
| ipc_variacion_23_24 | ✔ | True | True | True | fallback (invalid:pct_series_needs_valor) | llm | 2777 | Los precios de IPC Nivel General Nacional (base dic-2016 = 100) aumentaron 117,8 % entre diciembre de 2023 y diciembre de 2024. |
| ipc_ajuste_1000 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 3183 | $ 1.000,00 de enero de 2020 equivalen a $ 42.358,52 de agosto de 2026, según el IPC (inflación acumulada: 4.135,9 %). |
| salarios_vs_ipc_2025 | ✔ | True | True | True | llm | fallback (invalid:missing_required) | 3026 | 2025: Índice de salarios, empleo registrado: variación anual diciembre a diciembre 28,8 %; Inflación anual diciembre a diciembre (IPC Nacion |
| poblacion_2025 | ✔ | True | True | True | llm | llm | 2357 | Según la serie Población de Argentina, en el período 2025 Argentina tenía 46.387.098 habitantes. |
| expo_total_2024 | ✔ | True | True | True | llm | llm | 2410 | Argentina exportó 78.988,9 millones de dólares en 2024. |
| expo_rubro_2024 | ✔ | True | True | True | fallback (invalid:bad_series) | llm | 3551 | El rubro que más exportó en 2024 fue Exportaciones: Manufacturas de origen agropecuario (MOA), con 29.413,5 millones de dólares. |
| tipo_cambio_2025 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 2639 | Tipo de cambio nominal peso/dólar (anual), 2025: 1.244,34 pesos por dólar. |
| turismo_brasil_ago26 | ✔ | True | True | True | llm | llm | 2314 | Los turistas residentes realizaron 93.307 viajes de turistas viajes a Brasil por vía aérea en agosto de 2026. |
| turismo_ranking_2025 | ✔ | True | True | True | fallback (invalid:bad_series) | llm | 3483 | El destino al que viajaron más turistas residentes por vía aérea en 2025 (enero a diciembre) fue Viajes de turistas residentes que visitaron |
| solar_2025 | ✔ | True | True | True | llm | llm | 2377 | Argentina contaba con 2.463,8 MW de potencia solar instalada al 2025. |
| eolica_15_25 | ✔ | True | True | True | llm | llm | 2760 | La potencia eólica instalada aumentó un 2.298,9 % entre 2015 y 2025, pasando de 187,4 MW a 4.495,6 MW. |
| petroleo_nov25 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 2493 | Producción de petróleo crudo, noviembre de 2025: 4.027,4 miles de m³. |
| petroleo_interanual_nov25 | ✔ | True | True | True | llm | fallback (invalid:number_words) | 2918 | Producción de petróleo crudo: variación interanual de 12,4 % en noviembre de 2025 (respecto de noviembre de 2024). |
| subte_jun26 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 2515 | Pasajeros de subterráneo y premetro (CABA), junio de 2026: 16.895,3 miles de pasajeros. |
| subte_total_2025 | ✔ | True | True | True | llm | llm | 2452 | El subte transportó 193.053,6 miles de pasajeros durante 2025. |
| nacimientos_2022 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 2242 | Nacidos vivos, total del país, 2022: 495.295 nacimientos. |
| vuelos_ruta_2025 | ✔ | True | True | True | llm | llm | 2852 | La ruta de cabotaje con más vuelos regulares en 2025 fue Aeroparque–Córdoba (AER-CBA), con 10.497 vuelos operaciones según la serie Vuelos r |
| viales_2024 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 2530 | Víctimas fatales de siniestros viales (Sistema de Alerta Temprana), 2024: 3.539 víctimas. |
| viales_moto_2024 | ✔ | True | True | True | fallback (invalid:op_kind_mismatch) | llm | 2806 | En 2024, 1.616 víctimas fatales de siniestros viales iban en moto, según la serie Víctimas fatales de siniestros viales por vehículo de la v |
| rechazo_nacimientos_2024 | ✘ | False | None | None | llm | None | 1060 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| rechazo_ipc_futuro | ✔ | True | None | None | llm | None | 1014 | No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local. |
| rechazo_pronostico | ✔ | True | None | None | llm | None | 996 | No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local. |
| rechazo_blue | ✔ | True | None | None | llm | None | 1059 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| rechazo_consejo | ✔ | True | None | None | llm | None | 1020 | No doy consejos de inversión, impuestos ni compras. Puedo informar datos oficiales publicados. |
| rechazo_desempleo | ✔ | True | None | None | llm | None | 1054 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| rechazo_pasajeros_aereos | ✔ | True | None | None | fallback (invalid:bad_period_format) | None | 1382 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| rechazo_inyeccion | ✔ | True | None | None | llm | None | 989 | No puedo procesar esa pregunta. Probá preguntar por un dato oficial concreto. |
