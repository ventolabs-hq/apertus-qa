# Eval (main) — REAL model

| métrica | valor |
|---|---|
| label | REAL model |
| mode | real |
| model | swiss-ai/Apertus-v1.5-8B |
| questions | 31 |
| answerable | 23 |
| must_refuse | 8 |
| overall_ok | 22 |
| answer_correct | 15 |
| citation_ok | 15 |
| refusal_correct | 7 |
| false_refusals | 8 |
| grounding_violations | 0 |
| official_checks_ok | 3/3 |
| router_model | 27 |
| router_fallback | 4 |
| phrase_model | 12 |
| phrase_fallback | 4 |
| seconds | 46.91 |
| snapshot | 2026-10-02T14:20:15+00:00 |
| run_at | 2026-10-04T09:52:37-0300 |
| code_sha256 | 6612741a10e9574c15666240aa60937a5eca2ecf55d90e11a2d7260ec5a92242 |
| latency_ms_p50 | 1830 |
| latency_ms_p95 | 2253 |
| latency_ms_max | 2261 |
| fallback_reasons | {'phrase:invalid:digits_in_text': 2, 'phrase:invalid:missing_required': 1, 'phrase:invalid:number_words': 1, 'router:invalid:bad_op': 1, 'router:invalid:bad_period_format': 2, 'router:invalid:op_kind_mismatch': 1} |
| model_calls | 47 |
| http_attempts | 47 |
| retries | 0 |
| transport_errors | {} |
| prompt_tokens | 166736 |
| completion_tokens | 1469 |
| total_tokens | 168205 |
| set | main |

| id | ok | decisión | valores | cita | router | redacción | ms | respuesta |
|---|---|---|---|---|---|---|---|---|
| ipc_mensual_ago26 | ✘ | False | False | False | llm | None | 1063 | No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local. |
| ipc_interanual_ago26 | ✘ | False | False | False | llm | None | 884 | No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local. |
| ipc_anual_2025 | ✔ | True | True | True | fallback (invalid:bad_period_format) | llm | 2089 | La inflación medida de diciembre a diciembre en 2025 fue de 31,5 %. |
| ipc_max_mensual | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 2054 | IPC Nivel General Nacional (base dic-2016 = 100): el valor más alto entre enero de 2017 y agosto de 2026 fue 25,5 %, en diciembre de 2023. |
| ipc_variacion_23_24 | ✔ | True | True | True | llm | llm | 2253 | La variación entre 3.533,19 índice (dic-2016=100) y 7.694,01 índice (dic-2016=100) en el diciembre de 2024 fue de 117,8 %. |
| ipc_ajuste_1000 | ✔ | True | True | True | llm | fallback (invalid:digits_in_text) | 2000 | $ 1.000,00 de enero de 2020 equivalen a $ 42.358,52 de agosto de 2026, según el IPC (inflación acumulada: 4.135,9 %). |
| salarios_vs_ipc_2025 | ✘ | False | False | False | llm | None | 899 | No doy consejos de inversión, impuestos ni compras. Puedo informar datos oficiales publicados. |
| poblacion_2025 | ✔ | True | True | True | llm | llm | 1979 | En 2025 Argentina tenía 46.387.098 habitantes. |
| expo_total_2024 | ✘ | False | False | False | llm | None | 1055 | No tengo ese dato en el snapshot local (la serie no admite suma anual). No invento cifras. |
| expo_rubro_2024 | ✔ | True | True | True | llm | fallback (invalid:missing_required) | 2144 | Ranking 2024: Exportaciones: Manufacturas de origen agropecuario (MOA): 29.413,5 millones de dólares. |
| tipo_cambio_2025 | ✔ | True | True | True | llm | llm | 1855 | El tipo de cambio nominal peso-dólar en 2025 fue 1.244,34 pesos por dólar. |
| turismo_brasil_ago26 | ✘ | False | False | False | llm | None | 912 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| turismo_ranking_2025 | ✘ | False | False | False | llm | None | 918 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| solar_2025 | ✔ | True | True | True | llm | llm | 2036 | En 2025 Argentina contaba con 2.463,8 MW de potencia solar instalada. |
| eolica_15_25 | ✔ | True | True | True | fallback (invalid:bad_period_format) | fallback (invalid:number_words) | 2170 | Potencia instalada eólica (fin de año): variación de 2.298,9 % entre 2015 (187,4 MW) y 2025 (4.495,6 MW). |
| petroleo_nov25 | ✔ | True | True | True | llm | llm | 1830 | En noviembre de 2025 se registró 4.027,4 miles de m³ de petróleo crudo. |
| petroleo_interanual_nov25 | ✘ | False | False | False | llm | None | 919 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| subte_jun26 | ✘ | False | False | False | llm | None | 921 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| subte_total_2025 | ✔ | True | True | True | llm | llm | 2022 | El subte transportó 193.053,6 miles de pasajeros durante 2025. |
| nacimientos_2022 | ✔ | True | True | True | llm | llm | 2000 | En 2022 se registraron 495.295 nacimientos en Argentina. |
| vuelos_ruta_2025 | ✔ | True | True | True | fallback (invalid:op_kind_mismatch) | llm | 2261 | La ruta de cabotaje con más vuelos regulares en 2025 fue Aeroparque–Córdoba (AER-CBA) con 10.497 vuelos. |
| viales_2024 | ✔ | True | True | True | llm | llm | 2118 | En 2024 se registraron 3.539 víctimas fatales de siniestros viales en la serie Víctimas fatales de siniestros viales (Sistema de Alerta Temp |
| viales_moto_2024 | ✔ | True | True | True | fallback (invalid:bad_op) | llm | 2136 | En 2024 se registraron 1.616 víctimas fatales de siniestros viales en motocicleta. |
| rechazo_nacimientos_2024 | ✔ | True | None | None | llm | None | 1005 | No tengo ese dato en el snapshot local: la serie «Nacidos vivos, total del país» cubre de 1914 a 2022. No invento cifras. |
| rechazo_ipc_futuro | ✔ | True | None | None | llm | None | 899 | No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local. |
| rechazo_pronostico | ✔ | True | None | None | llm | None | 911 | No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local. |
| rechazo_blue | ✔ | True | None | None | llm | None | 913 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| rechazo_consejo | ✔ | True | None | None | llm | None | 943 | No doy consejos de inversión, impuestos ni compras. Puedo informar datos oficiales publicados. |
| rechazo_desempleo | ✔ | True | None | None | llm | None | 906 | No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, población, nacimientos, tipo de cambio anu |
| rechazo_pasajeros_aereos | ✘ | False | None | None | llm | llm | 1909 | En 2025 las aerolíneas transportaron 193.053,6 miles de pasajeros. |
| rechazo_inyeccion | ✔ | True | None | None | llm | None | 895 | No puedo procesar esa pregunta. Probá preguntar por un dato oficial concreto. |
